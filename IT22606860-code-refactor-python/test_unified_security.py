"""Test unified pipeline with security stage"""
from unified_refactor import refactor_complete

code = '''
import os
password = "admin123"
file = input("file:")
os.system("ls " + file)
result = eval("2+3")
'''

result = refactor_complete(code, {
    'apply_basic': False, 'apply_priority': False, 'apply_advanced': False,
    'apply_performance': False, 'apply_risk': False, 'apply_security': True
})

print()
print("=== SECURITY STAGE RESULT ===")
sec = result['stages'].get('security_ast', {})
print(f"Applied: {sec.get('applied')}")
print(f"Issues: {sec.get('total_issues')}")
print(f"Fixes: {sec.get('total_fixes')}")
print(f"Risk Score: {sec.get('risk_score')}")
print()
print("REFACTORED CODE:")
print(result['refactored_code'])
