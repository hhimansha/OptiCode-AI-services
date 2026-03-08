import ast
import json
from collections import defaultdict

def cyclomatic_complexity(code):
    try:
        tree = ast.parse(code)
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While,
                                  ast.Try, ast.ExceptHandler)):
                complexity += 1
        return complexity
    except:
        return 1

def count_ast_features(code):
    try:
        tree = ast.parse(code)
        features = {
            "functions": 0, "classes": 0, "loops": 0,
            "conditions": 0, "recursion": 0
        }
        func_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                features["functions"] += 1
                func_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                features["classes"] += 1
            elif isinstance(node, (ast.For, ast.While)):
                features["loops"] += 1
            elif isinstance(node, ast.If):
                features["conditions"] += 1
            elif isinstance(node, ast.Call):
                fn = getattr(node.func, 'id', None)
                if fn in func_names:
                    features["recursion"] += 1
        return features
    except:
        return {"functions":0,"classes":0,"loops":0,"conditions":0,"recursion":0}

# ─── LOAD DATASET ─────────────────────────────────────────────────────────
dataset_path = r"C:\Users\Dell\OptiCode2\server\data\new_dataset.jsonl"

try:
    with open(dataset_path, encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()]
    print(f"✅ Loaded {len(tasks)} tasks from dataset\n")
except FileNotFoundError:
    print(f"❌ File not found: {dataset_path}")
    print("Check the path and try again.")
    exit()

# ─── ANALYSE PER SKILL LEVEL ──────────────────────────────────────────────
skill_data = defaultdict(lambda: {
    "complexity": [], "functions": [], "classes": [],
    "loops": [], "conditions": [], "recursion": [], "count": 0
})

skipped = 0
for t in tasks:
    code = t.get("starter_code", "")
    if not code:
        skipped += 1
        continue
    skill = t.get("skill")
    if skill is None:
        skipped += 1
        continue

    cc = cyclomatic_complexity(code)
    feats = count_ast_features(code)

    skill_data[skill]["complexity"].append(cc)
    skill_data[skill]["functions"].append(feats["functions"])
    skill_data[skill]["classes"].append(feats["classes"])
    skill_data[skill]["loops"].append(feats["loops"])
    skill_data[skill]["conditions"].append(feats["conditions"])
    skill_data[skill]["recursion"].append(feats["recursion"])
    skill_data[skill]["count"] += 1

print(f"Skipped {skipped} tasks (no starter_code or skill field)\n")

# ─── PRINT RESULTS ────────────────────────────────────────────────────────
skill_labels = {
    1: "Beginner",
    2: "Beginner+",
    3: "Intermediate",
    4: "Intermediate+",
    5: "Advanced"
}

print("=" * 80)
print(f"{'Skill Level':<22} {'Tasks':<8} {'Avg CC':<10} {'Funcs':<8} {'Classes':<10} {'Loops':<8} {'Conds':<8} {'Recur'}")
print("=" * 80)

results = {}
for skill in sorted(skill_data.keys()):
    d = skill_data[skill]
    n = len(d["complexity"])
    if n == 0:
        continue

    avg = lambda key: round(sum(d[key]) / len(d[key]), 2)
    label = skill_labels.get(skill, f"Skill {skill}")

    avg_cc    = avg("complexity")
    avg_funcs = avg("functions")
    avg_cls   = avg("classes")
    avg_loops = avg("loops")
    avg_conds = avg("conditions")
    avg_recur = avg("recursion")

    print(f"Skill {skill} ({label:<14}) "
          f"Tasks: {d['count']:<5} "
          f"CC: {avg_cc:<7} "
          f"Funcs: {avg_funcs:<6} "
          f"Classes: {avg_cls:<6} "
          f"Loops: {avg_loops:<6} "
          f"Conds: {avg_conds:<6} "
          f"Recur: {avg_recur}")

    results[f"skill_{skill}"] = {
        "label":                        label,
        "task_count":                   d["count"],
        "avg_cyclomatic_complexity":    avg_cc,
        "avg_functions":                avg_funcs,
        "avg_classes":                  avg_cls,
        "avg_loops":                    avg_loops,
        "avg_conditions":               avg_conds,
        "avg_recursion":                avg_recur
    }

print("=" * 80)

# ─── BLOOM'S TAXONOMY MAPPING ─────────────────────────────────────────────
print("\nBloom's Taxonomy Mapping:")
print("  Skill 1 (Beginner)      → Remember    — recall basic syntax (print, variables)")
print("  Skill 2 (Beginner+)     → Understand  — apply simple functions")
print("  Skill 3 (Intermediate)  → Apply       — data processing, exceptions")
print("  Skill 4 (Intermediate+) → Analyze     — OOP design, class relationships")
print("  Skill 5 (Advanced)      → Evaluate    — recursion, algorithms, generators")

# ─── DIFFICULTY PROGRESSION CHECK ─────────────────────────────────────────
print("\nDifficulty Progression Check:")
skill_keys = sorted(results.keys())
prev_cc = None
progression_valid = True
for key in skill_keys:
    cc = results[key]["avg_cyclomatic_complexity"]
    label = results[key]["label"]
    if prev_cc is not None:
        direction = "✅ increases" if cc >= prev_cc else "⚠️  decreases"
        print(f"  {label}: CC={cc} {direction} from {prev_cc}")
    else:
        print(f"  {label}: CC={cc} (baseline)")
    prev_cc = cc

# ─── CONCEPT GATING CHECK ─────────────────────────────────────────────────
print("\nConcept Gating Verification:")
for key in skill_keys:
    r = results[key]
    flags = []
    if r["avg_functions"] > 0:  flags.append("functions ✅")
    if r["avg_classes"] > 0:    flags.append("classes ✅")
    if r["avg_recursion"] > 0:  flags.append("recursion ✅")
    if not flags:               flags.append("basic concepts only")
    print(f"  {r['label']}: {', '.join(flags)}")

# ─── SAVE RESULTS ─────────────────────────────────────────────────────────
output_path = r"C:\Users\Dell\OptiCode-AI-services\app\services\IT22604194\weakness_model\complexity_results.json"
try:
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_path}")
except Exception as e:
    print(f"\n⚠️  Could not save results file: {e}")
    print("Results printed above — copy them manually.")

print("\n✅ Analysis complete!")
