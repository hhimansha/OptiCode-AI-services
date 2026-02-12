"""
Python Best Practices Checker
Checks code against Python best practices and provides educational guidance
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/best_practices.py
"""

import ast
import re
from typing import Dict, List


class BestPracticesChecker:
    """Check code against Python best practices"""
    
    def __init__(self):
        self.violations = []
        self.recommendations = []
        self.good_practices = []
    
    def check_all(self, code: str) -> Dict:
        """Run all best practice checks"""
        
        results = {
            'success': True,
            'violations': [],
            'recommendations': [],
            'good_practices': [],
            'score': 100,
            'categories': {}
        }
        
        try:
            tree = ast.parse(code)
            
            # Run category checks
            results['categories']['solid_principles'] = self.check_solid_principles(tree, code)
            results['categories']['dry_principle'] = self.check_dry_principle(tree)
            results['categories']['documentation'] = self.check_documentation(tree)
            results['categories']['error_handling'] = self.check_error_handling(tree)
            results['categories']['pythonic_code'] = self.check_pythonic_patterns(tree, code)
            results['categories']['performance'] = self.check_performance(tree, code)
            results['categories']['testability'] = self.check_testability(tree)
            results['categories']['modularity'] = self.check_modularity(tree)
            
            # Aggregate results
            results['violations'] = self.violations
            results['recommendations'] = self.recommendations
            results['good_practices'] = self.good_practices
            
            # Calculate score
            results['score'] = self.calculate_best_practices_score()
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def check_solid_principles(self, tree: ast.AST, code: str) -> Dict:
        """
        Check SOLID principles:
        - Single Responsibility Principle
        - Open/Closed Principle
        - Liskov Substitution Principle
        - Interface Segregation Principle
        - Dependency Inversion Principle
        """
        
        violations = []
        recommendations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check Single Responsibility
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                
                if method_count > 15:
                    violations.append({
                        'principle': 'Single Responsibility Principle (SRP)',
                        'severity': 'high',
                        'line': node.lineno,
                        'class': node.name,
                        'description': f'Class "{node.name}" has {method_count} methods, suggesting multiple responsibilities',
                        'recommendation': 'Split into smaller, focused classes with single responsibilities',
                        'example': 'Instead of a "UserManager" that handles authentication, database, and email, create separate classes: UserAuthenticator, UserRepository, UserNotifier'
                    })
                
                # Check for private methods (encapsulation)
                private_methods = sum(1 for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('_') and not n.name.startswith('__'))
                public_methods = sum(1 for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_'))
                
                if public_methods > 10 and private_methods == 0:
                    recommendations.append({
                        'principle': 'Encapsulation',
                        'severity': 'medium',
                        'line': node.lineno,
                        'class': node.name,
                        'description': f'Class "{node.name}" has {public_methods} public methods but no private methods',
                        'recommendation': 'Consider making internal helper methods private to improve encapsulation',
                        'example': 'def _internal_helper(self): # Private method starts with underscore'
                    })
        
        self.violations.extend(violations)
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'violations': violations,
            'recommendations': recommendations
        }
    
    def check_dry_principle(self, tree: ast.AST) -> Dict:
        """Check for DRY (Don't Repeat Yourself) violations"""
        
        violations = []
        
        # Track function bodies to detect duplication
        function_bodies = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                body_str = ast.dump(node.body)
                
                if body_str in function_bodies:
                    violations.append({
                        'principle': 'DRY (Don\'t Repeat Yourself)',
                        'severity': 'medium',
                        'line': node.lineno,
                        'function': node.name,
                        'duplicate_of': function_bodies[body_str],
                        'description': f'Function "{node.name}" has identical implementation to "{function_bodies[body_str]}"',
                        'recommendation': 'Extract common functionality into a shared function',
                        'example': 'def common_logic():\n    # Shared code\n    pass\n\ndef func1():\n    common_logic()\n    # Specific code'
                    })
                else:
                    function_bodies[body_str] = node.name
        
        self.violations.extend(violations)
        
        return {
            'checked': True,
            'violations': violations
        }
    
    def check_documentation(self, tree: ast.AST) -> Dict:
        """Check documentation quality"""
        
        violations = []
        recommendations = []
        good_practices = []
        
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                docstring = ast.get_docstring(node)
                
                if docstring:
                    documented_functions += 1
                    
                    # Check docstring quality
                    if len(docstring) > 50 and 'Args:' in docstring and 'Returns:' in docstring:
                        good_practices.append({
                            'type': 'excellent_documentation',
                            'line': node.lineno,
                            'function': node.name,
                            'description': f'Function "{node.name}" has comprehensive docstring with Args and Returns'
                        })
                else:
                    if not node.name.startswith('_'):  # Public functions should be documented
                        violations.append({
                            'principle': 'Documentation',
                            'severity': 'low',
                            'line': node.lineno,
                            'function': node.name,
                            'description': f'Public function "{node.name}" lacks documentation',
                            'recommendation': 'Add docstring explaining purpose, parameters, and return value',
                            'example': '"""\\n    Brief description.\\n    \\n    Args:\\n        param1: Description\\n    \\n    Returns:\\n        Description\\n    """'
                        })
            
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                docstring = ast.get_docstring(node)
                
                if docstring:
                    documented_classes += 1
                else:
                    violations.append({
                        'principle': 'Documentation',
                        'severity': 'medium',
                        'line': node.lineno,
                        'class': node.name,
                        'description': f'Class "{node.name}" lacks documentation',
                        'recommendation': 'Add class docstring explaining purpose and responsibilities',
                        'example': '"""\\n    Brief description of the class.\\n    \\n    Attributes:\\n        attr1: Description\\n    """'
                    })
        
        doc_rate = (documented_functions / total_functions * 100) if total_functions > 0 else 100
        
        self.violations.extend(violations)
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'documentation_rate': round(doc_rate, 2),
            'total_functions': total_functions,
            'documented_functions': documented_functions,
            'total_classes': total_classes,
            'documented_classes': documented_classes,
            'violations': violations,
            'good_practices': good_practices
        }
    
    def check_error_handling(self, tree: ast.AST) -> Dict:
        """Check error handling practices"""
        
        violations = []
        recommendations = []
        
        bare_excepts = 0
        proper_exceptions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:  # Bare except
                    bare_excepts += 1
                    violations.append({
                        'principle': 'Error Handling',
                        'severity': 'high',
                        'line': node.lineno,
                        'description': 'Bare except clause catches all exceptions including system exits',
                        'recommendation': 'Catch specific exception types',
                        'example': 'except ValueError as e:\n    # Handle specific error'
                    })
                else:
                    proper_exceptions += 1
            
            # Check for assertions in non-test code
            if isinstance(node, ast.Assert):
                recommendations.append({
                    'principle': 'Error Handling',
                    'severity': 'low',
                    'line': node.lineno,
                    'description': 'Using assert for error handling',
                    'recommendation': 'Use explicit exception raising instead of assert for runtime checks',
                    'example': 'if not condition:\n    raise ValueError("Error message")'
                })
        
        self.violations.extend(violations)
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'bare_excepts': bare_excepts,
            'proper_exceptions': proper_exceptions,
            'violations': violations,
            'recommendations': recommendations
        }
    
    def check_pythonic_patterns(self, tree: ast.AST, code: str) -> Dict:
        """Check for Pythonic code patterns"""
        
        violations = []
        recommendations = []
        good_practices = []
        
        # Check for list comprehensions usage (good practice)
        has_list_comp = any(isinstance(node, ast.ListComp) for node in ast.walk(tree))
        if has_list_comp:
            good_practices.append({
                'type': 'list_comprehension',
                'description': 'Uses list comprehensions (Pythonic)',
                'example': 'squares = [x**2 for x in range(10)]'
            })
        
        # Check for context managers (with statements)
        has_with = any(isinstance(node, ast.With) for node in ast.walk(tree))
        if has_with:
            good_practices.append({
                'type': 'context_manager',
                'description': 'Uses context managers with "with" statement (Pythonic)',
                'example': 'with open(file) as f:\n    data = f.read()'
            })
        
        # Check for generator expressions
        has_generator = any(isinstance(node, ast.GeneratorExp) for node in ast.walk(tree))
        if has_generator:
            good_practices.append({
                'type': 'generator_expression',
                'description': 'Uses generator expressions for memory efficiency',
                'example': 'sum(x**2 for x in range(1000000))'
            })
        
        # Check for enumerate usage
        if 'enumerate(' in code:
            good_practices.append({
                'type': 'enumerate',
                'description': 'Uses enumerate() instead of range(len())',
                'example': 'for i, item in enumerate(items):'
            })
        
        # Check for string formatting
        if 'f"' in code or "f'" in code:
            good_practices.append({
                'type': 'f_strings',
                'description': 'Uses f-strings for string formatting (Python 3.6+)',
                'example': 'f"Hello {name}, you are {age} years old"'
            })
        elif '.format(' in code:
            recommendations.append({
                'principle': 'Pythonic Code',
                'severity': 'low',
                'description': 'Uses .format() instead of f-strings',
                'recommendation': 'Consider using f-strings for better readability (Python 3.6+)',
                'example': 'f"Value: {value}" instead of "Value: {}".format(value)'
            })
        
        # Check for defaultdict usage
        if 'defaultdict' in code:
            good_practices.append({
                'type': 'defaultdict',
                'description': 'Uses defaultdict from collections',
                'example': 'from collections import defaultdict\nd = defaultdict(list)'
            })
        
        # Check for pathlib usage
        if 'pathlib' in code or 'Path(' in code:
            good_practices.append({
                'type': 'pathlib',
                'description': 'Uses pathlib for file path operations (modern Python)',
                'example': 'from pathlib import Path\npath = Path("file.txt")'
            })
        
        # Check for type hints (Python 3.5+)
        has_type_hints = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns or any(arg.annotation for arg in node.args.args):
                    has_type_hints = True
                    break
        
        if has_type_hints:
            good_practices.append({
                'type': 'type_hints',
                'description': 'Uses type hints for better code clarity',
                'example': 'def greet(name: str) -> str:\n    return f"Hello {name}"'
            })
        
        self.violations.extend(violations)
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'good_practices': good_practices,
            'recommendations': recommendations
        }
    
    def check_performance(self, tree: ast.AST, code: str) -> Dict:
        """Check for performance-related best practices"""
        
        recommendations = []
        
        # Check for string concatenation in loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check body for string concatenation
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.op, ast.Add):
                            # This might be string concatenation
                            recommendations.append({
                                'principle': 'Performance',
                                'severity': 'medium',
                                'line': node.lineno,
                                'description': 'Potential string concatenation in loop',
                                'recommendation': 'Use list append and join for better performance',
                                'example': 'parts = []\nfor item in items:\n    parts.append(str(item))\nresult = "".join(parts)'
                            })
                            break
        
        # Check for global variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                recommendations.append({
                    'principle': 'Performance & Maintainability',
                    'severity': 'medium',
                    'line': node.lineno,
                    'description': 'Uses global variables',
                    'recommendation': 'Avoid global variables; use function parameters or class attributes',
                    'example': 'def process(config):\n    # Pass data as parameters'
                })
        
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'recommendations': recommendations
        }
    
    def check_testability(self, tree: ast.AST) -> Dict:
        """Check code testability"""
        
        recommendations = []
        
        # Check for functions with side effects
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function prints (side effect)
                has_print = any(
                    isinstance(n, ast.Call) and
                    isinstance(n.func, ast.Name) and
                    n.func.id == 'print'
                    for n in ast.walk(node)
                )
                
                if has_print:
                    recommendations.append({
                        'principle': 'Testability',
                        'severity': 'low',
                        'line': node.lineno,
                        'function': node.name,
                        'description': f'Function "{node.name}" uses print() statements',
                        'recommendation': 'Return values instead of printing for better testability',
                        'example': 'def process():\n    result = calculate()\n    return result  # Return instead of print'
                    })
        
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'recommendations': recommendations
        }
    
    def check_modularity(self, tree: ast.AST) -> Dict:
        """Check code modularity"""
        
        recommendations = []
        good_practices = []
        
        # Check for appropriate module structure
        has_main_guard = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    # Check for if __name__ == '__main__'
                    test_str = ast.dump(node.test)
                    if '__name__' in test_str and '__main__' in test_str:
                        has_main_guard = True
                        good_practices.append({
                            'type': 'main_guard',
                            'description': 'Uses if __name__ == "__main__" guard',
                            'example': 'if __name__ == "__main__":\n    main()'
                        })
                        break
        
        if not has_main_guard:
            # Check if there's executable code at module level
            module_level_code = any(
                isinstance(node, (ast.Expr, ast.Assign, ast.Call))
                for node in tree.body
            )
            
            if module_level_code:
                recommendations.append({
                    'principle': 'Modularity',
                    'severity': 'low',
                    'description': 'Module has executable code at top level without main guard',
                    'recommendation': 'Wrap executable code in if __name__ == "__main__" block',
                    'example': 'if __name__ == "__main__":\n    # Your executable code here\n    main()'
                })
        
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'has_main_guard': has_main_guard,
            'good_practices': good_practices,
            'recommendations': recommendations
        }
    
    def calculate_best_practices_score(self) -> int:
        """Calculate overall best practices score"""
        
        score = 100
        
        # Deduct for violations
        for violation in self.violations:
            if violation['severity'] == 'high':
                score -= 10
            elif violation['severity'] == 'medium':
                score -= 5
            elif violation['severity'] == 'low':
                score -= 2
        
        # Bonus for good practices
        bonus = min(len(self.good_practices), 20)
        score += bonus
        
        return max(0, min(100, score))


def check_best_practices(code: str) -> Dict:
    """
    Main entry point for best practices checking
    
    Args:
        code: Python source code to check
    
    Returns:
        Best practices analysis results
    """
    
    checker = BestPracticesChecker()
    return checker.check_all(code)
