import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TRANSFORMERS_NO_FLAX"] = "1"

from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

app = FastAPI()

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_PATH = "./qwen-lora-trained"

device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL,
    trust_remote_code=True
)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto",
    trust_remote_code=True
)

model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
def generate_text(data: Prompt):
    inputs = tokenizer(data.prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7
        )

    return {
        "response": tokenizer.decode(output[0], skip_special_tokens=True)
    }
