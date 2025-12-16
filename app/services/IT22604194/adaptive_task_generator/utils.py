# adaptive_task_generator/utils.py
import json

def load_dataset(path="new_dataset.jsonl"):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data
