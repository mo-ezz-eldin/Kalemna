import torch
import numpy as np
from sklearn.metrics import accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.onnxruntime import ORTModelForSequenceClassification
from tqdm import tqdm
import json
import os


root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

folder_path = os.path.join(root_dir, "metrics")
file_path = os.path.join(folder_path, "benchmark_accuracy_against_quantized_sentiment_model_vs_onnx_model.json")

print("Loading Models... ⏳")
tokenizer = AutoTokenizer.from_pretrained("FacebookAI/roberta-base")


pytorch_model = AutoModelForSequenceClassification.from_pretrained(
    r'D:\PycharmProjects\JupyterProject\models\sentiment-analysis-model')
pytorch_model.eval()

# ONNX O2 Model
onnx_model = ORTModelForSequenceClassification.from_pretrained(r"./onnx_sentiment_model")

# Quantized ONNX Model
onnx_model_quantized = ORTModelForSequenceClassification.from_pretrained(
    r"./onnx_sentiment_model",
    file_name="sentiment_quantized_onnx.onnx"
)

print("Loading Edge Cases Dataset... 📚")

sentiment_data_mapping = {
    0: [  # anger (Frustration, passive-aggressive, demanding)
        "I've asked three times already, fix this or I'm taking legal action.",
        "Stop giving me automated garbage responses and put a human on the line!",
        "Your system completely ruined my presentation today, totally unacceptable."
    ],
    1: [  # disgust (Revulsion, extreme disapproval of quality/behavior)
        "The food arrived cold, greasy, and honestly looked revolting.",
        "The customer service representative was condescending and completely toxic.",
        "The quality of this plastic feels cheap, dirty, and dangerous for kids."
    ],
    2: [  # fear (Anxiety, concern about security/privacy, uncertainty)
        "I got an alert that my account was accessed from abroad, am I hacked?",
        "I'm terrified my credit card details were exposed in your data leak.",
        "If this package doesn't arrive by tomorrow, I'm going to fail my class."
    ],
    3: [  # joy (Enthusiasm, delight, high praise, relief)
        "Honestly blown away by how fast this arrived, absolutely made my day!",
        "This is hands down the best customer experience I've had all year.",
        "So thrilled with the new update, everything works seamlessly now!"
    ],
    4: [  # neutral (Factual inquiries, status updates, matter-of-fact statements)
        "My order number is 88219 and I would like to check the invoice status.",
        "Does the subscription auto-renew at the end of the billing cycle?",
        "The package arrived at 3 PM yesterday as scheduled."
    ],
    5: [  # sadness (Disappointment, feeling let down, regret)
        "I was so excited for this gift, but it arrived broken and useless.",
        "It really hurts to see how degraded your service has become over the years.",
        "I guess my money is lost now, really disappointed with this experience."
    ],
    6: [  # surprise (Shock, unexpected outcomes, astonishment)
        "Wait, I didn't expect a full refund in less than 5 minutes!",
        "Out of nowhere the package showed up today, thought it was delayed!",
        "I was completely shocked when the app suddenly changed its whole layout."
    ]
}

test_texts = []
true_labels = []

for label, sentences in sentiment_data_mapping.items():
    for text in sentences:
        test_texts.append(text)
        true_labels.append(label)

# --- 3. Evaluation Loop ---
pt_preds = []
onnx_preds = []
quant_preds = []

print(f"Starting Evaluation on {len(test_texts)} Edge Cases... 🚀")
for text in tqdm(test_texts):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)


    with torch.no_grad():
        pt_outputs = pytorch_model(**inputs)
        pt_pred = torch.argmax(pt_outputs.logits, dim=-1).item()
        pt_preds.append(pt_pred)

    # 2. ONNX O2 Prediction
    onnx_outputs = onnx_model(**inputs)
    onnx_pred = np.argmax(onnx_outputs.logits, axis=-1)[0]
    onnx_preds.append(onnx_pred)

    # 3. Quantized ONNX Prediction
    quant_outputs = onnx_model_quantized(**inputs)
    quant_pred = np.argmax(quant_outputs.logits, axis=-1)[0]
    quant_preds.append(quant_pred)

# --- 4. Calculate Metrics ---
pt_acc = accuracy_score(true_labels, pt_preds)
onnx_acc = accuracy_score(true_labels, onnx_preds)
quant_acc = accuracy_score(true_labels, quant_preds)

fidelity = accuracy_score(pt_preds, quant_preds)


data = {
    "PyTorch Accuracy" : pt_acc * 100 ,
    "ONNX O2 Accuracy" : onnx_acc * 100 ,
    "Quantized INT8 Accuracy": quant_acc * 100 ,
    "Accuracy Drop (PT vs Quantized)": (pt_acc - quant_acc) * 100 ,
    "Fidelity (Agreement with Base)": fidelity * 100
}


with open(file_path ,"w") as f:
    json.dump(data,f , indent=4)

print(f'data saved to {file_path} successfully')

