"""
==========================================================================
  OptiCode - PATTERN VERIFICATION TEST SUITE
  Author: IT22606860
  Purpose: Verify all refactoring patterns work correctly
==========================================================================
  Run this file to test all patterns:
    python verify_patterns.py
==========================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────
# Test Helpers
# ─────────────────────────────────────────────

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS = {}

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{Colors.RESET}\n")

def print_section(title):
    print(f"\n{Colors.CYAN}── {title} ──{Colors.RESET}")

def test_pattern(name, before_code, after_code, expect_in=None, expect_not_in=None):
    """Test if transformation produced expected results"""
    global PASS_COUNT, FAIL_COUNT
    
    ok = True
    reasons = []
    
    # Check code was transformed
    if before_code.strip() == after_code.strip():
        ok = False
        reasons.append("Code NOT transformed (same as input)")
    
    # Check expected substrings are present
    if expect_in:
        for exp in (expect_in if isinstance(expect_in, list) else [expect_in]):
            if exp not in after_code:
                ok = False
                reasons.append(f"Missing expected: '{exp}'")
    
    # Check unwanted substrings are absent
    if expect_not_in:
        for exp in (expect_not_in if isinstance(expect_not_in, list) else [expect_not_in]):
            if exp in after_code:
                ok = False
                reasons.append(f"Should NOT contain: '{exp}'")
    
    if ok:
        PASS_COUNT += 1
        print(f"  {Colors.GREEN}[PASS]{Colors.RESET} {name}")
    else:
        FAIL_COUNT += 1
        print(f"  {Colors.RED}[FAIL]{Colors.RESET} {name}")
        for r in reasons:
            print(f"         {Colors.YELLOW}{r}{Colors.RESET}")
    
    return ok


def show_before_after(before, after):
    """Display before and after code snippets"""
    print(f"\n  {Colors.CYAN}BEFORE:{Colors.RESET}")
    for line in before.strip().split('\n')[:8]:
        print(f"    {line}")
    print(f"\n  {Colors.CYAN}AFTER:{Colors.RESET}")
    for line in after.strip().split('\n')[:8]:
        print(f"    {line}")
    print()


# ═══════════════════════════════════════════════════════════
# SECTION 1: NAMING & READABILITY PATTERNS
# ═══════════════════════════════════════════════════════════

def test_naming_patterns():
    print_header("1. NAMING & READABILITY PATTERNS")
    
    from advanced_ast_refactor import refactor_comprehensive
    
    # Pattern 1.1: camelCase to snake_case
    print_section("Pattern 1.1: camelCase → snake_case")
    before = '''
def calcTotal(x, y):
    return x + y

result = calcTotal(10, 20)
'''
    result = refactor_comprehensive(before, categories=['naming'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("camelCase function → snake_case", before, after, expect_in="calc_total")
    
    # Pattern 1.2: Class naming to PascalCase
    print_section("Pattern 1.2: Class Naming → PascalCase")
    before = '''
class myclass:
    def __init__(self):
        pass

obj = myclass()
'''
    result = refactor_comprehensive(before, categories=['naming'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("Class name → PascalCase", before, after, expect_in="Myclass")


# ═══════════════════════════════════════════════════════════
# SECTION 2: CONDITIONAL LOGIC PATTERNS
# ═══════════════════════════════════════════════════════════

def test_conditional_patterns():
    print_header("2. CONDITIONAL LOGIC PATTERNS")
    
    from advanced_ast_refactor import refactor_comprehensive
    
    # Pattern 2.1: Nested if flattening
    print_section("Pattern 2.1: Flatten Nested If → Combined Condition")
    before = '''
def check_valid(a, b):
    if a > 0:
        if b > 0:
            return True
    return False
'''
    result = refactor_comprehensive(before, categories=['conditionals'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("Nested if → if a and b", before, after, expect_in="and")
    
    # Pattern 2.2: Boolean return simplification
    print_section("Pattern 2.2: Simplify Boolean Return")
    before = '''
def is_positive(x):
    if x > 0:
        return True
    else:
        return False
'''
    result = refactor_comprehensive(before, categories=['conditionals'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("if/else True/False → return condition", before, after, expect_in="return x > 0")


# ═══════════════════════════════════════════════════════════
# SECTION 3: VARIABLE & MAGIC NUMBER PATTERNS
# ═══════════════════════════════════════════════════════════

def test_variable_patterns():
    print_header("3. VARIABLE & MAGIC NUMBER PATTERNS")
    
    from advanced_ast_refactor import refactor_comprehensive
    
    print_section("Pattern 3.1: Magic Numbers → Named Constants")
    before = '''
def calculate_price(quantity):
    tax = quantity * 2.5
    discount = quantity * 1.8
    shipping = quantity * 1.2
    return tax + discount + shipping
'''
    result = refactor_comprehensive(before, categories=['variables'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("Magic numbers → CONSTANT_", before, after, expect_in="CONSTANT_")


# ═══════════════════════════════════════════════════════════
# SECTION 4: TYPE HINTS PATTERNS
# ═══════════════════════════════════════════════════════════

def test_type_hint_patterns():
    print_header("4. TYPE HINTS PATTERNS")
    
    from advanced_ast_refactor import refactor_comprehensive
    
    print_section("Pattern 4.1: Add Type Hints to Function")
    before = '''
def get_user(user_id, name, include_details):
    return {"id": user_id, "name": name}

def calculate_sum(numbers):
    total = 0.0
    for n in numbers:
        total += n
    return total
'''
    result = refactor_comprehensive(before, categories=['type_hints'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("Add type hints (int, str)", before, after, expect_in="int")


# ═══════════════════════════════════════════════════════════
# SECTION 5: EXCEPTION HANDLING PATTERNS
# ═══════════════════════════════════════════════════════════

def test_exception_patterns():
    print_header("5. EXCEPTION HANDLING PATTERNS")
    
    from advanced_ast_refactor import refactor_comprehensive
    
    print_section("Pattern 5.1: Bare Except → except Exception as e")
    before = '''
def risky_operation():
    try:
        result = 1 / 0
    except:
        pass
'''
    result = refactor_comprehensive(before, categories=['exceptions'])
    after = result.get('refactored_code', before)
    show_before_after(before, after)
    test_pattern("bare except → except Exception as e", before, after, expect_in="except Exception as e")


# ═══════════════════════════════════════════════════════════
# SECTION 6: SECURITY PATTERNS (20 Patterns)
# ═══════════════════════════════════════════════════════════

def test_security_patterns():
    print_header("6. SECURITY AST PATTERNS (20 Patterns)")
    
    from security_ast_refactor import run_security_refactoring
    
    # Pattern 6.1: eval() Injection
    print_section("Pattern 6.1: eval() → ast.literal_eval()")
    before = '''
expr = input("Enter: ")
result = eval(expr)
print(result)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: eval → ast.literal_eval", before, after, expect_in="ast.literal_eval")
    
    # Pattern 6.2: exec() → whitelist
    print_section("Pattern 6.2: exec() → Whitelist Lookup")
    before = '''
code = input("Code: ")
exec(code)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: exec → allowed.get", before, after, expect_in="allowed.get")
    
    # Pattern 6.3: os.system() Command Injection
    print_section("Pattern 6.3: os.system() → subprocess.run()")
    before = '''
import os
filename = input("File: ")
os.system("ls " + filename)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: os.system → subprocess.run", before, after, expect_in="subprocess.run")
    
    # Pattern 6.4: subprocess shell=True
    print_section("Pattern 6.4: Remove shell=True")
    before = '''
import subprocess
cmd = input("Cmd: ")
subprocess.run(cmd, shell=True)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: Remove shell=True", before, after, expect_not_in="shell=True")
    
    # Pattern 6.5: Path Traversal
    print_section("Pattern 6.5: Path Traversal → Sandboxed Path")
    before = '''
name = input("File: ")
f = open(name)
data = f.read()
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: open → os.path.join sandboxed", before, after, expect_in="os.path.join")
    
    # Pattern 6.6: Insecure pickle
    print_section("Pattern 6.6: pickle.load() → json.load()")
    before = '''
import pickle
f = open("data.pkl", "rb")
data = pickle.load(f)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: pickle → json", before, after, expect_in="json.load")
    
    # Pattern 6.7: Unsafe yaml.load
    print_section("Pattern 6.7: yaml.load() → yaml.safe_load()")
    before = '''
import yaml
f = open("config.yaml")
data = yaml.load(f, Loader=yaml.Loader)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: yaml.load → yaml.safe_load", before, after, expect_in="yaml.safe_load")
    
    # Pattern 6.8: Hardcoded Password
    print_section("Pattern 6.8: Hardcoded Password → os.getenv()")
    before = '''
password = "admin123"
secret_key = "mysecret"
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: Hardcoded password → os.getenv", before, after, expect_in="os.getenv")
    
    # Pattern 6.9: SQL Injection
    print_section("Pattern 6.9: SQL Injection → Parameterized Query")
    before = '''
import sqlite3
name = input("Name: ")
query = "SELECT * FROM users WHERE name='"+name+"'"
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: SQL concat → parameterized (?)", before, after, expect_in="?")
    
    # Pattern 6.10: Weak random
    print_section("Pattern 6.10: random.randint() → secrets.randbelow()")
    before = '''
import random
token = random.randint(1000, 9999)
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: random → secrets", before, after, expect_in="secrets.randbelow")
    
    # Pattern 6.11: Weak Hash
    print_section("Pattern 6.11: hashlib.md5() → hashlib.sha256()")
    before = '''
import hashlib
h = hashlib.md5(b"test data")
digest = h.hexdigest()
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: md5 → sha256", before, after, expect_in="hashlib.sha256")
    
    # Pattern 6.12: Insecure tempfile
    print_section("Pattern 6.12: tempfile.mktemp() → tempfile.mkstemp()")
    before = '''
import tempfile
tmp = tempfile.mktemp()
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: mktemp → mkstemp", before, after, expect_in="mkstemp")
    
    # Pattern 6.13: assert for Security
    print_section("Pattern 6.13: assert → if/raise PermissionError")
    before = '''
user = {"is_admin": True}
assert user["is_admin"], "Not authorized"
print("Access granted")
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: assert → if/raise PermissionError", before, after, expect_in="PermissionError")
    
    # Pattern 6.14: FTP → FTP_TLS
    print_section("Pattern 6.14: ftplib.FTP() → ftplib.FTP_TLS()")
    before = '''
import ftplib
ftp = ftplib.FTP("server.example.com")
'''
    r = run_security_refactoring(before)
    after = r['refactored_code']
    show_before_after(before, after)
    test_pattern("Sec: FTP → FTP_TLS", before, after, expect_in="FTP_TLS")


# ═══════════════════════════════════════════════════════════
# SECTION 7: PERFORMANCE OPTIMIZATION PATTERNS
# ═══════════════════════════════════════════════════════════

def test_performance_patterns():
    print_header("7. PERFORMANCE OPTIMIZATION PATTERNS")
    
    from perf_optimizer_caching import run_caching_optimization
    from perf_optimizer_memory import run_memory_optimization
    
    # Pattern 7.1: Augmented assignment
    print_section("Pattern 7.1: x = x + 1 → x += 1")
    before = '''
def update_counter():
    counter = 0
    counter = counter + 1
    total = 1
    total = total * 2
    return counter, total
'''
    result = run_caching_optimization(before)
    after = result['optimized_code']
    show_before_after(before, after)
    test_pattern("Perf: x = x + 1 → x += 1", before, after, expect_in="+=")
    
    # Pattern 7.2: List comprehension
    print_section("Pattern 7.2: Loop append → List Comprehension")
    before = '''
def double_items(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
'''
    result = run_memory_optimization(before)
    after = result['optimized_code']
    show_before_after(before, after)
    test_pattern("Perf: Loop append → comprehension", before, after, expect_in="[")
    
    # Pattern 7.3: % formatting to f-string
    print_section("Pattern 7.3: % Formatting → f-string")
    before = '''
def greet(name, age):
    message = "Hello %s, you are %d years old" % (name, age)
    return message
'''
    result = run_memory_optimization(before)
    after = result['optimized_code']
    show_before_after(before, after)
    # Accept both f"..." and f'...' as valid f-strings
    has_fstring = "f\"" in after or "f'" in after
    if has_fstring:
        test_pattern("Perf: % formatting → f-string", before, after, expect_in="f'")
    else:
        test_pattern("Perf: % formatting → f-string", before, after, expect_in="f\"")


# ═══════════════════════════════════════════════════════════
# SECTION 8: RISK REFACTORING PATTERNS
# ═══════════════════════════════════════════════════════════

def test_risk_patterns():
    print_header("8. RISK REFACTORING PATTERNS")
    
    # Injection Risk
    print_section("Pattern 8.1: Injection Risk - os.system")
    try:
        from risk_refactor_injection import run_injection_risk_analysis
        
        before = '''
import os
os.system("ping -c 1 server.example.com")
'''
        r = run_injection_risk_analysis(before)
        after = r.get('refactored_code', before)
        show_before_after(before, after)
        test_pattern("Risk: os.system → subprocess", before, after, expect_in="subprocess")
    except ImportError as e:
        print(f"  {Colors.YELLOW}[SKIP] Module not available: {e}{Colors.RESET}")
    
    # Filesystem Risk
    print_section("Pattern 8.2: Filesystem Risk - open/close → with")
    try:
        from risk_refactor_filesystem import run_filesystem_risk_analysis
        
        before = '''
def read_data():
    f = open("data.txt", "r")
    content = f.read()
    f.close()
    return content
'''
        r = run_filesystem_risk_analysis(before)
        after = r.get('refactored_code', before)
        show_before_after(before, after)
        test_pattern("Risk: open/close → with statement", before, after, expect_in="with open")
    except ImportError as e:
        print(f"  {Colors.YELLOW}[SKIP] Module not available: {e}{Colors.RESET}")
    
    # Resource Risk
    print_section("Pattern 8.3: Resource Risk - Lock acquire/release → with")
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
        show_before_after(before, after)
        test_pattern("Risk: Lock acquire/release → with", before, after, expect_in="with lock")
    except ImportError as e:
        print(f"  {Colors.YELLOW}[SKIP] Module not available: {e}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════
# SECTION 9: UNIFIED RISK & PERFORMANCE ANALYSIS
# ═══════════════════════════════════════════════════════════

def test_unified_analysis():
    print_header("9. UNIFIED RISK & PERFORMANCE ANALYSIS")
    
    from unified_risk_refactor import refactor_risk_and_performance
    
    print_section("Pattern 9.1: Complete Service Analysis")
    before = '''
import os
import pickle
import sqlite3

class UserService:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
    
    def get_user(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()
    
    def run_command(self, cmd):
        os.system(cmd)
    
    def load_session(self, data):
        return pickle.loads(data)
'''
    result = refactor_risk_and_performance(before)
    after = result['refactored_code']
    
    print(f"\n  {Colors.CYAN}ANALYSIS RESULTS:{Colors.RESET}")
    print(f"    Total Issues: {result['total_issues']}")
    print(f"    Risk Score: {result['overall_risk_score']}/100")
    print(f"    Performance Score: {result['overall_perf_score']}/100")
    
    if result['issues']:
        print(f"\n  {Colors.CYAN}ISSUES FOUND:{Colors.RESET}")
        for issue in result['issues'][:5]:
            print(f"    [{issue.severity:8}] {issue.issue_type} @ line {issue.line}")
    
    show_before_after(before, after)
    
    # Verify some transformations occurred
    ok = result['total_issues'] > 0
    if ok:
        global PASS_COUNT
        PASS_COUNT += 1
        print(f"  {Colors.GREEN}[PASS]{Colors.RESET} Unified analysis detected issues")
    else:
        global FAIL_COUNT
        FAIL_COUNT += 1
        print(f"  {Colors.RED}[FAIL]{Colors.RESET} Unified analysis detected issues")


# ═══════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════

def run_all_tests():
    """Run all pattern verification tests"""
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           OptiCode - PATTERN VERIFICATION TEST SUITE                 ║")
    print("║                  Testing All Refactoring Patterns                    ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    # Run all test sections
    test_naming_patterns()
    test_conditional_patterns()
    test_variable_patterns()
    test_type_hint_patterns()
    test_exception_patterns()
    test_security_patterns()
    test_performance_patterns()
    test_risk_patterns()
    test_unified_analysis()
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*70}{Colors.RESET}\n")
    
    total = PASS_COUNT + FAIL_COUNT
    pass_rate = (PASS_COUNT / total * 100) if total > 0 else 0
    
    print(f"  {Colors.GREEN}PASSED: {PASS_COUNT}{Colors.RESET}")
    print(f"  {Colors.RED}FAILED: {FAIL_COUNT}{Colors.RESET}")
    print(f"  TOTAL:  {total}")
    print(f"\n  Pass Rate: {pass_rate:.1f}%")
    
    if FAIL_COUNT == 0:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}✓ ALL PATTERNS WORKING CORRECTLY!{Colors.RESET}")
    else:
        print(f"\n  {Colors.YELLOW}⚠ Some patterns need attention{Colors.RESET}")
    
    print()
    return FAIL_COUNT == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
