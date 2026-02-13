from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from code_executor import run_python

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Weakness Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load ML model
# -----------------------------
model = joblib.load("weakness_model.pkl")

# -----------------------------
# Feature names & labels
# -----------------------------
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

# -----------------------------
# Hint rules
# -----------------------------
HINT_RULES = {
    "syntax_error": {
        "Beginner": "Fix syntax.",
        "Intermediate": "Review syntax.",
        "Advanced": "Parser error."
    },
    "missing_base_case": {
        "Beginner": "Add base case.",
        "Intermediate": "Ensure termination.",
        "Advanced": "Validate recursion."
    },
    "infinite_loop": {
        "Beginner": "Add exit.",
        "Intermediate": "Change loop.",
        "Advanced": "Check invariant."
    },
    "logic_error": {
        "Beginner": "Wrong output.",
        "Intermediate": "Check logic.",
        "Advanced": "Edge cases."
    },
    "idle_stuck": {
        "Beginner": "Try first step.",
        "Intermediate": "Break problem.",
        "Advanced": "Re-evaluate."
    }
}

# -----------------------------
# Request schema
# -----------------------------
class CodeInput(BaseModel):
    code_text: str
    time_since_last_keystroke_s: int
    skill_level: str
    expected_output: str = ""  # optional
    test_input: str = ""

# -----------------------------
# Feature extraction
# -----------------------------
def extract_features(code: str, idle: int):
    lines = code.splitlines()
    n = len(lines)

    features = {
        "num_functions": code.count("def "),
        "num_loops": code.count("for ") + code.count("while "),
        "has_if": int("if " in code),
        "has_return": int("return" in code),
        "has_recursion": int("def" in code and code.count("(") > 1),
        "while_true": int("while True" in code),
        "syntax_error": int("def" in code and ":" not in code),
        "lines_of_code": n,
        "avg_line_length": sum(len(l) for l in lines) / max(1, n),
        "time_idle": idle,
        "edits_last_30s": 0
    }

    return pd.DataFrame(
        [[features[x] for x in FEATURE_NAMES]],
        columns=FEATURE_NAMES
    )

# -----------------------------
# MAIN ENDPOINT
# -----------------------------
@app.post("/predict")
def predict_weakness(input: CodeInput):

    # Normalize skill level
    skill = input.skill_level if input.skill_level in [
        "Beginner", "Intermediate", "Advanced"
    ] else "Beginner"

    # Extract ML features
    X = extract_features(
        input.code_text,
        input.time_since_last_keystroke_s
    ).astype(float)

    # Model prediction
    raw = model.predict(X)[0]
    prediction = dict(zip(WEAKNESS_LABELS, map(int, raw)))

    # Reduce false infinite loop detection
    if "break" in input.code_text:
        prediction["infinite_loop"] = 0

    # Execute code
    #exec_result = run_python(input.code_text)
    exec_result = run_python(input.code_text, input.test_input)


    # ---------------- CORRECTNESS CHECK ----------------
    # ---- CORRECTNESS CHECK ----
    if input.expected_output:
        if exec_result["error"] == "" and exec_result["output"].strip() == input.expected_output.strip():
            prediction = {k: 0 for k in prediction}
            return {
            "weaknesses": prediction,
            "primary": None,
            "hints": ["✅ Your answer is correct!"],
            "output": exec_result["output"],
            "error": ""
            }


    # ---------------- IDLE CHECK ----------------
    if input.time_since_last_keystroke_s >= 15:
        prediction["idle_stuck"] = 1

    # ---------------- HINT GENERATION ----------------
    primary = None
    for k, v in prediction.items():
        if v == 1:
            primary = k
            break

    hints = []
    if primary:
        hints.append(HINT_RULES[primary][skill])

    return {
        "weaknesses": prediction,
        "primary": primary,
        "hints": hints,
        "output": exec_result["output"],
        "error": exec_result["error"]
    }

# -----------------------------
# Execute-only endpoint
# -----------------------------
@app.post("/execute")
def execute_code(input: CodeInput):
    return run_python(input.code_text)

# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def health():
    return {"status": "Weakness Model API running"}
