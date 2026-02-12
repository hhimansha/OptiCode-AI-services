"""
Code Quality Analyzer Module
Analyzes Python code for quality, complexity, security issues, and more
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/code_analyzer.py
"""

import ast
import re
from typing import Dict, List, Tuple
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze
import bandit
from bandit.core import manager as bandit_manager
from bandit.core import config as bandit_config
import tempfile
import os


class CodeQualityAnalyzer:
    """Comprehensive code quality analyzer"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.suggestions = []
    
    def analyze(self, code: str) -> Dict:
        """
        Perform comprehensive code analysis
        
        Returns:
            Dictionary with all analysis results
        """
        
        results = {
            'success': True,
            'metrics': {},
            'complexity': {},
            'security': {},
            'style': {},
            'maintainability': {},
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Basic metrics
            results['metrics'] = self.analyze_metrics(code)
            
            # Complexity analysis
            results['complexity'] = self.analyze_complexity(code)
            
            # Security analysis
            results['security'] = self.analyze_security(code)
            
            # Style analysis
            results['style'] = self.analyze_style(code)
            
            # Maintainability
            results['maintainability'] = self.analyze_maintainability(code)
            
            # Code smells
            results['code_smells'] = self.detect_code_smells(code)
            
            # Aggregate issues
            results['issues'] = self.issues
            results['warnings'] = self.warnings
            results['suggestions'] = self.suggestions
            
            # Calculate overall score
            results['overall_score'] = self.calculate_overall_score(results)
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def analyze_metrics(self, code: str) -> Dict:
        """Analyze basic code metrics using radon"""
        
        try:
            raw_metrics = analyze(code)
            
            return {
                'loc': raw_metrics.loc,  # Lines of code
                'lloc': raw_metrics.lloc,  # Logical lines of code
                'sloc': raw_metrics.sloc,  # Source lines of code
                'comments': raw_metrics.comments,  # Comment lines
                'multi': raw_metrics.multi,  # Multi-line strings
                'blank': raw_metrics.blank,  # Blank lines
                'single_comments': raw_metrics.single_comments,
                'comment_ratio': (raw_metrics.comments / raw_metrics.loc * 100) if raw_metrics.loc > 0 else 0
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_complexity(self, code: str) -> Dict:
        """Analyze code complexity"""
        
        try:
            # Cyclomatic complexity
            complexity_results = cc_visit(code)
            
            complexities = []
            total_complexity = 0
            high_complexity_count = 0
            
            for item in complexity_results:
                complexity_data = {
                    'name': item.name,
                    'type': item.letter,  # F=function, M=method, C=class
                    'complexity': item.complexity,
                    'line': item.lineno,
                    'col': item.col_offset,
                    'endline': item.endline
                }
                
                total_complexity += item.complexity
                
                # Flag high complexity
                if item.complexity > 10:
                    high_complexity_count += 1
                    complexity_data['warning'] = 'High complexity'
                    self.warnings.append({
                        'type': 'high_complexity',
                        'name': item.name,
                        'complexity': item.complexity,
                        'line': item.lineno,
                        'description': f'{item.letter}: {item.name} has complexity {item.complexity} (threshold: 10)'
                    })
                elif item.complexity > 7:
                    complexity_data['warning'] = 'Moderate complexity'
                
                complexities.append(complexity_data)
            
            avg_complexity = total_complexity / len(complexities) if complexities else 0
            
            return {
                'functions': complexities,
                'average_complexity': round(avg_complexity, 2),
                'total_complexity': total_complexity,
                'high_complexity_count': high_complexity_count,
                'max_complexity': max([c['complexity'] for c in complexities]) if complexities else 0
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_security(self, code: str) -> Dict:
        """Analyze security vulnerabilities using Bandit"""
        
        try:
            # Write code to temporary file for Bandit
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Configure Bandit
                b_conf = bandit_config.BanditConfig()
                b_mgr = bandit_manager.BanditManager(b_conf, 'file')
                
                # Run Bandit
                b_mgr.discover_files([temp_file])
                b_mgr.run_tests()
                
                # Collect results
                issues = []
                severity_count = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                confidence_count = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                
                for result in b_mgr.results:
                    issue = {
                        'test_id': result.test_id,
                        'test_name': result.test,
                        'severity': result.severity,
                        'confidence': result.confidence,
                        'line': result.lineno,
                        'description': result.text,
                        'issue_text': result.issue_text
                    }
                    
                    issues.append(issue)
                    severity_count[result.severity] += 1
                    confidence_count[result.confidence] += 1
                    
                    # Add to global issues
                    if result.severity in ['HIGH', 'MEDIUM']:
                        self.issues.append({
                            'type': 'security',
                            'severity': result.severity.lower(),
                            'line': result.lineno,
                            'description': result.text
                        })
                
                return {
                    'total_issues': len(issues),
                    'severity_breakdown': severity_count,
                    'confidence_breakdown': confidence_count,
                    'issues': issues,
                    'has_critical': severity_count['HIGH'] > 0
                }
            
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        
        except Exception as e:
            return {'error': str(e), 'total_issues': 0}
    
    def analyze_style(self, code: str) -> Dict:
        """Analyze code style and PEP 8 compliance"""
        
        issues = []
        
        try:
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > 79:
                    issues.append({
                        'line': i,
                        'type': 'line_length',
                        'description': f'Line exceeds 79 characters ({len(line)} chars)',
                        'severity': 'low'
                    })
                
                # Check for trailing whitespace
                if line.endswith(' ') or line.endswith('\t'):
                    issues.append({
                        'line': i,
                        'type': 'trailing_whitespace',
                        'description': 'Line has trailing whitespace',
                        'severity': 'low'
                    })
                
                # Check for tabs
                if '\t' in line:
                    issues.append({
                        'line': i,
                        'type': 'tabs',
                        'description': 'Line uses tabs instead of spaces',
                        'severity': 'low'
                    })
                
                # Check for multiple statements on one line
                if ';' in line and not line.strip().startswith('#'):
                    issues.append({
                        'line': i,
                        'type': 'multiple_statements',
                        'description': 'Multiple statements on one line',
                        'severity': 'medium'
                    })
            
            # Check naming conventions
            naming_issues = self.check_naming_conventions(code)
            issues.extend(naming_issues)
            
            return {
                'total_issues': len(issues),
                'issues': issues,
                'pep8_compliant': len([i for i in issues if i['severity'] in ['medium', 'high']]) == 0
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def check_naming_conventions(self, code: str) -> List[Dict]:
        """Check Python naming conventions"""
        
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check function names (should be lowercase with underscores)
                if isinstance(node, ast.FunctionDef):
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('__'):
                        issues.append({
                            'line': node.lineno,
                            'type': 'naming_function',
                            'description': f'Function "{node.name}" should use lowercase with underscores',
                            'severity': 'low'
                        })
                
                # Check class names (should be CamelCase)
                elif isinstance(node, ast.ClassDef):
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        issues.append({
                            'line': node.lineno,
                            'type': 'naming_class',
                            'description': f'Class "{node.name}" should use CamelCase',
                            'severity': 'medium'
                        })
                
                # Check constants (should be UPPERCASE)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Check if it's a module-level constant
                            if isinstance(node.value, ast.Constant):
                                if target.id.isupper() and '_' not in target.id and len(target.id) > 1:
                                    # Might want underscores
                                    pass
        
        except:
            pass
        
        return issues
    
    def analyze_maintainability(self, code: str) -> Dict:
        """Calculate maintainability index and related metrics"""
        
        try:
            # Maintainability Index
            mi_results = mi_visit(code, multi=True)
            
            # Halstead metrics
            halstead = h_visit(code)
            
            mi_score = mi_results
            
            # Interpret MI score
            if mi_score >= 20:
                rating = 'A'  # Highly maintainable
                description = 'Excellent maintainability'
            elif mi_score >= 10:
                rating = 'B'  # Moderately maintainable
                description = 'Good maintainability'
            elif mi_score >= 0:
                rating = 'C'  # Difficult to maintain
                description = 'Poor maintainability'
            else:
                rating = 'F'  # Extremely difficult to maintain
                description = 'Very poor maintainability'
            
            return {
                'maintainability_index': round(mi_score, 2),
                'rating': rating,
                'description': description,
                'halstead_metrics': {
                    'vocabulary': halstead.total.vocabulary,
                    'length': halstead.total.length,
                    'volume': round(halstead.total.volume, 2),
                    'difficulty': round(halstead.total.difficulty, 2),
                    'effort': round(halstead.total.effort, 2),
                    'bugs': round(halstead.total.bugs, 2)
                } if halstead and halstead.total else None
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def detect_code_smells(self, code: str) -> Dict:
        """Detect common code smells"""
        
        smells = []
        
        try:
            tree = ast.parse(code)
            
            # Long parameter list
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    param_count = len(node.args.args)
                    
                    if param_count > 5:
                        smells.append({
                            'type': 'long_parameter_list',
                            'severity': 'medium',
                            'line': node.lineno,
                            'function': node.name,
                            'description': f'Function has {param_count} parameters (recommended: <= 5)',
                            'suggestion': 'Consider using a parameter object or reducing parameters'
                        })
                    
                    # Long method
                    body_length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if body_length > 50:
                        smells.append({
                            'type': 'long_method',
                            'severity': 'medium',
                            'line': node.lineno,
                            'function': node.name,
                            'description': f'Function is {body_length} lines long (recommended: <= 50)',
                            'suggestion': 'Consider breaking into smaller functions'
                        })
                    
                    # Missing docstring
                    if ast.get_docstring(node) is None:
                        smells.append({
                            'type': 'missing_docstring',
                            'severity': 'low',
                            'line': node.lineno,
                            'function': node.name,
                            'description': f'Function "{node.name}" is missing a docstring',
                            'suggestion': 'Add documentation to explain the function purpose'
                        })
                
                # Large class
                elif isinstance(node, ast.ClassDef):
                    method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                    
                    if method_count > 20:
                        smells.append({
                            'type': 'large_class',
                            'severity': 'high',
                            'line': node.lineno,
                            'class': node.name,
                            'description': f'Class has {method_count} methods (recommended: <= 20)',
                            'suggestion': 'Consider splitting into multiple classes'
                        })
                    
                    # God class (too many responsibilities)
                    class_length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if class_length > 200:
                        smells.append({
                            'type': 'god_class',
                            'severity': 'high',
                            'line': node.lineno,
                            'class': node.name,
                            'description': f'Class is {class_length} lines long (potential God class)',
                            'suggestion': 'Apply Single Responsibility Principle - split into focused classes'
                        })
                
                # Duplicate code detection
                elif isinstance(node, ast.If):
                    # Check for duplicate conditions
                    pass
            
            # Add smells to suggestions
            for smell in smells:
                if smell['severity'] in ['high', 'medium']:
                    self.suggestions.append(smell)
            
            return {
                'total_smells': len(smells),
                'by_severity': {
                    'high': len([s for s in smells if s['severity'] == 'high']),
                    'medium': len([s for s in smells if s['severity'] == 'medium']),
                    'low': len([s for s in smells if s['severity'] == 'low'])
                },
                'smells': smells
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_overall_score(self, results: Dict) -> Dict:
        """Calculate overall code quality score"""
        
        score = 100
        deductions = []
        
        # Deduct for complexity
        if 'complexity' in results and 'high_complexity_count' in results['complexity']:
            high_complex = results['complexity']['high_complexity_count']
            if high_complex > 0:
                deduction = min(high_complex * 10, 30)
                score -= deduction
                deductions.append(f'High complexity functions: -{deduction}')
        
        # Deduct for security issues
        if 'security' in results and 'severity_breakdown' in results['security']:
            high_sec = results['security']['severity_breakdown'].get('HIGH', 0)
            medium_sec = results['security']['severity_breakdown'].get('MEDIUM', 0)
            
            if high_sec > 0:
                deduction = min(high_sec * 15, 40)
                score -= deduction
                deductions.append(f'High security issues: -{deduction}')
            
            if medium_sec > 0:
                deduction = min(medium_sec * 5, 20)
                score -= deduction
                deductions.append(f'Medium security issues: -{deduction}')
        
        # Deduct for code smells
        if 'code_smells' in results and 'by_severity' in results['code_smells']:
            high_smells = results['code_smells']['by_severity'].get('high', 0)
            if high_smells > 0:
                deduction = min(high_smells * 5, 20)
                score -= deduction
                deductions.append(f'High severity code smells: -{deduction}')
        
        # Deduct for low maintainability
        if 'maintainability' in results and 'maintainability_index' in results['maintainability']:
            mi = results['maintainability']['maintainability_index']
            if mi < 10:
                deduction = 20
                score -= deduction
                deductions.append(f'Low maintainability index: -{deduction}')
            elif mi < 20:
                deduction = 10
                score -= deduction
                deductions.append(f'Moderate maintainability index: -{deduction}')
        
        score = max(0, score)
        
        # Determine grade
        if score >= 90:
            grade = 'A'
            quality = 'Excellent'
        elif score >= 80:
            grade = 'B'
            quality = 'Good'
        elif score >= 70:
            grade = 'C'
            quality = 'Fair'
        elif score >= 60:
            grade = 'D'
            quality = 'Poor'
        else:
            grade = 'F'
            quality = 'Very Poor'
        
        return {
            'score': score,
            'grade': grade,
            'quality': quality,
            'deductions': deductions
        }


def analyze_code(code: str) -> Dict:
    """
    Main entry point for code analysis
    
    Args:
        code: Python source code to analyze
    
    Returns:
        Comprehensive analysis results
    """
    
    analyzer = CodeQualityAnalyzer()
    return analyzer.analyze(code)
