import json
import re

def clean_code(code: str) -> str:
    # Remove extra spaces, comments etc.
    code = re.sub(r"//.*", "", code)  
    code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    return code.strip()

def preprocess_dataset(input_path, output_path):
    with open(input_path, "r") as f:
        raw_data = json.load(f)

    processed = []
    for item in raw_data:
        processed.append({
            "code": clean_code(item["code"]),
            "concept": item["concept"]
        })

    with open(output_path, "w") as f:
        json.dump(processed, f, indent=2)

    print("Dataset preprocessing completed.")

if __name__ == "__main__":
    preprocess_dataset(
        "training/dataset/example_dataset.json",
        "training/dataset/clean_dataset.json"
    )
