"""
Code Risk Detection System
Analyzes Python code for security, performance, and maintainability risks
"""

import subprocess
import json
import tempfile
import os
from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass
class CodeRisk:
    category: str  # 'security', 'performance', 'maintainability', 'bug'
    severity: str  # 'critical', 'high', 'medium', 'low'
    line: int
    code: str
    message: str
    explanation: str
    fix_suggestion: str
    impact: str

class RiskAnalyzer:
    
    def analyze(self, code: str) -> Dict:
        """Comprehensive risk analysis"""
        print("\n[RISK ANALYZER] Starting analysis...")
        
        risks = []
        
        # Security risks (using Bandit)
        security_risks = self._analyze_security(code)
        risks.extend(security_risks)
        print(f"  - Security: {len(security_risks)} risks found")
        
        # Complexity risks (using Radon)
        complexity_risks = self._analyze_complexity(code)
        risks.extend(complexity_risks)
        print(f"  - Complexity: {len(complexity_risks)} risks found")
        
        # Custom pattern matching
        custom_risks = self._analyze_custom_patterns(code)
        risks.extend(custom_risks)
        print(f"  - Custom patterns: {len(custom_risks)} risks found")
        
        # Categorize by severity
        by_severity = {
            'critical': [r for r in risks if r.severity == 'critical'],
            'high': [r for r in risks if r.severity == 'high'],
            'medium': [r for r in risks if r.severity == 'medium'],
            'low': [r for r in risks if r.severity == 'low']
        }
        
        risk_score = self._calculate_risk_score(risks)
        
        print(f"[RISK ANALYZER] Total: {len(risks)} risks, Score: {risk_score}/100")
        
        return {
            'risks': [asdict(r) for r in risks],
            'total': len(risks),
            'by_severity': {
                'critical': len(by_severity['critical']),
                'high': len(by_severity['high']),
                'medium': len(by_severity['medium']),
                'low': len(by_severity['low'])
            },
            'risk_score': risk_score
        }
    
    def _analyze_security(self, code: str) -> List[CodeRisk]:
        """Use Bandit to detect security issues"""
        risks = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                for issue in data.get('results', []):
                    risks.append(CodeRisk(
                        category='security',
                        severity=issue['issue_severity'].lower(),
                        line=issue['line_number'],
                        code=issue.get('code', '').strip()[:100],
                        message=issue['issue_text'],
                        explanation=self._get_security_explanation(issue.get('test_id', '')),
                        fix_suggestion=self._get_security_fix(issue.get('test_id', '')),
                        impact='Security vulnerability - could lead to data breach or system compromise'
                    ))
            
            os.unlink(temp_file)
        except Exception as e:
            print(f"  Security analysis error: {e}")
        
        return risks
    
    def _analyze_complexity(self, code: str) -> List[CodeRisk]:
        """Use Radon to detect complexity issues"""
        risks = []
        
        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
            
            # Cyclomatic complexity
            cc_results = cc_visit(code)
            for item in cc_results:
                if item.complexity > 10:
                    severity = 'high' if item.complexity > 20 else 'medium'
                    risks.append(CodeRisk(
                        category='maintainability',
                        severity=severity,
                        line=item.lineno,
                        code=item.name,
                        message=f'High cyclomatic complexity: {item.complexity}',
                        explanation=f'Function "{item.name}" has complexity {item.complexity}. Recommended maximum is 10. Higher complexity increases bug probability.',
                        fix_suggestion='Break down into smaller functions, reduce nested conditions, simplify logic',
                        impact=f'Harder to test and maintain (complexity: {item.complexity})'
                    ))
            
            # Maintainability Index
            mi_score = mi_visit(code, True)
            if mi_score < 65:
                severity = 'high' if mi_score < 40 else 'medium'
                risks.append(CodeRisk(
                    category='maintainability',
                    severity=severity,
                    line=1,
                    code='Overall Code',
                    message=f'Low maintainability index: {mi_score:.0f}/100',
                    explanation='Maintainability index measures how easy code is to maintain. Score below 65 indicates difficult maintenance.',
                    fix_suggestion='Simplify logic, add documentation, reduce complexity, improve naming conventions',
                    impact=f'Difficult to maintain and modify (score: {mi_score:.0f}/100, target: 65+)'
                ))
        
        except Exception as e:
            print(f"  Complexity analysis error: {e}")
        
        return risks
    
    def _analyze_custom_patterns(self, code: str) -> List[CodeRisk]:
        """Custom pattern matching for common issues"""
        risks = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # SQL Injection
            if ('execute(' in line or 'cursor.' in line) and ('+' in line or '%' in line or 'format(' in line):
                if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper():
                    risks.append(CodeRisk(
                        category='security',
                        severity='critical',
                        line=i,
                        code=line.strip()[:100],
                        message='Possible SQL injection vulnerability',
                        explanation='String concatenation or formatting in SQL queries allows attackers to inject malicious SQL commands',
                        fix_suggestion='Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))',
                        impact='CRITICAL: Database compromise, data theft, unauthorized access, data manipulation'
                    ))
            
            # eval() usage
            if 'eval(' in line and not line.strip().startswith('#'):
                risks.append(CodeRisk(
                    category='security',
                    severity='critical',
                    line=i,
                    code=line.strip()[:100],
                    message='Dangerous eval() function detected',
                    explanation='eval() executes arbitrary Python code and is a major security vulnerability',
                    fix_suggestion='Use ast.literal_eval() for safe evaluation, or json.loads() for JSON data',
                    impact='CRITICAL: Arbitrary code execution, full system compromise possible'
                ))
            
            # exec() usage
            if 'exec(' in line and not line.strip().startswith('#'):
                risks.append(CodeRisk(
                    category='security',
                    severity='critical',
                    line=i,
                    code=line.strip()[:100],
                    message='Dangerous exec() function detected',
                    explanation='exec() executes arbitrary Python statements and poses severe security risks',
                    fix_suggestion='Refactor to use safer alternatives, validate and sanitize all inputs',
                    impact='CRITICAL: Arbitrary code execution, security breach'
                ))
            
            # Hardcoded credentials
            if any(keyword in line.lower() for keyword in ['password', 'api_key', 'secret', 'token']) and '=' in line:
                if '"' in line or "'" in line:
                    if not 'input(' in line and not 'getenv' in line:
                        risks.append(CodeRisk(
                            category='security',
                            severity='high',
                            line=i,
                            code=line.strip()[:100].replace(line.split('=')[1].strip(), '***'),
                            message='Possible hardcoded credentials detected',
                            explanation='Hardcoded credentials in source code can be exposed in version control',
                            fix_suggestion='Use environment variables: password = os.getenv("PASSWORD")',
                            impact='HIGH: Credentials exposure, unauthorized access if code is leaked'
                        ))
            
            # No exception type (bare except)
            if line.strip() == 'except:':
                risks.append(CodeRisk(
                    category='bug',
                    severity='medium',
                    line=i,
                    code=line.strip(),
                    message='Bare except clause detected',
                    explanation='Catches all exceptions including KeyboardInterrupt and SystemExit',
                    fix_suggestion='Use specific exception types: except ValueError: or except Exception:',
                    impact='Hides bugs, makes debugging very difficult, prevents proper error handling'
                ))
            
            # String concatenation in loop
            if 'for ' in line and any(lines[j].strip().startswith('result +=') or lines[j].strip().startswith('text +=') for j in range(max(0, i-1), min(len(lines), i+3))):
                risks.append(CodeRisk(
                    category='performance',
                    severity='medium',
                    line=i,
                    code=line.strip()[:100],
                    message='String concatenation in loop - performance issue',
                    explanation='String concatenation in loops creates new string objects each iteration (O(n²) complexity)',
                    fix_suggestion='Use list.append() then "".join(list) for better performance',
                    impact='Poor performance with large datasets, memory inefficiency'
                ))
            
            # Global variable usage
            if line.strip().startswith('global '):
                risks.append(CodeRisk(
                    category='maintainability',
                    severity='low',
                    line=i,
                    code=line.strip(),
                    message='Global variable usage detected',
                    explanation='Global variables make code harder to test, debug, and maintain',
                    fix_suggestion='Pass values as function parameters instead of using globals',
                    impact='Harder to test, debug, and reason about code behavior'
                ))
            
            # TODO/FIXME comments
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                risks.append(CodeRisk(
                    category='maintainability',
                    severity='low',
                    line=i,
                    code=line.strip()[:100],
                    message='Unresolved TODO/FIXME comment',
                    explanation='Code marked for future changes or fixes',
                    fix_suggestion='Address the TODO item or create a tracking ticket',
                    impact='Incomplete functionality, potential bugs'
                ))
        
        return risks
    
    def _calculate_risk_score(self, risks: List[CodeRisk]) -> int:
        """Calculate overall risk score (0-100)"""
        if not risks:
            return 0
        
        weights = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3
        }
        
        total_score = sum(weights.get(r.severity, 0) for r in risks)
        return min(100, total_score)
    
    def _get_security_explanation(self, test_id: str) -> str:
        """Get detailed explanation for Bandit issues"""
        explanations = {
            'B201': 'Flask debug mode exposes sensitive information and allows code execution',
            'B301': 'Pickle module can execute arbitrary code during deserialization',
            'B303': 'MD5 and SHA1 are cryptographically broken hash functions',
            'B501': 'Disabling SSL verification exposes data to man-in-the-middle attacks',
            'B601': 'Using shell=True with Paramiko allows command injection',
            'B602': 'Using shell=True with subprocess allows command injection',
            'B608': 'SQL query construction using string formatting is vulnerable to injection',
        }
        return explanations.get(test_id, 'Security vulnerability detected by Bandit scanner')
    
    def _get_security_fix(self, test_id: str) -> str:
        """Get fix suggestions for Bandit issues"""
        fixes = {
            'B201': 'Never use debug=True in production: app.run(debug=False)',
            'B301': 'Use json module instead: json.dumps(data) / json.loads(data)',
            'B303': 'Use SHA256 or higher: hashlib.sha256(data)',
            'B501': 'Always verify SSL: requests.get(url, verify=True)',
            'B608': 'Use parameterized queries: cursor.execute("SELECT * FROM t WHERE id=?", (id,))',
        }
        return fixes.get(test_id, 'Review Bandit documentation for specific fix')