import ast
import re
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from code_executor import run_python
from ast_features_extractor import extract_basic_ast_features

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
    "num_functions", "num_loops", "has_if", "has_return", "has_recursion",
    "while_true", "syntax_error", "lines_of_code", "avg_line_length",
    "time_idle", "edits_last_30s",
    "cyclomatic_est", "max_nesting_depth", "num_recursion_calls", "num_try"
]

MODEL_WEAKNESS_LABELS = [
    "syntax_error",
    "missing_base_case",
    "infinite_loop",
    "logic_error",
    "idle_stuck"
]

ALL_WEAKNESS_LABELS = [
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
    requires_function: bool = False


def extract_features(code: str, idle: int):
    ast_feats = extract_basic_ast_features(code)
    lines = code.splitlines()
    n = len(lines)

    features = {
        "num_functions": ast_feats.get("num_functions", 0),
        "num_loops": ast_feats.get("num_for", 0) + ast_feats.get("num_while", 0),
        "has_if": int(ast_feats.get("num_if", 0) > 0),
        "has_return": int(ast_feats.get("num_return", 0) > 0),
        "has_recursion": ast_feats.get("has_recursion", 0),
        "while_true": int("while True" in code or "while 1" in code),
        "syntax_error": int(ast_feats.get("syntax_error_parse", 0)),
        "lines_of_code": ast_feats.get("loc", n),
        "avg_line_length": sum(len(l) for l in lines) / max(1, n),
        "time_idle": idle,
        "edits_last_30s": 0,
        "cyclomatic_est": ast_feats.get("cyclomatic_est", 1),
        "max_nesting_depth": ast_feats.get("max_nesting_depth", 0),
        "num_recursion_calls": ast_feats.get("num_recursion_calls", 0),
        "num_try": ast_feats.get("num_try", 0),
    }

    return pd.DataFrame([[features[x] for x in FEATURE_NAMES]], columns=FEATURE_NAMES)


def has_real_recursion(code_text: str) -> bool:
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        func_name = node.name

        # Only check calls INSIDE this function's body
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == func_name
            ):
                return True

    return False

def check_hardcoded(code_text: str, expected_output: str) -> bool:
    if not expected_output or not expected_output.strip():
        return False

    expected = expected_output.strip()
    code_lines = code_text.splitlines()

    code_without_comments = "\n".join(
        line for line in code_lines if not line.strip().startswith("#")
    )

    hardcoded_patterns = [
        f'print({expected})',
        f'print({expected} )',
        f'print("{expected}")',
        f"print('{expected}')"
    ]

    is_hardcoded = any(p in code_without_comments for p in hardcoded_patterns)

    if is_hardcoded:
        func_call_pattern = re.compile(r'\w+\([^)]*' + re.escape(expected) + r'[^)]*\)')
        direct_print = re.compile(r'print\s*\(\s*[\'"]?' + re.escape(expected) + r'[\'"]?\s*\)')
        if func_call_pattern.search(code_without_comments) and not direct_print.search(code_without_comments):
            is_hardcoded = False

    return is_hardcoded


@app.post("/predict")
def predict_weakness(input: CodeInput):
    skill = input.skill_level if input.skill_level in ["Beginner", "Intermediate", "Advanced"] else "Beginner"

    X = extract_features(input.code_text, input.time_since_last_keystroke_s).astype(float)
    raw = model.predict(X)[0]

    prediction = {k: 0 for k in ALL_WEAKNESS_LABELS}

    for label, value in zip(MODEL_WEAKNESS_LABELS, map(int, raw)):
        prediction[label] = value

    # Reduce false infinite loop detection
    if "break" in input.code_text:
        prediction["infinite_loop"] = 0

    # ---------------- SYNTAX ERROR CHECK ----------------
    try:
        ast.parse(input.code_text)
    except SyntaxError:
        prediction = {k: 0 for k in ALL_WEAKNESS_LABELS}
        prediction["syntax_error"] = 1
        return {
            "weaknesses": prediction,
            "primary": "syntax_error",
            "hints": [HINT_RULES["syntax_error"][skill]],
            "output": "",
            "error": "SyntaxError: Check your indentation and syntax."
        }

    # ---------------- DISABLE FALSE RECURSION WARNINGS ----------------
    if not has_real_recursion(input.code_text):
        prediction["missing_base_case"] = 0

    # ---------------- NO FUNCTION CHECK ----------------
    if input.requires_function and "def " not in input.code_text and input.code_text.strip() != "":
        prediction = {k: 0 for k in ALL_WEAKNESS_LABELS}
        prediction["no_function"] = 1
        return {
            "weaknesses": prediction,
            "primary": "no_function",
            "hints": [HINT_RULES["no_function"][skill]],
            "output": "",
            "error": ""
        }

    # ---------------- EXECUTE CODE ----------------
    exec_result = run_python(input.code_text, input.test_input)

    # ---------------- HARDCODED VALUE CHECK ----------------
    if check_hardcoded(input.code_text, input.expected_output):
        prediction = {k: 0 for k in ALL_WEAKNESS_LABELS}
        prediction["hardcoded_value"] = 1
        return {
            "weaknesses": prediction,
            "primary": "hardcoded_value",
            "hints": [HINT_RULES["hardcoded_value"][skill]],
            "output": exec_result["output"],
            "error": exec_result["error"]
        }

    # ---------------- CORRECTNESS CHECK ----------------
    if input.expected_output:
        if exec_result["error"] == "" and exec_result["output"].strip() == input.expected_output.strip():
            prediction = {k: 0 for k in ALL_WEAKNESS_LABELS}
            return {
                "weaknesses": prediction,
                "primary": None,
                "hints": ["✅ Your answer is correct!"],
                "output": exec_result["output"],
                "error": ""
            }
        elif exec_result["error"] == "" and exec_result["output"].strip() != input.expected_output.strip():
            prediction["logic_error"] = 1

    # ---------------- RUNTIME ERROR CHECK ----------------
    if exec_result["error"]:
        prediction["logic_error"] = 1

    # ---------------- IDLE CHECK ----------------
    if input.time_since_last_keystroke_s >= 15:
        prediction["idle_stuck"] = 1

    # ---------------- MISSING PRINT CHECK ----------------
    if (
        input.expected_output.strip()
        and exec_result["error"] == ""
        and exec_result["output"].strip() == ""
        and not input.requires_function
        and "print(" not in input.code_text
    ):
        prediction["missing_print"] = 1

    # ---------------- PRIMARY WEAKNESS PRIORITY ----------------
    priority_order = [
        "syntax_error",
        "no_function",
        "hardcoded_value",
        "missing_base_case",
        "infinite_loop",
        "missing_print",
        "logic_error",
        "idle_stuck",
    ]

    primary = None
    for k in priority_order:
        if prediction.get(k) == 1:
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
    return run_python(input.code_text, input.test_input)


@app.get("/debug")
def debug():
    result = run_python("print(5+10)", "")
    return {"debug_result": result, "type": str(type(result))}


@app.get("/")
def health():
    return {"status": "Weakness Model API running"}