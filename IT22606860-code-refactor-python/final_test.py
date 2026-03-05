"""
Final comprehensive test of all refactoring transformations
"""
from unified_risk_refactor import refactor_risk_and_performance

code = '''
import os
import pickle
import sqlite3
import threading
import requests
import yaml

counter = 0

class UserService:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.lock = threading.Lock()
        self.valid_roles = ["admin", "user", "guest"]
    
    def increment_counter(self):
        global counter
        self.lock.acquire()
        counter = counter + 1
        self.lock.release()
    
    def fetch_data(self, url):
        return requests.get(url).json()
    
    def read_config(self, path):
        f = open(path)
        return yaml.load(f)
    
    def has_role(self, role):
        return role in self.valid_roles
    
    def process(self, users):
        result = ""
        for i in range(len(users)):
            try:
                result = result + str(users[i]) + ","
            except:
                pass
        return result
    
    def fib(self, n):
        if n <= 1:
            return n
        return self.fib(n-1) + self.fib(n-2)
'''

print('='*60)
print('ORIGINAL CODE:')
print('='*60)
print(code)
print()
print('='*60)
print('RUNNING REFACTORING...')
print('='*60)
print()

result = refactor_risk_and_performance(code)

print('Total issues found:', result['total_issues'])
print('Code was modified:', code.strip() != result['refactored_code'].strip())
print()
print('='*60)
print('REFACTORED CODE:')
print('='*60)
print(result['refactored_code'])

# Check what was transformed
refactored = result['refactored_code']
print()
print('='*60)
print('TRANSFORMATION CHECK:')
print('='*60)
checks = [
    ('Lock -> with block', 'with self.lock:' in refactored),
    ('Timeout added', 'timeout=10' in refactored or 'timeout=' in refactored),
    ('File open -> with', 'with open(path)' in refactored),
    ('yaml.load -> safe_load', 'safe_load' in refactored),
    ('List -> Set', 'valid_roles = {' in refactored or "valid_roles = {" in refactored),
    ('Bare except -> Exception', 'except Exception' in refactored),
    ('range(len) -> enumerate', 'enumerate' in refactored),
    ('counter + 1 -> +=', 'counter += 1' in refactored),
    ('lru_cache added', 'lru_cache' in refactored),
]
for name, passed in checks:
    status = '✓ PASS' if passed else '✗ FAIL'
    print(f'{status}: {name}')
