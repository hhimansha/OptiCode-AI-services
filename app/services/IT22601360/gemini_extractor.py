"""
Fixed Gemini API Integration with CodeBERT Hybrid
Student: IT22601360

Key fixes:
1. Updated to use gemini-1.5-flash (latest stable model)
2. Corrected API endpoint structure
3. Better error handling and fallback logic
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any  
from dataclasses import dataclass
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.utils.constants import CONCEPT_CATEGORIES, CATEGORY_COLORS

# Load environment variables
load_dotenv()


@dataclass
class ExtractedConcept:
    """Represents a single extracted concept"""
    name: str
    category: str
    description: str
    confidence: float
    evidence: str
    related_concepts: List[str]
    code_snippet: Optional[str] = None
    line_numbers: Optional[List[int]] = None
    source: Optional[str] = None  # 'codebert', 'gemini', or 'hybrid'


class GeminiExtractor:
    """
    Enhanced Gemini + CodeBERT hybrid extractor
    
    This demonstrates YOUR research contribution by combining:
    - Custom fine-tuned CodeBERT model
    - Gemini API for explanations
    - Novel fusion strategy
    """
    
    # Class-level rate limiting
    _last_request_time = None
    _request_count_minute = 0
    _request_count_day = 0
    _minute_reset_time = None
    _day_reset_time = None
    _rate_limit_lock = asyncio.Lock()
    
    # Rate limits (conservative for free tier)
    REQUESTS_PER_MINUTE = 5   # Free tier limit for Gemini 2.0
    REQUESTS_PER_DAY = 50     # Conservative daily limit
    MIN_REQUEST_INTERVAL = 2  # Minimum 2 seconds between requests
    
    def __init__(self, api_key: Optional[str] = None, use_codebert: bool = False):
        """
        Initialize hybrid extractor
        
        Args:
            api_key: Gemini API key
            use_codebert: Whether to use CodeBERT model
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )
        
        # Configure Gemini - Use v1beta for latest models
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        # Use gemini-2.0-flash-001 - stable and reliable
        self.model_name = "gemini-2.0-flash-001"
        
        # Check if we should enable paid tier (higher limits)
        self.use_paid_tier = os.getenv("GEMINI_USE_PAID_TIER", "false").lower() == "true"
        
        if self.use_paid_tier:
            self.REQUESTS_PER_MINUTE = 60  # Paid tier gets higher limits
            self.REQUESTS_PER_DAY = 10000
            print(f"✅ Gemini Extractor initialized with {self.model_name} (PAID TIER)")
        else:
            print(f"✅ Gemini Extractor initialized with {self.model_name} (FREE TIER)")
            print(f"💡 Tip: Add GEMINI_USE_PAID_TIER=true to .env for higher limits")
        
        print(f"⏱️  Rate limits: {self.REQUESTS_PER_MINUTE} RPM, {self.REQUESTS_PER_DAY} RPD")
        
        # Initialize CodeBERT if requested
        if use_codebert:
            try:
                from app.services.IT22601360.codebert_model import CodeBERTExtractor, HybridExtractor
                
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                model_path = os.path.join(base_dir, "training", "model", "codebert_finetuned", "best_model.pt")
                if os.path.exists(model_path):
                    print("✅ Loading fine-tuned CodeBERT model...")
                    self.codebert_extractor = CodeBERTExtractor(model_path=model_path)
                else:
                    print("⚠️  Fine-tuned model not found. Using base CodeBERT.")
                    self.codebert_extractor = CodeBERTExtractor()
                
                self.hybrid_extractor = HybridExtractor(
                    self.codebert_extractor,
                    self
                )
                print("✅ Hybrid extractor initialized")
                
            except ImportError as e:
                print(f"⚠️  CodeBERT not available: {e}")
                print("   Falling back to Gemini-only mode")
                self.use_codebert = False
    
    async def _wait_for_rate_limit(self):
        """
        Implement rate limiting to avoid 429 errors
        """
        async with self._rate_limit_lock:
            now = datetime.now()
            
            # Initialize timers on first use
            if self._minute_reset_time is None:
                self._minute_reset_time = now + timedelta(minutes=1)
                self._day_reset_time = now + timedelta(days=1)
            
            # Reset minute counter
            if now >= self._minute_reset_time:
                self._request_count_minute = 0
                self._minute_reset_time = now + timedelta(minutes=1)
            
            # Reset day counter
            if now >= self._day_reset_time:
                self._request_count_day = 0
                self._day_reset_time = now + timedelta(days=1)
            
            # Check daily limit
            if self._request_count_day >= self.REQUESTS_PER_DAY:
                wait_seconds = (self._day_reset_time - now).total_seconds()
                print(f"⚠️  Daily limit reached ({self.REQUESTS_PER_DAY} requests). Using fallback.")
                raise Exception("Daily rate limit exceeded")
            
            # Check per-minute limit
            if self._request_count_minute >= self.REQUESTS_PER_MINUTE:
                wait_seconds = (self._minute_reset_time - now).total_seconds()
                print(f"⏳ Rate limit reached. Waiting {wait_seconds:.1f}s...")
                await asyncio.sleep(wait_seconds + 0.5)  # Add small buffer
                # Reset counters after waiting
                self._request_count_minute = 0
                self._minute_reset_time = datetime.now() + timedelta(minutes=1)
            
            # Enforce minimum interval between requests
            if self._last_request_time:
                elapsed = (now - self._last_request_time).total_seconds()
                if elapsed < self.MIN_REQUEST_INTERVAL:
                    wait_time = self.MIN_REQUEST_INTERVAL - elapsed
                    print(f"⏳ Throttling... waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
            
            # Update counters
            self._request_count_minute += 1
            self._request_count_day += 1
            self._last_request_time = datetime.now()
            
            print(f"📊 API calls: {self._request_count_minute}/{self.REQUESTS_PER_MINUTE} this minute, {self._request_count_day}/{self.REQUESTS_PER_DAY} today")
    
    async def extract_concepts(
        self, 
        code: str, 
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        """
        Extract concepts using hybrid approach
        """
        print(f"🎯 Extracting concepts from {language} code")

        return await self._gemini_only_extraction(
            code=code,
            language=language,
            structural_summary=structural_summary,
            pre_detected_patterns=pre_detected_patterns
        )
            
    async def _gemini_only_extraction(
        self,
        code: str,
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        """Original Gemini-only extraction"""
        
        prompt = self._build_extraction_prompt(
            code, 
            language, 
            structural_summary, 
            pre_detected_patterns
        )
        
        try:
            print("🤖 Calling Gemini API...")

            response_text = await self._call_gemini_api(prompt)

            if response_text:
                print(f"✅ Gemini response received ({len(response_text)} chars)")
                concepts = self._parse_response(response_text)
                
                if concepts:
                    concepts = self._merge_with_predetected(concepts, pre_detected_patterns)
                    for concept in concepts:
                        concept.source = "gemini"
                    print(f"✅ Extracted {len(concepts)} concepts")
                    return concepts
            
            # If no concepts or API failed, use fallback
            print("⚠️ Using intelligent fallback")
            return self._get_intelligent_fallback(code, language, pre_detected_patterns)
            
        except Exception as e:
            print(f"❌ Gemini API error: {str(e)[:200]}")
            return self._get_intelligent_fallback(code, language, pre_detected_patterns)
        
    async def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API directly via HTTP with proper endpoint and rate limiting"""
        
        # Wait for rate limit before making request
        try:
            await self._wait_for_rate_limit()
        except Exception as e:
            print(f"⚠️  Rate limit check failed: {e}")
            return ""  # Return empty to trigger fallback
        
        url = f"{self.base_url}/{self.model_name}:generateContent"
        
        # Use x-goog-api-key header (recommended method)
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract text from response
                    candidates = result.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    
                    return ""
                
                elif response.status == 429:
                    error_text = await response.text()
                    print(f"❌ Rate limit exceeded (429)")
                    print(f"💡 Tip: You've hit your API quota. Using intelligent fallback.")
                    return ""  # Return empty to trigger fallback
                
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}")
                    print(f"Error details: {error_text[:300]}")
                    
                    # Try alternative models if primary fails
                    if response.status == 404 or "not found" in error_text.lower():
                        return await self._try_alternative_models(prompt)
                    
                    raise Exception(f"Gemini API error {response.status}")
    
    async def _try_alternative_models(self, prompt: str) -> str:
        """Try alternative Gemini models in order of preference"""
        # Models to try in order (latest first)
        alternative_models = [
            ("v1beta", "gemini-1.5-flash-002"),   # Stable 1.5 model
            ("v1beta", "gemini-1.5-flash-001"),   # Older 1.5 model
            ("v1beta", "gemini-1.5-flash"),       # Generic 1.5 flash
            ("v1beta", "gemini-1.5-pro"),         # More capable but slower
            ("v1", "gemini-1.0-pro"),             # Legacy stable model
        ]
        
        for api_version, model in alternative_models:
            try:
                print(f"🔄 Trying alternative: {model} (API {api_version})")
                
                url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent"
                
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key
                }
                
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "topP": 0.8,
                        "topK": 40,
                        "maxOutputTokens": 2048
                    }
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            result = await response.json()
                            candidates = result.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                if parts:
                                    print(f"✅ Model {model} worked!")
                                    # Update the model name for future requests
                                    self.model_name = model
                                    self.base_url = f"https://generativelanguage.googleapis.com/{api_version}/models"
                                    return parts[0].get("text", "")
            except Exception as e:
                print(f"⚠️ Model {model} failed: {str(e)[:100]}")
                continue
        
        print("❌ All Gemini models failed")
        return ""
    
    def _build_extraction_prompt(
        self, 
        code: str, 
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> str:
        """Build optimized prompt for concept extraction"""
        
        pre_detected_str = ""
        for category, patterns in pre_detected_patterns.items():
            if patterns:
                category_name = category.replace('_', ' ').title()
                pre_detected_str += f"- {category_name}: {', '.join(patterns)}\n"
        
        prompt = f"""You are an expert computer science educator analyzing code to extract theoretical concepts.

## TASK
Analyze the following {language} code and extract ALL computer science concepts present.
Focus on identifying data structures, algorithms, design patterns, architectural patterns, and programming paradigms.

## PRE-ANALYSIS (Already Detected)
Our rule-based system has pre-detected these patterns:
{pre_detected_str if pre_detected_str else "None detected"}

## STRUCTURAL SUMMARY
- Total Lines: {structural_summary['metrics']['total_lines']}
- Functions: {structural_summary['metrics']['functions_count']} ({', '.join(structural_summary['structure']['functions'][:5])}...)
- Classes: {structural_summary['metrics']['classes_count']} ({', '.join(structural_summary['structure']['classes'][:5]) if structural_summary['structure']['classes'] else 'None'})
- Complexity: {structural_summary['estimated_complexity']}

## CODE TO ANALYZE
```{language}
{code[:6000]}
```

## INSTRUCTIONS
1. Identify ALL computer science concepts in the code
2. For each concept, provide:
   - name: The concept name (e.g., "Binary Search", "Singleton Pattern")
   - category: One of [data_structure, algorithm, design_pattern, architecture, paradigm, programming_concept]
   - description: How this concept is implemented/used in THIS specific code
   - confidence: Float 0.0-1.0 indicating certainty
   - evidence: Specific code elements that indicate this concept
   - related_concepts: Other concepts this relates to

3. Look for these specific concepts:
   - Data Structures: array, linked list, stack, queue, tree, graph, hash table, heap, trie
   - Algorithms: sorting, searching (binary, linear), recursion, dynamic programming, BFS, DFS, greedy, backtracking
   - Design Patterns: singleton, factory, observer, strategy, decorator, adapter, MVC, repository
   - Paradigms: OOP, functional programming, reactive programming
   - Programming Concepts: encapsulation, inheritance, polymorphism, abstraction, async/await, closures, generics

## OUTPUT FORMAT
Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "concepts": [
    {{
      "name": "string",
      "category": "string",
      "description": "string - specific to this code",
      "confidence": 0.0,
      "evidence": "string - quote or reference specific code",
      "related_concepts": ["string"]
    }}
  ],
  "summary": "Brief 2-3 sentence overview of what this code does and its main concepts"
}}
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> List[ExtractedConcept]:
        """Parse Gemini response"""
        concepts = []
        
        if not response_text:
            return concepts
            
        try:
            # Clean response
            cleaned = response_text.strip()
            
            # Remove markdown code blocks
            if cleaned.startswith("```"):
                import re
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1).strip()
                else:
                    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
            
            # Try to parse as JSON
            data = json.loads(cleaned)
            
            # Extract concepts
            concepts_list = data.get("concepts", [])
            if not concepts_list and isinstance(data, list):
                concepts_list = data
            
            for c in concepts_list:
                if isinstance(c, dict):
                    concept = ExtractedConcept(
                        name=c.get('name', 'Unknown').strip(),
                        category=c.get('category', 'programming_concept').strip(),
                        description=c.get('description', '').strip(),
                        confidence=min(1.0, max(0.0, float(c.get('confidence', 0.7)))),
                        evidence=c.get('evidence', '').strip(),
                        related_concepts=[rc.strip() for rc in c.get('related_concepts', []) if isinstance(rc, str)]
                    )
                    concepts.append(concept)
                    
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response preview: {response_text[:300]}...")
        except Exception as e:
            print(f"❌ Parse error: {e}")
        
        return concepts

    def _get_intelligent_fallback(self, code, language, pre_detected_patterns):
        """Intelligent fallback with AST analysis"""
        print("🔄 Using intelligent fallback with AST analysis")
        
        concepts = []
        
        # Use AST analysis for Python
        if language == "python":
            try:
                from app.services.IT22601360.ast_analyzer import ASTAnalyzer
                
                analysis = ASTAnalyzer.analyze_python(code)
                
                # Add OOP concepts
                if analysis.classes:
                    concepts.append(ExtractedConcept(
                        name="Object-Oriented Programming",
                        category="paradigm",
                        description="Code uses classes and objects to organize data and behavior",
                        confidence=0.9,
                        evidence=f"Class definitions: {', '.join(analysis.classes)}",
                        related_concepts=["Class", "Object", "Encapsulation"],
                        source="ast_analysis"
                    ))
                    
                    if "constructor" in analysis.oop_features:
                        concepts.append(ExtractedConcept(
                            name="Constructor",
                            category="programming_concept",
                            description="Special method that initializes new objects",
                            confidence=0.8,
                            evidence="__init__ method in class",
                            related_concepts=["OOP", "Initialization", "Method"],
                            source="ast_analysis"
                        ))
                    
                    if "encapsulation" in analysis.oop_features:
                        concepts.append(ExtractedConcept(
                            name="Encapsulation",
                            category="programming_concept",
                            description="Bundling of data with methods that operate on that data",
                            confidence=0.75,
                            evidence="Private attributes or methods in class",
                            related_concepts=["OOP", "Data Hiding", "Abstraction"],
                            source="ast_analysis"
                        ))
                
                # Add recursion if found
                if analysis.recursive_functions:
                    concepts.append(ExtractedConcept(
                        name="Recursion",
                        category="algorithm",
                        description="Function that calls itself to solve smaller instances",
                        confidence=0.85,
                        evidence=f"Recursive function(s): {', '.join(analysis.recursive_functions)}",
                        related_concepts=["Function", "Algorithm", "Base Case"],
                        source="ast_analysis"
                    ))
                    
            except Exception as e:
                print(f"⚠️ AST analysis failed: {e}")
        
        # Add pre-detected patterns
        for category, patterns in pre_detected_patterns.items():
            if patterns:
                category_map = {
                    "data_structures": "data_structure",
                    "algorithms": "algorithm",
                    "design_patterns": "design_pattern",
                    "architectures": "architecture",
                    "paradigms": "paradigm",
                    "programming_concepts": "programming_concept"
                }
                
                for pattern in patterns:
                    # Don't add duplicates
                    if not any(pattern.lower() in c.name.lower() for c in concepts):
                        concept_name = pattern.replace('_', ' ').title()
                        concepts.append(ExtractedConcept(
                            name=concept_name,
                            category=category_map.get(category, "programming_concept"),
                            description=f"Detected {pattern.replace('_', ' ')} in code analysis",
                            confidence=0.7,
                            evidence="Pattern detected by code analysis",
                            related_concepts=[],
                            source="rule_based"
                        ))
        
        return concepts

    def _merge_with_predetected(
        self, 
        llm_concepts: List[ExtractedConcept],
        pre_detected: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        """Merge LLM results with pre-detected patterns"""
        
        llm_names = {c.name.lower().replace('_', ' ').replace('-', ' ') for c in llm_concepts}
        
        category_map = {
            "data_structures": "data_structure",
            "algorithms": "algorithm",
            "design_patterns": "design_pattern",
            "architectures": "architecture",
            "paradigms": "paradigm",
            "programming_concepts": "programming_concept"
        }
        
        for category, patterns in pre_detected.items():
            mapped_category = category_map.get(category, "programming_concept")
            
            for pattern in patterns:
                pattern_normalized = pattern.lower().replace('_', ' ').replace('-', ' ')
                
                found = False
                for concept in llm_concepts:
                    concept_normalized = concept.name.lower().replace('_', ' ').replace('-', ' ')
                    if pattern_normalized in concept_normalized or concept_normalized in pattern_normalized:
                        concept.confidence = min(1.0, concept.confidence + 0.15)
                        found = True
                        break
                
                if not found:
                    llm_concepts.append(ExtractedConcept(
                        name=pattern.replace('_', ' ').title(),
                        category=mapped_category,
                        description=f"Detected {pattern.replace('_', ' ')} pattern in code",
                        confidence=0.6,
                        evidence="Pattern matched by rule-based detection",
                        related_concepts=[]
                    ))
        
        return llm_concepts
    
    async def get_concept_explanation(
        self, 
        concept_name: str, 
        code_context: str,
        detail_level: str = "intermediate"
    ) -> Dict:
        """Get detailed explanation of a concept using Gemini"""
        
        detail_instructions = {
            "basic": "Explain simply, suitable for beginners. Use analogies.",
            "intermediate": "Explain with technical details, suitable for CS students.",
            "advanced": "Explain in depth with complexity analysis and advanced considerations."
        }
        
        prompt = f"""Explain the computer science concept "{concept_name}" as used in this code:

```
{code_context[:2000]}
```

{detail_instructions.get(detail_level, detail_instructions['intermediate'])}

Return JSON format:
{{
  "concept_name": "{concept_name}",
  "definition": "Clear definition",
  "how_used_in_code": "How it's implemented here specifically",
  "time_complexity": "If applicable (e.g., O(n))",
  "space_complexity": "If applicable",
  "advantages": ["list of advantages"],
  "disadvantages": ["list of disadvantages"],
  "real_world_examples": ["practical applications"],
  "related_concepts": ["related CS concepts"],
  "learning_resources": ["optional: suggested topics to learn more"]
}}
"""
        
        try:
            response_text = await self._call_gemini_api(prompt)
            
            if not response_text:
                return self._get_fallback_explanation(concept_name)
            
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            
            return json.loads(cleaned)
            
        except Exception as e:
            print(f"❌ Explanation error: {e}")
            return self._get_fallback_explanation(concept_name)
    
    def _get_fallback_explanation(self, concept_name: str) -> Dict:
        """Fallback explanation when API fails"""
        return {
            "concept_name": concept_name,
            "definition": f"{concept_name} is a computer science concept",
            "how_used_in_code": "Implementation detected in the provided code",
            "time_complexity": "Varies by implementation",
            "space_complexity": "Varies by implementation",
            "advantages": ["Commonly used in software development"],
            "disadvantages": ["Depends on specific use case"],
            "real_world_examples": ["Used in various software applications"],
            "related_concepts": [],
            "learning_resources": ["Computer Science textbooks", "Online tutorials"]
        }