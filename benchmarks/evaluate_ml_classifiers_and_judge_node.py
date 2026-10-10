import asyncio
import json
import os
import re

import evaluate
import numpy as np
import pandas as pd
from datasets import load_from_disk
from langchain_core.messages import HumanMessage
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

from src.application.decision_maker import DecisionMaker
from src.application.graphs.Nodes import judge_and_extract_entities
from src.config.Constant import INTENT_LABELS, SENTIMENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents
from src.config.settings import settings
from src.infrastructure.ai_models.llm_proxy import LLMProxy

decision_maker = DecisionMaker()

llm_proxy = LLMProxy(
    primary_provider="google_gemini",
    fallback_provider="cohere",
    primary_api_key=settings.gemini_api_key,
    fallback_api_key=settings.cohere_api_key,
    temperature=0.0,
)

eval_judge_extract = judge_and_extract_entities(decision_maker, llm_proxy)


root_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(root_dir, "metrics", "evaluate_ml_classifiers_and_judge_node.json")
eval_data_path = os.path.join(root_dir, "Synthetic_Evaluation_Data")

acc = evaluate.load("accuracy")
precision = evaluate.load("precision")
recall = evaluate.load("recall")
f1 = evaluate.load("f1")

intents = list(Meta_Data_Intents.keys())

intent_model = ORTModelForSequenceClassification.from_pretrained(
    os.path.join(root_dir, "onnx_intent_model"), file_name="model_quantized.onnx", local_files_only=True
)
intent_tokenizer = AutoTokenizer.from_pretrained(os.path.join(root_dir, "onnx_intent_model"))


sentiment_model = ORTModelForSequenceClassification.from_pretrained(
    os.path.join(root_dir, "onnx_sentiment_model"), file_name="sentiment_quantized_onnx.onnx", local_files_only=True
)
sentiment_tokenizer = AutoTokenizer.from_pretrained("FacebookAI/roberta-base")


def make_prediction(data, model, tokenizer):
    if not data:
        return []
    tokens = tokenizer(
        data,
        return_tensors="np",
        padding=True,
        truncation=True,
        max_length=128,
    )

    tokens = {key: np.int64(value) for key, value in tokens.items()}
    outputs = model(**tokens)
    logits = outputs.logits

    exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))

    probabilities = exp_logits / exp_logits.sum()

    indices = np.argmax(probabilities, axis=-1)

    return indices.tolist()


def calc_metrics(preds, refs):
    return {
        "accuracy": acc.compute(predictions=preds, references=refs)["accuracy"],
        "precision": precision.compute(predictions=preds, references=refs, average="macro")["precision"],
        "recall": recall.compute(predictions=preds, references=refs, average="macro")["recall"],
        "f1": f1.compute(predictions=preds, references=refs, average="macro")["f1"],
    }


# These fields have deterministic, structured values. Normalising display
# formats avoids counting the same identifier/rating as an error solely because
# the judge used Arabic-Indic digits or wrote e.g. "5 نجوم" instead of 5.
STRUCTURED_ENTITY_FIELDS = {"order_id", "refund_id_or_order_id", "rating"}
_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize_structured_entity_value(key, value):
    """Return a canonical value for the structured entity fields under test."""
    text = str(value).strip().translate(_DIGIT_TRANSLATION).casefold()

    if key in {"order_id", "refund_id_or_order_id"}:
        return re.sub(r"[\s#]", "", text)

    if key == "rating":
        match = re.search(r"\d+", text)
        if match:
            rating = int(match.group())
            if 1 <= rating <= 5:
                return rating

    return text


sent_to_int = {key: val for val, key in SENTIMENT_LABELS.items()}


all_en_intent_preds = []
all_en_intent_gt = []
all_eg_intent_preds = []
all_eg_intent_gt = []

# Pooled arrays for sentiment classification
all_en_sent_preds = []
all_en_sent_gt = []
all_eg_sent_preds = []
all_eg_sent_gt = []

# Per-intent accuracy (only metric that makes sense per-folder)
per_intent_accuracy = {}

print(f"Evaluating {len(intents)} intents...")

all_dataset = []

