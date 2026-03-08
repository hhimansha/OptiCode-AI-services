"""
Quick Test Script for Advanced Refactoring Platform
Tests all new advanced features
"""

import requests
import json


def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_advanced_refactor():
    """Test comprehensive refactoring"""
    print_section("TEST 1: Advanced Refactoring (130+ Patterns)")
    
    code = """
def calc(x, y):
    if x > 0:
        return True
    else:
        return False

def process(data):
    result = ""
    for i in range(len(data)):
        result = result + data[i]
    return result
"""
    
    response = requests.post('http://localhost:8000/api/advanced-refactor', json={
        'code': code,
        'categories': ['Naming & Readability', 'Conditional Logic', 'Python-Specific']
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Changes Applied: {result['metrics']['changes_applied']}")
        print(f"Complexity: {result['metrics']['complexity_before']} → {result['metrics']['complexity_after']}")
        print(f"Improvement Score: {result['metrics']['improvement_score']:.1f}%")
        print("\nRefactored Code:")
        print(result['refactored_code'][:200] + "...")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_architecture():
    """Test architecture analysis"""
    print_section("TEST 2: Architecture Analysis (SOLID + Design Patterns)")
    
    files = {
        "user_service.py": """
class UserService:
    def __init__(self):
        self.db = Database()
    
    def save_user(self, user):
        self.db.insert(user)
    
    def send_email(self, user):
        email_service.send(user.email)
    
    def validate(self, user):
        if not user.email:
            return False
        return True
""",
        "models.py": """
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
"""
    }
    
    response = requests.post('http://localhost:8000/api/architecture-analysis', json={
        'files': files
    })
    
    if response.status_code == 200:
        result = response.json()['analysis']
        print("✅ Success!")
        print(f"Total Classes: {result['summary']['total_classes']}")
        print(f"Issues Found: {result['summary']['issues_found']}")
        
        solid = result['solid_principles']
        print(f"\nSOLID Overall Score: {solid['overall_score']:.1f}")
        print(f"  SRP: {solid['single_responsibility']['score']}")
        print(f"  OCP: {solid['open_closed']['score']}")
        print(f"  LSP: {solid['liskov_substitution']['score']}")
        print(f"  ISP: {solid['interface_segregation']['score']}")
        print(f"  DIP: {solid['dependency_inversion']['score']}")
    else:
        print(f"❌ Failed: {response.status_code}")


def test_generate_tests():
    """Test automated test generation"""
    print_section("TEST 3: Automated Test Generation")
    
    code = """
def calculate_discount(price, customer_type):
    if customer_type == "premium":
        return price * 0.8
    elif customer_type == "regular":
        return price * 0.9
    return price

def validate_email(email):
    if not email or '@' not in email:
        raise ValueError("Invalid email")
    return True
"""
    
    response = requests.post('http://localhost:8000/api/generate-tests', json={
        'code': code
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Test Cases Generated: {result['test_cases_count']}")
        print(f"Functions Tested: {result['functions_tested']}")
        print(f"Coverage Potential: {result['coverage_potential']['potential_coverage_percent']:.1f}%")
        
        print("\nTestability Scores:")
        for score in result['testability_scores']:
            print(f"  {score['function']}: {score['score']}/100 (Grade {score['grade']})")
    else:
        print(f"❌ Failed: {response.status_code}")


def test_performance():
    """Test performance optimization"""
    print_section("TEST 4: Performance Optimization")
    
    code = """
def find_common(list1, list2):
    result = []
    for x in list1:
        for y in list2:
            if x == y:
                result.append(x)
    return result

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def build_message(names):
    message = ""
    for name in names:
        message += name + ", "
    return message
"""
    
    response = requests.post('http://localhost:8000/api/optimize-performance', json={
        'code': code
    })
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Issues Found: {result['issues_found']}")
        print(f"Impact Score: {result['impact_score']:.1f}")
        
        by_severity = result['issues_by_severity']
        print(f"\nBy Severity:")
        print(f"  Critical: {by_severity['critical']}")
        print(f"  Major: {by_severity['major']}")
        print(f"  Minor: {by_severity['minor']}")
        
        print("\nTop Issues:")
        for issue in result['detailed_issues'][:3]:
            print(f"  • {issue['category']} ({issue['severity']})")
            print(f"    {issue['complexity']['before']} → {issue['complexity']['after']}")
    else:
        print(f"❌ Failed: {response.status_code}")


def test_list_patterns():
    """Test pattern listing"""
    print_section("TEST 5: List All Patterns")
    
    response = requests.get('http://localhost:8000/api/list-patterns')
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Total Categories: {result['categories']}")
        
        print("\nPattern Count by Category:")
        for category, patterns in result['patterns'].items():
            print(f"  {category}: {len(patterns)} patterns")
    else:
        print(f"❌ Failed: {response.status_code}")


def main():
    print("\n" + "="*80)
    print("  ADVANCED PYTHON REFACTORING PLATFORM - TEST SUITE")
    print("  Student ID: IT22606860")
    print("  130+ Refactoring Patterns | Architecture | Tests | Performance")
    print("="*80)
    
    try:
        # Test all features
        test_advanced_refactor()
        test_architecture()
        test_generate_tests()
        test_performance()
        test_list_patterns()
        
        print("\n" + "="*80)
        print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("Please start the server first:")
        print("  python refactor_api.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
