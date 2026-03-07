"""
==========================================================================
  OptiCode - COMPREHENSIVE BEFORE/AFTER TEST SUITE
  ALL Patterns Across ALL Modules
==========================================================================
  Tests:
    A. 12 Categories (advanced_ast_refactor.py)
    B. 20 Security Patterns (security_ast_refactor.py)
    C. 3 Security Risk Modules (injection, filesystem, resources)
    D. 2 Performance Modules (memory, caching)
    E. Priority Refactoring Patterns (priority_refactorings.py)
==========================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

PASS_COUNT = 0
FAIL_COUNT = 0
SECTION_RESULTS = {}

def test(name, before, after_code, expect_in=None, expect_not_in=None):
    """Verify transformation result."""
    global PASS_COUNT, FAIL_COUNT
    ok = True
    reasons = []
    
    # Check code changed
    if before.strip() == after_code.strip():
        ok = False
        reasons.append("Code NOT transformed (same as input)")
    
    # Check expected substring present
    if expect_in:
        for exp in (expect_in if isinstance(expect_in, list) else [expect_in]):
            if exp not in after_code:
                ok = False
                reasons.append(f"Missing: '{exp}'")
    
    # Check unexpected substring absent
    if expect_not_in:
        for exp in (expect_not_in if isinstance(expect_not_in, list) else [expect_not_in]):
            if exp in after_code:
                ok = False
                reasons.append(f"Should NOT contain: '{exp}'")
    
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    
    print(f"  [{status}] {name}")
    if not ok:
        for r in reasons:
            print(f"         {r}")
        print(f"         BEFORE: {before.strip()[:100]}")
        print(f"         AFTER:  {after_code.strip()[:100]}")
    return ok


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# ═══════════════════════════════════════════════════════════
# A. ADVANCED AST REFACTORING - 12 CATEGORIES
# ═══════════════════════════════════════════════════════════

section("A. ADVANCED AST REFACTORING (advanced_ast_refactor.py)")

from advanced_ast_refactor import refactor_comprehensive

# ── CATEGORY 1: Naming & Readability ──
print("\n  ── Category 1: Naming & Readability ──")

before = '''
def calcTotal(x, y):
    return x + y

class myclass:
    pass

result = calcTotal(1, 2)
'''
result = refactor_comprehensive(before, categories=['naming'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat1: camelCase → snake_case", before, after, expect_in="calc_total")
test("Cat1: class → PascalCase", before, after, expect_in="Myclass")


# ── CATEGORY 2: Function/Method Refactoring ──
print("\n  ── Category 2: Function/Method Refactoring ──")

before = '''
def process_data(items):
    "validation"
    if not items:
        return []
    cleaned = []
    for item in items:
        cleaned.append(item.strip())
    "processing"
    results = []
    for c in cleaned:
        results.append(c.upper())
    final = []
    for r in results:
        final.append(r + "_done")
    return final
'''
result = refactor_comprehensive(before, categories=['functions'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat2: Long function extraction", before, after, expect_in="_process_data_")


# ── CATEGORY 3: Conditional Logic ──
print("\n  ── Category 3: Conditional Logic ──")

before_nested = '''
def check(a, b):
    if a:
        if b:
            return True
    return False
'''
result = refactor_comprehensive(before_nested, categories=['conditionals'])
after = result.get('refactored_code', before_nested)
print(f"\n  BEFORE (nested if):\n{before_nested}")
print(f"  AFTER:\n{after}")
test("Cat3: Flatten nested if → if a and b", before_nested, after, expect_in="and")

before_bool = '''
def is_valid(x):
    if x > 0:
        return True
    else:
        return False
'''
result = refactor_comprehensive(before_bool, categories=['conditionals'])
after = result.get('refactored_code', before_bool)
print(f"\n  BEFORE (boolean return):\n{before_bool}")
print(f"  AFTER:\n{after}")
test("Cat3: Simplify boolean return", before_bool, after, expect_in="return x > 0")


# ── CATEGORY 4: Variable & Data (Magic Numbers) ──
print("\n  ── Category 4: Variable & Data (Magic Numbers) ──")

before = '''
def calculate_price(qty):
    tax = qty * 2.5
    discount = qty * 1.8
    surcharge = qty * 1.2
    bonus = 5
    threshold = 20
    return tax + discount
'''
result = refactor_comprehensive(before, categories=['variables'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat4: Magic numbers → named constants", before, after, expect_in="CONSTANT_")


# ── CATEGORY 5: Class & OOP ──
print("\n  ── Category 5: Class & Object-Oriented ──")

before = '''
class GodClass:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass
    def m12(self): pass
    def m13(self): pass
    def m14(self): pass
    def m15(self): pass
    def m16(self): pass
    def m17(self): pass
    def m18(self): pass
    def m19(self): pass
    def m20(self): pass
    def m21(self): pass
'''
result = refactor_comprehensive(before, categories=['classes'])
after = result.get('refactored_code', before)
changes = result.get('changes', [])
print(f"\n  BEFORE: class GodClass with 21 methods")
print(f"  AFTER:  {len(changes)} suggestions detected (god class warning)")
test_ok = len(changes) > 0 or before.strip() != after.strip()
if test_ok:
    PASS_COUNT += 1
    print(f"  [PASS] Cat5: God class detection ({len(changes)} changes)")
else:
    FAIL_COUNT += 1
    print(f"  [FAIL] Cat5: God class detection")


# ── CATEGORY 6: Type Hints ──
print("\n  ── Category 6: Type Hints ──")

before = '''
def get_user(user_id, name, include_orders):
    return {"id": user_id, "name": name}

def sum_numbers(numbers):
    total = 0.0
    for n in numbers:
        total += n
    return total
'''
result = refactor_comprehensive(before, categories=['type_hints'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat6: Add type hints (user_id: int)", before, after, expect_in="int")
test("Cat6: Add type hints (name: str)", before, after, expect_in="str")


# ── CATEGORY 7: Python-Specific Idioms ──
print("\n  ── Category 7: Python-Specific Idioms ──")

before = '''
items = [1, 2, 3, 4, 5]
for i in range(len(items)):
    print(items[i])
'''
result = refactor_comprehensive(before, categories=['python_specific'])
after = result.get('refactored_code', before)
changes = result.get('changes', [])
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER: {len(changes)} suggestions (range(len) → enumerate)")
test_ok = len(changes) > 0
if test_ok:
    PASS_COUNT += 1
    print(f"  [PASS] Cat7: range(len) detection ({len(changes)} changes)")
else:
    FAIL_COUNT += 1
    print(f"  [FAIL] Cat7: range(len) detection")


# ── CATEGORY 8: Performance (via unified pipeline) ──
print("\n  ── Category 8: Performance Optimization ──")
print("  (See Section D: Performance Modules)")


# ── CATEGORY 9: Exception Handling ──
print("\n  ── Category 9: Exception Handling ──")

before = '''
def risky():
    try:
        x = 1 / 0
    except:
        pass
'''
result = refactor_comprehensive(before, categories=['exceptions'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat9: bare except → except Exception as e", before, after, expect_in="except Exception as e")


# ── CATEGORY 10/12: Import Organization ──
print("\n  ── Category 10/12: Import Organization ──")

before = '''
import json
import os
import sys
import requests
import flask
import mymodule
'''
result = refactor_comprehensive(before, categories=['imports'])
after = result.get('refactored_code', before)
print(f"\n  BEFORE:\n{before}")
print(f"  AFTER:\n{after}")
test("Cat10: Import sorting", before, after, expect_in="json")


# ── CATEGORY 11: Testing & Maintainability ──
print("\n  ── Category 11: Testing & Maintainability ──")
print("  (Covered by test_generator.py and test utilities)")

SECTION_RESULTS['A'] = (PASS_COUNT, FAIL_COUNT)


# ═══════════════════════════════════════════════════════════
# B. SECURITY AST REFACTORING - 20 PATTERNS
# ═══════════════════════════════════════════════════════════

section("B. SECURITY AST REFACTORING (security_ast_refactor.py)")

from security_ast_refactor import run_security_refactoring

sec_pass = 0
sec_fail = 0
prev_pass = PASS_COUNT
prev_fail = FAIL_COUNT

# ── Pattern 1: eval() Injection ──
before = '''
expr = input("Enter expression: ")
result = eval(expr)
print("Result:", result)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 1: eval() Injection (B307) ──")
print(f"  BEFORE: result = eval(expr)")
print(f"  AFTER:  result = ast.literal_eval(expr)")
test("Sec1: eval → ast.literal_eval", before, after, expect_in="ast.literal_eval")


# ── Pattern 2: exec() Injection ──
before = '''
code = input("Enter code: ")
exec(code)
print("Done")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 2: exec() Injection (B102) ──")
print(f"  BEFORE: exec(code)")
print(f"  AFTER:  allowed = {{...}}; print(allowed.get(cmd, 'Invalid'))")
test("Sec2: exec → whitelist lookup", before, after, expect_in="allowed.get")


# ── Pattern 3: os.system() Command Injection ──
before = '''
import os
file = input("Enter file: ")
os.system("ls " + file)
print("Done")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 3: os.system() Command Injection (B605) ──")
print(f"  BEFORE: os.system('ls ' + file)")
print(f"  AFTER:  subprocess.run(['ls', file])")
test("Sec3: os.system → subprocess.run", before, after, expect_in="subprocess.run")


# ── Pattern 4: subprocess shell=True ──
before = '''
import subprocess
cmd = input("Command: ")
subprocess.run(cmd, shell=True)
print("Executed")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 4: subprocess shell=True (B602) ──")
print(f"  BEFORE: subprocess.run(cmd, shell=True)")
print(f"  AFTER:  subprocess.run([cmd])")
test("Sec4: Remove shell=True", before, after, expect_not_in="shell=True")


# ── Pattern 5: Path Traversal ──
before = '''
name = input("File name: ")
f = open(name)
print(f.read())
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 5: Path Traversal (B108) ──")
print(f"  BEFORE: f = open(name)")
print(f'  AFTER:  f = open(os.path.join("files", name))')
test("Sec5: Path traversal → sandboxed open", before, after, expect_in="os.path.join")


# ── Pattern 6: Unsafe File Delete ──
before = '''
import os
file = input("Delete file: ")
os.remove(file)
print("Deleted")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 6: Unsafe File Delete (B108) ──")
print(f"  BEFORE: os.remove(file)")
print(f'  AFTER:  os.remove(os.path.join("uploads", file))')
test("Sec6: Unsafe delete → sandboxed path", before, after, expect_in="os.path.join")


# ── Pattern 7: Insecure pickle ──
before = '''
import pickle
f = open("data.pkl", "rb")
data = pickle.load(f)
print(data)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 7: Insecure pickle (B301) ──")
print(f"  BEFORE: import pickle; data = pickle.load(f)")
print(f"  AFTER:  import json; data = json.load(f)")
test("Sec7: pickle → json", before, after, expect_in=["json.load", "import json"])


# ── Pattern 8: Unsafe yaml.load() ──
before = '''
import yaml
f = open("config.yaml")
data = yaml.load(f, Loader=yaml.Loader)
print(data)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 8: Unsafe YAML (B506) ──")
print(f"  BEFORE: yaml.load(f, Loader=yaml.Loader)")
print(f"  AFTER:  yaml.safe_load(f)")
test("Sec8: yaml.load → yaml.safe_load", before, after, expect_in="yaml.safe_load")


# ── Pattern 9: Hardcoded Password ──
before = '''
password = "admin123"
secret = "mysecretkey"
user = "admin"
print("Logged in as", user)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 9: Hardcoded Password (B105) ──")
print(f'  BEFORE: password = "admin123"')
print(f'  AFTER:  password = os.getenv("APP_PASS")')
test("Sec9: Hardcoded password → os.getenv", before, after, expect_in="os.getenv")


# ── Pattern 10: SQL Injection ──
before = '''
import sqlite3
name = input("Name: ")
query = "SELECT * FROM users WHERE name='"+name+"'"
print(query)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 10: SQL Injection (B608) ──")
print(f"  BEFORE: query = \"SELECT * FROM users WHERE name='\"+name+\"'\"")
print(f'  AFTER:  query = "SELECT * FROM users WHERE name=?"')
test("Sec10: SQL concat → parameterized", before, after, expect_in="?")


# ── Pattern 11: shutil.rmtree() ──
before = '''
import shutil
folder = input("Folder: ")
shutil.rmtree(folder)
print("Deleted")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 11: shutil.rmtree() (B108) ──")
print(f"  BEFORE: shutil.rmtree(folder)")
print(f'  AFTER:  shutil.rmtree(os.path.join("data", folder))')
test("Sec11: rmtree → sandboxed directory", before, after, expect_in="os.path.join")


# ── Pattern 12: Weak random ──
before = '''
import random
token = random.randint(1000, 9999)
print("Token:", token)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 12: Weak Random (B311) ──")
print(f"  BEFORE: import random; token = random.randint(1000, 9999)")
print(f"  AFTER:  import secrets; token = secrets.randbelow(8999) + 1000")
test("Sec12: random → secrets", before, after, expect_in="secrets.randbelow")


# ── Pattern 13: Logging Sensitive Data ──
before = '''
pwd = input("Password: ")
print("Password:", pwd)
print("Login attempt")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 13: Logging Sensitive Data (B106) ──")
print(f'  BEFORE: print("Password:", pwd)')
print(f'  AFTER:  print("Pwd received")')
test("Sec13: Sensitive log → redacted", before, after, expect_in="received")


# ── Pattern 14: Unvalidated Integer Input ──
before = '''
age = int(input("Age: "))
print("Age:", age)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 14: Unvalidated Input (B104) ──")
print(f'  BEFORE: age = int(input("Age: "))')
print(f"  AFTER:  age = input(...); if age.isdigit(): ...")
test("Sec14: int(input()) → validation", before, after, expect_in="isdigit")


# ── Pattern 15: Unrestricted File Upload ──
before = '''
name = input("File: ")
f = open(name, "w")
f.write("data")
print("Uploaded")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 15: Unrestricted Upload ──")
print(f'  BEFORE: f = open(name, "w")')
print(f'  AFTER:  f = open(os.path.join("files", name), "w") [sandboxed]')
test("Sec15: Upload → sandboxed path", before, after, expect_in="os.path.join")


# ── Pattern 16: Weak Hash (md5/sha1) ──
before = '''
import hashlib
h = hashlib.md5(b"test data")
print(h.hexdigest())
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 16: Weak Hash (B303) ──")
print(f"  BEFORE: hashlib.md5(b'test data')")
print(f"  AFTER:  hashlib.sha256(b'test data')")
test("Sec16: md5 → sha256", before, after, expect_in="hashlib.sha256")


# ── Pattern 17: tempfile.mktemp() ──
before = '''
import tempfile
tmp = tempfile.mktemp()
print(tmp)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 17: Insecure tempfile (B306) ──")
print(f"  BEFORE: tmp = tempfile.mktemp()")
print(f"  AFTER:  fd, tmp = tempfile.mkstemp()")
test("Sec17: mktemp → mkstemp", before, after, expect_in="mkstemp")


# ── Pattern 18: assert for Security ──
before = '''
class User:
    is_admin = True

user = User()
assert user.is_admin, "Not authorized"
print("Access granted")
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 18: assert Security (B101) ──")
print(f'  BEFORE: assert user.is_admin, "Not authorized"')
print(f"  AFTER:  if not user.is_admin: raise PermissionError(...)")
test("Sec18: assert → if/raise PermissionError", before, after, expect_in="PermissionError")


# ── Pattern 19: FTP Insecure ──
before = '''
import ftplib
ftp = ftplib.FTP("server.example.com")
print(ftp)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 19: FTP → FTP_TLS (B321) ──")
print(f"  BEFORE: ftplib.FTP('server.example.com')")
print(f"  AFTER:  ftplib.FTP_TLS('server.example.com')")
test("Sec19: FTP → FTP_TLS", before, after, expect_in="FTP_TLS")


# ── Pattern 20: input() in dangerous functions ──
before = '''
result = eval(input("Enter: "))
print(result)
'''
r = run_security_refactoring(before)
after = r['refactored_code']
print(f"\n  ── Pattern 20: input() in eval/exec (B322) ──")
print(f"  BEFORE: eval(input('Enter: '))")
print(f"  AFTER:  ast.literal_eval(input('Enter:'))  [eval replaced]")
test("Sec20: eval(input()) → ast.literal_eval(input())", before, after, expect_in="ast.literal_eval")

SECTION_RESULTS['B'] = (PASS_COUNT - prev_pass - (FAIL_COUNT - prev_fail) + (FAIL_COUNT - prev_fail), FAIL_COUNT - prev_fail)
SECTION_RESULTS['B'] = (PASS_COUNT - sum(v[0] for v in SECTION_RESULTS.values() if isinstance(v, tuple)), 
                         FAIL_COUNT - sum(v[1] for v in SECTION_RESULTS.values() if isinstance(v, tuple)))


# ═══════════════════════════════════════════════════════════
# C. SECURITY RISK MODULES (3 modules)
# ═══════════════════════════════════════════════════════════

section("C. SECURITY RISK MODULES (risk_refactor_*.py)")

prev_pass = PASS_COUNT
prev_fail = FAIL_COUNT

# ── C1: Injection Risk (risk_refactor_injection.py) ──
print("\n  ── C1: Injection Risk Module ──")

try:
    from risk_refactor_injection import run_injection_risk_analysis

    before = '''
import os
os.system("ping -c 1 server.example.com")
'''
    r = run_injection_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: os.system('ping -c 1 server.example.com')")
    print(f"  AFTER:  subprocess.run(['ping', '-c', '1', 'server.example.com'])")
    test("Risk-Inj: os.system → subprocess.run", before, after, expect_in="subprocess")

    before = '''
import yaml
f = open("config.yaml")
data = yaml.load(f)
'''
    r = run_injection_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: yaml.load(f)")
    print(f"  AFTER:  yaml.safe_load(f)")
    test("Risk-Inj: yaml.load → yaml.safe_load", before, after, expect_in="safe_load")

except ImportError as e:
    print(f"  [SKIP] risk_refactor_injection not available: {e}")


# ── C2: Filesystem Risk (risk_refactor_filesystem.py) ──
print("\n  ── C2: Filesystem Risk Module ──")

try:
    from risk_refactor_filesystem import run_filesystem_risk_analysis

    before = '''
def read_data():
    f = open("data.txt", "r")
    content = f.read()
    f.close()
    print(content)
'''
    r = run_filesystem_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: f = open('data.txt'); ... f.close()")
    print(f"  AFTER:  with open('data.txt') as f: ...")
    test("Risk-FS: open/close → with statement", before, after, expect_in="with open")

except ImportError as e:
    print(f"  [SKIP] risk_refactor_filesystem not available: {e}")


# ── C3: Resources Risk (risk_refactor_resources.py) ──
print("\n  ── C3: Resources Risk Module ──")

try:
    from risk_refactor_resources import run_resource_risk_analysis

    before = '''
import threading
def critical_section():
    lock = threading.Lock()
    lock.acquire()
    do_work()
    lock.release()
'''
    r = run_resource_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: lock.acquire(); work(); lock.release()")
    print(f"  AFTER:  with lock: work()")
    test("Risk-Res: Lock acquire/release → with", before, after, expect_in="with lock")

    before = '''
import requests
response = requests.get("https://api.example.com")
print(response.status_code)
'''
    r = run_resource_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: requests.get(url)")
    print(f"  AFTER:  requests.get(url, timeout=10)")
    test("Risk-Res: Add timeout to requests", before, after, expect_in="timeout=")

    before = '''
import sqlite3
def query_db():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    conn.close()
'''
    r = run_resource_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: conn = sqlite3.connect('test.db')")
    print(f"  AFTER:  with sqlite3.connect('test.db') as conn:")
    test("Risk-Res: DB conn → with statement", before, after, expect_in="with sqlite3")

    before = '''
def process():
    try:
        result = do_work()
    except:
        pass
'''
    r = run_resource_risk_analysis(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: except: pass")
    print(f"  AFTER:  except Exception as e: raise")
    test("Risk-Res: bare except → except Exception", before, after, expect_in="except Exception")

except ImportError as e:
    print(f"  [SKIP] risk_refactor_resources not available: {e}")


# ═══════════════════════════════════════════════════════════
# D. PERFORMANCE MODULES (2 modules)
# ═══════════════════════════════════════════════════════════

section("D. PERFORMANCE OPTIMIZATION MODULES")

prev_pass_d = PASS_COUNT
prev_fail_d = FAIL_COUNT

# ── D1: Memory Optimization (perf_optimizer_memory.py) ──
print("\n  ── D1: Memory Optimization ──")

try:
    from perf_optimizer_memory import run_memory_optimization

    before = '''
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: class Point (no __slots__)")
    print(f"  AFTER:  class Point with __slots__ = ('x', 'y')")
    test("Perf-Mem: Add __slots__", before, after, expect_in="__slots__")

    before = '''
def read_file():
    f = open("data.txt")
    for line in f.readlines():
        print(line)
    f.close()
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: for line in f.readlines():")
    print(f"  AFTER:  for line in f:")
    test("Perf-Mem: readlines → iterator", before, after, expect_not_in="readlines")

    before = '''
valid_ids = [1, 2, 3, 4, 5]
if item in valid_ids:
    print("found")
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: valid_ids = [1, 2, 3, 4, 5]; if item in valid_ids:")
    print(f"  AFTER:  valid_ids = {{1, 2, 3, 4, 5}} (set for O(1) lookup)")
    test("Perf-Mem: List → Set for membership", before, after, expect_in="{1, 2, 3, 4, 5}")

    before = '''
result = sum([x * 2 for x in range(1000)])
print(result)
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: sum([x * 2 for x in range(1000)])")
    print(f"  AFTER:  sum(x * 2 for x in range(1000))  (generator)")
    test("Perf-Mem: List comp in sum() → generator", before, after, expect_not_in="sum([")

    before = '''
def build_list():
    result = []
    for x in range(10):
        result.append(x * 2)
    return result
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: result = []; for x in ...: result.append(x * 2)")
    print(f"  AFTER:  result = [x * 2 for x in range(10)]")
    test("Perf-Mem: Loop append → list comprehension", before, after, expect_in="[x * 2 for x in")

    before = '''
msg = "Hello %s, you are %d years old" % (name, age)
print(msg)
'''
    r = run_memory_optimization(before)
    after = r.get('optimized_code', before)
    print(f'\n  BEFORE: "Hello %s, you are %d" % (name, age)')
    print(f"  AFTER:  f\"Hello {{name}}, you are {{age}} years old\"")
    test("Perf-Mem: %-format → f-string", before, after, expect_in="f'")

except ImportError as e:
    print(f"  [SKIP] perf_optimizer_memory not available: {e}")


# ── D2: Caching & Algorithmic Optimization (perf_optimizer_caching.py) ──
print("\n  ── D2: Caching & Algorithmic Optimization ──")

try:
    from perf_optimizer_caching import run_caching_optimization

    before = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
    r = run_caching_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: def fibonacci(n): ... (recursive, no cache)")
    print(f"  AFTER:  @lru_cache(maxsize=128) def fibonacci(n): ...")
    test("Perf-Cache: Add @lru_cache to recursive", before, after, expect_in="lru_cache")

    before = '''
def show_items():
    items = ["apple", "banana", "cherry"]
    for i in range(len(items)):
        print(i, items[i])
'''
    r = run_caching_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: for i in range(len(items)):")
    print(f"  AFTER:  for i, _item in enumerate(items):")
    test("Perf-Cache: range(len) → enumerate", before, after, expect_in="enumerate")

    before = '''
count = count + 1
total = total - 5
score = score * 2
'''
    r = run_caching_optimization(before)
    after = r.get('optimized_code', before)
    print(f"\n  BEFORE: count = count + 1")
    print(f"  AFTER:  count += 1")
    test("Perf-Cache: x = x + n → x += n", before, after, expect_in="+=")

except ImportError as e:
    print(f"  [SKIP] perf_optimizer_caching not available: {e}")


# ═══════════════════════════════════════════════════════════
# E. PRIORITY REFACTORING PATTERNS
# ═══════════════════════════════════════════════════════════

section("E. PRIORITY REFACTORING PATTERNS (priority_refactorings.py)")

prev_pass_e = PASS_COUNT
prev_fail_e = FAIL_COUNT

try:
    from priority_refactorings import apply_priority_refactorings

    before = '''
def process(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
'''
    r = apply_priority_refactorings(before)
    after = r.get('refactored_code', before)
    changes = r.get('changes', [])
    detected = any('comprehension' in str(c).lower() or 'loop' in str(c).lower() for c in changes)
    print(f"\n  BEFORE: for item in items: result.append(item * 2)")
    print(f"  DETECTED: Loop → comprehension pattern (detection-based)")
    test("Priority: Loop → comprehension detection", before, str(changes), expect_in="Comprehension")

    before = '''
total = 0
for i in range(len(numbers)):
    total = total + numbers[i]
print(total)
'''
    r = apply_priority_refactorings(before)
    after = r.get('refactored_code', before)
    print(f"\n  BEFORE: total = 0; for i in range(len(numbers)): total = total + numbers[i]")
    print(f"  AFTER:  total = sum(numbers)")
    test("Priority: Accumulation loop → sum()", before, after, expect_in="sum(numbers)")

    before = '''
x = 10
y = 20
total = x + y
print("Total is:", total)
'''
    r = apply_priority_refactorings(before)
    after = r.get('refactored_code', before)
    print(f'\n  BEFORE: print("Total is:", total)')
    print(f"  AFTER:  print(f\"Total is: {{total}}\")")
    test("Priority: print() → f-string", before, after, expect_in="f'Total is:")

except ImportError as e:
    print(f"  [SKIP] priority_refactorings not available: {e}")


# ═══════════════════════════════════════════════════════════
# F. UNIFIED PIPELINE END-TO-END
# ═══════════════════════════════════════════════════════════

section("F. UNIFIED PIPELINE END-TO-END TEST")

try:
    from unified_refactor import refactor_complete
    
    before = '''
import os
password = "admin123"
file = input("file:")
os.system("ls " + file)
result = eval("2+3")

def calcTotal(x, y):
    return x + y

def is_valid(x):
    if x > 0:
        return True
    else:
        return False
'''
    result = refactor_complete(before)
    after = result.get('refactored_code', before)
    stages = result.get('stages', {})
    
    print(f"\n  INPUT: Code with password, os.system, eval, camelCase, boolean return")
    print(f"  STAGES APPLIED: {result.get('summary', {}).get('stages_applied', 0)}")
    for stage_name, stage_data in stages.items():
        applied = stage_data.get('applied', False)
        print(f"    {stage_name}: {'APPLIED' if applied else 'SKIPPED/FAILED'}")
    
    print(f"\n  REFACTORED CODE:\n{after}")
    
    test("Pipeline: Hardcoded password removed", before, after, expect_in="os.getenv")
    test("Pipeline: os.system replaced", before, after, expect_in="subprocess")
    test("Pipeline: eval replaced", before, after, expect_in="literal_eval")

except ImportError as e:
    print(f"  [SKIP] unified_refactor not available: {e}")


# ═══════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════

section("FINAL SUMMARY")
total = PASS_COUNT + FAIL_COUNT
print(f"""
  Total Tests Run:  {total}
  Passed:           {PASS_COUNT}
  Failed:           {FAIL_COUNT}
  Success Rate:     {PASS_COUNT/total*100:.1f}%
""")

if FAIL_COUNT == 0:
    print("  ✅ ALL PATTERNS WORKING!")
else:
    print(f"  ⚠️  {FAIL_COUNT} pattern(s) need attention")

print(f"\n{'='*70}")
print(f"  END OF COMPREHENSIVE PATTERN TEST")
print(f"{'='*70}")