for ind, intent in enumerate(intents):
    intent_path = os.path.join(eval_data_path, intent)
    intent_data = load_from_disk(intent_path)

    egypt_data = intent_data.filter(lambda x: x["language"] == "Egyptian Arabic")
    english_data = intent_data.filter(lambda x: x["language"] == "English")

    pd_egypt = egypt_data.to_pandas()

    pd_en = english_data.to_pandas()

    df = pd.concat([pd_egypt, pd_en], axis=0, ignore_index=True)

    egypt_queries = [row for row in egypt_data["query"]]
    en_queries = [row for row in english_data["query"]]

    eg_intent_pred = make_prediction(egypt_queries, intent_model, intent_tokenizer)
    eg_sentiment_pred = make_prediction(egypt_queries, sentiment_model, sentiment_tokenizer)

    en_intent_pred = make_prediction(en_queries, intent_model, intent_tokenizer)
    en_sentiment_pred = make_prediction(en_queries, sentiment_model, sentiment_tokenizer)

    group_predicted_intent = []

    group_predicted_intent.extend(eg_intent_pred)
    group_predicted_intent.extend(en_intent_pred)

    group_predicted_sentiment = []

    group_predicted_sentiment.extend(eg_sentiment_pred)
    group_predicted_sentiment.extend(en_sentiment_pred)

    df["predicted_intent_by_ml"] = group_predicted_intent

    df["predicted_sentiment_by_ml"] = group_predicted_sentiment

    all_dataset.append(df)

    # Ground Truths
    eg_intent_gt = [ind] * len(egypt_queries)
    en_intent_gt = [ind] * len(en_queries)

    eg_sent_gt = [sent_to_int.get(sent) for sent in egypt_data["sentiment"]]
    en_sent_gt = [sent_to_int.get(sent) for sent in english_data["sentiment"]]

    # Pool into global arrays
    all_en_intent_preds.extend(en_intent_pred)
    all_en_intent_gt.extend(en_intent_gt)
    all_eg_intent_preds.extend(eg_intent_pred)
    all_eg_intent_gt.extend(eg_intent_gt)

    all_en_sent_preds.extend(en_sentiment_pred)
    all_en_sent_gt.extend(en_sent_gt)
    all_eg_sent_preds.extend(eg_sentiment_pred)
    all_eg_sent_gt.extend(eg_sent_gt)

    # Per-intent accuracy (the only metric that is valid per-folder)
    en_correct = sum(1 for p, g in zip(en_intent_pred, en_intent_gt) if p == g)
    eg_correct = sum(1 for p, g in zip(eg_intent_pred, eg_intent_gt) if p == g)

    per_intent_accuracy[intent] = {
        "english_accuracy": en_correct / len(en_queries) if en_queries else 0.0,
        "arabic_accuracy": eg_correct / len(egypt_queries) if egypt_queries else 0.0,
        "english_samples": len(en_queries),
        "arabic_samples": len(egypt_queries),
    }

    print(
        f"  [{ind + 1}/{len(intents)}] {intent}: "
        f"EN acc={per_intent_accuracy[intent]['english_accuracy']:.2f},"
        f"AR acc={per_intent_accuracy[intent]['arabic_accuracy']:.2f}"
    )


# ──────────────────────────────────────────────────────────────────────
#  Phase 2: Compute global metrics from pooled arrays
# ──────────────────────────────────────────────────────────────────────

print(
    f"\nComputing global metrics across {len(all_en_intent_preds)} English + "
    f"{len(all_eg_intent_preds)} Arabic samples..."
)

en_intent_metrics = calc_metrics(all_en_intent_preds, all_en_intent_gt)
eg_intent_metrics = calc_metrics(all_eg_intent_preds, all_eg_intent_gt)

en_sent_metrics = calc_metrics(all_en_sent_preds, all_en_sent_gt)
eg_sent_metrics = calc_metrics(all_eg_sent_preds, all_eg_sent_gt)


async def execute_node(example):
    state = {
        "user_query": example["query"],
        "predicted_intent": INTENT_LABELS.get(example["predicted_intent_by_ml"], "needing guidance"),
        "predicted_sentiment": SENTIMENT_LABELS.get(example["predicted_sentiment_by_ml"], "neutral"),
        "num_of_mis_understanding": 0,
        "messages": [HumanMessage(content=example["query"])],
    }

    config = {"configurable": {"thread_id": "evaluate"}}
    try:
        node_out = await eval_judge_extract(state, config)

        example["intent_by_judge"] = node_out.get("final_intent")
        example["sentiment_by_judge"] = node_out.get("final_sentiment")
        example["extracted_entities_by_judge"] = node_out.get("extracted_entities")
        example["action"] = node_out.get("action")

    except Exception as e:
        print(f"  ⚠️ Judge failed for query: {example['query'][:50]}... Error: {e}")
        example["intent_by_judge"] = None
        example["sentiment_by_judge"] = None
        example["extracted_entities_by_judge"] = None
        example["action"] = None

    return example


