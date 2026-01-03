"""
Python Best Practices Detection System
Analyzes code for PEP 8, Pythonic patterns, and anti-patterns
"""

import ast
import re
from typing import List
from dataclasses import dataclass, asdict

@dataclass
class BestPracticeViolation:
    category: str  # 'pep8', 'pythonic', 'anti-pattern'
    severity: str  # 'error', 'warning', 'info'
    line: int
    code: str
    message: str
    recommendation: str
    good_example: str
    bad_example: str
    reference: str

class BestPracticesDetector:
    
    def analyze(self, code: str) -> List[dict]:
        """Comprehensive best practices analysis"""
        print("\n[BEST PRACTICES] Starting analysis...")
        
        violations = []
        
        try:
            tree = ast.parse(code)
            
            # Run all checks
            violations.extend(self._check_naming(tree))
            violations.extend(self._check_pythonic_patterns(tree, code))
            violations.extend(self._check_anti_patterns(tree))
            violations.extend(self._check_pep8(code))
            violations.extend(self._check_docstrings(tree, code))
            
            print(f"[BEST PRACTICES] Found {len(violations)} violations")
            
        except SyntaxError as e:
            print(f"[BEST PRACTICES] Syntax error: {e}")
            return []
        
        return [asdict(v) for v in violations]
    
    def _check_naming(self, tree) -> List[BestPracticeViolation]:
        """Check PEP 8 naming conventions"""
        violations = []
        
        for node in ast.walk(tree):
            # Functions should be snake_case
            if isinstance(node, ast.FunctionDef):
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    violations.append(BestPracticeViolation(
                        category='pep8',
                        severity='warning',
                        line=node.lineno,
                        code=node.name,
                        message=f'Function name "{node.name}" should be snake_case',
                        recommendation=f'Rename to: {self._to_snake_case(node.name)}',
                        good_example='def calculate_total():\n    pass',
                        bad_example='def calculateTotal():\n    pass',
                        reference='PEP 8: https://pep8.org/#function-and-variable-names'
                    ))
            
            # Classes should be PascalCase
            elif isinstance(node, ast.ClassDef):
                if not self._is_pascal_case(node.name):
                    violations.append(BestPracticeViolation(
                        category='pep8',
                        severity='warning',
                        line=node.lineno,
                        code=node.name,
                        message=f'Class name "{node.name}" should be PascalCase',
                        recommendation=f'Rename to: {self._to_pascal_case(node.name)}',
                        good_example='class UserAccount:\n    pass',
                        bad_example='class user_account:\n    pass',
                        reference='PEP 8: https://pep8.org/#class-names'
                    ))
        
        return violations
    
    def _check_pythonic_patterns(self, tree, code) -> List[BestPracticeViolation]:
        """Check for Pythonic patterns"""
        violations = []
        
        for node in ast.walk(tree):
            # range(len()) pattern
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if (isinstance(node.iter.func, ast.Name) and 
                        node.iter.func.id == 'range' and 
                        node.iter.args):
                        arg = node.iter.args[0]
                        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                            if arg.func.id == 'len':
                                violations.append(BestPracticeViolation(
                                    category='pythonic',
                                    severity='warning',
                                    line=node.lineno,
                                    code='range(len(...))',
                                    message='Avoid range(len()) pattern - use direct iteration or enumerate()',
                                    recommendation='Use: for item in items: or for i, item in enumerate(items):',
                                    good_example='for item in items:\n    print(item)',
                                    bad_example='for i in range(len(items)):\n    print(items[i])',
                                    reference='Pythonic Iteration Patterns'
                                ))
            
            # List building with append in loop
            if isinstance(node, ast.For):
                for child in node.body:
                    if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                        if isinstance(child.value.func, ast.Attribute):
                            if child.value.func.attr == 'append':
                                violations.append(BestPracticeViolation(
                                    category='pythonic',
                                    severity='info',
                                    line=node.lineno,
                                    code='loop with append',
                                    message='Consider using list comprehension instead of loop with append',
                                    recommendation='Use: result = [expr for item in items]',
                                    good_example='result = [item * 2 for item in numbers]',
                                    bad_example='result = []\nfor item in numbers:\n    result.append(item * 2)',
                                    reference='List Comprehensions'
                                ))
                                break
        
        # Check for old-style string formatting
        if '%' in code and not code.count('%') == code.count('%%') // 2:
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                if '%s' in line or '%d' in line or '%f' in line:
                    violations.append(BestPracticeViolation(
                        category='pythonic',
                        severity='info',
                        line=i,
                        code='% formatting',
                        message='Old-style % formatting detected - use f-strings (Python 3.6+)',
                        recommendation='Use: f"Hello {name}"',
                        good_example='message = f"Hello {name}, age {age}"',
                        bad_example='message = "Hello %s, age %d" % (name, age)',
                        reference='PEP 498: f-strings'
                    ))
                    break
        
        return violations
    
    def _check_anti_patterns(self, tree) -> List[BestPracticeViolation]:
        """Check for anti-patterns"""
        violations = []
        
        for node in ast.walk(tree):
            # Mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for i, default in enumerate(node.args.defaults):
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        violations.append(BestPracticeViolation(
                            category='anti-pattern',
                            severity='error',
                            line=node.lineno,
                            code=f'{node.name}(..., default={ast.unparse(default)})',
                            message='Mutable default argument - this is a common bug!',
                            recommendation='Use None as default and create mutable object in function body',
                            good_example='def func(items=None):\n    if items is None:\n        items = []',
                            bad_example='def func(items=[]):  # BUG: shared across calls!',
                            reference='Common Python Gotchas'
                        ))
            
            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                violations.append(BestPracticeViolation(
                    category='anti-pattern',
                    severity='warning',
                    line=node.lineno,
                    code='except:',
                    message='Bare except clause catches all exceptions including system exits',
                    recommendation='Use: except Exception: or specific exception types',
                    good_example='try:\n    risky_code()\nexcept ValueError:\n    handle_error()',
                    bad_example='try:\n    risky_code()\nexcept:  # Too broad!',
                    reference='Exception Handling Best Practices'
                ))
            
            # Comparing with == None
            if isinstance(node, ast.Compare):
                if any(isinstance(op, ast.Eq) for op in node.ops):
                    if any(isinstance(comp, ast.Constant) and comp.value is None for comp in node.comparators):
                        violations.append(BestPracticeViolation(
                            category='pythonic',
                            severity='info',
                            line=node.lineno,
                            code='== None',
                            message='Use "is None" instead of "== None"',
                            recommendation='Use identity check: if value is None:',
                            good_example='if value is None:',
                            bad_example='if value == None:',
                            reference='PEP 8: Comparisons'
                        ))
        
        return violations
    
    def _check_pep8(self, code) -> List[BestPracticeViolation]:
        """Check PEP 8 style"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Line too long
            if len(line) > 79 and not line.strip().startswith('#'):
                violations.append(BestPracticeViolation(
                    category='pep8',
                    severity='info',
                    line=i,
                    code=line[:50] + '...',
                    message=f'Line too long ({len(line)} > 79 characters)',
                    recommendation='Break line into multiple lines',
                    good_example='result = (\n    long_function_name(arg1, arg2)\n    .method()\n)',
                    bad_example='result = very_long_function_call_with_many_arguments_that_exceeds_limit()',
                    reference='PEP 8: Maximum Line Length'
                ))
            
            # Multiple statements on one line
            if ';' in line and not line.strip().startswith('#'):
                violations.append(BestPracticeViolation(
                    category='pep8',
                    severity='warning',
                    line=i,
                    code=line.strip(),
                    message='Multiple statements on one line',
                    recommendation='Use separate lines for each statement',
                    good_example='x = 1\ny = 2',
                    bad_example='x = 1; y = 2',
                    reference='PEP 8: Other Recommendations'
                ))
            
            # Trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                violations.append(BestPracticeViolation(
                    category='pep8',
                    severity='info',
                    line=i,
                    code='trailing whitespace',
                    message='Trailing whitespace detected',
                    recommendation='Remove trailing spaces/tabs',
                    good_example='code_line',
                    bad_example='code_line   ',
                    reference='PEP 8: Whitespace'
                ))
        
        return violations
    
    def _check_docstrings(self, tree, code) -> List[BestPracticeViolation]:
        """Check for missing docstrings"""
        violations = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions
                if node.name.startswith('_'):
                    continue
                
                # Check if function has docstring
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, (ast.Str, ast.Constant))
                )
                
                if not has_docstring:
                    violations.append(BestPracticeViolation(
                        category='pep8',
                        severity='info',
                        line=node.lineno,
                        code=node.name,
                        message=f'Public function "{node.name}" missing docstring',
                        recommendation='Add docstring explaining purpose, parameters, and return value',
                        good_example='def calculate(x: int) -> int:\n    """Double the input value.\n    \n    Args:\n        x: Input number\n    \n    Returns:\n        Doubled value\n    """',
                        bad_example='def calculate(x):\n    return x * 2',
                        reference='PEP 257: Docstring Conventions'
                    ))
        
        return violations
    
    # Helper methods
    def _is_snake_case(self, name: str) -> bool:
        """Check if name is snake_case"""
        if not name:
            return False
        return name.islower() and (('_' in name and len(name) > 1) or len(name) <= 3)
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name is PascalCase"""
        if not name:
            return False
        return name[0].isupper() and '_' not in name
    
    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))