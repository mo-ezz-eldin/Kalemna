import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.onnxruntime import ORTModelForSequenceClassification
import json
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

folder_path = os.path.join(root_dir, "metrics")
file_path = os.path.join(folder_path, "compare_latency_of_intent_model.json")




print('Loading quantized ONNX model o2.......')

onnx_model_quantized = ORTModelForSequenceClassification.from_pretrained(
    r"./onnx_intent_model",
    file_name="model_quantized.onnx"
)

tokenizer = AutoTokenizer.from_pretrained(r'./onnx_intent_model')

text = "I want to cancel my order"

inputs = tokenizer(text, return_tensors="pt")

print('Loading ONNX model o2.......')

onnx_model = ORTModelForSequenceClassification.from_pretrained(r"./onnx_intent_model")


print('Loading PyTorch model.......')
pytorch_model = AutoModelForSequenceClassification.from_pretrained(
    r'./customer_intents/distilbert-base-uncased/checkpoint-1452')
pytorch_model.eval()


onnx_model(**inputs)
onnx_model_quantized(**inputs)
with torch.no_grad():
    pytorch_model(**inputs)



start_time = time.perf_counter()
for _ in range(100):
    outputs_onnx = onnx_model_quantized(**inputs)
end_time = time.perf_counter()

quantized_onnx_avg_ms = ((end_time - start_time) * 1000) / 100


start_time = time.perf_counter()
for _ in range(100):
    outputs_onnx = onnx_model(**inputs)
end_time = time.perf_counter()

onnx_avg_ms = ((end_time - start_time) * 1000) / 100




with torch.no_grad():
    start_time = time.perf_counter()
    for _ in range(100):
        outputs_pt = pytorch_model(**inputs)
    end_time = time.perf_counter()

pytorch_avg_ms = ((end_time - start_time) * 1000) / 100


data = {
    "Average Time taken for pytorch in ms" : pytorch_avg_ms,
    "Average Time taken for onnx_o2 in ms" : onnx_avg_ms,
    "Average Time taken for onnx_o2_quantized in ms" : quantized_onnx_avg_ms,
    "ratio of speed of onnx versus pytorch" : pytorch_avg_ms / onnx_avg_ms ,
    "ratio of speed of quantized_ONNX versus pytorch" : pytorch_avg_ms / quantized_onnx_avg_ms ,
    "ratio of speed of quantized_ONNX versus  usual onnx" : onnx_avg_ms / quantized_onnx_avg_ms
}


with open(file_path, "w") as f:
    json.dump(data , f, indent=4)

print(f'data saved to {file_path} successfully')