async def run_judge_evaluation(df):
    """Run judge node on all rows sequentially (async but one at a time to respect API rate limits)."""
    results = []
    total = len(df)
    for idx, (_, row) in enumerate(df.iterrows()):
        print(f"  [{idx + 1}/{total}] Processing: {row['query'][:60]}...")
        result = await execute_node(row.to_dict())
        results.append(result)
    return pd.DataFrame(results)


final_df = pd.concat(all_dataset, axis=0, ignore_index=True)

print(f"\n🔄 Running judge node on {len(final_df)} samples...")
final_df = asyncio.run(run_judge_evaluation(final_df))

final_df.to_csv("all_evaluation_dataset.csv")
print("📁 Saved evaluation dataset to all_evaluation_dataset.csv")

# ──────────────────────────────────────────────────────────────────────
#  Phase 2.5: Compute Judge Node Metrics (Task 4.2)
# ──────────────────────────────────────────────────────────────────────

print("\n📊 Computing judge evaluation metrics...")

valid_judge_df = final_df[final_df["intent_by_judge"].notna()].copy()
total_valid = len(valid_judge_df)
total_failed = len(final_df) - total_valid

print(f"  Valid judge responses: {total_valid}/{len(final_df)} (failed: {total_failed})")

judge_metrics = {}

if total_valid > 0:
    valid_judge_df["ml_intent_label"] = valid_judge_df["predicted_intent_by_ml"].map(INTENT_LABELS)

    # Metric 1: joint_correct_rate (given both correct)
    # How often ML and Judge BOTH agree AND BOTH match ground truth.
    # HIGH = ML is already strong, judge just confirms = judge adds little value
    # LOW  = they rarely both get it right = judge's corrective role is justified
    both_correct = (
        (valid_judge_df["ml_intent_label"] == valid_judge_df["intent"])
        & (valid_judge_df["intent_by_judge"] == valid_judge_df["intent"])
    ).sum()
    joint_correct_rate = both_correct / total_valid

    # Metric 2: Override Precision
    # When judge DISAGREES with ML, how often is the judge correct vs ground truth?
    # HIGH = judge accurate when it intervenes
    # LOW  = judge overrides but gets it wrong
    overrides_df = valid_judge_df[valid_judge_df["ml_intent_label"] != valid_judge_df["intent_by_judge"]]
    total_overrides = len(overrides_df)

    if total_overrides > 0:
        correct_overrides = (overrides_df["intent_by_judge"] == overrides_df["intent"]).sum()
        override_precision = correct_overrides / total_overrides
    else:
        correct_overrides = 0
        override_precision = 0.0

    # Metric 3: structured entity-value extraction F1.
    # A true positive requires both the entity key and its value to match.
    # Keep a strict score as an audit baseline and a canonical score for
    # equivalent numeric representations across English and Arabic.
    strict_tp = strict_fp = strict_fn = 0
    normalized_tp = normalized_fp = normalized_fn = 0

    for _, row in valid_judge_df.iterrows():
        gt_entities = row.get("entities")
        judge_entities = row.get("extracted_entities_by_judge")

        if isinstance(gt_entities, str):
            try:
                gt_entities = json.loads(gt_entities.replace("'", '"'))
            except (json.JSONDecodeError, ValueError):
                gt_entities = {}
        if isinstance(judge_entities, str):
            try:
                judge_entities = json.loads(judge_entities.replace("'", '"'))
            except (json.JSONDecodeError, ValueError):
                judge_entities = {}

        if not isinstance(gt_entities, dict):
            gt_entities = {}
        if not isinstance(judge_entities, dict):
            judge_entities = {}
        strict_ground_truth_pairs = {
            (key, value) for key, value in gt_entities.items() if key in STRUCTURED_ENTITY_FIELDS
        }

        strict_judge_pairs = {(key, value) for key, value in judge_entities.items() if key in STRUCTURED_ENTITY_FIELDS}

        normalized_ground_truth_pairs = {
            (key, normalize_structured_entity_value(key, value))
            for key, value in gt_entities.items()
            if key in STRUCTURED_ENTITY_FIELDS
        }

        normalized_judge_pairs = {
            (key, normalize_structured_entity_value(key, value))
            for key, value in judge_entities.items()
            if key in STRUCTURED_ENTITY_FIELDS
        }

        strict_tp += len(strict_judge_pairs & strict_ground_truth_pairs)
        strict_fp += len(strict_judge_pairs - strict_ground_truth_pairs)
        strict_fn += len(strict_ground_truth_pairs - strict_judge_pairs)

        normalized_tp += len(normalized_judge_pairs & normalized_ground_truth_pairs)
        normalized_fp += len(normalized_judge_pairs - normalized_ground_truth_pairs)
        normalized_fn += len(normalized_ground_truth_pairs - normalized_judge_pairs)

    strict_precision = strict_tp / (strict_tp + strict_fp) if (strict_tp + strict_fp) else 0.0
    strict_recall = strict_tp / (strict_tp + strict_fn) if (strict_tp + strict_fn) else 0.0
    strict_entity_f1 = (
        2 * strict_precision * strict_recall / (strict_precision + strict_recall)
        if (strict_precision + strict_recall)
        else 0.0
    )

    normalized_precision = normalized_tp / (normalized_tp + normalized_fp) if (normalized_tp + normalized_fp) else 0.0
    normalized_recall = normalized_tp / (normalized_tp + normalized_fn) if (normalized_tp + normalized_fn) else 0.0
    normalized_entity_f1 = (
        2 * normalized_precision * normalized_recall / (normalized_precision + normalized_recall)
        if (normalized_precision + normalized_recall)
        else 0.0
    )

    judge_metrics = {
        "total_samples_evaluated": total_valid,
        "total_api_failures": total_failed,
        "joint_correct_rate": joint_correct_rate,
        "total_overrides": int(total_overrides),
        "correct_overrides": int(correct_overrides),
        "override_precision": override_precision,
        "structured_entity_value_fields": sorted(STRUCTURED_ENTITY_FIELDS),
        "strict_entity_value_extraction_f1": strict_entity_f1,
        "strict_entity_value_counts": {
            "true_positives": strict_tp,
            "false_positives": strict_fp,
            "false_negatives": strict_fn,
        },
        "normalized_structured_entity_value_f1": normalized_entity_f1,
        "normalized_structured_entity_value_counts": {
            "true_positives": normalized_tp,
            "false_positives": normalized_fp,
            "false_negatives": normalized_fn,
        },
    }

    print(f"  Joint Correct Rate: {joint_correct_rate:.4f}")
    print(f"  Override Precision: {override_precision:.4f} ({correct_overrides}/{total_overrides} correct)")
    print(f"  Strict Entity-Value F1: {strict_entity_f1:.4f}")
    print(f"  Normalized Structured Entity-Value F1: {normalized_entity_f1:.4f}")

