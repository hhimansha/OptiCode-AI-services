"""Test the recursive method detection fix"""
from perf_optimizer_caching import run_caching_optimization

code = '''
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

result = run_caching_optimization(code)
print('='*60)
print('Result keys:', result.keys())
print('Issues found:', len(result['issues']))
for issue in result['issues']:
    print(f"  - {issue.issue_type} at line {issue.line}")
print()
print('='*60)
print('Refactored code:')
print('='*60)
print(result['optimized_code'])
