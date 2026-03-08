import json, glob
import pandas as pd
from tqdm import tqdm
from ast_features_extractor import extract_basic_ast_features

RAW_DIR = "data/raw/*.jsonl"

def auto_label(row):
    labels = {
        "syntax_error": 0,
        "logic_error": 0,
        "infinite_loop": 0,
        "missing_base_case": 0,
        "stuck_idle": 0
    }

    status = row.get("runtime_status","")
    exc = row.get("exception","").lower()
    code = row.get("code_text","")

    if status == "CE":
        labels["syntax_error"] = 1
    if status == "WA":
        labels["logic_error"] = 1
    if status == "TLE":
        labels["infinite_loop"] = 1
    if "recursion" in exc:
        labels["missing_base_case"] = 1
    if row.get("time_since_last_keystroke_s",0) > 60:
        labels["stuck_idle"] = 1

    return labels

rows = []

for file in glob.glob(RAW_DIR):
    with open(file,"r") as f:
        for line in f:
            obj = json.loads(line)
            code = obj["code_text"]
            ast_feats = extract_basic_ast_features(code)
            labels = auto_label(obj)
            rows.append({ **obj, **ast_feats, **labels })

df = pd.DataFrame(rows)
df.to_parquet("data/combined_features.parquet")
print(df.head())
print("Saved dataset!")
