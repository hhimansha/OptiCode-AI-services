import json
import re
from pathlib import Path

INPUT_FILE = "new_dataset.jsonl"
OUTPUT_DIR = "cleaned_output"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def normalize_expected_output(expected_output):
    if expected_output is None:
        return ""

    if isinstance(expected_output, list):
        return "\n".join(str(x).strip() for x in expected_output if str(x).strip())

    return str(expected_output).strip()


def get_skill_group(skill):
    if skill in [1, 2]:
        return "Beginner"
    elif skill in [3, 4]:
        return "Intermediate"
    elif skill == 5:
        return "Advanced"
    return "Unknown"


def infer_requires_function(task, starter_code):
    text = f"{task}\n{starter_code}".lower()
    return ("write a function" in text) or ("def " in starter_code)


def infer_requires_print(task, starter_code, task_type):
    text = f"{task}\n{starter_code}".lower()
    if "print" in text or "display" in text or "output" in text:
        return True
    if task_type == "practice":
        return True
    return False


def infer_weakness_targets(concept, task, starter_code, requires_function, requires_print):
    concept_l = (concept or "").lower()
    task_l = (task or "").lower()
    starter_l = (starter_code or "").lower()

    weaknesses = set()

    if concept_l in {"print", "variables", "strings", "conditionals", "functions", "loops"}:
        weaknesses.add("syntax_error")

    if concept_l in {"math", "boolean", "conditionals", "lists", "algorithm", "strings"}:
        weaknesses.add("logic_error")

    if concept_l in {"loops", "loop"} or "while" in starter_l or "while" in task_l:
        weaknesses.add("infinite_loop")

    if concept_l == "recursion" or "recursive" in task_l:
        weaknesses.add("missing_base_case")

    if requires_function:
        weaknesses.add("no_function")

    if requires_print:
        weaknesses.add("missing_print")

    if concept_l in {"math", "algorithm", "loops", "boolean"}:
        weaknesses.add("hardcoded_value")

    if concept_l in {"print", "variables", "math"}:
        weaknesses.add("idle_stuck")

    return sorted(list(weaknesses))


def get_subconcept(concept, task, starter_code):
    concept_l = (concept or "").lower()
    task_l = (task or "").lower()
    starter_l = (starter_code or "").lower()

    if concept_l == "loops":
        if "while" in task_l or "while" in starter_l:
            return "while_loop"
        return "for_loop"

    if concept_l == "functions":
        if "return true" in task_l or "false" in task_l:
            return "boolean_function"
        return "basic_function"

    if concept_l == "strings":
        return "string_manipulation"

    if concept_l == "lists":
        return "list_operations"

    if concept_l == "conditionals":
        return "if_else"

    if concept_l == "math":
        return "basic_math"

    if concept_l == "recursion":
        return "recursive_problem"

    if concept_l == "algorithm":
        return "algorithmic_problem"

    return concept_l or "general"


def get_difficulty_score(skill_group, task_type, concept):
    concept_l = (concept or "").lower()

    if skill_group == "Beginner":
        return 1
    if skill_group == "Intermediate":
        return 2
    if skill_group == "Advanced":
        if concept_l in {"recursion", "algorithm", "oop"}:
            return 3
        return 3
    return 1


def should_keep_record(skill_group, task_type, concept):
    concept_l = (concept or "").lower()

    if task_type in {"file", "error"}:
        return False

    if skill_group == "Beginner":
        banned = {"recursion", "oop", "algorithm", "file", "dict_comprehension", "generator", "decorator"}
        return concept_l not in banned

    if skill_group == "Intermediate":
        banned = {"file"}
        return concept_l not in banned

    if skill_group == "Advanced":
        return True

    return False


def has_exact_call(task):
    return bool(re.search(r"\b(Print|Call)\s+[a-zA-Z_]\w*\([^)]*\)", task or ""))


def is_vague_task(task):
    task_l = (task or "").lower()
    vague_patterns = [
        "a number",
        "a string",
        "a list",
        "some numbers",
        "any number",
        "of words",
        "of strings",
        "of numbers",
        "user input"
    ]
    return any(p in task_l for p in vague_patterns)


def is_task_precise(task, requires_function):
    if not task:
        return False

    if requires_function:
        return has_exact_call(task)

    if is_vague_task(task) and not has_exact_call(task):
        return False

    return True


def make_id(skill_group, concept, idx):
    prefix = {
        "Beginner": "beg",
        "Intermediate": "int",
        "Advanced": "adv",
    }.get(skill_group, "unk")

    concept_slug = re.sub(r"[^a-z0-9]+", "_", (concept or "general").lower()).strip("_")
    return f"{prefix}_{concept_slug}_{idx:04d}"


cleaned_records = []
beginner_records = []
intermediate_records = []
advanced_records = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        skill = obj.get("skill")
        concept = obj.get("concept", "").strip()
        task = obj.get("task", "").strip()
        starter_code = obj.get("starter_code", "").strip()
        expected_output = normalize_expected_output(obj.get("expected_output"))
        task_type = obj.get("type", "practice").strip()

        if not task or skill is None:
            continue

        skill_group = get_skill_group(skill)
        requires_function = infer_requires_function(task, starter_code)
        requires_print = infer_requires_print(task, starter_code, task_type)
        weakness_targets = infer_weakness_targets(
            concept, task, starter_code, requires_function, requires_print
        )
        subconcept = get_subconcept(concept, task, starter_code)
        difficulty_score = get_difficulty_score(skill_group, task_type, concept)

        is_valid = (
            should_keep_record(skill_group, task_type, concept)
            and is_task_precise(task, requires_function)
            and bool(expected_output)
        )

        record = {
            "id": make_id(skill_group, concept, idx),
            "skill": skill,
            "skill_group": skill_group,
            "skill_min": 1 if skill_group == "Beginner" else (3 if skill_group == "Intermediate" else 5),
            "skill_max": 2 if skill_group == "Beginner" else (4 if skill_group == "Intermediate" else 5),
            "concept": concept,
            "subconcept": subconcept,
            "weakness_target": weakness_targets,
            "task_type": task_type,
            "task": task,
            "starter_code": starter_code,
            "expected_output": expected_output,
            "test_input": "",
            "requires_function": requires_function,
            "requires_print": requires_print,
            "difficulty_score": difficulty_score,
            "source": "cleaned_dataset",
            "is_valid": is_valid
        }

        cleaned_records.append(record)

        if is_valid:
            if skill_group == "Beginner":
                beginner_records.append(record)
            elif skill_group == "Intermediate":
                intermediate_records.append(record)
            elif skill_group == "Advanced":
                advanced_records.append(record)


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


write_jsonl(f"{OUTPUT_DIR}/cleaned_tasks.jsonl", cleaned_records)
write_jsonl(f"{OUTPUT_DIR}/beginner_tasks.jsonl", beginner_records)
write_jsonl(f"{OUTPUT_DIR}/intermediate_tasks.jsonl", intermediate_records)
write_jsonl(f"{OUTPUT_DIR}/advanced_tasks.jsonl", advanced_records)

print("Done.")
print(f"Total cleaned records: {len(cleaned_records)}")
print(f"Beginner valid records: {len(beginner_records)}")
print(f"Intermediate valid records: {len(intermediate_records)}")
print(f"Advanced valid records: {len(advanced_records)}")