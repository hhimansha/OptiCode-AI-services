"""
Debug the unified pipeline stages
"""

code = '''
import threading
import sqlite3
import requests

class Test:
    def __init__(self):
        self.lock = threading.Lock()
    
    def test_lock(self):
        self.lock.acquire()
        self.counter = 1
        self.lock.release()
    
    def test_db(self):
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        return cursor.fetchall()
    
    def test_requests(self):
        response = requests.get('http://example.com')
        return response.json()
'''

print('=' * 60)
print('Stage 1: Filesystem')
from risk_refactor_filesystem import run_filesystem_risk_analysis
r1 = run_filesystem_risk_analysis(code)
code = r1.get('refactored_code', code)
print(f'Issues: {len(r1.get("issues", []))}')
print(f'Code length: {len(code)}')

print('=' * 60)
print('Stage 2: Injection')
from risk_refactor_injection import run_injection_risk_analysis
r2 = run_injection_risk_analysis(code)
code = r2.get('refactored_code', code)
print(f'Issues: {len(r2.get("issues", []))}')
print(f'Code length: {len(code)}')

print('=' * 60)
print('Stage 3: Resources')
from risk_refactor_resources import run_resource_risk_analysis
r3 = run_resource_risk_analysis(code)
code = r3.get('refactored_code', code)
print(f'Issues: {len(r3.get("issues", []))}')
for i in r3.get('issues', []):
    print(f'  {i.risk_type}')
print(f'Code length: {len(code)}')

print('=' * 60)
print('Final code:')
print(code)
