"""
Enhanced Extractor combining AST, CodeBERT, and Gemini
"""
from typing import List, Dict
from app.services.IT22601360.ast_analyzer import ASTAnalyzer
from app.services.IT22601360.gemini_extractor import GeminiExtractor, ExtractedConcept

class EnhancedExtractor(GeminiExtractor):
    """
    Enhanced extractor with AST analysis for better accuracy
    """
    
    async def extract_concepts(
        self, 
        code: str, 
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        """
        Extract concepts with AST-enhanced detection
        """
        print(f"🔍 Enhanced extraction for {language} code")
        
        # Enhance pre-detected patterns with AST analysis
        enhanced_patterns = self._enhance_with_ast(code, language, pre_detected_patterns)
        
        # Update structural summary
        enhanced_summary = structural_summary.copy()
        enhanced_summary["ast_enhanced"] = True
        
        # Use parent class extraction with enhanced patterns
        return await super().extract_concepts(
            code=code,
            language=language,
            structural_summary=enhanced_summary,
            pre_detected_patterns=enhanced_patterns
        )
    
    def _enhance_with_ast(
        self, 
        code: str, 
        language: str, 
        patterns: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Enhance patterns with AST analysis
        """
        enhanced = patterns.copy()
        
        if language == "python":
            try:
                analysis = ASTAnalyzer.analyze_python(code)
                ast_concepts = ASTAnalyzer.convert_to_concepts(analysis)
                
                # Merge concepts
                for category, ast_list in ast_concepts.items():
                    if ast_list:
                        if category not in enhanced:
                            enhanced[category] = []
                        
                        for concept in ast_list:
                            if concept not in enhanced[category]:
                                enhanced[category].append(concept)
                                
                        print(f"📊 AST added to {category}: {ast_list}")
                        
            except Exception as e:
                print(f"AST enhancement failed: {e}")
        
        return enhanced
    
    def _build_extraction_prompt(
        self, 
        code: str, 
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> str:
        """Build enhanced prompt with AST information"""
        
        # Get AST analysis
        ast_info = ""
        if language == "python":
            try:
                from app.services.IT22601360.ast_analyzer import ASTAnalyzer
                analysis = ASTAnalyzer.analyze_python(code)
                
                ast_info = f"""

    ## ADVANCED CODE ANALYSIS (AST-based)
    The code has been analyzed using Abstract Syntax Trees:

    **STRUCTURE:**
    - Classes: {', '.join(analysis.classes) if analysis.classes else 'None'}
    - Functions: {', '.join(analysis.functions) if analysis.functions else 'None'}
    - Recursive Functions: {', '.join(analysis.recursive_functions) if analysis.recursive_functions else 'None'}

    **OOP FEATURES DETECTED:**
    {', '.join(analysis.oop_features) if analysis.oop_features else 'No OOP features detected'}

    **DESIGN PATTERNS DETECTED:**
    {', '.join(analysis.design_patterns) if analysis.design_patterns else 'No design patterns detected'}

    **CONTROL FLOW:**
    - Loops: {analysis.control_flow.get('loops', 0)}
    - Conditionals: {analysis.control_flow.get('conditionals', 0)}
    - Try blocks: {analysis.control_flow.get('try_blocks', 0)}

    **DECORATORS USED:**
    {', '.join(analysis.decorators) if analysis.decorators else 'No decorators'}
    """
            except Exception as e:
                ast_info = f"\n## AST Analysis Error: {str(e)}\n"
        
        # Format pre-detected patterns
        pre_detected_str = ""
        for category, patterns in pre_detected_patterns.items():
            if patterns:
                category_name = category.replace('_', ' ').title()
                pre_detected_str += f"- {category_name}: {', '.join(patterns)}\n"
        
            # Escape any quotes in the code for JSON safety
            escaped_code = code.replace('"', '\\"').replace('\n', '\\n')
            
            prompt = f"""You are an expert computer science educator analyzing code to extract theoretical concepts.
    
    ## TASK
    Analyze the following {language} code and extract ALL computer science concepts present.
    Be precise and accurate - only extract concepts that are actually implemented in the code.

    {ast_info}

    ## PRE-DETECTED PATTERNS (from static analysis)
    {pre_detected_str if pre_detected_str else "No patterns pre-detected"}

    ## STRUCTURAL SUMMARY
    - Total Lines: {structural_summary['metrics']['total_lines']}
    - Functions: {structural_summary['metrics']['functions_count']}
    - Classes: {structural_summary['metrics']['classes_count']}
    - Complexity: {structural_summary['estimated_complexity']}

    ## CODE TO ANALYZE
    ```{language}
    {code[:8000]}
    """
            
            # Continue building the rest of the prompt
            return prompt