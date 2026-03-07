"""
AST-based Code Analyzer for Enhanced Concept Detection
"""
import ast
import inspect
from typing import Dict, List, Set, Any
from dataclasses import dataclass

@dataclass
class ASTAnalysis:
    """Results of AST analysis"""
    classes: List[str]
    functions: List[str]
    imports: List[str]
    decorators: List[str]
    inheritance_chains: Dict[str, List[str]]
    recursive_functions: List[str]
    oop_features: Set[str]
    control_flow: Dict[str, int]
    design_patterns: List[str]


class ASTAnalyzer:
    """
    Advanced code analysis using Abstract Syntax Trees
    """
    
    @staticmethod
    def analyze_python(code: str) -> ASTAnalysis:
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(code)
            
            classes = []
            functions = []
            imports = []
            decorators = []
            inheritance_chains = {}
            recursive_functions = []
            oop_features = set()
            control_flow = {"loops": 0, "conditionals": 0, "try_blocks": 0}
            design_patterns = []
            
            # Function definitions to check for recursion
            defined_functions = set()
            
            for node in ast.walk(tree):
                # Classes
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    
                    # Check inheritance
                    if node.bases:
                        oop_features.add("inheritance")
                        inheritance_chains[node.name] = [
                            ASTAnalyzer._get_base_name(base) 
                            for base in node.bases
                        ]
                    
                    # Check for __init__ method
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                            oop_features.add("constructor")
                    
                    # Check for private methods (starting with __)
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("__"):
                            oop_features.add("encapsulation")
                
                # Functions
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                    defined_functions.add(node.name)
                    
                    # Check decorators
                    for decorator in node.decorator_list:
                        decorator_name = ASTAnalyzer._get_decorator_name(decorator)
                        if decorator_name:
                            decorators.append(decorator_name)
                    
                    # Check for recursion
                    if ASTAnalyzer._has_recursive_call(node, defined_functions):
                        recursive_functions.append(node.name)
                
                # Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                
                # Control flow
                elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                    control_flow["loops"] += 1
                elif isinstance(node, ast.If):
                    control_flow["conditionals"] += 1
                elif isinstance(node, ast.Try):
                    control_flow["try_blocks"] += 1
            
            # Analyze for design patterns
            design_patterns = ASTAnalyzer._detect_design_patterns(tree)
            
            # If classes exist, add OOP
            if classes:
                oop_features.add("oop")
            
            return ASTAnalysis(
                classes=classes,
                functions=functions,
                imports=imports,
                decorators=decorators,
                inheritance_chains=inheritance_chains,
                recursive_functions=recursive_functions,
                oop_features=oop_features,
                control_flow=control_flow,
                design_patterns=design_patterns
            )
            
        except SyntaxError as e:
            print(f"AST parsing failed: {e}")
            # Return empty analysis
            return ASTAnalysis([], [], [], [], {}, [], set(), {}, [])
    
    @staticmethod
    def _get_base_name(base_node: ast.AST) -> str:
        """Extract base class name from AST node"""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            return base_node.attr
        return "unknown"
    
    @staticmethod
    def _get_decorator_name(decorator_node: ast.AST) -> str:
        """Extract decorator name"""
        if isinstance(decorator_node, ast.Name):
            return decorator_node.id
        elif isinstance(decorator_node, ast.Attribute):
            return decorator_node.attr
        elif isinstance(decorator_node, ast.Call):
            if isinstance(decorator_node.func, ast.Name):
                return decorator_node.func.id
        return ""
    
    @staticmethod
    def _has_recursive_call(func_node: ast.FunctionDef, defined_functions: Set[str]) -> bool:
        """Check if function calls itself (recursion)"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_node.name:
                    return True
        return False
    
    @staticmethod
    def _detect_design_patterns(tree: ast.AST) -> List[str]:
        """Detect common design patterns from AST"""
        patterns = []
        
        # Singleton pattern detection
        class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        for cls in class_nodes:
            # Check for singleton (class with _instance variable and __new__ method)
            has_instance_var = False
            has_new_method = False
            
            for item in cls.body:
                # Check for class-level _instance assignment
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "_instance":
                            has_instance_var = True
                
                # Check for __new__ method
                if isinstance(item, ast.FunctionDef) and item.name == "__new__":
                    has_new_method = True
            
            if has_instance_var and has_new_method:
                patterns.append("singleton")
            
            # Check for factory methods (methods returning new instances)
            for item in cls.body:
                if isinstance(item, ast.FunctionDef):
                    # Look for methods that create and return instances
                    if ASTAnalyzer._is_factory_method(item, cls.name):
                        patterns.append("factory_method")
        
        return patterns
    
    @staticmethod
    def _is_factory_method(method_node: ast.FunctionDef, class_name: str) -> bool:
        """Check if method is a factory method"""
        # Check if method returns an instance of the class
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == class_name:
                            return True
        return False
    
    @staticmethod
    def convert_to_concepts(analysis: ASTAnalysis) -> Dict[str, List[str]]:
        """Convert AST analysis to concept dictionary"""
        concepts = {
            "data_structures": [],
            "algorithms": [],
            "design_patterns": analysis.design_patterns.copy(),
            "architectures": [],
            "paradigms": [],
            "programming_concepts": []
        }
        
        # Add OOP features
        if analysis.oop_features:
            concepts["paradigms"].append("oop")
            for feature in analysis.oop_features:
                if feature != "oop":
                    concepts["programming_concepts"].append(feature)
        
        # Add recursion
        if analysis.recursive_functions:
            concepts["algorithms"].append("recursion")
        
        # Add decorator patterns
        if any(d in ["property", "staticmethod", "classmethod"] for d in analysis.decorators):
            concepts["programming_concepts"].append("decorators")
        
        # Add control flow concepts
        if analysis.control_flow.get("loops", 0) > 0:
            concepts["programming_concepts"].append("iteration")
        if analysis.control_flow.get("conditionals", 0) > 0:
            concepts["programming_concepts"].append("conditional_logic")
        
        return concepts