import ast
import re
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from code_executor import run_python

app = FastAPI(title="Weakness Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("weakness_model.pkl")

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
    "idle_stuck",
    "no_function",
    "missing_print",
    "hardcoded_value"
]

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
    },
    "no_function": {
        "Beginner": "Try writing a function using def.",
        "Intermediate": "Define the required function.",
        "Advanced": "Encapsulate logic in a function."
    },
    "missing_print": {
        "Beginner": "Use print() to display the result.",
        "Intermediate": "Ensure output is printed.",
        "Advanced": "Return or print the final result."
    },
    "hardcoded_value": {
        "Beginner": "Avoid fixed values. Use the input.",
        "Intermediate": "Compute result dynamically.",
        "Advanced": "Do not hardcode expected output."
    }
}

class CodeInput(BaseModel):
    code_text: str
    time_since_last_keystroke_s: int
    skill_level: str
    expected_output: str = ""
    test_input: str = ""

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
    return pd.DataFrame([[features[x] for x in FEATURE_NAMES]], columns=FEATURE_NAMES)

def check_hardcoded(code_text: str, expected_output: str) -> bool:
    if not expected_output or not expected_output.strip():
        return False
    expected = expected_output.strip()
    code_lines = code_text.splitlines()
    code_without_comments = "\n".join(
        line for line in code_lines
        if not line.strip().startswith("#")
    )
    hardcoded_patterns = [
        f'print({expected})',
        f'print({expected} )',
    ]
    is_hardcoded = any(p in code_without_comments for p in hardcoded_patterns)
    if is_hardcoded:
        func_call_pattern = re.compile(r'\w+\([^)]*' + re.escape(expected) + r'[^)]*\)')
        direct_print = re.compile(r'print\s*\(\s*' + re.escape(expected) + r'\s*\)')
        if func_call_pattern.search(code_without_comments) and \
                not direct_print.search(code_without_comments):
            is_hardcoded = False
    return is_hardcoded

@app.post("/predict")
def predict_weakness(input: CodeInput):

    skill = input.skill_level if input.skill_level in ["Beginner", "Intermediate", "Advanced"] else "Beginner"

    X = extract_features(input.code_text, input.time_since_last_keystroke_s).astype(float)
    raw = model.predict(X)[0]
    prediction = dict(zip(WEAKNESS_LABELS, map(int, raw)))

    if "break" in input.code_text:
        prediction["infinite_loop"] = 0

    # ---------------- SYNTAX ERROR CHECK (before running code) ----------------
    try:
        ast.parse(input.code_text)
    except SyntaxError:
        prediction["syntax_error"] = 1
        return {
            "weaknesses": prediction,
            "primary": "syntax_error",
            "hints": [HINT_RULES["syntax_error"][skill]],
            "output": "",
            "error": "SyntaxError: Check your indentation and syntax."
        }

    # Execute code only if syntax is valid
    exec_result = run_python(input.code_text, input.test_input)

    # ---------------- HARDCODED VALUE CHECK ----------------
    if check_hardcoded(input.code_text, input.expected_output):
        prediction["hardcoded_value"] = 1
        return {
            "weaknesses": prediction,
            "primary": "hardcoded_value",
            "hints": [HINT_RULES["hardcoded_value"][skill]],
            "output": exec_result["output"],
            "error": ""
        }

    # ---------------- CORRECTNESS CHECK ----------------
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
        elif exec_result["error"] == "" and exec_result["output"].strip() != input.expected_output.strip():
            prediction["logic_error"] = 1

    # ---------------- RULE BASED DETECTION ----------------
    primary = None

    if input.expected_output and "def " not in input.code_text and input.code_text.strip() != "":
        prediction["no_function"] = 1

    if input.expected_output and "print(" not in input.code_text:
        prediction["missing_print"] = 1

    for k in ["idle_stuck", "no_function", "missing_print", "hardcoded_value"]:
        if prediction.get(k) == 1:
            primary = k
            break

    # ---------------- IDLE CHECK ----------------
    if input.time_since_last_keystroke_s >= 15:
        prediction["idle_stuck"] = 1

    # ---------------- HINT GENERATION ----------------
    if not primary:
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

@app.post("/execute")
def execute_code(input: CodeInput):
    return run_python(input.code_text)

@app.get("/")
def health():
    return {"status": "Weakness Model API running"}