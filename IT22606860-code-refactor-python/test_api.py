"""
Test the refactor API endpoint - Comprehensive
"""
import requests

code = '''
import threading
import requests as req
import yaml

class Service:
    def __init__(self):
        self.lock = threading.Lock()
        self.roles = ["admin", "user"]
    
    def work(self):
        self.lock.acquire()
        x = 1
        self.lock.release()
    
    def fetch(self, url):
        return req.get(url).json()
    
    def read_cfg(self, path):
        f = open(path)
        return yaml.load(f)
    
    def has_role(self, r):
        return r in self.roles
    
    def fib(self, n):
        if n <= 1:
            return n
        return self.fib(n-1) + self.fib(n-2)
'''

print("Testing /api/refactor endpoint...")
try:
    response = requests.post("http://localhost:8000/api/refactor", json={"code": code})
    print("Status:", response.status_code)
    
    if response.status_code == 200:
        result = response.json()
        refactored = result.get('refactored_code', '')
        
        print()
        print("="*60)
        print("REFACTORED CODE:")
        print("="*60)
        print(refactored)
        
        print()
        print("="*60)
        print("TRANSFORMATION CHECK:")
        print("="*60)
        checks = [
            ('Lock -> with block', 'with self.lock:' in refactored),
            ('Timeout added to requests', 'timeout=' in refactored),
            ('File open -> with', 'with open(path)' in refactored),
            ('yaml.load -> safe_load', 'safe_load' in refactored),
            ('List -> Set', 'roles = {' in refactored or "roles = {" in refactored),
            ('lru_cache added', 'lru_cache' in refactored),
        ]
        for name, passed in checks:
            status = 'PASS' if passed else 'FAIL'
            print(f'{status}: {name}')
except Exception as e:
    print(f"Error: {e}")
