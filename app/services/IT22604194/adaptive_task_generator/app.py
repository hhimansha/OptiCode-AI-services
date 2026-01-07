from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import load_dataset
from generator import pick_reference_problem, build_prompt
from qwen_client import generate_with_qwen
from gemini_client import generate_with_fallback

app = FastAPI(title="Adaptive Coding Task Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load dataset once at startup
dataset = load_dataset("new_dataset.jsonl")

class SkillRequest(BaseModel):
    student_skill: int  # 1–5

@app.post("/generate-task")
def generate_task_api(body: SkillRequest):
    example = pick_reference_problem(dataset, body.student_skill)
    prompt = build_prompt(example, body.student_skill)

    task = ""
    used_model = "qwen"

    try:
        task, qwen_time = generate_with_qwen(body.student_skill)


        # fallback conditions
        if qwen_time > 15 or len(task) < 20:
            task = generate_with_fallback(prompt)
            used_model = "gemini"

    except Exception:
        task = generate_with_fallback(prompt)
        used_model = "gemini"

    return {
        "skill_level": body.student_skill,
        "reference_concept": example.get("concept"),
        "generated_task": task,
        "generated_by": used_model
    }

@app.get("/")
def root():
    return {"message": "Adaptive Task Generator API is running"}
