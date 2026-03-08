"""
Simple test for priority refactorings - No Unicode characters
"""
import requests
import json


# Test code with multiple refactoring opportunities
test_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
    print("This will never execute")  # Dead code
    
def get_even_numbers(numbers):
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num)
    return result
"""

print("="*80)
print(" TESTING PRIORITY REFACTORINGS")
print("="*80)

# Test 1: Apply priority refactorings
print("\n1. Testing /api/priority-refactor...")
try:
    response = requests.post('http://localhost:8000/api/priority-refactor', json={
        'code': test_code
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Status: {response.status_code}")
        print(f"Patterns Applied: {result.get('patterns_applied', 0)}")
        print(f"Total Changes: {len(result.get('changes', []))}")
        
        print("\nDetected Issues:")
        for change in result.get('changes', [])[:5]:
            print(f"  - {change['pattern_name']} (Line {change['line']})")
            print(f"    {change['description']}")
        
    else:
        print(f"ERROR: Status {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Get priority patterns list
print("\n2. Testing /api/priority-patterns...")
try:
    response = requests.get('http://localhost:8000/api/priority-patterns')
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Total Patterns: {result.get('count', 0)}")
        
        print("\nTop 10 Priority Patterns:")
        for i, pattern in enumerate(result.get('patterns', [])[:10], 1):
            print(f"  {i}. {pattern}")
        
    else:
        print(f"ERROR: Status {response.status_code}")
        
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Test advanced refactor
print("\n3. Testing /api/advanced-refactor...")
try:
    response = requests.post('http://localhost:8000/api/advanced-refactor', json={
        'code': test_code
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Status: {response.status_code}")
        print(f"Improvement Score: {result.get('metrics', {}).get('improvement_score', 0)}%")
        print(f"Changes Applied: {result.get('metrics', {}).get('changes_applied', 0)}")
        
    else:
        print(f"ERROR: Status {response.status_code}")
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*80)
print(" ALL TESTS COMPLETED!")
print("="*80)
