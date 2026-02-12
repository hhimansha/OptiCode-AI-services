"""
Automated Test Generation Module
Generates unit tests, test coverage analysis, and testability scoring

Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/test_generator.py
Author: IT22606860
"""

import ast
import astor
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TestCase:
    """Represents a generated test case"""
    function_name: str
    test_name: str
    test_code: str
    test_type: str  # 'unit', 'edge_case', 'error_handling'
    complexity: int


@dataclass
class TestabilityScore:
    """Testability assessment for a function"""
    function_name: str
    score: int  # 0-100
    issues: List[str]
    recommendations: List[str]
    has_side_effects: bool
    dependency_count: int
    complexity: int


class TestGenerator:
    """Generate comprehensive unit tests"""
    
    def __init__(self):
        self.test_cases = []
        self.coverage = {}
        
    def generate_tests(self, code: str) -> Dict:
        """
        Generate comprehensive tests for given code
        
        Args:
            code: Source code to generate tests for
        
        Returns:
            Dictionary with generated tests and analysis
        """
        
        try:
            tree = ast.parse(code)
            
            # Extract all functions
            functions = self._extract_functions(tree)
            
            # Generate tests for each function
            for func in functions:
                tests = self._generate_function_tests(func)
                self.test_cases.extend(tests)
            
            # Generate test file content
            test_file = self._generate_test_file()
            
            # Analyze testability
            testability = self._analyze_testability(functions)
            
            # Calculate coverage potential
            coverage = self._calculate_coverage_potential(functions)
            
            return {
                'success': True,
                'test_file': test_file,
                'test_cases_count': len(self.test_cases),
                'functions_tested': len(functions),
                'testability_scores': testability,
                'coverage_potential': coverage,
                'test_cases': [self._format_test_case(tc) for tc in self.test_cases]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_file': '',
                'test_cases_count': 0
            }
    
    def _extract_functions(self, tree: ast.AST) -> List[ast.FunctionDef]:
        """Extract all functions from AST"""
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private methods unless explicitly testing
                if not node.name.startswith('__'):
                    functions.append(node)
        
        return functions
    
    def _generate_function_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate multiple test cases for a function"""
        
        tests = []
        
        # 1. Basic functionality test
        basic_test = self._generate_basic_test(func)
        if basic_test:
            tests.append(basic_test)
        
        # 2. Edge cases
        edge_tests = self._generate_edge_case_tests(func)
        tests.extend(edge_tests)
        
        # 3. Error handling tests
        error_tests = self._generate_error_tests(func)
        tests.extend(error_tests)
        
        # 4. Boundary tests
        boundary_tests = self._generate_boundary_tests(func)
        tests.extend(boundary_tests)
        
        return tests
    
    def _generate_basic_test(self, func: ast.FunctionDef) -> Optional[TestCase]:
        """Generate basic functionality test"""
        
        func_name = func.name
        test_name = f"test_{func_name}_basic"
        
        # Analyze function parameters
        params = func.args.args
        param_count = len(params) - (1 if params and params[0].arg == 'self' else 0)
        
        # Generate sample inputs
        sample_inputs = self._generate_sample_inputs(func)
        
        # Build test code
        test_code = self._build_test_code(
            test_name,
            func_name,
            sample_inputs,
            "Basic functionality test"
        )
        
        return TestCase(
            function_name=func_name,
            test_name=test_name,
            test_code=test_code,
            test_type='unit',
            complexity=1
        )
    
    def _generate_edge_case_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate edge case tests"""
        
        tests = []
        func_name = func.name
        
        # Detect parameter types and generate edge cases
        for i, param in enumerate(func.args.args):
            if param.arg == 'self':
                continue
            
            # Empty/None test
            test_name = f"test_{func_name}_edge_empty_{param.arg}"
            test_code = self._build_edge_test(func_name, param.arg, None)
            
            tests.append(TestCase(
                function_name=func_name,
                test_name=test_name,
                test_code=test_code,
                test_type='edge_case',
                complexity=2
            ))
        
        return tests
    
    def _generate_error_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate error handling tests"""
        
        tests = []
        func_name = func.name
        
        # Check if function has error handling
        has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(func))
        
        if has_try_except:
            test_name = f"test_{func_name}_error_handling"
            test_code = self._build_error_test(func_name)
            
            tests.append(TestCase(
                function_name=func_name,
                test_name=test_name,
                test_code=test_code,
                test_type='error_handling',
                complexity=3
            ))
        
        return tests
    
    def _generate_boundary_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """Generate boundary condition tests"""
        
        tests = []
        func_name = func.name
        
        # Analyze function body for numeric comparisons
        for node in ast.walk(func):
            if isinstance(node, ast.Compare):
                # Found a comparison - generate boundary test
                test_name = f"test_{func_name}_boundary"
                test_code = self._build_boundary_test(func_name)
                
                tests.append(TestCase(
                    function_name=func_name,
                    test_name=test_name,
                    test_code=test_code,
                    test_type='edge_case',
                    complexity=2
                ))
                break  # One boundary test per function
        
        return tests
    
    def _generate_sample_inputs(self, func: ast.FunctionDef) -> List[str]:
        """Generate sample input values based on parameter names"""
        
        inputs = []
        
        for param in func.args.args:
            if param.arg == 'self':
                continue
            
            param_name = param.arg.lower()
            
            # Infer type from name
            if any(x in param_name for x in ['num', 'count', 'age', 'year']):
                inputs.append('10')
            elif any(x in param_name for x in ['name', 'text', 'str', 'message']):
                inputs.append('"test_value"')
            elif any(x in param_name for x in ['list', 'items', 'array']):
                inputs.append('[1, 2, 3]')
            elif any(x in param_name for x in ['dict', 'data', 'config']):
                inputs.append('{"key": "value"}')
            elif any(x in param_name for x in ['flag', 'enabled', 'active']):
                inputs.append('True')
            else:
                inputs.append('None')
        
        return inputs
    
    def _build_test_code(self, test_name: str, func_name: str, 
                        inputs: List[str], description: str) -> str:
        """Build test method code"""
        
        input_str = ', '.join(inputs) if inputs else ''
        
        test_code = f'''
    def {test_name}(self):
        """{description}"""
        # Arrange
        {'# TODO: Set up test data' if not inputs else ''}
        
        # Act
        result = {func_name}({input_str})
        
        # Assert
        self.assertIsNotNone(result)
        # TODO: Add specific assertions
'''
        
        return test_code
    
    def _build_edge_test(self, func_name: str, param_name: str, value: any) -> str:
        """Build edge case test"""
        
        test_code = f'''
    def test_{func_name}_edge_{param_name}(self):
        """Test with edge case value"""
        # Test with None
        with self.assertRaises(Exception):
            {func_name}(None)
        
        # Test with empty value
        result = {func_name}("")
        self.assertIsNotNone(result)
'''
        
        return test_code
    
    def _build_error_test(self, func_name: str) -> str:
        """Build error handling test"""
        
        test_code = f'''
    def test_{func_name}_error_handling(self):
        """Test error handling"""
        # Test with invalid input
        with self.assertRaises(Exception):
            {func_name}("invalid_input")
'''
        
        return test_code
    
    def _build_boundary_test(self, func_name: str) -> str:
        """Build boundary test"""
        
        test_code = f'''
    def test_{func_name}_boundary(self):
        """Test boundary conditions"""
        # Test minimum boundary
        result_min = {func_name}(0)
        self.assertIsNotNone(result_min)
        
        # Test maximum boundary
        result_max = {func_name}(999999)
        self.assertIsNotNone(result_max)
'''
        
        return test_code
    
    def _generate_test_file(self) -> str:
        """Generate complete test file"""
        
        header = '''"""
