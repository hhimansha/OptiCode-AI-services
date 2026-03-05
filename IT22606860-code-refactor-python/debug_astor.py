"""
Debug astor conversion
"""
import ast
import astor

code = '''
import threading

counter = 0

class UserService:
    def __init__(self):
        self.lock = threading.Lock()
    
    def increment_counter(self):
        global counter
        self.lock.acquire()
        counter = counter + 1
        self.lock.release()
'''

print("Testing transformer directly + astor conversion...")

# Parse and transform
tree = ast.parse(code)

# Import and run transformer
import sys
sys.path.insert(0, '.')
from risk_refactor_resources import ConvertLockToWith

t = ConvertLockToWith()
tree = t.visit(tree)
ast.fix_missing_locations(tree)

print(f"Changes recorded: {t.changes}")

# Try to convert with astor
try:
    refactored = astor.to_source(tree)
    print("astor SUCCESS")
    print(refactored)
except Exception as e:
    print(f"astor FAILED: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Now testing run_resource_risk_analysis function...")
print("=" * 60)

from risk_refactor_resources import run_resource_risk_analysis
result = run_resource_risk_analysis(code)

print(f"Issues: {len(result['issues'])}")
print(f"Changes: {result['changes_applied']}")
print(f"Refactored code same as original: {result['refactored_code'].strip() == code.strip()}")
print()
print("REFACTORED CODE:")
print(result['refactored_code'])
