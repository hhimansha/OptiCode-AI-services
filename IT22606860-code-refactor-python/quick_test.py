"""Quick test for transformer fixes"""

from perf_optimizer_caching import run_caching_optimization
from perf_optimizer_memory import run_memory_optimization

# Test 1: Augmented assignment
code1 = '''
def test():
    counter = 0
    counter = counter + 1
    total = 1
    total = total * 2
    return counter
'''
result1 = run_caching_optimization(code1)
print('=== AUGMENTED ASSIGNMENT TEST ===')
print(result1['optimized_code'])
print('Changes:', result1['changes_applied'])
print()

# Test 2: List comprehension
code2 = '''
def test():
    result = []
    for item in items:
        result.append(item * 2)
    return result
'''
result2 = run_memory_optimization(code2)
print('=== LIST COMPREHENSION TEST ===')
print(result2['optimized_code'])
print('Changes:', result2['changes_applied'])
print()

# Test 3: % formatting to f-string
code3 = '''
def test():
    name = "John"
    age = 30
    message = "Hello %s, you are %d years old" % (name, age)
    return message
'''
result3 = run_memory_optimization(code3)
print('=== PERCENT TO F-STRING TEST ===')
print(result3['optimized_code'])
print('Changes:', result3['changes_applied'])
print()

# Test 4: range(len()) to enumerate
code4 = '''
def test():
    items = [1, 2, 3]
    for i in range(len(items)):
        print(items[i])
'''
result4 = run_caching_optimization(code4)
print('=== RANGE(LEN) TO ENUMERATE TEST ===')
print(result4['optimized_code'])
print('Changes:', result4['changes_applied'])
