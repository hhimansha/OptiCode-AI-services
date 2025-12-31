from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re

model_path = r"E:\opticode-ai-services-local\OptiCode-AI-services\IT22606860-code-refactor-python\model\final-code-refactor-model"

tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

print("✅ Model loaded successfully. Type 'exit' to stop.\n")

def fix_syntax(code: str) -> str:
    while code.count('(') > code.count(')'):
        code += ')'
    while code.count('[') > code.count(']'):
        code += ']'
    return code

def remove_docstrings(code: str) -> str:
    return re.sub(r'""".*?"""', '', code, flags=re.DOTALL).strip()

def pythonize_loops(code: str, original_code: str) -> str:
    # Convert 'for i in range(len(arr))' to 'for item in arr:'
    pattern = r'for\s+\w+\s+in\s+range\((?:0,\s*)?len\((\w+)\)\):'
    matches = re.finditer(pattern, code)
    for m in matches:
        array_name = m.group(1)
        code = code.replace(m.group(0), f"for item in {array_name}:")
        code = re.sub(rf'{array_name}\[\w+\]', "item", code)

    # Remove injected variables or invalid return statements
    cleaned_lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith(("count =", "try:", "except", "return err", "return total / count")):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def enforce_type_hints(code: str) -> str:
    func_pattern = r'def\s+(\w+)\((\w+)\):'
    return re.sub(func_pattern, r'def \1(\2: Iterable[int]) -> int:', code)

while True:
    task = input("Enter task (refactor / fix / summarize): ").strip().lower()
    if task == "exit":
        break
    if task not in ["refactor", "fix", "summarize"]:
        print("❌ Invalid task. Use refactor, fix, or summarize")
        continue

    print("Enter code (type 'END' on a new line to finish):")
    code_lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        code_lines.append(line)
    code = "\n".join(code_lines)
    if not code.strip():
        print("❌ No code entered. Try again.")
        continue

    prompt = f"Refactor or fix this code without changing logic:\n{code}"

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=512,
            num_beams=5,
            early_stopping=True,
            do_sample=False
        )

    raw_result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # If model output is invalid, fallback to regex-only fixes
    if not raw_result.strip() or re.search(r'\bcount\b|\breturn total / count\b', raw_result):
        print("⚠️ Model output invalid. Applying automatic Pythonic fixes.")
        raw_result = code

    result = remove_docstrings(raw_result)
    result = pythonize_loops(result, code)
    result = fix_syntax(result)
    result = enforce_type_hints(result)

    print("\n✅ Model Output:\n")
    print(result)
    print("-"*60)