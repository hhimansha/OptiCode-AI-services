import requests
import time

QWEN_API_URL = (
    "https://ashani-shashikala-qwen-lora-task-generator-own.hf.space"
    "/api/tasks/generate"
)

def generate_with_qwen(student_skill: int):
    start = time.time()

    resp = requests.post(
        QWEN_API_URL,
        json={"student_skill": student_skill},
        headers={"Content-Type": "application/json"},
        timeout=40
    )

    elapsed = time.time() - start

    if resp.status_code != 200:
        raise RuntimeError(f"Qwen failed: {resp.status_code} {resp.text}")

    task = resp.json().get("generated_task", "")
    return task.strip(), elapsed
