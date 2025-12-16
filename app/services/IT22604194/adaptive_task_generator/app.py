# adaptive_task_generator/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import load_dataset
from generator import pick_reference_problem, build_prompt, generate_task

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
    task = generate_task(prompt)

    return {
        "skill_level": body.student_skill,
        "reference_concept": example.get("concept"),
        "reference_task": example.get("task"),
        "generated_task": task,
    }


@app.get("/")
def root():
    return {"message": "Adaptive Task Generator API is running"}
