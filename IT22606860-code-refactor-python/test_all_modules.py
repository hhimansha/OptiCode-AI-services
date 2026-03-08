"""
Comprehensive test script to identify what's not being refactored.
"""

from unified_risk_refactor import refactor_risk_and_performance

# Test 1: Shell Injection
print("=" * 70)
print("TEST 1: SHELL INJECTION")
print("=" * 70)

code1 = '''
import os
import subprocess

class CommandExecutor:
    def run_system_command(self, user_command):
        os.system(user_command)
    
    def run_subprocess_shell(self, cmd_parts):
        full_cmd = " ".join(cmd_parts)
        result = subprocess.run(full_cmd, shell=True, capture_output=True)
        return result.stdout.decode()
'''

result1 = refactor_risk_and_performance(code1)
print(f"Issues found: {result1['total_issues']}")
for issue in result1['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result1['refactored_code'])


# Test 2: SQL Injection
print("\n" + "=" * 70)
print("TEST 2: SQL INJECTION")
print("=" * 70)

code2 = '''
import sqlite3

class UserDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def get_user_by_id(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        self.cursor.execute(query)
        return self.cursor.fetchone()
    
    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username = '" + username + "'"
        self.cursor.execute(query)
        return self.cursor.fetchone()
'''

result2 = refactor_risk_and_performance(code2)
print(f"Issues found: {result2['total_issues']}")
for issue in result2['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result2['refactored_code'])


# Test 3: Resource Leaks (Lock, File, DB)
print("\n" + "=" * 70)
print("TEST 3: RESOURCE LEAKS")
print("=" * 70)

code3 = '''
import threading
import sqlite3

class ResourceManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.counter = 0
    
    def increment_counter(self):
        self.lock.acquire()
        self.counter += 1
        self.lock.release()
    
    def read_file(self, path):
        f = open(path)
        return f.read()
    
    def query_database(self, query):
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
'''

result3 = refactor_risk_and_performance(code3)
print(f"Issues found: {result3['total_issues']}")
for issue in result3['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result3['refactored_code'])


# Test 4: Recursive without caching
print("\n" + "=" * 70)
print("TEST 4: RECURSIVE WITHOUT CACHING")
print("=" * 70)

code4 = '''
class MathSolver:
    def fibonacci(self, n):
        if n <= 1:
            return n
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)
    
    def factorial(self, n):
        if n <= 1:
            return 1
        return n * self.factorial(n - 1)
'''

result4 = refactor_risk_and_performance(code4)
print(f"Issues found: {result4['total_issues']}")
for issue in result4['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result4['refactored_code'])


# Test 5: Bare except
print("\n" + "=" * 70)
print("TEST 5: BARE EXCEPT")
print("=" * 70)

code5 = '''
class DataService:
    def fetch_user(self, user_id):
        try:
            response = self.api.get_user(user_id)
            return response
        except:
            pass
    
    def risky_calculation(self, x, y):
        try:
            return x / y
        except:
            pass
'''

result5 = refactor_risk_and_performance(code5)
print(f"Issues found: {result5['total_issues']}")
for issue in result5['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result5['refactored_code'])


# Test 6: Pickle & YAML
print("\n" + "=" * 70)
print("TEST 6: UNSAFE DESERIALIZATION (PICKLE/YAML)")
print("=" * 70)

code6 = '''
import pickle
import yaml

class DataLoader:
    def load_pickle_data(self, filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        return data
    
    def load_yaml_config(self, filepath):
        with open(filepath) as f:
            config = yaml.load(f)
        return config
'''

result6 = refactor_risk_and_performance(code6)
print(f"Issues found: {result6['total_issues']}")
for issue in result6['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result6['refactored_code'])


# Test 7: String concatenation in loop
print("\n" + "=" * 70)
print("TEST 7: STRING CONCAT IN LOOP")
print("=" * 70)

code7 = '''
class ReportGenerator:
    def generate_csv_report(self, records):
        csv_output = ""
        csv_output += "id,name,email\\n"
        for record in records:
            csv_output += str(record['id']) + ","
            csv_output += record['name'] + ","
            csv_output += record['email'] + "\\n"
        return csv_output
'''

result7 = refactor_risk_and_performance(code7)
print(f"Issues found: {result7['total_issues']}")
for issue in result7['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result7['refactored_code'])


# Test 8: List instead of set
print("\n" + "=" * 70)
print("TEST 8: LIST INSTEAD OF SET")
print("=" * 70)

code8 = '''
class DataProcessor:
    def __init__(self):
        self.valid_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.blocked_ips = ['192.168.1.1', '10.0.0.1', '172.16.0.1']
    
    def is_valid_id(self, id_value):
        return id_value in self.valid_ids
    
    def is_blocked_ip(self, ip):
        return ip in self.blocked_ips
'''

result8 = refactor_risk_and_performance(code8)
print(f"Issues found: {result8['total_issues']}")
for issue in result8['issues']:
    print(f"  [{issue.severity}] {issue.issue_type} at line {issue.line}")
print("\nRefactored code:")
print(result8['refactored_code'])


print("\n" + "=" * 70)
print("SUMMARY OF ISSUES FOUND")
print("=" * 70)
print(f"Test 1 (Shell Injection):    {result1['total_issues']} issues")
print(f"Test 2 (SQL Injection):      {result2['total_issues']} issues")
print(f"Test 3 (Resource Leaks):     {result3['total_issues']} issues")
print(f"Test 4 (Recursive/Cache):    {result4['total_issues']} issues")
print(f"Test 5 (Bare Except):        {result5['total_issues']} issues")
print(f"Test 6 (Pickle/YAML):        {result6['total_issues']} issues")
print(f"Test 7 (String Concat):      {result7['total_issues']} issues")
print(f"Test 8 (List vs Set):        {result8['total_issues']} issues")
