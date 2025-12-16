import json

file1 = "final_merged.jsonl"
file2 = "newest.jsonl"
output = "merged_output.jsonl"

merged = []

# Load File 1
with open(file1, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                merged.append(json.loads(line))
            except:
                pass

# Load File 2
with open(file2, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                merged.append(json.loads(line))
            except:
                pass

# Save merged file
with open(output, "w", encoding="utf-8") as f:
    for item in merged:
        f.write(json.dumps(item) + "\n")

print("Merged:", len(merged), "items")
print("Saved as:", output)
