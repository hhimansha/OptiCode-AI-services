"""Test all 12 refactoring categories - before/after verification"""
from advanced_ast_refactor import refactor_comprehensive

def test_category(name, code):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    result = refactor_comprehensive(code)
    refactored = result.get('refactored_code', code)
    changes = result.get('changes', [])
    print(f"BEFORE:\n{code.strip()}")
    print(f"\nAFTER:\n{refactored.strip()}")
    print(f"\nChanges: {len(changes)}")
    for c in changes:
        print(f"  - {c.get('type', c.get('pattern', ''))}: {c.get('description', c.get('after', ''))}")
    changed = code.strip() != refactored.strip()
    print(f"  >>> {'TRANSFORMED' if changed else 'NO CHANGE'}")
    return changed

results = {}

# CATEGORY 1: Naming (camelCase -> snake_case, class naming)
results['Cat1-Naming'] = test_category("CATEGORY 1: Naming Conventions", '''
def calcTtl(x, y):
    Res = x + y
    return Res

class myClass:
    def GetData(self):
        pass
''')

# CATEGORY 3: Complex Conditionals (nested if -> flattened)
results['Cat3-Conditionals'] = test_category("CATEGORY 3: Complex Conditionals", '''
def check(x, y):
    if x > 0:
        if y > 0:
            print("both positive")
''')

# CATEGORY 4: Magic Numbers
results['Cat4-MagicNumbers'] = test_category("CATEGORY 4: Magic Numbers", '''
def calculate_shipping(weight):
    if weight < 5:
        return weight * 2.5
    elif weight < 20:
        return weight * 1.8
    else:
        return weight * 1.2
''')

# CATEGORY 5: Type Hints
results['Cat5-TypeHints'] = test_category("CATEGORY 5: Type Hints", '''
def fetch_user(user_id, include_orders):
    pass

def calculate_average(numbers):
    return sum(numbers) / len(numbers)
''')

# CATEGORY 6: Exception Handling (bare except)
results['Cat6-Exceptions'] = test_category("CATEGORY 6: Exception Handling", '''
def read_file(path):
    try:
        f = open(path)
        data = f.read()
        return data
    except:
        pass
''')

# CATEGORY 7: Import Organization
results['Cat7-Imports'] = test_category("CATEGORY 7: Import Organization", '''
from collections import defaultdict
import sys
import os
from typing import List
import json
from pathlib import Path
''')

# CATEGORY 8: Boolean return simplification
results['Cat8-BoolReturn'] = test_category("CATEGORY 8: Boolean Return Simplification", '''
def is_valid(x):
    if x > 0:
        return True
    else:
        return False
''')

# SUMMARY
print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
for name, worked in results.items():
    status = "PASS" if worked else "FAIL"
    print(f"  [{status}] {name}")

passed = sum(1 for v in results.values() if v)
total = len(results)
print(f"\n  {passed}/{total} categories transforming correctly")
