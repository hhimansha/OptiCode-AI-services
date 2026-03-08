"""
Final comprehensive test - Testing ALL documentation examples
"""

from unified_risk_refactor import refactor_risk_and_performance

# ══════════════════════════════════════════════════════════════════════
# TEST: Complete Application with Multiple Issues (from documentation)
# ══════════════════════════════════════════════════════════════════════

code = '''
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

result = refactor_risk_and_performance(code)

print("=" * 70)
print("COMPREHENSIVE CODE ANALYSIS RESULTS")
print("=" * 70)
print()
print(f"Total Issues Found: {result['total_issues']}")
print(f"Risk Score: {result['overall_risk_score']}/100")
print(f"Performance Score: {result['overall_perf_score']}/100")
print()
print("─" * 70)
print("ISSUES DETECTED:")
print("─" * 70)
for issue in result['issues']:
    print(f"  [{issue.severity:8}] {issue.issue_type:30} @ line {issue.line}")
print()
print("─" * 70)
print("CATEGORY BREAKDOWN:")
print("─" * 70)
for cat, info in result['category_breakdown'].items():
    if 'count' in info:
        print(f"  {cat}: {info['count']} issues")
    elif 'error' in info:
        print(f"  {cat}: ERROR - {info['error']}")
print()
print("=" * 70)
print("REFACTORED CODE:")
print("=" * 70)
print(result['refactored_code'])
