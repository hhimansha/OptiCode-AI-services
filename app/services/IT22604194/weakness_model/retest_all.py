"""
IT22604194 — Full Re-Test Script for All 15 Weakness Detection Test Cases
Run: python retest_all.py
"""
import requests
import json

API = "http://localhost:8002/predict"

tests = [
    {
        "id": 1,
        "name": "Correct Answer Detection",
        "payload": {
            "code_text": "print(sum(range(1,11)))",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": None,
        "expect_hint_contains": "correct"
    },
    {
        "id": 2,
        "name": "Hardcoded Value Detection",
        "payload": {
            "code_text": "print(55)",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "hardcoded_value",
        "expect_hint_contains": None
    },
    {
        "id": 3,
        "name": "Missing Print Detection",
        "payload": {
            "code_text": "total = sum(range(1,11))",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "missing_print",
        "expect_hint_contains": None
    },
    {
        "id": 4,
        "name": "Idle/Stuck Detection (high idle)",
        "payload": {
            "code_text": "# Write your Python solution here",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 20,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "idle_stuck",
        "expect_hint_contains": None
    },
    {
        "id": 5,
        "name": "Infinite Loop Detection",
        "payload": {
            "code_text": 'while True:\n    print("hello")',
            "skill_level": "Intermediate",
            "time_since_last_keystroke_s": 5,
            "expected_output": "hello",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "infinite_loop",
        "expect_hint_contains": None
    },
    {
        "id": 6,
        "name": "No Function Definition",
        "payload": {
            "code_text": "a = 3\nb = 7\nprint(a if a > b else b)",
            "skill_level": "Intermediate",
            "time_since_last_keystroke_s": 5,
            "expected_output": "7",
            "test_input": "",
            "requires_function": True
        },
        "expect_primary": "no_function",
        "expect_hint_contains": None
    },
    {
        "id": 7,
        "name": "Correct Function Definition",
        "payload": {
            "code_text": "def max_of_two(a,b):\n    return a if a > b else b\nprint(max_of_two(3,7))",
            "skill_level": "Intermediate",
            "time_since_last_keystroke_s": 5,
            "expected_output": "7",
            "test_input": "",
            "requires_function": True
        },
        "expect_primary": None,
        "expect_hint_contains": "correct"
    },
    {
        "id": 8,
        "name": "Syntax/Indentation Error",
        "payload": {
            "code_text": "def max_of_two(a, b):\nreturn a if a > b else b",
            "skill_level": "Intermediate",
            "time_since_last_keystroke_s": 5,
            "expected_output": "7",
            "test_input": "",
            "requires_function": True
        },
        "expect_primary": "syntax_error",
        "expect_hint_contains": None
    },
    {
        "id": 9,
        "name": "Missing Base Case (Recursion)",
        "payload": {
            "code_text": "def factorial(n):\n    return n * factorial(n-1)\nprint(factorial(5))",
            "skill_level": "Advanced",
            "time_since_last_keystroke_s": 5,
            "expected_output": "120",
            "test_input": "",
            "requires_function": True
        },
        "expect_primary": "missing_base_case",
        "expect_hint_contains": None
    },
    {
        "id": 10,
        "name": "Logic Error (off-by-one)",
        "payload": {
            "code_text": "total = 0\nfor i in range(1, 10):\n    total += i\nprint(total)",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "logic_error",
        "expect_hint_contains": None
    },
    {
        "id": 11,
        "name": "Wrong Task Answer",
        "payload": {
            "code_text": "print(sum(range(1,11)))",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "7",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "logic_error",
        "expect_hint_contains": None
    },
    {
        "id": 12,
        "name": "Beginner Skill Level Hints",
        "payload": {
            "code_text": "print(55)",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "hardcoded_value",
        "expect_hint_contains": "fixed values"
    },
    {
        "id": 13,
        "name": "Advanced Skill Level Hints",
        "payload": {
            "code_text": "print(55)",
            "skill_level": "Advanced",
            "time_since_last_keystroke_s": 5,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "hardcoded_value",
        "expect_hint_contains": "hardcode"
    },
    {
        "id": 14,
        "name": "Empty Code — Low Idle Time",
        "payload": {
            "code_text": "",
            "skill_level": "Beginner",
            "time_since_last_keystroke_s": 3,
            "expected_output": "55",
            "test_input": "",
            "requires_function": False
        },
        "expect_primary": "idle_stuck",
        "expect_hint_contains": None
    },
    {
        "id": 15,
        "name": "Correct Recursion With Base Case",
        "payload": {
            "code_text": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)\nprint(factorial(5))",
            "skill_level": "Advanced",
            "time_since_last_keystroke_s": 5,
            "expected_output": "120",
            "test_input": "",
            "requires_function": True
        },
        "expect_primary": None,
        "expect_hint_contains": "correct"
    },
]

# ── Run all tests ──────────────────────────────────────────────────────────
print("=" * 70)
print("  IT22604194 — Weakness Detection API Re-Test (15 Test Cases)")
print("=" * 70)

passed = 0
failed = 0
results = []

for t in tests:
    try:
        res  = requests.post(API, json=t["payload"], timeout=15)
        data = res.json()

        actual_primary = data.get("primary")
        actual_hints   = data.get("hints", [])
        hint_text      = " ".join(actual_hints).lower()

        # Determine pass/fail
        primary_ok = (t["expect_primary"] == actual_primary)
        hint_ok    = (t["expect_hint_contains"] is None or
                      t["expect_hint_contains"].lower() in hint_text)

        status = "PASS" if (primary_ok and hint_ok) else "FAIL"

        if status == "PASS":
            passed += 1
            icon = "✅"
        else:
            failed += 1
            icon = "❌"

        print(f"\n{icon} Test {t['id']:02d}: {t['name']}")
        print(f"   Expected primary : {t['expect_primary']}")
        print(f"   Actual primary   : {actual_primary}")
        print(f"   Hints            : {actual_hints}")
        print(f"   Status           : {status}")

        if status == "FAIL":
            print(f"   ⚠ primary_ok={primary_ok}, hint_ok={hint_ok}")

        results.append({
            "id":      t["id"],
            "name":    t["name"],
            "status":  status,
            "primary": actual_primary,
            "hints":   actual_hints,
            "output":  data.get("output", ""),
            "error":   data.get("error", "")
        })

    except Exception as e:
        failed += 1
        print(f"\n❌ Test {t['id']:02d}: {t['name']} — ERROR: {e}")
        results.append({
            "id": t["id"], "name": t["name"],
            "status": "ERROR", "primary": None,
            "hints": [], "output": "", "error": str(e)
        })

print("\n" + "=" * 70)
print(f"  RESULTS: {passed}/15 PASSED  |  {failed} FAILED")
print(f"  Pass Rate: {(passed/15)*100:.1f}%")
print("=" * 70)

# Save results to JSON for Excel report
with open("retest_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n✅ Results saved to retest_results.json")
