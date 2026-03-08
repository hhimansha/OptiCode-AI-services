import csv
import json

csv.field_size_limit(2**31 - 1)

input_csv = "train.csv"
output_jsonl = "training_data.jsonl"

def map_difficulty_to_skill(diff):
    diff = int(diff)
    if diff <= 2:
        return 1
    elif diff <= 4:
        return 2
    elif diff <= 6:
        return 3
    elif diff <= 8:
        return 4
    else:
        return 5

with open(input_csv, newline='', encoding='utf-8') as csvfile, open(output_jsonl, 'w', encoding='utf-8') as jsonlfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        difficulty = row["difficulty"]
        if not difficulty.isdigit():
            continue

        skill = map_difficulty_to_skill(difficulty)

        jsonl = {
            "question": row["question"],
            "solution": row["solution"],
            "difficulty": skill,
            "starter_code": row.get("starter_code", "")
        }

        jsonlfile.write(json.dumps(jsonl) + "\n")

print("Dataset converted → training_data.jsonl")
