"""
Code Preprocessor Service
Student: IT22601360

Fix applied:
  preprocess() now passes `language` to _detect_patterns() so non-Python
  files (JS, Java, etc.) don't silently attempt Python AST parsing.
  The AST path now only runs when language == "python".
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
    blank_lines:   int = 0
    comment_lines: int = 0
    functions:  List[str] = field(default_factory=list)
    classes:    List[str] = field(default_factory=list)
    imports:    List[str] = field(default_factory=list)
    variables:  List[str] = field(default_factory=list)


@dataclass
class PreprocessedCode:
    """Result of code preprocessing"""
    original_code:     str
    cleaned_code:      str
    language:          str
    metrics:           CodeMetrics
    detected_patterns: Dict[str, List[str]]
    structural_summary: Dict


class CodePreprocessor:
    """
    Preprocesses code for concept extraction.
    Analyses code structure and identifies patterns BEFORE calling Gemini.
    """

    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
        self.known_concepts      = KNOWN_CONCEPTS

    def preprocess(self, code: str, language: str = "python") -> PreprocessedCode:
        """
        Main preprocessing pipeline.

        Returns PreprocessedCode with:
          .metrics             — CodeMetrics (lines_of_code, functions, classes, imports)
          .detected_patterns   — { "data_structures": [], "algorithms": [], ... }
          .structural_summary  — { "metrics": {}, "structure": {}, "pre_detected_patterns": {}, ... }
        """
        cleaned_code = self._clean_code(code)

        if language == "python":
            metrics = self._extract_python_metrics(code)
        else:
            metrics = self._extract_generic_metrics(code, language)

        # FIX: pass language so _detect_patterns only runs AST path for Python
        detected_patterns = self._detect_patterns(code, language)

        structural_summary = self._generate_summary(code, metrics, detected_patterns)

        return PreprocessedCode(
            original_code=code,
            cleaned_code=cleaned_code,
            language=language,
            metrics=metrics,
            detected_patterns=detected_patterns,
            structural_summary=structural_summary,
        )

    def _clean_code(self, code: str) -> str:
        """Remove excessive whitespace and normalise code."""
        lines = [line.rstrip() for line in code.split('\n')]
        cleaned = []
        blank_count = 0
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)
        return '\n'.join(cleaned)

    def _extract_python_metrics(self, code: str) -> CodeMetrics:
        """AST-based extraction for Python."""
        metrics = CodeMetrics()
        lines = code.split('\n')
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        metrics.blank_lines   = len([l for l in lines if not l.strip()])
        metrics.comment_lines = len([l for l in lines if l.strip().startswith('#')])

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metrics.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        metrics.imports.append(f"{module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    metrics.classes.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics.functions.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            metrics.variables.append(target.id)
        except SyntaxError:
            metrics = self._extract_generic_metrics(code, "python")

        return metrics

    def _extract_generic_metrics(self, code: str, language: str) -> CodeMetrics:
        """Regex-based extraction for non-Python languages."""
        metrics = CodeMetrics()
        lines = code.split('\n')
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        metrics.blank_lines   = len([l for l in lines if not l.strip()])

        lang_config   = self.supported_languages.get(language, {})
        comment_single = lang_config.get('comment_single', '//')
        metrics.comment_lines = len([l for l in lines if l.strip().startswith(comment_single)])

        func_patterns = [
            r'def\s+(\w+)\s*\(',
            r'function\s+(\w+)\s*\(',
            r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*{',
            r'func\s+(\w+)\s*\(',
            r'fn\s+(\w+)\s*\(',
        ]
        for pattern in func_patterns:
            metrics.functions.extend(re.findall(pattern, code))

        class_patterns = [
            r'class\s+(\w+)',
            r'struct\s+(\w+)',
            r'interface\s+(\w+)',
        ]
        for pattern in class_patterns:
            metrics.classes.extend(re.findall(pattern, code))

        import_patterns = [
            r'import\s+([\w.]+)',
            r'from\s+([\w.]+)\s+import',
            r'require\([\'"](.+?)[\'"]\)',
            r'import\s+.*?from\s+[\'"](.+?)[\'"]',
            r'#include\s*[<"](.+?)[>"]',
        ]
        for pattern in import_patterns:
            metrics.imports.extend(re.findall(pattern, code))

        return metrics

    def _detect_patterns(self, code: str, language: str = "python") -> Dict[str, List[str]]:
        """
        Enhanced pattern detection.
        AST path runs only when language == "python" to avoid wasted work
        (and silent SyntaxErrors) on JS/Java/etc. files.
        """
        detected = {
            "data_structures":    [],
            "algorithms":         [],
            "design_patterns":    [],
            "architectures":      [],
            "paradigms":          [],
            "programming_concepts": [],
        }

        # AST-based detection — Python only
        if language == "python":
            try:
                from app.services.IT22601360.ast_analyzer import ASTAnalyzer
                analysis    = ASTAnalyzer.analyze_python(code)
                ast_concepts = ASTAnalyzer.convert_to_concepts(analysis)
                for category in detected:
                    detected[category].extend(ast_concepts.get(category, []))
                    detected[category] = list(set(detected[category]))
            except ImportError:
                print("AST analyzer not available, using regex detection")
            except Exception as e:
                print(f"AST detection failed: {e}")

        # Regex/keyword patterns — all languages
        code_lower = code.lower()
        for category, concepts in self.known_concepts.items():
            for concept_name, patterns in concepts.items():
                for pattern in patterns:
                    if pattern.lower() in code_lower:
                        if concept_name not in detected[category]:
                            detected[category].append(concept_name)
                        break
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
        patterns: Dict[str, List[str]],
    ) -> Dict:
        """
        Generate structural summary for LLM context.

        Returns dict with keys:
          "metrics"              → total_lines, functions_count, classes_count, imports_count
          "structure"            → functions[], classes[], imports[]
          "pre_detected_patterns"→ same as patterns arg
          "pattern_count"        → int
          "estimated_complexity" → "simple" | "moderate" | "complex"
        """
        total_patterns = sum(len(v) for v in patterns.values())

        complexity = "simple"
        if metrics.lines_of_code > 100 or len(metrics.classes) > 3 or len(metrics.functions) > 10:
            complexity = "complex"
        elif metrics.lines_of_code > 50:
            complexity = "moderate"

        return {
            "metrics": {
                "total_lines":     metrics.lines_of_code,
                "functions_count": len(metrics.functions),
                "classes_count":   len(metrics.classes),
                "imports_count":   len(metrics.imports),
            },
            "structure": {
                "functions": metrics.functions[:20],
                "classes":   metrics.classes[:10],
                "imports":   metrics.imports[:20],
            },
            "pre_detected_patterns": patterns,
            "pattern_count":         total_patterns,
            "estimated_complexity":  complexity,
        }

    def detect_language(self, code: str, filename: Optional[str] = None) -> str:
        """Auto-detect programming language from filename or code patterns."""
        if filename:
            ext = '.' + filename.split('.')[-1].lower()
            for lang, config in self.supported_languages.items():
                if ext in config.get('extensions', []):
                    return lang

        patterns = {
            'python':     [r'def\s+\w+\s*\(', r'import\s+\w+', r'print\s*\(', r':\s*$'],
            'javascript': [r'const\s+\w+', r'let\s+\w+', r'function\s+\w+', r'=>', r'console\.log'],
            'typescript': [r'interface\s+\w+', r':\s*\w+\[\]', r'<\w+>'],
            'java':       [r'public\s+class', r'public\s+static\s+void\s+main', r'System\.out'],
            'cpp':        [r'#include\s*<', r'std::', r'cout\s*<<', r'int\s+main\s*\('],
            'c':          [r'#include\s*<stdio', r'printf\s*\(', r'int\s+main\s*\('],
            'go':         [r'package\s+main', r'func\s+\w+', r'fmt\.'],
            'rust':       [r'fn\s+main', r'let\s+mut', r'println!'],
        }
        scores = {lang: 0 for lang in patterns}
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                if re.search(pattern, code):
                    scores[lang] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else 'python'