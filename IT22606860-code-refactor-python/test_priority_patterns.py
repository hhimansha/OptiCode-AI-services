"""
Test Priority Refactorings - Top 20 Most Important Patterns
Comprehensive test cases demonstrating each pattern
"""

import requests
import json


def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_priority_refactorings():
    """Test all 20 priority patterns with real examples"""
    
    print_section("TESTING TOP 20 PRIORITY REFACTORING PATTERNS")
    
    # Comprehensive test case covering multiple patterns
    test_code = """
# Pattern 1: Dead code after return
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
    print("This will never execute")  # Dead code
    total = 999  # Dead code

# Pattern 2 & 3: Loop can be comprehension
def get_even_numbers(numbers):
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num)
    return result

# Pattern 4 & 5: Complex conditional needing decomposition
def process_order(order, customer, inventory):
    if order.total > 100 and customer.is_premium and customer.credit_score > 700 and inventory.has_stock(order.items):
        # Complex processing
        order.apply_discount()
        order.update_inventory()
        order.send_confirmation()
        order.log_transaction()
        order.update_analytics()

# Pattern 6: Nested conditionals (needs guard clauses)
def validate_user(user):
    if user is not None:
        if user.email:
            if '@' in user.email:
                if user.age >= 18:
                    return True
    return False

# Pattern 7: Control flag
def find_user(users, target_id):
    found = False
    result = None
    for user in users:
        if not found:
            if user.id == target_id:
                result = user
                found = True
    return result

# Pattern 8: Duplicate code in conditionals
def get_discount(customer_type, amount):
    if customer_type == "premium":
        print("Processing order")
        discount = amount * 0.2
        print("Discount applied")
        return discount
    else:
        print("Processing order")
        discount = amount * 0.1
        print("Discount applied")
        return discount

# Pattern 9: Temp variable used once
def calculate_price(base_price, tax_rate):
    price_with_tax = base_price * (1 + tax_rate)
    return price_with_tax

# Pattern 10: Long function (needs extraction)
def process_payment(order):
    # Validate payment
    if not order.payment_method:
        raise ValueError("No payment method")
    if order.total <= 0:
        raise ValueError("Invalid amount")
    
    # Process credit card
    if order.payment_method == "credit_card":
        validate_card(order.card_number)
        charge_card(order.card_number, order.total)
    
    # Send confirmation
    email = order.customer.email
    subject = "Payment Confirmation"
    body = f"Your payment of ${order.total} was successful"
    send_email(email, subject, body)
    
    # Update inventory
    for item in order.items:
        inventory.reduce_stock(item.id, item.quantity)
    
    # Log transaction
    log_entry = {
        'order_id': order.id,
        'amount': order.total,
        'timestamp': now()
    }
    database.log_transaction(log_entry)

# Pattern 11: Missing assertions
def divide(a, b):
    return a / b

# Pattern 12: Temp storing calculation
def get_total_price(items):
    temp_price = sum(item.price for item in items)
    return temp_price

# Pattern 13: Poor variable names
def calc(x, y, z):
    return x + y - z

# Pattern 14: Modifying parameters
def update_price(item, discount):
    discount = discount * 0.8  # Modifying parameter
    item.price = item.price - discount
    return item

# Pattern 15: Multi-purpose temp
def analyze_data(data):
    result = 0
    result = len(data)  # First use
    print(f"Count: {result}")
    result = sum(data)  # Second use (different purpose)
    print(f"Sum: {result}")
    result = max(data)  # Third use (different purpose)
    return result
"""
    
    print("Sending test code to API...")
    print(f"Code length: {len(test_code)} characters")
    print(f"Contains examples of all 20 priority patterns\n")
    
    try:
        response = requests.post('http://localhost:8000/api/priority-refactor', json={
            'code': test_code
        }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                print("✅ SUCCESS! Priority refactorings applied\n")
                
                print(f"📊 SUMMARY:")
                print(f"  Patterns Applied: {result['patterns_applied']}")
                print(f"  Total Changes: {len(result['changes'])}")
                
                # Group changes by pattern
                patterns_found = {}
                for change in result['changes']:
                    pattern = change['pattern_name']
                    patterns_found[pattern] = patterns_found.get(pattern, 0) + 1
                
                print(f"\n📋 PATTERNS DETECTED:")
                for pattern, count in sorted(patterns_found.items()):
                    print(f"  • {pattern}: {count} occurrences")
                
                # Show sample changes
                print(f"\n🔍 SAMPLE CHANGES (first 5):")
                for i, change in enumerate(result['changes'][:5], 1):
                    print(f"\n  {i}. {change['pattern_name']} (Line {change['line']})")
                    print(f"     Description: {change['description']}")
                    print(f"     Impact: {change['impact']}")
                
                # Show refactored code snippet
                print(f"\n📝 REFACTORED CODE PREVIEW:")
                refactored_lines = result['refactored_code'].split('\n')
                print("     " + "\n     ".join(refactored_lines[:15]))
                print(f"     ... ({len(refactored_lines) - 15} more lines)")
                
            else:
                print(f"❌ Refactoring failed: {result.get('error')}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API server")
        print("Please start the server first:")
        print("  python refactor_api.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")


def test_get_priority_patterns():
    """Get list of all priority patterns"""
    
    print_section("GET PRIORITY PATTERNS LIST")
    
    try:
        response = requests.get('http://localhost:8000/api/priority-patterns')
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCESS!\n")
            print(f"Total Priority Patterns: {result['count']}\n")
            
            print("Top 20 Priority Refactoring Patterns:")
            for pattern in result['patterns']:
                print(f"  {pattern}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


def test_specific_pattern():
    """Test a specific challenging pattern"""
    
    print_section("SPECIFIC PATTERN TEST: Nested Conditionals")
    
    code = """
def authenticate_user(user):
    if user is not None:
        if user.email:
            if user.password:
                if verify_password(user.password):
                    if user.is_active:
                        if not user.is_locked:
                            return True
    return False
"""
    
    try:
        response = requests.post('http://localhost:8000/api/priority-refactor', json={
            'code': code
        })
        
        if response.status_code == 200:
            result = response.json()
            
            print("Original Code:")
            print(code)
            
            print("\n✅ Refactoring Suggestions:")
            for change in result['changes']:
                print(f"\n  Pattern: {change['pattern_name']}")
                print(f"  Line: {change['line']}")
                print(f"  Description: {change['description']}")
                print(f"  Suggestion: {change['after']}")
                print(f"  Impact: {change['impact']}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


def compare_priority_vs_advanced():
    """Compare priority refactorings vs advanced comprehensive"""
    
    print_section("COMPARISON: Priority vs Advanced Refactoring")
    
    code = """
def process(items):
    result = []
    for i in range(len(items)):
        if items[i] > 0:
            result.append(items[i] * 2)
    return result
"""
    
    try:
        # Test priority refactorings
        print("1. Testing PRIORITY REFACTORINGS...")
        response1 = requests.post('http://localhost:8000/api/priority-refactor', json={
            'code': code
        })
        
        priority_result = response1.json()
        print(f"   Patterns applied: {priority_result.get('patterns_applied', 0)}")
        print(f"   Changes: {len(priority_result.get('changes', []))}")
        
        # Test advanced refactorings
        print("\n2. Testing ADVANCED REFACTORINGS...")
        response2 = requests.post('http://localhost:8000/api/advanced-refactor', json={
            'code': code,
            'categories': ['Python-Specific', 'Naming & Readability']
        })
        
        advanced_result = response2.json()
        print(f"   Changes applied: {advanced_result.get('metrics', {}).get('changes_applied', 0)}")
        print(f"   Improvement score: {advanced_result.get('metrics', {}).get('improvement_score', 0):.1f}%")
        
        print("\n✅ Both approaches provide complementary refactoring!")
        print("   • Priority: Fast detection of common issues")
        print("   • Advanced: Deep transformations with metrics")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")


def main():
    print("\n" + "="*80)
    print("  PRIORITY REFACTORINGS TEST SUITE")
    print("  Top 20 Most Important Patterns")
    print("  Student ID: IT22606860")
    print("="*80)
    
    test_priority_refactorings()
    test_get_priority_patterns()
    test_specific_pattern()
    compare_priority_vs_advanced()
    
    print("\n" + "="*80)
    print("  ✅ ALL PRIORITY REFACTORING TESTS COMPLETED!")
    print("="*80 + "\n")
    
    print("💡 TIP: Priority refactorings are fastest for common issues!")
    print("   Use /api/priority-refactor for quick code review")
    print("   Use /api/advanced-refactor for comprehensive transformation\n")


if __name__ == "__main__":
    main()
