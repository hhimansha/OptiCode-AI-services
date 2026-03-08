"""
Debug transformer behavior
"""
import ast
import astor

code = '''
import threading

class Service:
    def __init__(self):
        self.lock = threading.Lock()
    
    def test(self):
        self.lock.acquire()
        print("in lock")
        self.lock.release()
'''

print("ORIGINAL:")
print(code)

# Import our transformer
import sys
sys.path.insert(0, '.')
from risk_refactor_resources import ConvertLockToWith

tree = ast.parse(code)
print("\nTREE BEFORE:")
print(ast.dump(tree, indent=2)[:1000])

t = ConvertLockToWith()
transformed_tree = t.visit(tree)
ast.fix_missing_locations(transformed_tree)

print("\nCHANGES:")
print(t.changes)

print("\nTREE AFTER:")
print(ast.dump(transformed_tree, indent=2)[:1000])

print("\nCODE AFTER:")
result = astor.to_source(transformed_tree)
print(result)

print("\nSAME?", code.strip() == result.strip())
