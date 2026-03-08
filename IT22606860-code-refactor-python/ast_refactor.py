"""
AST-Based Python Code Refactoring Module
This module provides AST-based refactoring capabilities for Python code
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/ast_refactor.py
"""

import ast
import astor
from typing import List, Dict, Tuple, Optional
import re


class ASTRefactorer(ast.NodeTransformer):
    """
    Main AST-based refactoring class
    Applies various refactoring techniques to improve code quality
    """
    
    def __init__(self):
        self.changes = []
        self.issues = []
        
    def add_change(self, change_type: str, description: str, line_num: int = 0):
        """Track changes made during refactoring"""
        self.changes.append({
            'type': change_type,
            'description': description,
            'line': line_num
        })
    
    def add_issue(self, issue_type: str, description: str, line_num: int = 0):
        """Track issues found during refactoring"""
        self.issues.append({
            'type': issue_type,
            'description': description,
            'line': line_num
        })


class RemoveUnusedVariables(ast.NodeTransformer):
    """Remove unused variable assignments"""
    
    def __init__(self):
        super().__init__()
        self.assigned_vars = set()
        self.used_vars = set()
        self.unused_assignments = []
        
    def visit_Assign(self, node):
        """Track variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned_vars.add(target.id)
        self.generic_visit(node)
        return node
    
    def visit_Name(self, node):
        """Track variable usage"""
        if isinstance(node.ctx, ast.Load):
            self.used_vars.add(node.id)
        self.generic_visit(node)
        return node


class SimplifyConditionals(ast.NodeTransformer):
    """Simplify conditional expressions"""
    
    def visit_If(self, node):
        """Simplify if statements"""
        self.generic_visit(node)
        
        # Simplify: if condition: return True else: return False
        # To: return condition
        if (len(node.body) == 1 and len(node.orelse) == 1 and
            isinstance(node.body[0], ast.Return) and isinstance(node.orelse[0], ast.Return)):
            
            body_return = node.body[0]
            else_return = node.orelse[0]
            
            if (isinstance(body_return.value, ast.Constant) and 
                isinstance(else_return.value, ast.Constant)):
                
                if body_return.value.value is True and else_return.value.value is False:
                    # Return the condition directly
                    return ast.Return(value=node.test)
                elif body_return.value.value is False and else_return.value.value is True:
                    # Return the negated condition
                    return ast.Return(value=ast.UnaryOp(op=ast.Not(), operand=node.test))
        
        return node
    
    def visit_Compare(self, node):
        """Simplify comparisons"""
        self.generic_visit(node)
        
        # Simplify: x == True to x
        if (len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and
            len(node.comparators) == 1):
            
            comparator = node.comparators[0]
            if isinstance(comparator, ast.Constant) and comparator.value is True:
                return node.left
            elif isinstance(comparator, ast.Constant) and comparator.value is False:
                return ast.UnaryOp(op=ast.Not(), operand=node.left)
        
        return node


class ExtractComplexExpressions(ast.NodeTransformer):
    """Extract complex expressions into variables"""
    
    def __init__(self, threshold=3):
        super().__init__()
        self.threshold = threshold
        self.extracted_vars = []
        self.counter = 0
    
    def visit_Return(self, node):
        """Extract complex return expressions"""
        self.generic_visit(node)
        
        if node.value and self._is_complex(node.value):
            var_name = f"result_{self.counter}"
            self.counter += 1
            
            # Create assignment
            assign = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=node.value
            )
            
            # Update return to use variable
            node.value = ast.Name(id=var_name, ctx=ast.Load())
            
            self.extracted_vars.append(assign)
        
        return node
    
    def _is_complex(self, node):
        """Check if expression is complex"""
        if isinstance(node, (ast.BinOp, ast.BoolOp)):
            count = self._count_operations(node)
            return count >= self.threshold
        return False
    
    def _count_operations(self, node):
        """Count number of operations in expression"""
        if isinstance(node, (ast.BinOp, ast.BoolOp, ast.UnaryOp)):
            count = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.BinOp, ast.BoolOp, ast.UnaryOp)) and child != node:
                    count += 1
            return count
        return 0


class ImproveLoops(ast.NodeTransformer):
    """Improve loop constructs"""
    
    def visit_For(self, node):
        """Optimize for loops"""
        self.generic_visit(node)
        
        # Convert range(len(list)) to enumerate
        if isinstance(node.iter, ast.Call):
            if (isinstance(node.iter.func, ast.Name) and 
                node.iter.func.id == 'range' and
                len(node.iter.args) == 1):
                
                arg = node.iter.args[0]
                if isinstance(arg, ast.Call):
                    if isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                        # This is range(len(something))
                        # Check if we're indexing the same thing in the loop
                        # This is a simplified check
                        pass
        
        return node


class AddTypeHints(ast.NodeTransformer):
    """Add type hints where missing"""
    
    def visit_FunctionDef(self, node):
        """Add return type hints"""
        self.generic_visit(node)
        
        # Check if function has return statement
        has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
        
        # If no return type annotation exists, we could infer it
        # For now, just track that it's missing
        if has_return and node.returns is None:
            # Could add a comment or annotation here
            pass
        
        return node


class RemoveDuplicateCode(ast.NodeTransformer):
    """Identify and remove duplicate code blocks"""
    
    def __init__(self):
        super().__init__()
        self.code_blocks = []
        self.duplicates = []
    
    def visit_FunctionDef(self, node):
        """Track function bodies for duplication"""
        self.generic_visit(node)
        
        # Create a hash of the function body
        body_str = ast.dump(node)
        
        for existing in self.code_blocks:
            if existing['body'] == body_str and existing['name'] != node.name:
                self.duplicates.append({
                    'original': existing['name'],
                    'duplicate': node.name,
                    'line': node.lineno
                })
        
        self.code_blocks.append({
            'name': node.name,
            'body': body_str,
            'line': node.lineno
        })
        
        return node


class RefactorMagicNumbers(ast.NodeTransformer):
    """Replace magic numbers with named constants"""
    
    def __init__(self):
        super().__init__()
        self.magic_numbers = []
        self.constants = {}
    
    def visit_Constant(self, node):
        """Find magic numbers"""
        self.generic_visit(node)
        
        # Track numeric constants (excluding 0, 1, -1)
        if isinstance(node.value, (int, float)):
            if node.value not in [0, 1, -1, 0.0, 1.0]:
                if node.value not in self.constants:
                    const_name = f"CONSTANT_{len(self.constants) + 1}"
                    self.constants[node.value] = const_name
                    self.magic_numbers.append({
                        'value': node.value,
                        'name': const_name,
                        'line': getattr(node, 'lineno', 0)
                    })
        
        return node


# ============================================
# MAIN REFACTORING FUNCTIONS
# ============================================

def refactor_code_ast(code: str, options: Dict = None) -> Dict:
    """
    Main AST-based refactoring function
    
    Args:
        code: Python source code to refactor
        options: Dictionary of refactoring options
            - simplify_conditionals: bool
            - extract_complex: bool
            - remove_unused: bool
            - improve_loops: bool
            - remove_duplicates: bool
            - refactor_magic_numbers: bool
    
    Returns:
        Dictionary with refactored code and analysis
    """
    
    if options is None:
        options = {
            'simplify_conditionals': True,
            'extract_complex': True,
            'remove_unused': False,  # Can be risky
            'improve_loops': True,
            'remove_duplicates': False,  # Informational only
            'refactor_magic_numbers': True
        }
    
    try:
        # Parse the code
        tree = ast.parse(code)
        original_tree = ast.parse(code)  # Keep original for comparison
        
        changes = []
        issues = []
        warnings = []
        
        # Apply refactorings based on options
        if options.get('simplify_conditionals', True):
            transformer = SimplifyConditionals()
            tree = transformer.visit(tree)
            changes.append({
                'type': 'simplify_conditionals',
                'description': 'Simplified conditional expressions'
            })
        
        if options.get('remove_unused', False):
            analyzer = RemoveUnusedVariables()
            analyzer.visit(tree)
            # Note: We identify but don't remove automatically as it can be risky
            if analyzer.assigned_vars - analyzer.used_vars:
                unused = analyzer.assigned_vars - analyzer.used_vars
                warnings.append({
                    'type': 'unused_variables',
                    'variables': list(unused),
                    'description': f'Found {len(unused)} potentially unused variables'
                })
        
        if options.get('extract_complex', True):
            transformer = ExtractComplexExpressions(threshold=3)
            tree = transformer.visit(tree)
            if transformer.extracted_vars:
                changes.append({
                    'type': 'extract_complex',
                    'description': f'Extracted {len(transformer.extracted_vars)} complex expressions',
                    'count': len(transformer.extracted_vars)
                })
        
        if options.get('refactor_magic_numbers', True):
            analyzer = RefactorMagicNumbers()
            analyzer.visit(tree)
            if analyzer.magic_numbers:
                warnings.append({
                    'type': 'magic_numbers',
                    'numbers': analyzer.magic_numbers,
                    'description': f'Found {len(analyzer.magic_numbers)} magic numbers'
                })
        
        if options.get('remove_duplicates', False):
            analyzer = RemoveDuplicateCode()
            analyzer.visit(tree)
            if analyzer.duplicates:
                warnings.append({
                    'type': 'duplicate_code',
                    'duplicates': analyzer.duplicates,
                    'description': f'Found {len(analyzer.duplicates)} duplicate code blocks'
                })
        
        # Fix missing locations in the AST
        ast.fix_missing_locations(tree)
        
        # Convert back to source code
        try:
            refactored_code = astor.to_source(tree)
        except Exception as e:
            # Fallback: use ast.unparse if astor fails (Python 3.9+)
            try:
                refactored_code = ast.unparse(tree)
            except:
                return {
                    'success': False,
                    'error': f'Failed to generate source code: {str(e)}',
                    'original_code': code
                }
        
        # Validate syntax
        try:
            ast.parse(refactored_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            issues.append({
                'type': 'syntax_error',
                'description': str(e),
                'line': e.lineno
            })
        
        return {
            'success': True,
            'refactored_code': refactored_code,
            'original_code': code,
            'changes': changes,
            'warnings': warnings,
            'issues': issues,
            'syntax_valid': syntax_valid,
            'method': 'AST-based refactoring'
        }
    
    except SyntaxError as e:
        return {
            'success': False,
            'error': f'Syntax error in original code: {str(e)} at line {e.lineno}',
            'original_code': code,
            'syntax_valid': False
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Refactoring failed: {str(e)}',
            'original_code': code
        }


def analyze_code_structure(code: str) -> Dict:
    """
    Analyze code structure using AST
    
    Returns:
        Dictionary with code metrics and structure analysis
    """
    
    try:
        tree = ast.parse(code)
        
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity': {},
            'lines_of_code': len(code.split('\n')),
            'total_statements': 0
        }
        
        for node in ast.walk(tree):
            # Count statements
            if isinstance(node, ast.stmt):
                analysis['total_statements'] += 1
            
            # Analyze functions
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args),
                    'returns': node.returns is not None,
                    'decorators': len(node.decorator_list),
                    'docstring': ast.get_docstring(node) is not None
                }
                
                # Calculate cyclomatic complexity
                complexity = calculate_complexity(node)
                func_info['complexity'] = complexity
                
                analysis['functions'].append(func_info)
            
            # Analyze classes
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': sum(1 for n in node.body if isinstance(n, ast.FunctionDef)),
                    'bases': len(node.bases),
                    'docstring': ast.get_docstring(node) is not None
                }
                analysis['classes'].append(class_info)
            
            # Analyze imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                else:
                    module = node.module or ''
                    for alias in node.names:
                        analysis['imports'].append({
                            'module': f"{module}.{alias.name}",
                            'alias': alias.asname,
                            'line': node.lineno
                        })
        
        return {
            'success': True,
            'analysis': analysis
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def calculate_complexity(node: ast.AST) -> int:
    """
    Calculate cyclomatic complexity of a function
    Complexity = 1 + number of decision points
    """
    complexity = 1
    
    for child in ast.walk(node):
        # Decision points
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp)):
            complexity += 1
    
    return complexity


def suggest_refactorings(code: str) -> List[Dict]:
    """
    Analyze code and suggest possible refactorings
    
    Returns:
        List of refactoring suggestions
    """
    
    suggestions = []
    
    try:
        tree = ast.parse(code)
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_length = len(node.body)
                complexity = calculate_complexity(node)
                
                if func_length > 20:
                    suggestions.append({
                        'type': 'long_function',
                        'severity': 'medium',
                        'function': node.name,
                        'line': node.lineno,
                        'description': f'Function "{node.name}" is {func_length} statements long. Consider breaking it into smaller functions.',
                        'suggestion': 'Extract method refactoring recommended'
                    })
                
                if complexity > 10:
                    suggestions.append({
                        'type': 'high_complexity',
                        'severity': 'high',
                        'function': node.name,
                        'line': node.lineno,
                        'complexity': complexity,
                        'description': f'Function "{node.name}" has high cyclomatic complexity ({complexity}). Consider simplifying.',
                        'suggestion': 'Reduce conditional nesting or extract complex logic'
                    })
                
                # Check for too many parameters
                if len(node.args.args) > 5:
                    suggestions.append({
                        'type': 'too_many_parameters',
                        'severity': 'low',
                        'function': node.name,
                        'line': node.lineno,
                        'parameter_count': len(node.args.args),
                        'description': f'Function "{node.name}" has {len(node.args.args)} parameters.',
                        'suggestion': 'Consider using a configuration object or reducing parameters'
                    })
        
        # Check for deeply nested code
        max_nesting = get_max_nesting_level(tree)
        if max_nesting > 4:
            suggestions.append({
                'type': 'deep_nesting',
                'severity': 'medium',
                'max_nesting': max_nesting,
                'description': f'Code has deep nesting level ({max_nesting}). This reduces readability.',
                'suggestion': 'Use early returns or extract nested logic into functions'
            })
        
        return suggestions
    
    except Exception as e:
        return [{
            'type': 'error',
            'severity': 'high',
            'description': f'Failed to analyze code: {str(e)}'
        }]


def get_max_nesting_level(node: ast.AST, current_level: int = 0) -> int:
    """Calculate maximum nesting level in code"""
    max_level = current_level
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
            child_max = get_max_nesting_level(child, current_level + 1)
            max_level = max(max_level, child_max)
        else:
            child_max = get_max_nesting_level(child, current_level)
            max_level = max(max_level, child_max)
    
    return max_level


def format_code_pep8(code: str) -> Dict:
    """
    Format code according to PEP 8 standards using AST
    
    Returns:
        Dictionary with formatted code
    """
    
    try:
        # Parse and regenerate to get basic formatting
        tree = ast.parse(code)
        ast.fix_missing_locations(tree)
        
        try:
            formatted_code = astor.to_source(tree)
        except:
            formatted_code = ast.unparse(tree)
        
        return {
            'success': True,
            'formatted_code': formatted_code,
            'original_code': code,
            'method': 'AST-based formatting'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'original_code': code
        }
