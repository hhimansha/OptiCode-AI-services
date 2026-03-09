"""
Performance Optimization Module
Detects performance issues and suggests optimizations

Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/performance_optimizer.py
Author: IT22606860
"""

import ast
import astor
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum


class OptimizationCategory(Enum):
    """Performance optimization categories"""
    ALGORITHMIC = "Algorithmic Complexity"
    DATA_STRUCTURE = "Data Structure"
    MEMORY = "Memory Usage"
    ITERATION = "Iteration Efficiency"
    STRING = "String Operations"
    FUNCTION_CALL = "Function Call Overhead"
    CACHING = "Caching Opportunities"
    LAZY_EVALUATION = "Lazy Evaluation"


@dataclass
class PerformanceIssue:
    """Represents a performance issue"""
    category: OptimizationCategory
    severity: str  # 'critical', 'major', 'minor'
    line: int
    description: str
    current_code: str
    optimized_code: str
    impact: str
    complexity_before: str  # Big-O notation
    complexity_after: str


class PerformanceOptimizer:
    """Comprehensive performance analysis and optimization"""
    
    def __init__(self):
        self.issues = []
        
    def optimize(self, code: str) -> Dict:
        """
        Analyze and optimize code for performance
        
        Args:
            code: Source code to optimize
        
        Returns:
            Optimization report with suggestions
        """
        
        try:
            tree = ast.parse(code)
            
            # Run all optimizations
            self._optimize_iterations(tree)
            self._optimize_data_structures(tree)
            self._optimize_string_operations(tree)
            self._optimize_function_calls(tree)
            self._detect_caching_opportunities(tree)
            self._optimize_algorithmic_complexity(tree)
            
            # Generate optimized code
            ast.fix_missing_locations(tree)
            try:
                optimized_code = astor.to_source(tree)
            except:
                optimized_code = ast.unparse(tree)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score()
            
            return {
                'success': True,
                'original_code': code,
                'optimized_code': optimized_code,
                'issues_found': len(self.issues),
                'impact_score': impact_score,
                'issues_by_severity': self._group_by_severity(),
                'issues_by_category': self._group_by_category(),
                'detailed_issues': [self._format_issue(i) for i in self.issues],
                'summary': self._generate_summary()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'issues_found': 0
            }
    
    def _optimize_iterations(self, tree: ast.AST):
        """Optimize iteration patterns"""
        
        for node in ast.walk(tree):
            # Pattern 1: range(len(x)) → enumerate(x)
            if isinstance(node, ast.For):
                if self._is_range_len_pattern(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.ITERATION,
                        severity='minor',
                        line=node.lineno,
                        description='Using range(len()) instead of enumerate()',
                        current_code='for i in range(len(items)): value = items[i]',
                        optimized_code='for i, value in enumerate(items):',
                        impact='Improves readability and slight performance gain',
                        complexity_before='O(n)',
                        complexity_after='O(n)'
                    ))
                
                # Pattern 2: Nested loops that can be optimized
                if self._has_inefficient_nested_loops(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.ALGORITHMIC,
                        severity='major',
                        line=node.lineno,
                        description='Inefficient nested loop - consider set/dict for lookups',
                        current_code='for x in list1:\n    for y in list2:\n        if x == y: ...',
                        optimized_code='set2 = set(list2)\nfor x in list1:\n    if x in set2: ...',
                        impact='Reduces complexity from O(n*m) to O(n+m)',
                        complexity_before='O(n*m)',
                        complexity_after='O(n+m)'
                    ))
                
                # Pattern 3: List comprehension opportunity
                if self._can_use_comprehension(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.ITERATION,
                        severity='minor',
                        line=node.lineno,
                        description='Loop can be replaced with list comprehension',
                        current_code='result = []\nfor x in items:\n    result.append(x*2)',
                        optimized_code='result = [x*2 for x in items]',
                        impact='Faster execution and better readability',
                        complexity_before='O(n)',
                        complexity_after='O(n)'
                    ))
    
    def _optimize_data_structures(self, tree: ast.AST):
        """Optimize data structure usage"""
        
        for node in ast.walk(tree):
            # Pattern 1: List used for membership testing
            if isinstance(node, ast.Compare):
                if self._list_membership_test(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.DATA_STRUCTURE,
                        severity='major',
                        line=node.lineno,
                        description='Using list for membership testing - use set instead',
                        current_code='if item in my_list:',
                        optimized_code='my_set = set(my_list)\nif item in my_set:',
                        impact='Reduces lookup from O(n) to O(1)',
                        complexity_before='O(n)',
                        complexity_after='O(1)'
                    ))
            
            # Pattern 2: Repeated list concatenation
            if isinstance(node, ast.AugAssign):
                if isinstance(node.op, ast.Add) and self._is_string_or_list(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.MEMORY,
                        severity='major',
                        line=node.lineno,
                        description='Repeated concatenation creates many intermediate objects',
                        current_code='result += item  # in loop',
                        optimized_code='items = []\nitems.append(item)\nresult = "".join(items)',
                        impact='Reduces memory allocations and improves speed',
                        complexity_before='O(n²)',
                        complexity_after='O(n)'
                    ))
    
    def _optimize_string_operations(self, tree: ast.AST):
        """Optimize string operations"""
        
        for node in ast.walk(tree):
            # Pattern 1: String concatenation in loop
            if isinstance(node, ast.For):
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.AugAssign):
                        if isinstance(subnode.op, ast.Add):
                            self.issues.append(PerformanceIssue(
                                category=OptimizationCategory.STRING,
                                severity='major',
                                line=node.lineno,
                                description='String concatenation in loop',
                                current_code='result = ""\nfor s in strings:\n    result += s',
                                optimized_code='result = "".join(strings)',
                                impact='Dramatically faster for large strings',
                                complexity_before='O(n²)',
                                complexity_after='O(n)'
                            ))
                            break
            
            # Pattern 2: % formatting vs f-strings
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Mod) and self._is_string_formatting(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.STRING,
                        severity='minor',
                        line=node.lineno,
                        description='Old-style string formatting',
                        current_code='"Hello %s" % name',
                        optimized_code='f"Hello {name}"',
                        impact='Slight performance improvement and better readability',
                        complexity_before='O(1)',
                        complexity_after='O(1)'
                    ))
    
    def _optimize_function_calls(self, tree: ast.AST):
        """Optimize function call patterns"""
        
        # Track function calls in loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                calls_in_loop = []
                
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        calls_in_loop.append(subnode)
                
                # Check for invariant function calls
                if len(calls_in_loop) > 0:
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.FUNCTION_CALL,
                        severity='minor',
                        line=node.lineno,
                        description='Function call inside loop - consider hoisting if invariant',
                        current_code='for item in items:\n    result = expensive_func(constant)',
                        optimized_code='cached = expensive_func(constant)\nfor item in items:\n    result = cached',
                        impact='Reduces redundant function calls',
                        complexity_before='O(n)',
                        complexity_after='O(1) + O(n)'
                    ))
    
    def _detect_caching_opportunities(self, tree: ast.AST):
        """Detect opportunities for caching/memoization"""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for recursive functions
                if self._is_recursive(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.CACHING,
                        severity='critical',
                        line=node.lineno,
                        description='Recursive function without memoization',
                        current_code=f'def {node.name}(n):\n    return {node.name}(n-1) + {node.name}(n-2)',
                        optimized_code=f'@lru_cache(maxsize=None)\ndef {node.name}(n):\n    return {node.name}(n-1) + {node.name}(n-2)',
                        impact='Exponential to linear time complexity',
                        complexity_before='O(2ⁿ)',
                        complexity_after='O(n)'
                    ))
                
                # Check for pure functions that could benefit from caching
                if self._is_pure_function(node) and self._has_complex_computation(node):
                    self.issues.append(PerformanceIssue(
                        category=OptimizationCategory.CACHING,
                        severity='minor',
                        line=node.lineno,
                        description='Pure function with complex computation - consider caching',
                        current_code=f'def {node.name}(...):',
                        optimized_code=f'@lru_cache(maxsize=128)\ndef {node.name}(...):',
                        impact='Caches results for repeated calls',
                        complexity_before='O(n)',
                        complexity_after='O(1) amortized'
                    ))
    
    def _optimize_algorithmic_complexity(self, tree: ast.AST):
        """Detect and suggest algorithmic improvements"""
        
        for node in ast.walk(tree):
            # Pattern 1: Repeated linear searches
            if isinstance(node, ast.For):
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Compare):
                        if any(isinstance(op, ast.In) for op in subnode.ops):
                            self.issues.append(PerformanceIssue(
                                category=OptimizationCategory.ALGORITHMIC,
                                severity='major',
                                line=node.lineno,
                                description='Linear search in loop - preprocess to hash table',
                                current_code='for x in list1:\n    if x in list2: ...',
                                optimized_code='set2 = set(list2)\nfor x in list1:\n    if x in set2: ...',
                                impact='Significant speedup for large datasets',
                                complexity_before='O(n*m)',
                                complexity_after='O(n+m)'
                            ))
            
            # Pattern 2: Sorting when not needed
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'sort':
                        self.issues.append(PerformanceIssue(
                            category=OptimizationCategory.ALGORITHMIC,
                            severity='minor',
                            line=node.lineno,
                            description='Sorting - verify if full sort is needed',
                            current_code='items.sort()\nresult = items[0]',
                            optimized_code='result = min(items)',
                            impact='Use min/max if only extremes needed',
                            complexity_before='O(n log n)',
                            complexity_after='O(n)'
                        ))
    
    # Helper methods
    
    def _is_range_len_pattern(self, node: ast.For) -> bool:
        """Check for range(len(x)) pattern"""
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                if len(node.iter.args) == 1:
                    arg = node.iter.args[0]
                    if isinstance(arg, ast.Call):
                        if isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                            return True
        return False
    
    def _has_inefficient_nested_loops(self, node: ast.For) -> bool:
        """Check for inefficient nested loops"""
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.For) and subnode != node:
                # Found nested loop - check for membership testing
                for comparison in ast.walk(subnode):
                    if isinstance(comparison, ast.Compare):
                        return True
        return False
    
    def _can_use_comprehension(self, node: ast.For) -> bool:
        """Check if loop can be a comprehension"""
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute):
                        return stmt.value.func.attr == 'append'
        return False
    
    def _list_membership_test(self, node: ast.Compare) -> bool:
        """Check if comparing with list"""
        # Simple heuristic - would need more context in real implementation
        return any(isinstance(op, ast.In) for op in node.ops)
    
    def _is_string_or_list(self, node: ast.AugAssign) -> bool:
        """Check if augmented assignment is on string or list"""
        # Simplified check
        return True
    
    def _is_string_formatting(self, node: ast.BinOp) -> bool:
        """Check if % operator is for string formatting"""
        return isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
    
    def _is_recursive(self, func: ast.FunctionDef) -> bool:
        """Check if function is recursive"""
        func_name = func.name
        
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == func_name:
                        return True
        return False
    
    def _is_pure_function(self, func: ast.FunctionDef) -> bool:
        """Check if function is pure (no side effects)"""
        for node in ast.walk(func):
            # Check for I/O
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['print', 'open', 'write']:
                        return False
            # Check for global modifications
            if isinstance(node, ast.Global):
                return False
        return True
    
    def _has_complex_computation(self, func: ast.FunctionDef) -> bool:
        """Check if function has complex computation"""
        # Count loops and operations
        complexity = 0
        for node in ast.walk(func):
            if isinstance(node, (ast.For, ast.While)):
                complexity += 1
        
        return complexity > 0
    
    def _calculate_impact_score(self) -> float:
        """Calculate overall performance impact score"""
        if not self.issues:
            return 0.0
        
        severity_weights = {
            'critical': 10.0,
            'major': 5.0,
            'minor': 1.0
        }
        
        total_impact = sum(severity_weights.get(issue.severity, 1.0) for issue in self.issues)
        return min(100.0, total_impact)
    
    def _group_by_severity(self) -> Dict:
        """Group issues by severity"""
        groups = {'critical': [], 'major': [], 'minor': []}
        
        for issue in self.issues:
            groups[issue.severity].append(issue)
        
        return {
            'critical': len(groups['critical']),
            'major': len(groups['major']),
            'minor': len(groups['minor'])
        }
    
    def _group_by_category(self) -> Dict:
        """Group issues by category"""
        groups = {}
        
        for issue in self.issues:
            category = issue.category.value
            if category not in groups:
                groups[category] = 0
            groups[category] += 1
        
        return groups
    
    def _format_issue(self, issue: PerformanceIssue) -> Dict:
        """Format issue for output"""
        return {
            'category': issue.category.value,
            'severity': issue.severity,
            'line': issue.line,
            'description': issue.description,
            'current_code': issue.current_code,
            'optimized_code': issue.optimized_code,
            'impact': issue.impact,
            'complexity': {
                'before': issue.complexity_before,
                'after': issue.complexity_after
            }
        }
    
    def _generate_summary(self) -> Dict:
        """Generate optimization summary"""
        if not self.issues:
            return {
                'message': 'No significant performance issues detected',
                'recommendations': []
            }
        
        critical_count = sum(1 for i in self.issues if i.severity == 'critical')
        major_count = sum(1 for i in self.issues if i.severity == 'major')
        
        recommendations = []
        
        if critical_count > 0:
            recommendations.append('Address critical performance issues immediately')
        if major_count > 0:
            recommendations.append('Optimize major performance bottlenecks')
        
        return {
            'message': f'Found {len(self.issues)} optimization opportunities',
            'priority': 'High' if critical_count > 0 else 'Medium' if major_count > 0 else 'Low',
            'recommendations': recommendations
        }


def optimize_performance(code: str) -> Dict:
    """
    Main entry point for performance optimization
    
    Args:
        code: Source code to optimize
    
    Returns:
        Optimization report
    """
    
    optimizer = PerformanceOptimizer()
    return optimizer.optimize(code)
