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
    "num_functions","num_loops","has_if","has_return","has_recursion",
    "while_true","syntax_error","lines_of_code","avg_line_length",
    "time_idle","edits_last_30s"
]

WEAKNESS_LABELS = [
    "syntax_error","missing_base_case","infinite_loop","logic_error","idle_stuck"
]

HINT_RULES = {
    "syntax_error":{"Beginner":"Fix syntax.","Intermediate":"Review syntax.","Advanced":"Parser error."},
    "missing_base_case":{"Beginner":"Add base case.","Intermediate":"Ensure termination.","Advanced":"Validate recursion."},
    "infinite_loop":{"Beginner":"Add exit.","Intermediate":"Change loop.","Advanced":"Check invariant."},
    "logic_error":{"Beginner":"Wrong output.","Intermediate":"Check logic.","Advanced":"Edge cases."},
    "idle_stuck":{"Beginner":"Try first step.","Intermediate":"Break problem.","Advanced":"Re-evaluate."}
}

class CodeInput(BaseModel):
    code_text: str
    time_since_last_keystroke_s: int
    skill_level: str

def extract_features(code, idle):
    lines = code.splitlines()
    n = len(lines)

    f = {
        "num_functions": code.count("def "),
        "num_loops": code.count("for ") + code.count("while "),
        "has_if": int("if " in code),
        "has_return": int("return" in code),
        "has_recursion": int("def" in code and code.count("(") > 1),
        "while_true": int("while True" in code),
        "syntax_error": int("def" in code and ":" not in code),
        "lines_of_code": n,
        "avg_line_length": sum(len(l) for l in lines)/max(1,n),
        "time_idle": idle,
        "edits_last_30s": 0
    }

    return pd.DataFrame([[f[x] for x in FEATURE_NAMES]], columns=FEATURE_NAMES)

@app.post("/predict")
def predict_weakness(input: CodeInput):

    skill = input.skill_level if input.skill_level in ["Beginner","Intermediate","Advanced"] else "Beginner"

    X = extract_features(input.code_text,input.time_since_last_keystroke_s).astype(float)

    raw = model.predict(X)[0]
    prediction = dict(zip(WEAKNESS_LABELS,map(int,raw)))

    # Reduce false positives
    if "break" in input.code_text:
        prediction["infinite_loop"]=0

    exec_result = run_python(input.code_text)

    # ✅ REAL correctness FIRST
    if exec_result["error"]=="" and exec_result["output"].strip()!="":
        # clear ML weaknesses
        prediction = {k:0 for k in prediction}
        return {
            "weaknesses": prediction,
            "hints": ["✅ Your answer is correct!"],
            "output": exec_result["output"],
            "error": exec_result["error"]
        }

    # idle AFTER correctness
    if input.time_since_last_keystroke_s>=15:
        prediction["idle_stuck"]=1

    hints=[HINT_RULES[k][skill] for k,v in prediction.items() if v==1]

    return {
        "weaknesses":prediction,
        "hints":hints,
        "output":exec_result["output"],
        "error":exec_result["error"]
    }

@app.post("/execute")
def execute_code(input:CodeInput):
    return run_python(input.code_text)

@app.get("/")
def health():
    return {"status":"Weakness Model API running"}
