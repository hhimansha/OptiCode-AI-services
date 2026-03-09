"""
Ethical Code Analyzer Module
Analyzes code for ethical coding practices, inclusivity, and responsible development
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/ethical_code_analyzer.py
"""

import ast
import re
from typing import Dict, List


class EthicalCodeAnalyzer:
    """Analyze code for ethical and responsible coding practices"""
    
    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.good_practices = []
    
    def analyze(self, code: str) -> Dict:
        """Perform comprehensive ethical code analysis"""
        
        results = {
            'success': True,
            'categories': {},
            'issues': [],
            'recommendations': [],
            'good_practices': [],
            'ethical_score': 100
        }
        
        try:
            # Run different ethical checks
            results['categories']['inclusive_language'] = self.check_inclusive_language(code)
            results['categories']['data_privacy'] = self.check_data_privacy(code)
            results['categories']['accessibility'] = self.check_accessibility(code)
            results['categories']['error_messages'] = self.check_error_messages(code)
            results['categories']['transparency'] = self.check_transparency(code)
            results['categories']['security_ethics'] = self.check_security_ethics(code)
            results['categories']['environmental'] = self.check_environmental_impact(code)
            
            # Aggregate results
            results['issues'] = self.issues
            results['recommendations'] = self.recommendations
            results['good_practices'] = self.good_practices
            
            # Calculate ethical score
            results['ethical_score'] = self.calculate_ethical_score()
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def check_inclusive_language(self, code: str) -> Dict:
        """Check for non-inclusive or biased language"""
        
        issues = []
        recommendations = []
        
        # Problematic terms and their alternatives
        problematic_terms = {
            'master': {
                'alternatives': ['main', 'primary', 'leader'],
                'context': 'version control or hierarchy',
                'severity': 'medium'
            },
            'slave': {
                'alternatives': ['replica', 'secondary', 'follower'],
                'context': 'system architecture',
                'severity': 'high'
            },
            'blacklist': {
                'alternatives': ['blocklist', 'denylist'],
                'context': 'filtering or blocking',
                'severity': 'medium'
            },
            'whitelist': {
                'alternatives': ['allowlist', 'permitlist'],
                'context': 'filtering or allowing',
                'severity': 'medium'
            },
            'dummy': {
                'alternatives': ['placeholder', 'sample', 'mock'],
                'context': 'test data',
                'severity': 'low'
            },
            'sanity': {
                'alternatives': ['validation', 'verification', 'health check'],
                'context': 'checks or tests',
                'severity': 'low'
            }
        }
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip comments that explain the issue
            if 'inclusive' in line.lower() or 'legacy' in line.lower():
                continue
            
            line_lower = line.lower()
            for term, info in problematic_terms.items():
                if re.search(rf'\b{term}\b', line_lower):
                    issues.append({
                        'type': 'non_inclusive_language',
                        'severity': info['severity'],
                        'line': i,
                        'term': term,
                        'alternatives': info['alternatives'],
                        'context': info['context'],
                        'description': f'Non-inclusive term "{term}" found',
                        'recommendation': f'Consider using: {", ".join(info["alternatives"])}',
                        'example': f'# Instead of {term}, use {info["alternatives"][0]}'
                    })
        
        # Check for gendered language
        gendered_terms = ['he', 'him', 'his', 'she', 'her', 'hers', 'guys']
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):  # Comments only
                for term in gendered_terms:
                    if re.search(rf'\b{term}\b', line.lower()):
                        recommendations.append({
                            'type': 'gendered_language',
                            'severity': 'low',
                            'line': i,
                            'description': 'Consider using gender-neutral language in comments',
                            'recommendation': 'Use "they/them" or restructure to avoid pronouns',
                            'example': '# The user can update their profile (instead of his/her profile)'
                        })
                        break
        
        self.issues.extend(issues)
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'issues_found': len(issues),
            'issues': issues,
            'recommendations': recommendations
        }
    
    def check_data_privacy(self, code: str) -> Dict:
        """Check for data privacy and protection practices"""
        
        issues = []
        recommendations = []
        good_practices = []
        
        try:
            tree = ast.parse(code)
            
            # Check for hardcoded sensitive data
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.lower()
                            
                            # Check for sensitive variable names
                            if any(sensitive in var_name for sensitive in ['password', 'secret', 'api_key', 'token', 'credential']):
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    issues.append({
                                        'type': 'hardcoded_sensitive_data',
                                        'severity': 'critical',
                                        'line': node.lineno,
                                        'variable': target.id,
                                        'description': f'Sensitive data "{target.id}" appears to be hardcoded',
                                        'recommendation': 'Use environment variables or secure configuration management',
                                        'example': 'import os\napi_key = os.getenv("API_KEY")'
                                    })
            
            # Check for proper password handling
            if 'password' in code.lower():
                if 'hash' in code.lower() or 'bcrypt' in code.lower() or 'pbkdf2' in code.lower():
                    good_practices.append({
                        'type': 'password_hashing',
                        'description': 'Uses password hashing (good practice)',
                        'example': 'Never store passwords in plain text'
                    })
                else:
                    recommendations.append({
                        'type': 'password_handling',
                        'severity': 'high',
                        'description': 'Password handling detected without obvious hashing',
                        'recommendation': 'Always hash passwords using bcrypt, argon2, or pbkdf2',
                        'example': 'from bcrypt import hashpw\nhashed = hashpw(password.encode(), gensalt())'
                    })
            
            # Check for PII (Personally Identifiable Information)handling
            pii_terms = ['ssn', 'social_security', 'credit_card', 'email', 'phone_number', 'address']
            for term in pii_terms:
                if term in code.lower():
                    recommendations.append({
                        'type': 'pii_handling',
                        'severity': 'medium',
                        'description': f'PII data ({term}) detected',
                        'recommendation': 'Ensure proper encryption, access controls, and compliance with privacy regulations (GDPR, CCPA)',
                        'example': '# Encrypt PII data\n# Implement access logging\n# Follow data retention policies'
                    })
                    break
            
            # Check for logging sensitive data
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['debug', 'info', 'warning', 'error']:
                            # This is a logging call
                            recommendations.append({
                                'type': 'logging_privacy',
                                'severity': 'low',
                                'line': node.lineno,
                                'description': 'Logging detected - ensure sensitive data is not logged',
                                'recommendation': 'Review log statements to avoid logging passwords, tokens, or PII',
                                'example': '# Never log: password, tokens, credit cards, SSN, etc.'
                            })
                            break
        
        except Exception as e:
            pass
        
        self.issues.extend(issues)
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'critical_issues': len([i for i in issues if i.get('severity') == 'critical']),
            'issues': issues,
            'recommendations': recommendations,
            'good_practices': good_practices
        }
    
    def check_accessibility(self, code: str) -> Dict:
        """Check for accessibility considerations"""
        
        recommendations = []
        good_practices = []
        
        # Check for UI-related code
        ui_indicators = ['print', 'display', 'show', 'render', 'ui', 'interface']
        
        if any(indicator in code.lower() for indicator in ui_indicators):
            recommendations.append({
                'type': 'accessibility',
                'severity': 'low',
                'description': 'UI-related code detected',
                'recommendation': 'Ensure output is accessible: provide alternative formats, support screen readers, use clear language',
                'example': '# Provide text alternatives for visual information\n# Use semantic markup\n# Support keyboard navigation'
            })
        
        # Check for color usage in output
        if 'color' in code.lower() or 'colour' in code.lower():
            recommendations.append({
                'type': 'color_accessibility',
                'severity': 'low',
                'description': 'Color usage detected',
                'recommendation': 'Do not rely solely on color to convey information',
                'example': '# Use both color and text/symbols\n# Ensure sufficient contrast ratios'
            })
        
        # Check for error messages
        if 'error' in code.lower() or 'exception' in code.lower():
            good_practices.append({
                'type': 'error_handling',
                'description': 'Includes error handling (ensure errors are user-friendly)',
                'example': 'Provide clear, actionable error messages'
            })
        
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'recommendations': recommendations,
            'good_practices': good_practices
        }
    
    def check_error_messages(self, code: str) -> Dict:
        """Check for helpful and respectful error messages"""
        
        recommendations = []
        good_practices = []
        
        # Extract string literals that might be error messages
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise):
                    if isinstance(node.exc, ast.Call):
                        if node.exc.args:
                            if isinstance(node.exc.args[0], ast.Constant):
                                error_msg = node.exc.args[0].value
                                
                                # Check for negative language
                                negative_terms = ['stupid', 'dumb', 'idiot', 'invalid', 'wrong', 'bad']
                                if any(term in error_msg.lower() for term in negative_terms):
                                    recommendations.append({
                                        'type': 'error_message_tone',
                                        'severity': 'medium',
                                        'line': node.lineno,
                                        'description': 'Error message uses negative language',
                                        'recommendation': 'Use constructive, helpful language in error messages',
                                        'example': 'Instead of "Invalid input", use "Please provide a value between 1 and 10"'
                                    })
                                
                                # Check if error message is actionable
                                if len(error_msg) > 20 and ('please' in error_msg.lower() or 'try' in error_msg.lower()):
                                    good_practices.append({
                                        'type': 'helpful_error_message',
                                        'line': node.lineno,
                                        'description': 'Error message is actionable and helpful',
                                        'example': error_msg
                                    })
        
        except Exception as e:
            pass
        
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'recommendations': recommendations,
            'good_practices': good_practices
        }
    
    def check_transparency(self, code: str) -> Dict:
        """Check for code transparency and explainability"""
        
        recommendations = []
        good_practices = []
        
        try:
            tree = ast.parse(code)
            
            # Check for documentation
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                good_practices.append({
                    'type': 'module_documentation',
                    'description': 'Module has documentation explaining its purpose',
                    'example': 'Clear documentation helps users understand the code'
                })
            
            # Check for complex algorithms without comments
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for mathematical operations (potential algorithm)
                    has_complex_math = any(
                        isinstance(n, (ast.BinOp, ast.UnaryOp))
                        for n in ast.walk(node)
                    )
                    
                    if has_complex_math:
                        docstring = ast.get_docstring(node)
                        if not docstring or len(docstring) < 30:
                            recommendations.append({
                                'type': 'algorithm_transparency',
                                'severity': 'low',
                                'line': node.lineno,
                                'function': node.name,
                                'description': f'Function "{node.name}" contains complex operations but lacks detailed documentation',
                                'recommendation': 'Document algorithms and decision-making logic for transparency',
                                'example': '# Explain the algorithm, its purpose, and any assumptions'
                            })
        
        except Exception as e:
            pass
        
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'recommendations': recommendations,
            'good_practices': good_practices
        }
    
    def check_security_ethics(self, code: str) -> Dict:
        """Check for ethical security practices"""
        
        issues = []
        recommendations = []
        
        # Check for potentially harmful patterns
        dangerous_imports = ['os.system', 'subprocess', 'eval', 'exec', '__import__']
        
        for dangerous in dangerous_imports:
            if dangerous in code:
                issues.append({
                    'type': 'potentially_dangerous_code',
                    'severity': 'high' if dangerous in ['eval', 'exec'] else 'medium',
                    'description': f'Uses potentially dangerous function: {dangerous}',
                    'recommendation': f'Avoid {dangerous} if possible. If necessary, validate and sanitize all inputs',
                    'example': '# Never use eval/exec with untrusted input\n# Validate and sanitize all user inputs'
                })
        
        # Check for SQL without parameterization
        if 'sql' in code.lower() and ('%s' in code or '.format(' in code or '{' in code):
            issues.append({
                'type': 'sql_injection_risk',
                'severity': 'critical',
                'description': 'SQL query construction detected - possible SQL injection risk',
                'recommendation': 'Use parameterized queries or ORM to prevent SQL injection',
                'example': 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'
            })
        
        # Check for file operations without validation
        if 'open(' in code:
            recommendations.append({
                'type': 'file_operations',
                'severity': 'medium',
                'description': 'File operations detected',
                'recommendation': 'Validate file paths and limit access to authorized directories only',
                'example': '# Validate paths\n# Use os.path.normpath() and check path prefixes\n# Implement proper access controls'
            })
        
        self.issues.extend(issues)
        self.recommendations.extend(recommendations)
        
        return {
            'checked': True,
            'critical_issues': len([i for i in issues if i.get('severity') == 'critical']),
            'issues': issues,
            'recommendations': recommendations
        }
    
    def check_environmental_impact(self, code: str) -> Dict:
        """Check for environmental considerations (efficiency, resource usage)"""
        
        recommendations = []
        good_practices = []
        
        # Check for infinite loops without break conditions
        if 'while True' in code:
            recommendations.append({
                'type': 'resource_efficiency',
                'severity': 'low',
                'description': 'Infinite loop detected',
                'recommendation': 'Ensure proper exit conditions and resource cleanup',
                'example': 'while running:\n    if should_stop():\n        break'
            })
        
        # Check for resource management
        if 'with open(' in code:
            good_practices.append({
                'type': 'resource_management',
                'description': 'Uses context managers for proper resource cleanup',
                'example': 'with open(file) as f: # Automatically closes'
            })
        
        # Check for caching
        if 'cache' in code.lower() or '@lru_cache' in code or '@cache' in code:
            good_practices.append({
                'type': 'efficiency',
                'description': 'Uses caching to reduce redundant computations',
                'example': 'from functools import lru_cache\n@lru_cache'
            })
        
        self.recommendations.extend(recommendations)
        self.good_practices.extend(good_practices)
        
        return {
            'checked': True,
            'recommendations': recommendations,
            'good_practices': good_practices
        }
    
    def calculate_ethical_score(self) -> int:
        """Calculate overall ethical coding score"""
        
        score = 100
        
        # Deduct for issues
        for issue in self.issues:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                score -= 20
            elif severity == 'high':
                score -= 10
            elif severity == 'medium':
                score -= 5
            elif severity == 'low':
                score -= 2
        
        # Bonus for good practices
        bonus = min(len(self.good_practices) * 2, 15)
        score += bonus
        
        return max(0, min(100, score))


def analyze_ethical_code(code: str) -> Dict:
    """
    Main entry point for ethical code analysis
    
    Args:
        code: Python source code to analyze
    
    Returns:
        Ethical analysis results
    """
    
    analyzer = EthicalCodeAnalyzer()
    return analyzer.analyze(code)
