# generate_dataset.py  — run this once to expand your training data
import pandas as pd
import random

random.seed(42)
rows = []

templates = [
    # (num_functions, num_loops, has_if, has_return, has_recursion, while_true,
    #  syntax_error, loc, avg_ll, idle, edits,
    #  cyclomatic, max_depth, recursion_calls, num_try,
    #  label_syntax, label_missing_base, label_infinite, label_logic, label_idle)

    # Clean correct code patterns
    lambda: (1,1,1,1,0,0,0, random.randint(4,10), random.uniform(18,28),
             random.randint(0,5), random.randint(3,8),
             random.randint(2,4), random.randint(2,5), 0, 0,
             0,0,0,0,0),

    # Syntax errors
    lambda: (0,0,0,0,0,0,1, random.randint(1,3), random.uniform(5,12),
             random.randint(1,5), random.randint(1,3),
             1, 1, 0, 0,
             1,0,0,0,0),

    # Missing base case in recursion
    lambda: (1,0,0,1,1,0,0, random.randint(2,5), random.uniform(18,26),
             random.randint(8,20), random.randint(0,2),
             random.randint(1,3), random.randint(2,6), random.randint(1,3), 0,
             0,1,0,1,0),

    # Infinite loop
    lambda: (0,1,0,0,0,1,0, random.randint(2,4), random.uniform(12,18),
             random.randint(3,8), random.randint(1,3),
             random.randint(2,4), random.randint(1,3), 0, 0,
             0,0,1,0,0),

    # Logic error
    lambda: (1,1,1,1,0,0,0, random.randint(4,8), random.uniform(20,28),
             random.randint(1,4), random.randint(3,7),
             random.randint(3,6), random.randint(2,5), 0, 0,
             0,0,0,1,0),

    # Idle stuck
    lambda: (0,0,0,0,0,0,0, 0, 0,
             random.randint(18,60), 0,
             1, 0, 0, 0,
             0,0,0,0,1),
]

cols = [
    "num_functions","num_loops","has_if","has_return","has_recursion",
    "while_true","syntax_error","lines_of_code","avg_line_length",
    "time_idle","edits_last_30s",
    "cyclomatic_est","max_nesting_depth","num_recursion_calls","num_try",
    "label_syntax_error","label_missing_base_case","label_infinite_loop",
    "label_logic_error","label_idle_stuck"
]

# Generate 600 rows — 100 per pattern
for _ in range(100):
    for t in templates:
        rows.append(t())

df = pd.DataFrame(rows, columns=cols)
df.to_csv("weakness_dataset.csv", index=False)
print(f"Generated {len(df)} rows → weakness_dataset.csv")