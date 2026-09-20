import os

import torch
import numpy as np
from sklearn.metrics import accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.onnxruntime import ORTModelForSequenceClassification
from tqdm import tqdm
import json



root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

folder_path = os.path.join(root_dir, "metrics")
file_path = os.path.join(folder_path, "benchmark_accuracy_against_quantized_intent_model_vs_onnx_model.json")

print("Loading Models... ⏳")
tokenizer = AutoTokenizer.from_pretrained(r'./onnx_intent_model')

# PyTorch Model
pytorch_model = AutoModelForSequenceClassification.from_pretrained(
    r'./customer_intents/distilbert-base-uncased/checkpoint-1452')
pytorch_model.eval()

# ONNX O2 Model
onnx_model = ORTModelForSequenceClassification.from_pretrained(r"./onnx_intent_model")

# Quantized ONNX Model
onnx_model_quantized = ORTModelForSequenceClassification.from_pretrained(
    r"./onnx_intent_model",
    file_name="model_quantized.onnx"
)

# --- 2. The Edge Cases Dataset (15 Labels) ---
print("Loading Edge Cases Dataset... 📚")

data_mapping = {
    0: [  # place_order
        "Hook me up with the premium package.", "I need two of those red ones sent to my house.",
        "Can we get the ball rolling on a new purchase?"
    ],
    1: [  # get_invoice
        "My accountant is screaming at me, where is the tax breakdown?",
        "I need the official receipt with the VAT on it.",
        "Can you send the billing document for my records?"
    ],
    2: [  # track_order
        "Is the driver lost or something?", "Are my shoes still sitting in your warehouse?",
        "I saw it was dispatched, but where exactly is the truck?"
    ],
    3: [  # get_refund
        "Reverse the charge on my credit card right now.", "I want my cash back, this is unacceptable.",
        "Put the funds back into my bank account."
    ],
    4: [  # contact_customer_service
        "I'm sick of this bot, give me a real breathing human.", "Is there a manager or a supervisor I can speak with?",
        "Stop giving me automated links and let me talk to someone."
    ],
    5: [  # delivery_options
        "Do you guys do same-day drop-off?", "Can the package be left at the back door instead of standard shipping?",
        "What are the tiers for shipping speed?"
    ],
    6: [  # complaint
        "The packaging was completely destroyed and the box is wet.",
        "I waited two hours and the food is literally freezing.",
        "Your app charged me twice and crashed, this is ridiculous."
    ],
    7: [  # change_shipping_address
        "I moved out last week, send it to the new apartment.", "Oops, I put my office zip code instead of my home.",
        "Can we reroute the delivery to my friend's house?"
    ],
    8: [  # check_cancellation_fee
        "Will I get penalized if I back out of the purchase now?",
        "How much will you deduct if I drop the subscription?",
        "Is there a penalty charge for aborting the transaction?"
    ],
    9: [  # track_refund
        "It's been 5 days, when will the reversed transaction reflect?",
        "The money hasn't hit my bank account yet, where is it?",
        "You said you returned the money, but my balance says otherwise."
    ],
    10: [  # delivery_period
        "How many business days does it usually take to cross the border?",
        "Are we talking weeks or months for this to arrive?",
        "What is the standard timeframe for getting the package?"
    ],
    11: [  # check_refund_policy
        "Under what strict conditions can I return this for money?",
        "What are the rules and regulations for getting cash back?",
        "How many days do I have to return this if I hate it?"
    ],
    12: [  # change_order
        "Wait, scratch the medium, make it a large instead.", "Can I swap the blue shirt in my cart for a red one?",
        "I selected standard, but I want to upgrade the item."
    ],
    13: [  # cancel_order
        "Actually, forget it, don't send it at all.", "Abort the purchase immediately!",
        "I wanted to change it, but you know what, just terminate the whole order."
    ],
    14: [  # review
        "I'm giving this a 1-star because the material feels like cheap plastic.",
        "Absolutely loved it, five stars all the way!",
        "Leaving my feedback here: great service but terrible UI."
    ]
}

test_texts = []
true_labels = []

for label, sentences in data_mapping.items():
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

    # 1. PyTorch Prediction
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


with open(file_path, "w") as f:
    json.dump(data, f)


print(f'data saved to {file_path} successfully')
