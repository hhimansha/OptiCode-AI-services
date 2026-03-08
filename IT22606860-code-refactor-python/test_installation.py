"""
Test Script - Verify OptiCode Installation
Run this script to test if all modules are properly installed and working
"""

import sys
import importlib

print("="*70)
print("OptiCode - Installation Test Script")
print("="*70)
print()

# Required modules
required_modules = [
    ('flask', 'Flask'),
    ('flask_cors', 'Flask-CORS'),
    ('transformers', 'Transformers'),
    ('torch', 'PyTorch'),
    ('openai', 'OpenAI'),
    ('astor', 'Astor'),
    ('bandit', 'Bandit'),
    ('radon', 'Radon'),
    ('pylint', 'Pylint'),
    ('autopep8', 'Autopep8'),
]

print("[1/3] Checking Required Packages...")
print("-" * 70)

all_installed = True
for module_name, display_name in required_modules:
    try:
        importlib.import_module(module_name)
        print(f"✓ {display_name:20} - Installed")
    except ImportError:
        print(f"✗ {display_name:20} - NOT INSTALLED")
        all_installed = False

print()

# Check custom modules
print("[2/3] Checking Custom Modules...")
print("-" * 70)

custom_modules = [
    'ast_refactor',
    'code_analyzer',
    'best_practices',
    'ethical_code_analyzer',
]

modules_ok = True
for module_name in custom_modules:
    try:
        module = importlib.import_module(module_name)
        print(f"✓ {module_name:25} - OK")
    except Exception as e:
        print(f"✗ {module_name:25} - ERROR: {str(e)}")
        modules_ok = False

print()

# Quick functionality test
print("[3/3] Testing Functionality...")
print("-" * 70)

try:
    from ast_refactor import refactor_code_ast
    
    # Test simple refactoring
    test_code = """
def check_positive(x):
    if x > 0:
        return True
    else:
        return False
"""
    
    result = refactor_code_ast(test_code)
    
    if result['success'] and 'return x > 0' in result['refactored_code']:
        print("✓ AST Refactoring - Working correctly")
    else:
        print("✗ AST Refactoring - Unexpected result")
        
except Exception as e:
    print(f"✗ AST Refactoring - ERROR: {str(e)}")

try:
    from code_analyzer import analyze_code
    
    result = analyze_code("def hello():\n    print('Hello')")
    
    if result['success']:
        print("✓ Code Analysis - Working correctly")
    else:
        print("✗ Code Analysis - Failed")
        
except Exception as e:
    print(f"✗ Code Analysis - ERROR: {str(e)}")

try:
    from best_practices import check_best_practices
    
    result = check_best_practices("def test():\n    pass")
    
    if result['success']:
        print("✓ Best Practices - Working correctly")
    else:
        print("✗ Best Practices - Failed")
        
except Exception as e:
    print(f"✗ Best Practices - ERROR: {str(e)}")

try:
    from ethical_code_analyzer import analyze_ethical_code
    
    result = analyze_ethical_code("def test():\n    pass")
    
    if result['success']:
        print("✓ Ethical Analysis - Working correctly")
    else:
        print("✗ Ethical Analysis - Failed")
        
except Exception as e:
    print(f"✗ Ethical Analysis - ERROR: {str(e)}")

print()
print("="*70)

if all_installed and modules_ok:
    print("✅ All Tests Passed! You're ready to start the services.")
    print()
    print("Next Steps:")
    print("1. Start refactor API:        python refactor_api.py")
    print("2. Start risk analysis API:   python risk_analysis_api.py")
    print("3. Start learning API:        python learning_api.py")
    print()
    print("Then test with: http://localhost:8000/health")
else:
    print("❌ Some tests failed. Please install missing packages:")
    print()
    print("Run: pip install -r requirements.txt")

print("="*70)
