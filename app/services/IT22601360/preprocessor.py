"""
Code Preprocessor Service
Handles code parsing, tokenization, and structural analysis
Student: IT22601360
"""

import re
import ast
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from app.utils.constants import SUPPORTED_LANGUAGES, KNOWN_CONCEPTS


@dataclass
class CodeMetrics:
    """Metrics extracted from code"""
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)


@dataclass
class PreprocessedCode:
    """Result of code preprocessing"""
    original_code: str
    cleaned_code: str
    language: str
    metrics: CodeMetrics
    detected_patterns: Dict[str, List[str]]
    structural_summary: Dict


class CodePreprocessor:
    """
    Preprocesses code for concept extraction
    It analyzes code structure and identifies patterns BEFORE calling Gemini
    """
    
    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
        self.known_concepts = KNOWN_CONCEPTS
    
    def preprocess(self, code: str, language: str = "python") -> PreprocessedCode:
        """
        Main preprocessing pipeline
        
        Args:
            code: Raw source code string
            language: Programming language
            
        Returns:
            PreprocessedCode object with all analysis results
        """
        # Step 1: Clean the code
        cleaned_code = self._clean_code(code)
        
        # Step 2: Extract metrics based on language
        if language == "python":
            metrics = self._extract_python_metrics(code)
        else:
            metrics = self._extract_generic_metrics(code, language)
        
        # Step 3: Detect known patterns (rule-based, before LLM)
        detected_patterns = self._detect_patterns(code)
        
        # Step 4: Generate structural summary
        structural_summary = self._generate_summary(code, metrics, detected_patterns)
        
        return PreprocessedCode(
            original_code=code,
            cleaned_code=cleaned_code,
            language=language,
            metrics=metrics,
            detected_patterns=detected_patterns,
            structural_summary=structural_summary
        )
    
    def _clean_code(self, code: str) -> str:
        """Remove excessive whitespace and normalize code"""
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in code.split('\n')]
        
        # Remove excessive blank lines (keep max 2 consecutive)
        cleaned_lines = []
        blank_count = 0
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_python_metrics(self, code: str) -> CodeMetrics:
        """
        AST-based extraction for Python - More accurate
        """
        metrics = CodeMetrics()
        
        lines = code.split('\n')
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        metrics.blank_lines = len([l for l in lines if not l.strip()])
        metrics.comment_lines = len([l for l in lines if l.strip().startswith('#')])
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metrics.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        metrics.imports.append(f"{module}.{alias.name}")
                
                # Extract class names
                elif isinstance(node, ast.ClassDef):
                    metrics.classes.append(node.name)
                
                # Extract function names
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    metrics.functions.append(node.name)
                
                # Extract variable assignments (top-level)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            metrics.variables.append(target.id)
                            
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            metrics = self._extract_generic_metrics(code, "python")
        
        return metrics
    
    def _extract_generic_metrics(self, code: str, language: str) -> CodeMetrics:
        """
        Regex-based extraction for other languages
        """
        metrics = CodeMetrics()
        
        lines = code.split('\n')
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        metrics.blank_lines = len([l for l in lines if not l.strip()])
        
        # Comment detection based on language
        lang_config = self.supported_languages.get(language, {})
        comment_single = lang_config.get('comment_single', '//')
        
        metrics.comment_lines = len([
            l for l in lines 
            if l.strip().startswith(comment_single)
        ])
        
        # Generic patterns
        # Functions
        func_patterns = [
            r'def\s+(\w+)\s*\(',           # Python
            r'function\s+(\w+)\s*\(',       # JavaScript
            r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*{',  # Java/C++
            r'func\s+(\w+)\s*\(',           # Go
            r'fn\s+(\w+)\s*\(',             # Rust
        ]
        
        for pattern in func_patterns:
            matches = re.findall(pattern, code)
            metrics.functions.extend(matches)
        
        # Classes
        class_patterns = [
            r'class\s+(\w+)',               # Python/Java/C++
            r'struct\s+(\w+)',              # C/C++/Go/Rust
            r'interface\s+(\w+)',           # Java/TypeScript
        ]
        
        for pattern in class_patterns:
            matches = re.findall(pattern, code)
            metrics.classes.extend(matches)
        
        # Imports
        import_patterns = [
            r'import\s+([\w.]+)',           # Python/Java
            r'from\s+([\w.]+)\s+import',    # Python
            r'require\([\'"](.+?)[\'"]\)',  # Node.js
            r'import\s+.*?from\s+[\'"](.+?)[\'"]',  # ES6
            r'#include\s*[<"](.+?)[>"]',    # C/C++
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            metrics.imports.extend(matches)
        
        return metrics
    
    # def _detect_patterns(self, code: str) -> Dict[str, List[str]]:
    #     """
    #     Rule-based pattern detection
        
    #     This identifies concepts BEFORE sending to LLM
    #     Reduces API calls and improves accuracy
    #     """
    #     detected = {
    #         "data_structures": [],
    #         "algorithms": [],
    #         "design_patterns": [],
    #         "architectures": [],
    #         "paradigms": [],
    #         "programming_concepts": []
    #     }
        
    #     code_lower = code.lower()
        
    #     for category, concepts in self.known_concepts.items():
    #         for concept_name, patterns in concepts.items():
    #             for pattern in patterns:
    #                 # Check if pattern exists in code
    #                 if pattern.lower() in code_lower:
    #                     if concept_name not in detected[category]:
    #                         detected[category].append(concept_name)
    #                     break
                    
    #                 # Try regex pattern matching
    #                 try:
    #                     if re.search(pattern, code, re.IGNORECASE):
    #                         if concept_name not in detected[category]:
    #                             detected[category].append(concept_name)
    #                         break
    #                 except re.error:
    #                     continue
        
    #     return detected
    def _detect_patterns(self, code: str, language: str = "python") -> Dict[str, List[str]]:
        """
        Enhanced pattern detection with AST for Python
        """
        detected = {
            "data_structures": [],
            "algorithms": [],
            "design_patterns": [],
            "architectures": [],
            "paradigms": [],
            "programming_concepts": []
        }
        
        # For Python, use AST-based detection
        if language == "python":
            try:
                from app.services.IT22601360.ast_analyzer import ASTAnalyzer
                
                analysis = ASTAnalyzer.analyze_python(code)
                ast_concepts = ASTAnalyzer.convert_to_concepts(analysis)
                
                # Merge AST concepts
                for category in detected:
                    detected[category].extend(ast_concepts.get(category, []))
                    detected[category] = list(set(detected[category]))  # Remove duplicates
                    
            except ImportError:
                print("AST analyzer not available, using regex detection")
        
        # Fallback to regex detection for all languages
        code_lower = code.lower()
        
        for category, concepts in self.known_concepts.items():
            for concept_name, patterns in concepts.items():
                for pattern in patterns:
                    # Check if pattern exists in code
                    if pattern.lower() in code_lower:
                        if concept_name not in detected[category]:
                            detected[category].append(concept_name)
                        break
                    
                    # Try regex pattern matching
                    try:
                        if re.search(pattern, code, re.IGNORECASE):
                            if concept_name not in detected[category]:
                                detected[category].append(concept_name)
                            break
                    except re.error:
                        continue
        
        return detected
    def _generate_summary(
        self, 
        code: str, 
        metrics: CodeMetrics, 
        patterns: Dict[str, List[str]]
    ) -> Dict:
        """
        Generate a structural summary for LLM context
        """
        # Count total detected patterns
        total_patterns = sum(len(v) for v in patterns.values())
        
        # Determine code complexity (simple heuristic)
        complexity = "simple"
        if metrics.lines_of_code > 100:
            complexity = "complex"
        elif metrics.lines_of_code > 50:
            complexity = "moderate"
        
        if len(metrics.classes) > 3 or len(metrics.functions) > 10:
            complexity = "complex"
        
        return {
            "metrics": {
                "total_lines": metrics.lines_of_code,
                "functions_count": len(metrics.functions),
                "classes_count": len(metrics.classes),
                "imports_count": len(metrics.imports)
            },
            "structure": {
                "functions": metrics.functions[:20],  # Limit for LLM context
                "classes": metrics.classes[:10],
                "imports": metrics.imports[:20]
            },
            "pre_detected_patterns": patterns,
            "pattern_count": total_patterns,
            "estimated_complexity": complexity
        }
    
    def detect_language(self, code: str, filename: Optional[str] = None) -> str:
        """
        Auto-detect programming language from code or filename
        """
        if filename:
            ext = '.' + filename.split('.')[-1].lower()
            for lang, config in self.supported_languages.items():
                if ext in config.get('extensions', []):
                    return lang
        
        # Heuristic detection from code patterns
        patterns = {
            'python': [r'def\s+\w+\s*\(', r'import\s+\w+', r'print\s*\(', r':\s*$'],
            'javascript': [r'const\s+\w+', r'let\s+\w+', r'function\s+\w+', r'=>', r'console\.log'],
            'typescript': [r'interface\s+\w+', r':\s*\w+\[\]', r'<\w+>'],
            'java': [r'public\s+class', r'public\s+static\s+void\s+main', r'System\.out'],
            'cpp': [r'#include\s*<', r'std::', r'cout\s*<<', r'int\s+main\s*\('],
            'c': [r'#include\s*<stdio', r'printf\s*\(', r'int\s+main\s*\('],
            'go': [r'package\s+main', r'func\s+\w+', r'fmt\.'],
            'rust': [r'fn\s+main', r'let\s+mut', r'println!'],
        }
        
        scores = {lang: 0 for lang in patterns}
        
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                if re.search(pattern, code):
                    scores[lang] += 1
        
        # Return language with highest score
        best_lang = max(scores, key=scores.get)
        return best_lang if scores[best_lang] > 0 else 'python'
