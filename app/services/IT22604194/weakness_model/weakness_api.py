from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ast
import joblib

app = FastAPI()

# ✅ ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeSnapshot(BaseModel):
    code_text: str
    time_since_last_keystroke_s: float = 0

@app.post("/predict")
def predict(snapshot: CodeSnapshot):
    code = snapshot.code_text

    # Syntax error
    try:
        ast.parse(code)
        syntax_error = 0
    except:
        syntax_error = 1

    missing_base_case = 1 if "def" in code and "return" in code and "if" not in code else 0
    infinite_loop = 1 if "while True" in code else 0
    logic_error = 1 if "def" in code and "return" not in code else 0
    idle_stuck = 1 if snapshot.time_since_last_keystroke_s > 10 else 0

    return {
        "syntax_error": syntax_error,
        "missing_base_case": missing_base_case,
        "infinite_loop": infinite_loop,
        "logic_error": logic_error,
        "idle_stuck": idle_stuck
    }
