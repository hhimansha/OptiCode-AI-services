"""
Architecture & Dependency Analysis Module
Analyzes project structure, design patterns, SOLID principles, and dependencies

Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/architecture_analyzer.py
Author: IT22606860
"""

import ast
import os
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import re


class DesignPattern(Enum):
    """Common design patterns"""
    SINGLETON = "Singleton"
    FACTORY = "Factory"
    OBSERVER = "Observer"
    STRATEGY = "Strategy"
    DECORATOR = "Decorator"
    ADAPTER = "Adapter"
    FACADE = "Facade"
    BUILDER = "Builder"
    PROTOTYPE = "Prototype"
    PROXY = "Proxy"


@dataclass
class ClassDependency:
    """Represents a dependency between classes"""
    source_class: str
    target_class: str
    dependency_type: str  # 'inheritance', 'composition', 'usage'
    line_number: int


@dataclass
class ArchitectureIssue:
    """Architecture-level issue"""
    severity: str  # 'critical', 'major', 'minor'
    category: str
    description: str
    location: str
    suggestion: str


class ArchitectureAnalyzer:
    """Comprehensive architecture analysis"""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
        self.classes = {}
        self.dependencies = []
        self.modules = {}
        self.issues = []
        
    def analyze_project(self, code_files: Dict[str, str]) -> Dict:
        """
        Analyze entire project architecture
        
        Args:
            code_files: Dict mapping file paths to code content
        
        Returns:
            Complete architecture analysis
        """
        
        # Parse all files
        for filepath, code in code_files.items():
            try:
                tree = ast.parse(code)
                self._analyze_module(filepath, tree)
            except SyntaxError:
                continue
        
        # Perform analysis
        solid_analysis = self._analyze_solid_principles()
        patterns = self._detect_design_patterns()
        coupling = self._analyze_coupling()
        cohesion = self._analyze_cohesion()
        layers = self._analyze_layer_separation()
        
        return {
            'summary': {
                'total_classes': len(self.classes),
                'total_modules': len(self.modules),
                'total_dependencies': len(self.dependencies),
                'issues_found': len(self.issues)
            },
            'solid_principles': solid_analysis,
            'design_patterns': patterns,
            'coupling_metrics': coupling,
            'cohesion_metrics': cohesion,
            'layer_separation': layers,
            'dependencies': self._format_dependencies(),
            'issues': [self._format_issue(i) for i in self.issues]
        }
    
    def _analyze_module(self, filepath: str, tree: ast.AST):
        """Analyze a single module"""
        
        module_name = os.path.basename(filepath).replace('.py', '')
        
        # Extract classes
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, filepath)
                classes.append(class_info)
                self.classes[node.name] = class_info
        
        self.modules[module_name] = {
            'filepath': filepath,
            'classes': classes
        }
    
    def _extract_class_info(self, node: ast.ClassDef, filepath: str) -> Dict:
        """Extract detailed class information"""
        
        methods = []
        attributes = []
        dependencies = set()
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'is_public': not item.name.startswith('_'),
                    'params': len(item.args.args),
                    'line': item.lineno
                })
            
            # Extract dependencies
            for subnode in ast.walk(item):
                if isinstance(subnode, ast.Name):
                    dependencies.add(subnode.id)
        
        return {
            'name': node.name,
            'filepath': filepath,
            'line': node.lineno,
            'bases': [self._get_base_name(b) for b in node.bases],
            'methods': methods,
            'method_count': len(methods),
            'public_methods': sum(1 for m in methods if m['is_public']),
            'dependencies': list(dependencies)
        }
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return 'Unknown'
    
    def _analyze_solid_principles(self) -> Dict:
        """Analyze SOLID principles compliance"""
        
        results = {
            'single_responsibility': self._check_srp(),
            'open_closed': self._check_ocp(),
            'liskov_substitution': self._check_lsp(),
            'interface_segregation': self._check_isp(),
            'dependency_inversion': self._check_dip()
        }
        
        # Calculate overall score
        scores = [r['score'] for r in results.values()]
        results['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        return results
    
    def _check_srp(self) -> Dict:
        """Check Single Responsibility Principle"""
        
        violations = []
        
        for class_name, class_info in self.classes.items():
            # Check if class has too many responsibilities
            method_count = class_info['method_count']
            
            if method_count > 15:
                violations.append({
                    'class': class_name,
                    'method_count': method_count,
                    'file': class_info['filepath'],
                    'line': class_info['line'],
                    'description': f'Class has {method_count} methods - likely multiple responsibilities'
                })
                
                self.issues.append(ArchitectureIssue(
                    severity='major',
                    category='SRP Violation',
                    description=f'Class {class_name} has {method_count} methods',
                    location=f"{class_info['filepath']}:{class_info['line']}",
                    suggestion='Consider splitting into smaller classes with single responsibilities'
                ))
        
        score = 100 - (len(violations) * 10)
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'score': max(0, score),
            'description': 'Single Responsibility Principle: A class should have one reason to change'
        }
    
    def _check_ocp(self) -> Dict:
        """Check Open/Closed Principle"""
        
        violations = []
        
        for class_name, class_info in self.classes.items():
            # Check if class uses inheritance properly
            if not class_info['bases'] and class_info['method_count'] > 10:
                # Large class with no inheritance - might not be extendable
                violations.append({
                    'class': class_name,
                    'issue': 'No inheritance, large class - hard to extend',
                    'file': class_info['filepath']
                })
        
        score = 100 - (len(violations) * 15)
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'score': max(0, score),
            'description': 'Open/Closed: Open for extension, closed for modification'
        }
    
    def _check_lsp(self) -> Dict:
        """Check Liskov Substitution Principle"""
        
        violations = []
        
        # Check inheritance relationships
        for class_name, class_info in self.classes.items():
            if class_info['bases']:
                # Check if derived class maintains base class interface
                for base in class_info['bases']:
                    if base in self.classes:
                        base_info = self.classes[base]
                        
                        # Simple heuristic: check method count similarity
                        base_methods = base_info['public_methods']
                        derived_methods = class_info['public_methods']
                        
                        if derived_methods < base_methods * 0.5:
                            violations.append({
                                'class': class_name,
                                'base': base,
                                'issue': 'Derived class has significantly fewer methods than base',
                                'file': class_info['filepath']
                            })
        
        score = 100 - (len(violations) * 20)
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'score': max(0, score),
            'description': 'Liskov Substitution: Derived classes must be substitutable for base classes'
        }
    
    def _check_isp(self) -> Dict:
        """Check Interface Segregation Principle"""
        
        violations = []
        
        # Check for fat interfaces (classes with too many public methods)
        for class_name, class_info in self.classes.items():
            public_methods = class_info['public_methods']
            
            if public_methods > 10:
                violations.append({
                    'class': class_name,
                    'public_methods': public_methods,
                    'issue': 'Interface too large - clients may depend on methods they don\'t use',
                    'file': class_info['filepath']
                })
                
                self.issues.append(ArchitectureIssue(
                    severity='minor',
                    category='ISP Violation',
                    description=f'Class {class_name} has {public_methods} public methods',
                    location=class_info['filepath'],
                    suggestion='Consider splitting into smaller, more focused interfaces'
                ))
        
        score = 100 - (len(violations) * 8)
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'score': max(0, score),
            'description': 'Interface Segregation: No client should be forced to depend on unused methods'
        }
    
    def _check_dip(self) -> Dict:
        """Check Dependency Inversion Principle"""
        
        violations = []
        
        # Check for concrete class dependencies vs abstract
        for class_name, class_info in self.classes.items():
            concrete_deps = 0
            
            for dep in class_info['dependencies']:
                if dep in self.classes:
                    # It's a concrete class dependency
                    concrete_deps += 1
            
            if concrete_deps > 5:
                violations.append({
                    'class': class_name,
                    'concrete_dependencies': concrete_deps,
                    'issue': 'Too many concrete class dependencies',
                    'file': class_info['filepath'],
                    'suggestion': 'Depend on abstractions, not concrete classes'
                })
        
        score = 100 - (len(violations) * 12)
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'score': max(0, score),
            'description': 'Dependency Inversion: Depend on abstractions, not concrete classes'
        }
    
    def _detect_design_patterns(self) -> Dict:
        """Detect common design patterns"""
        
        patterns = {
            'singleton': self._detect_singleton(),
            'factory': self._detect_factory(),
            'observer': self._detect_observer(),
            'strategy': self._detect_strategy(),
            'decorator': self._detect_decorator()
        }
        
        return patterns
    
    def _detect_singleton(self) -> List[Dict]:
        """Detect Singleton pattern"""
        
        singletons = []
        
        for class_name, class_info in self.classes.items():
            # Check for common singleton indicators
            methods = [m['name'] for m in class_info['methods']]
            
            if 'instance' in str(class_info['dependencies']).lower():
                singletons.append({
                    'class': class_name,
                    'confidence': 'medium',
                    'file': class_info['filepath']
                })
        
        return singletons
    
    def _detect_factory(self) -> List[Dict]:
        """Detect Factory pattern"""
        
        factories = []
        
        for class_name, class_info in self.classes.items():
            # Look for 'Factory' in name or 'create' methods
            if 'Factory' in class_name or 'Builder' in class_name:
                factories.append({
                    'class': class_name,
                    'type': 'Factory' if 'Factory' in class_name else 'Builder',
                    'confidence': 'high',
                    'file': class_info['filepath']
                })
            else:
                # Check for create methods
                create_methods = [m for m in class_info['methods'] 
                                if 'create' in m['name'].lower()]
                if len(create_methods) >= 2:
                    factories.append({
                        'class': class_name,
                        'type': 'Potential Factory',
                        'confidence': 'low',
                        'file': class_info['filepath']
                    })
        
        return factories
    
    def _detect_observer(self) -> List[Dict]:
        """Detect Observer pattern"""
        
        observers = []
        
        for class_name, class_info in self.classes.items():
            methods = [m['name'] for m in class_info['methods']]
            
            # Look for notify/update methods
            if any(x in methods for x in ['notify', 'update', 'subscribe', 'unsubscribe']):
                observers.append({
                    'class': class_name,
                    'confidence': 'medium',
                    'file': class_info['filepath']
                })
        
        return observers
    
    def _detect_strategy(self) -> List[Dict]:
        """Detect Strategy pattern"""
        
        strategies = []
        
        for class_name, class_info in self.classes.items():
            if 'Strategy' in class_name:
                strategies.append({
                    'class': class_name,
                    'confidence': 'high',
                    'file': class_info['filepath']
                })
        
        return strategies
    
    def _detect_decorator(self) -> List[Dict]:
        """Detect Decorator pattern"""
        
        decorators = []
        
        for class_name, class_info in self.classes.items():
            if 'Decorator' in class_name or 'Wrapper' in class_name:
                decorators.append({
                    'class': class_name,
                    'confidence': 'high',
                    'file': class_info['filepath']
                })
        
        return decorators
    
    def _analyze_coupling(self) -> Dict:
        """Analyze coupling between classes"""
        
        # Calculate efferent coupling (outgoing dependencies)
        efferent = {}
        for class_name, class_info in self.classes.items():
            deps = set(class_info['dependencies'])
            efferent[class_name] = len(deps & set(self.classes.keys()))
        
        # Calculate afferent coupling (incoming dependencies)
        afferent = defaultdict(int)
        for class_name, class_info in self.classes.items():
            for dep in class_info['dependencies']:
                if dep in self.classes:
                    afferent[dep] += 1
        
        # Calculate instability: I = Ce / (Ce + Ca)
        instability = {}
        for class_name in self.classes:
            ce = efferent.get(class_name, 0)
            ca = afferent.get(class_name, 0)
            total = ce + ca
            instability[class_name] = ce / total if total > 0 else 0
        
        avg_efferent = sum(efferent.values()) / len(efferent) if efferent else 0
        avg_afferent = sum(afferent.values()) / len(self.classes) if self.classes else 0
        avg_instability = sum(instability.values()) / len(instability) if instability else 0
        
        return {
            'average_efferent_coupling': round(avg_efferent, 2),
            'average_afferent_coupling': round(avg_afferent, 2),
            'average_instability': round(avg_instability, 2),
            'highly_coupled_classes': [
                {'class': name, 'coupling': efferent[name]}
                for name, coupling in efferent.items() if coupling > 10
            ]
        }
    
    def _analyze_cohesion(self) -> Dict:
        """Analyze cohesion within classes"""
        
        cohesion_scores = {}
        
        for class_name, class_info in self.classes.items():
            # Simple cohesion heuristic: ratio of shared dependencies
            methods = class_info['methods']
            if not methods:
                cohesion_scores[class_name] = 0
                continue
            
            # If methods are reasonably sized, cohesion is likely good
            avg_params = sum(m['params'] for m in methods) / len(methods)
            cohesion_scores[class_name] = min(100, avg_params * 20)
        
        avg_cohesion = sum(cohesion_scores.values()) / len(cohesion_scores) if cohesion_scores else 0
        
        return {
            'average_cohesion': round(avg_cohesion, 2),
            'low_cohesion_classes': [
                {'class': name, 'cohesion': round(score, 2)}
                for name, score in cohesion_scores.items() if score < 40
            ]
        }
    
    def _analyze_layer_separation(self) -> Dict:
        """Analyze architectural layers"""
        
        layers = {
            'presentation': [],
            'business': [],
            'data': [],
            'utility': []
        }
        
        for class_name, class_info in self.classes.items():
            filepath = class_info['filepath'].lower()
            
            # Classify based on file path or class name
            if any(x in filepath for x in ['api', 'router', 'controller', 'view']):
                layers['presentation'].append(class_name)
            elif any(x in filepath for x in ['service', 'business', 'logic']):
                layers['business'].append(class_name)
            elif any(x in filepath for x in ['db', 'data', 'repository', 'model']):
                layers['data'].append(class_name)
            else:
                layers['utility'].append(class_name)
        
        return {
            'layers': {k: len(v) for k, v in layers.items()},
            'details': layers,
            'has_clear_separation': all(v for v in layers.values())
        }
    
    def _format_dependencies(self) -> List[Dict]:
        """Format dependencies for output"""
        return [
            {
                'source': dep.source_class,
                'target': dep.target_class,
                'type': dep.dependency_type,
                'line': dep.line_number
            }
            for dep in self.dependencies
        ]
    
    def _format_issue(self, issue: ArchitectureIssue) -> Dict:
        """Format issue for output"""
        return {
            'severity': issue.severity,
            'category': issue.category,
            'description': issue.description,
            'location': issue.location,
            'suggestion': issue.suggestion
        }


def analyze_architecture(code_files: Dict[str, str]) -> Dict:
    """
    Main entry point for architecture analysis
    
    Args:
        code_files: Dictionary mapping file paths to code content
    
    Returns:
        Complete architecture analysis report
    """
    
    analyzer = ArchitectureAnalyzer()
    return analyzer.analyze_project(code_files)
