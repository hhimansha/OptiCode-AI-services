"""
Code Quality Metrics Calculator
Calculates various code quality metrics
"""

from typing import Dict
import ast

class MetricsCalculator:
    
    def calculate(self, code: str) -> Dict:
        """Calculate comprehensive code metrics"""
        
        try:
            from radon.complexity import cc_visit, average_complexity
            from radon.metrics import mi_visit, h_visit
            from radon.raw import analyze
            
            # Raw metrics
            raw = analyze(code)
            
            # Cyclomatic Complexity
            cc = cc_visit(code)
            avg_complexity = average_complexity(cc) if cc else 0
            max_complexity = max([item.complexity for item in cc], default=0)
            
            # Maintainability Index
            mi = mi_visit(code, True)
            
            # Halstead metrics
            halstead = h_visit(code)
            
            # Lines of code
            loc = raw.loc
            lloc = raw.lloc
            sloc = raw.sloc
            comments = raw.comments
            
            # Count functions and classes
            tree = ast.parse(code)
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            
            return {
                'loc': loc,  # Lines of Code
                'lloc': lloc,  # Logical Lines of Code
                'sloc': sloc,  # Source Lines of Code
                'comments': comments,
                'complexity': {
                    'average': round(avg_complexity, 2),
                    'max': max_complexity,
                    'total_functions': len(cc)
                },
                'maintainability_index': round(mi, 2),
                'halstead': {
                    'volume': round(halstead.total.volume, 2) if halstead and halstead.total else 0,
                    'difficulty': round(halstead.total.difficulty, 2) if halstead and halstead.total else 0,
                    'effort': round(halstead.total.effort, 2) if halstead and halstead.total else 0
                },
                'functions_count': functions,
                'classes_count': classes
            }
        
        except Exception as e:
            print(f"Metrics calculation error: {e}")
            return {
                'loc': len(code.split('\n')),
                'error': str(e)
            }
    
    def compare(self, original_metrics: Dict, refactored_metrics: Dict) -> Dict:
        """Compare metrics and calculate improvements"""
        
        improvements = {}
        
        # LOC reduction
        if 'loc' in original_metrics and 'loc' in refactored_metrics:
            loc_change = original_metrics['loc'] - refactored_metrics['loc']
            improvements['loc_reduction'] = {
                'before': original_metrics['loc'],
                'after': refactored_metrics['loc'],
                'change': loc_change,
                'percentage': round((loc_change / original_metrics['loc'] * 100), 2) if original_metrics['loc'] > 0 else 0
            }
        
        # Complexity reduction
        if 'complexity' in original_metrics and 'complexity' in refactored_metrics:
            complexity_change = original_metrics['complexity']['average'] - refactored_metrics['complexity']['average']
            improvements['complexity_reduction'] = {
                'before': original_metrics['complexity']['average'],
                'after': refactored_metrics['complexity']['average'],
                'change': round(complexity_change, 2),
                'percentage': round((complexity_change / original_metrics['complexity']['average'] * 100), 2) if original_metrics['complexity']['average'] > 0 else 0
            }
        
        # Maintainability improvement
        if 'maintainability_index' in original_metrics and 'maintainability_index' in refactored_metrics:
            mi_change = refactored_metrics['maintainability_index'] - original_metrics['maintainability_index']
            improvements['maintainability_improvement'] = {
                'before': original_metrics['maintainability_index'],
                'after': refactored_metrics['maintainability_index'],
                'change': round(mi_change, 2),
                'percentage': round((mi_change / original_metrics['maintainability_index'] * 100), 2) if original_metrics['maintainability_index'] > 0 else 0
            }
        
        # Overall quality score (0-100)
        quality_score = self._calculate_quality_score(refactored_metrics)
        quality_improvement = quality_score - self._calculate_quality_score(original_metrics)
        
        improvements['overall_quality'] = {
            'before': self._calculate_quality_score(original_metrics),
            'after': quality_score,
            'improvement': round(quality_improvement, 2)
        }
        
        return improvements
    
    def _calculate_quality_score(self, metrics: Dict) -> int:
        """Calculate overall quality score (0-100)"""
        score = 0
        
        # Maintainability Index (40 points max)
        if 'maintainability_index' in metrics:
            mi = metrics['maintainability_index']
            score += min(40, (mi / 100) * 40)
        
        # Complexity (30 points max - lower is better)
        if 'complexity' in metrics:
            avg_complexity = metrics['complexity']['average']
            if avg_complexity <= 5:
                score += 30
            elif avg_complexity <= 10:
                score += 20
            elif avg_complexity <= 15:
                score += 10
        
        # Comments ratio (15 points max)
        if 'loc' in metrics and 'comments' in metrics:
            if metrics['loc'] > 0:
                comment_ratio = metrics['comments'] / metrics['loc']
                score += min(15, comment_ratio * 100)
        
        # LOC efficiency (15 points max - prefer concise code)
        if 'loc' in metrics and 'functions_count' in metrics:
            if metrics['functions_count'] > 0:
                loc_per_func = metrics['loc'] / metrics['functions_count']
                if loc_per_func <= 20:
                    score += 15
                elif loc_per_func <= 50:
                    score += 10
                elif loc_per_func <= 100:
                    score += 5
        
        return int(min(100, score))