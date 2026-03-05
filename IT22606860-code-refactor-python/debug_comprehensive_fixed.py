"""
Debug comprehensive test case - FIXED
"""

original_code = '''
import os
import pickle
import sqlite3
import threading
import requests

counter = 0

class UserService:
    """Complete service with MULTIPLE ISSUES"""
    
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.lock = threading.Lock()
        self.valid_roles = ['admin', 'user', 'guest', 'moderator']
    
    def get_user(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()
    
    def run_admin_command(self, cmd):
        os.system(cmd)
    
    def load_session(self, session_data):
        return pickle.loads(session_data)
    
    def increment_counter(self):
        global counter
        self.lock.acquire()
        counter = counter + 1
        self.lock.release()
    
    def fetch_external_data(self, url):
        response = requests.get(url)
        return response.json()
    
    def read_config(self, path):
        f = open(path)
        return f.read()
    
    def has_permission(self, user_role):
        return user_role in self.valid_roles
    
    def process_users(self, users):
        result = ""
        for i in range(len(users)):
            try:
                result += str(users[i]['name']) + ","
            except:
                pass
        return result
    
    def calculate_fib(self, n):
        if n <= 1:
            return n
        return self.calculate_fib(n-1) + self.calculate_fib(n-2)
'''

code = original_code

print('=' * 60)
print('STAGE 1: Filesystem')
print('=' * 60)
from risk_refactor_filesystem import run_filesystem_risk_analysis
r1 = run_filesystem_risk_analysis(code)
prev_code = code
code = r1.get('refactored_code', code)
print(f'Issues: {len(r1.get("issues", []))}')
print(f'Changes: {r1.get("changes_applied", [])}')
print(f'Code changed: {prev_code != code}')

print()
print('=' * 60)
print('STAGE 2: Injection')
print('=' * 60)
from risk_refactor_injection import run_injection_risk_analysis
r2 = run_injection_risk_analysis(code)
prev_code = code
code = r2.get('refactored_code', code)
print(f'Issues: {len(r2.get("issues", []))}')
print(f'Changes: {r2.get("changes_applied", [])}')
print(f'Code changed: {prev_code != code}')

print()
print('=' * 60)
print('STAGE 3: Resources')
print('=' * 60)
from risk_refactor_resources import run_resource_risk_analysis
r3 = run_resource_risk_analysis(code)
prev_code = code
code = r3.get('refactored_code', code)
print(f'Issues: {len(r3.get("issues", []))}')
print(f'Changes: {r3.get("changes_applied", [])}')
print(f'Code changed: {prev_code != code}')

print()
print('=' * 60)
print('STAGE 4: Memory')
print('=' * 60)
from perf_optimizer_memory import run_memory_optimization
r4 = run_memory_optimization(code)
prev_code = code
code = r4.get('optimized_code', code)
print(f'Issues: {len(r4.get("issues", []))}')
print(f'Changes: {r4.get("changes_applied", [])}')
print(f'Code changed: {prev_code != code}')

print()
print('=' * 60)
print('STAGE 5: Caching')
print('=' * 60)
from perf_optimizer_caching import run_caching_optimization
r5 = run_caching_optimization(code)
prev_code = code
code = r5.get('optimized_code', code)
print(f'Issues: {len(r5.get("issues", []))}')
print(f'Changes: {r5.get("changes_applied", [])}')
print(f'Code changed: {prev_code != code}')

print()
print('=' * 60)
print('TOTAL CHANGE SUMMARY:')
print('=' * 60)
print(f'Original code length: {len(original_code)}')
print(f'Final code length: {len(code)}')
print(f'Code was modified: {original_code != code}')

print()
print('=' * 60)
print('FINAL CODE:')
print('=' * 60)
print(code)
