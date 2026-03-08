from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------
# FastAPI app
# --------------------------------
app = FastAPI(title="Weakness Detection API")

# --------------------------------
# Load trained model
# --------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("weakness_model.pkl")

# --------------------------------
# Feature & label definitions
# --------------------------------
FEATURE_NAMES = [
    "num_functions",
    "num_loops",
    "has_if",
    "has_return",
    "has_recursion",
    "while_true",
    "syntax_error",
    "lines_of_code",
    "avg_line_length",
    "time_idle",
    "edits_last_30s"
]

WEAKNESS_LABELS = [
    "syntax_error",
    "missing_base_case",
    "infinite_loop",
    "logic_error",
    "idle_stuck"
]

# --------------------------------
# Skill-based hint rules
# --------------------------------
HINT_RULES = {
    "syntax_error": {
        "Beginner": "Check indentation, missing colons, or brackets.",
        "Intermediate": "Review function definitions and control statements.",
        "Advanced": "Verify Python syntax at the parser level."
    },
    "missing_base_case": {
        "Beginner": "Recursion needs a stopping condition to avoid infinite calls.",
        "Intermediate": "Ensure your recursive function reaches a base case.",
        "Advanced": "Validate termination conditions of recursive calls."
    },
    "infinite_loop": {
        "Beginner": "Your loop may never stop. Add a condition to exit the loop.",
        "Intermediate": "Ensure loop conditions change to terminate execution.",
        "Advanced": "Check loop invariants and exit conditions."
    },
    "logic_error": {
        "Beginner": "Your code runs, but the output may be incorrect.",
        "Intermediate": "Check if your logic matches the problem requirements.",
        "Advanced": "Review edge cases and algorithm correctness."
    },
    "idle_stuck": {
        "Beginner": "You seem stuck. Try writing the first step in plain English.",
        "Intermediate": "Break the problem into smaller steps.",
        "Advanced": "Re-evaluate constraints and edge cases."
    }
}

# --------------------------------
# Request schema
# --------------------------------
class CodeInput(BaseModel):
    code_text: str
    time_since_last_keystroke_s: int
    skill_level: str  # Beginner | Intermediate | Advanced

# --------------------------------
# Feature extraction
# --------------------------------
def extract_features(code: str, idle_time: int):
    lines = code.splitlines()
    num_lines = len(lines)

    features = {
        "num_functions": code.count("def "),
        "num_loops": code.count("for ") + code.count("while "),
        "has_if": int("if " in code),
        "has_return": int("return" in code),
        "has_recursion": int(code.count("def") > 0 and code.count("def") < code.count("(")),
        "while_true": int("while True" in code),
        "syntax_error": int("def" in code and ":" not in code),
        "lines_of_code": num_lines,
        "avg_line_length": (
            sum(len(l) for l in lines) / max(1, num_lines)
        ),
        "time_idle": idle_time,
        "edits_last_30s": 0
    }

    return pd.DataFrame(
        [[features[f] for f in FEATURE_NAMES]],
        columns=FEATURE_NAMES
    )

# --------------------------------
# Prediction endpoint
# --------------------------------
@app.post("/predict")
def predict_weakness(input: CodeInput):

    # Validate skill level
    skill_level = input.skill_level
    if skill_level not in ["Beginner", "Intermediate", "Advanced"]:
        skill_level = "Beginner"

    # Extract features
    X = extract_features(
        input.code_text,
        input.time_since_last_keystroke_s
    )

    # Ensure safe numeric types
    X = X.astype(float)

    # Predict weaknesses
    raw_pred = model.predict(X)[0]
    #MLprediction endpoint

    prediction = {
        label: int(value)
        for label, value in zip(WEAKNESS_LABELS, raw_pred)
    }
    # RULE-BASED OVERRIDE FOR IDLE / STUCK
    if input.time_since_last_keystroke_s >= 6:
        prediction["idle_stuck"] = 1

    # Generate skill-based hints
    hints = [
        HINT_RULES[w][skill_level]
        for w, v in prediction.items()
        if v == 1
    ]

    return {
        "weaknesses": prediction,
        "hints": hints
    }

# --------------------------------
# Health check
# --------------------------------
@app.get("/")
def health():
    return {"status": "Weakness Model API running"}
