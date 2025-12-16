# adaptive_task_generator/generator.py
import os
import random
from dotenv import load_dotenv
import google.generativeai as gen

# 1. Load .env
load_dotenv()

# 2. Read API key from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    gen.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ GEMINI_API_KEY is not set. Will use local fallback.")

def pick_reference_problem(dataset, student_skill: int):
    """Pick a task from dataset whose skill is close to student_skill."""
    candidates = [row for row in dataset if abs(int(row["skill"]) - int(student_skill)) <= 1]
    if not candidates:
        candidates = dataset  # fallback if nothing matches
    return random.choice(candidates)

def build_prompt(example: dict, student_skill: int) -> str:
    """Build a Gemini prompt using the reference example."""
    skill = int(student_skill)
    concept = example.get("concept", "")
    base_task = example.get("task", "")

    if skill == 1:
        level_desc = "absolute beginner"
    elif skill == 2:
        level_desc = "beginner+"
    elif skill == 3:
        level_desc = "intermediate"
    elif skill == 4:
        level_desc = "intermediate+"
    else:
        level_desc = "advanced"

    return f"""
You are an adaptive coding task generator for PYTHON ONLY.

STUDENT LEVEL: {level_desc} (skill {skill})
REFERENCE CONCEPT: {concept}
REFERENCE TASK EXAMPLE:
\"\"\"{base_task}\"\"\"

Generate ONE NEW Python coding task that:
- matches the SAME difficulty level
- uses the SAME general concept (e.g., {concept})
- does NOT copy the example text
- is short and clear (1–3 sentences)
- does NOT include any solution code
- does NOT mention skill level or difficulty
- ONLY outputs the task description, nothing else.
"""

def generate_task(prompt: str) -> str:
    """
    Call Gemini to generate the new task text. 
    If Gemini is not available, return a simple fallback.
    """
    if not GEMINI_API_KEY:
        # Fallback — simple local template
        return "Write a Python function that returns the sum of two numbers."

    try:
        # ✅ IMPORTANT: use the Gemini model name exactly like this
        model = gen.GenerativeModel("models/gemini-2.0-flash-001")

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,        # lower = simpler, more controlled
                "max_output_tokens": 80,   # keep task short
            },
        )

        text = (response.text or "").strip()
        if not text:
            return "Write a Python program that prints the numbers from 1 to 5."
        return text

    except Exception as e:
        print("❌ Gemini error, using fallback:", e)
        return "Write a Python function that returns the sum of two numbers."