Auto-generated test suite
Generated by IT22606860 Test Generator
"""

import unittest
from unittest.mock import Mock, patch


class TestGeneratedCode(unittest.TestCase):
    """Test cases for refactored code"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
'''
        
        # Add all test cases
        test_methods = '\n'.join([tc.test_code for tc in self.test_cases])
        
        footer = '''

if __name__ == '__main__':
    unittest.main()
'''
        
        return header + test_methods + footer
    
    def _analyze_testability(self, functions: List[ast.FunctionDef]) -> List[Dict]:
        """Analyze how testable each function is"""
        
        testability_scores = []
        
        for func in functions:
            score_obj = self._calculate_testability_score(func)
            testability_scores.append({
                'function': score_obj.function_name,
                'score': score_obj.score,
                'grade': self._score_to_grade(score_obj.score),
                'issues': score_obj.issues,
                'recommendations': score_obj.recommendations,
                'metrics': {
                    'has_side_effects': score_obj.has_side_effects,
                    'dependency_count': score_obj.dependency_count,
                    'complexity': score_obj.complexity
                }
            })
        
        return testability_scores
    
    def _calculate_testability_score(self, func: ast.FunctionDef) -> TestabilityScore:
        """Calculate testability score for a function"""
        
        score = 100
        issues = []
        recommendations = []
        
        # Check for side effects
        has_side_effects = self._has_side_effects(func)
        if has_side_effects:
            score -= 20
            issues.append("Function has side effects")
            recommendations.append("Refactor to pure function or dependency injection")
        
        # Check complexity
        complexity = self._calculate_complexity(func)
        if complexity > 10:
            score -= 15
            issues.append(f"High complexity: {complexity}")
            recommendations.append("Split into smaller functions")
        
        # Check dependencies
        dependencies = self._count_dependencies(func)
        if dependencies > 5:
            score -= 10
            issues.append(f"Many dependencies: {dependencies}")
            recommendations.append("Use dependency injection")
        
        # Check parameter count
        param_count = len(func.args.args)
        if param_count > 5:
            score -= 10
            issues.append(f"Too many parameters: {param_count}")
            recommendations.append("Group parameters into objects")
        
        # Check for global variables
        has_globals = self._uses_globals(func)
        if has_globals:
            score -= 15
            issues.append("Uses global variables")
            recommendations.append("Pass dependencies as parameters")
        
        return TestabilityScore(
            function_name=func.name,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            has_side_effects=has_side_effects,
            dependency_count=dependencies,
            complexity=complexity
        )
    
    def _has_side_effects(self, func: ast.FunctionDef) -> bool:
        """Check if function has side effects"""
        
        for node in ast.walk(func):
            # I/O operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['print', 'open', 'write']:
                        return True
            
            # Global modifications
            if isinstance(node, ast.Global):
                return True
            
            # Attribute modifications
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                return True
        
        return False
    
    def _calculate_complexity(self, func: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        
        complexity = 1
        
        for node in ast.walk(func):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _count_dependencies(self, func: ast.FunctionDef) -> int:
        """Count external dependencies"""
        
        dependencies = set()
        
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    dependencies.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    dependencies.add(node.func.attr)
        
        return len(dependencies)
    
    def _uses_globals(self, func: ast.FunctionDef) -> bool:
        """Check if function uses global variables"""
        
        for node in ast.walk(func):
            if isinstance(node, ast.Global):
                return True
        
        return False
    
    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _calculate_coverage_potential(self, functions: List[ast.FunctionDef]) -> Dict:
        """Calculate potential test coverage"""
        
        total_lines = 0
        testable_lines = 0
        
        for func in functions:
            func_lines = (func.end_lineno - func.lineno) if hasattr(func, 'end_lineno') else 10
            total_lines += func_lines
            
            # Estimate testable lines (exclude docstrings, comments)
            testable_lines += func_lines * 0.8
        
        coverage_percent = (testable_lines / total_lines * 100) if total_lines > 0 else 0
        
        return {
            'potential_coverage_percent': round(coverage_percent, 2),
            'total_lines': total_lines,
            'testable_lines': int(testable_lines),
            'functions_count': len(functions)
        }
    
    def _format_test_case(self, tc: TestCase) -> Dict:
        """Format test case for output"""
        return {
            'function': tc.function_name,
            'test_name': tc.test_name,
            'test_type': tc.test_type,
            'complexity': tc.complexity,
            'code': tc.test_code
        }


def generate_tests(code: str) -> Dict:
    """
    Main entry point for test generation
    
    Args:
        code: Source code to generate tests for
    
    Returns:
        Dictionary with generated tests and analysis
    """
    
    generator = TestGenerator()
    return generator.generate_tests(code)


def analyze_testability(code: str) -> Dict:
    """
    Analyze code testability without generating tests
    
    Args:
        code: Source code to analyze
    
    Returns:
        Testability analysis
    """
    
    generator = TestGenerator()
    try:
        tree = ast.parse(code)
        functions = generator._extract_functions(tree)
        testability = generator._analyze_testability(functions)
        
        return {
            'success': True,
            'testability_scores': testability,
            'average_score': sum(t['score'] for t in testability) / len(testability) if testability else 0
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