else:
    print("  ⚠️ No valid judge responses — all API calls failed.")
    judge_metrics = {"error": "All API calls failed. No judge metrics computed."}


# ──────────────────────────────────────────────────────────────────────
#  Phase 3: Structure and save results
# ──────────────────────────────────────────────────────────────────────

data_metrics = {
    "intent_classification": {
        "english": {
            "overall_accuracy": en_intent_metrics["accuracy"],
            "macro_precision": en_intent_metrics["precision"],
            "macro_recall": en_intent_metrics["recall"],
            "macro_f1": en_intent_metrics["f1"],
            "total_samples": len(all_en_intent_preds),
            "per_intent_accuracy": {
                intent: details["english_accuracy"] for intent, details in per_intent_accuracy.items()
            },
        },
        "arabic": {
            "overall_accuracy": eg_intent_metrics["accuracy"],
            "macro_precision": eg_intent_metrics["precision"],
            "macro_recall": eg_intent_metrics["recall"],
            "macro_f1": eg_intent_metrics["f1"],
            "total_samples": len(all_eg_intent_preds),
            "per_intent_accuracy": {
                intent: details["arabic_accuracy"] for intent, details in per_intent_accuracy.items()
            },
        },
    },
    "sentiment_classification": {
        "english": {
            "overall_accuracy": en_sent_metrics["accuracy"],
            "macro_precision": en_sent_metrics["precision"],
            "macro_recall": en_sent_metrics["recall"],
            "macro_f1": en_sent_metrics["f1"],
            "total_samples": len(all_en_sent_preds),
        },
        "arabic": {
            "overall_accuracy": eg_sent_metrics["accuracy"],
            "macro_precision": eg_sent_metrics["precision"],
            "macro_recall": eg_sent_metrics["recall"],
            "macro_f1": eg_sent_metrics["f1"],
            "total_samples": len(all_eg_sent_preds),
        },
    },
    "judge_node_evaluation": judge_metrics,
}

os.makedirs(os.path.dirname(file_path), exist_ok=True)
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data_metrics, f, indent=4, ensure_ascii=False)

print(f"\n✅ Evaluation completed successfully and saved to {file_path}")
