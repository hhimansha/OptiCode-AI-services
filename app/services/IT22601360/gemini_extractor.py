"""
Gemini Extractor — IT22601360

429 fix: Daily quota exhaustion is now written to a temp file so it
persists across server restarts. Previously the in-memory counter reset
to 0 on every uvicorn reload, so the rate limiter thought it had budget
when Google's quota was already exhausted.

New: supports extraction_mode param ('hybrid' | 'llm_only') for the
frontend research comparison toggle.
"""

import os
import json
import re
import time as _time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Persistent quota state ─────────────────────────────────────────────────────
# Written to a temp file so daily exhaustion survives server restarts.
_QUOTA_STATE_FILE = os.path.join(os.path.dirname(__file__), ".gemini_quota_state.json")


def _load_quota_state() -> dict:
    try:
        with open(_QUOTA_STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_quota_state(state: dict):
    try:
        with open(_QUOTA_STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


@dataclass
class ExtractedConcept:
    name: str
    category: str
    description: str
    confidence: float
    evidence: str
    related_concepts: List[str]
    code_snippet: Optional[str] = None
    line_numbers: Optional[List[int]] = None
    source: Optional[str] = None  # 'gemini' | 'ast_analysis' | 'rule_based' | 'hybrid'


class GeminiExtractor:
    _rate_limit_lock = asyncio.Lock()

    REQUESTS_PER_MINUTE = 5
    REQUESTS_PER_DAY = 50
    MIN_REQUEST_INTERVAL = 2.0

    def __init__(self, api_key: Optional[str] = None, use_codebert: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env")

        self.base_url  = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model_name = "gemini-3.1-flash-lite-preview"

        self.use_paid_tier = os.getenv("GEMINI_USE_PAID_TIER", "false").lower() == "true"
        if self.use_paid_tier:
            self.REQUESTS_PER_MINUTE = 60
            self.REQUESTS_PER_DAY    = 10000
            print(f"✅ Gemini Extractor initialized with {self.model_name} (PAID TIER)")
        else:
            print(f"✅ Gemini Extractor initialized with {self.model_name} (FREE TIER)")
            print("💡 Tip: Add GEMINI_USE_PAID_TIER=true to .env for higher limits")

        print(f"⏱️  Rate limits: {self.REQUESTS_PER_MINUTE} RPM, {self.REQUESTS_PER_DAY} RPD")

        # Load persisted state — survives uvicorn --reload
        state = _load_quota_state()
        now   = datetime.now()

        # Per-minute window (short-lived, don't persist)
        self._request_count_minute = 0
        self._minute_reset_time    = now + timedelta(minutes=1)

        # Per-day window — restore from disk
        day_reset_str = state.get("day_reset_time")
        if day_reset_str:
            try:
                day_reset = datetime.fromisoformat(day_reset_str)
                if now < day_reset:
                    self._request_count_day = state.get("request_count_day", 0)
                    self._day_reset_time    = day_reset
                    if self._request_count_day >= self.REQUESTS_PER_DAY:
                        remaining = (day_reset - now).total_seconds() / 3600
                        print(f"⚠️  Daily quota already exhausted (restored from disk). "
                              f"Resets in {remaining:.1f}h. Using AST fallback.")
                else:
                    # New day
                    self._request_count_day = 0
                    self._day_reset_time    = now + timedelta(days=1)
            except Exception:
                self._request_count_day = 0
                self._day_reset_time    = now + timedelta(days=1)
        else:
            self._request_count_day = 0
            self._day_reset_time    = now + timedelta(days=1)

        self._last_request_time = None

    # ── Rate limiting ──────────────────────────────────────────────────────────

    async def _wait_for_rate_limit(self):
        async with self._rate_limit_lock:
            now = datetime.now()

            # Reset minute window
            if now >= self._minute_reset_time:
                self._request_count_minute = 0
                self._minute_reset_time    = now + timedelta(minutes=1)

            # Reset day window
            if now >= self._day_reset_time:
                self._request_count_day = 0
                self._day_reset_time    = now + timedelta(days=1)
                _save_quota_state({
                    "request_count_day": 0,
                    "day_reset_time": self._day_reset_time.isoformat(),
                })

            # Daily hard stop
            if self._request_count_day >= self.REQUESTS_PER_DAY:
                remaining = (self._day_reset_time - now).total_seconds() / 3600
                raise Exception(
                    f"Daily quota exhausted ({self.REQUESTS_PER_DAY} RPD). "
                    f"Resets in {remaining:.1f}h."
                )

            # Per-minute throttle
            if self._request_count_minute >= self.REQUESTS_PER_MINUTE:
                wait = (self._minute_reset_time - now).total_seconds()
                print(f"⏳ Rate limit reached. Waiting {wait:.1f}s...")
                await asyncio.sleep(wait + 0.5)
                self._request_count_minute = 0
                self._minute_reset_time    = datetime.now() + timedelta(minutes=1)

            # Minimum interval between calls
            if self._last_request_time:
                elapsed = (now - self._last_request_time).total_seconds()
                if elapsed < self.MIN_REQUEST_INTERVAL:
                    await asyncio.sleep(self.MIN_REQUEST_INTERVAL - elapsed)

            self._request_count_minute += 1
            self._request_count_day    += 1
            self._last_request_time     = datetime.now()

            # Persist day counter
            _save_quota_state({
                "request_count_day": self._request_count_day,
                "day_reset_time":    self._day_reset_time.isoformat(),
            })

            print(
                f"📊 API calls: {self._request_count_minute}/{self.REQUESTS_PER_MINUTE}"
                f" this minute, {self._request_count_day}/{self.REQUESTS_PER_DAY} today"
            )

    def _mark_daily_quota_exhausted(self):
        """Call when the API itself returns 429 — marks quota as exhausted on disk."""
        self._request_count_day = self.REQUESTS_PER_DAY
        _save_quota_state({
            "request_count_day": self.REQUESTS_PER_DAY,
            "day_reset_time":    self._day_reset_time.isoformat(),
        })
        print("💡 Daily quota exhausted — saved to disk. AST fallback will be used until reset.")

    # ── Core API call ──────────────────────────────────────────────────────────

    async def _call_gemini_api(self, prompt: str, max_tokens: int = 4096) -> str:
        try:
            await self._wait_for_rate_limit()
        except Exception as e:
            print(f"⚠️  Rate limit: {e}")
            return ""

        url     = f"{self.base_url}/{self.model_name}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature":    0.1,
                "topP":           0.8,
                "topK":           40,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        parts  = (result.get("candidates", [{}])[0]
                                  .get("content", {}).get("parts", []))
                        return parts[0].get("text", "") if parts else ""

                    elif resp.status == 429:
                        print("❌ Rate limit exceeded (429)")
                        print("💡 Tip: You've hit your API quota. Using intelligent fallback.")
                        self._mark_daily_quota_exhausted()
                        return ""

                    elif resp.status == 404:
                        return await self._try_alternative_models(prompt)

                    else:
                        err = await resp.text()
                        print(f"❌ HTTP {resp.status}: {err[:200]}")
                        return ""

        except asyncio.TimeoutError:
            print("❌ Timeout")
            return ""
        except Exception as e:
            print(f"❌ API error: {e}")
            return ""

    async def _try_alternative_models(self, prompt: str) -> str:
        for api_version, model in [
            ("v1beta", "gemini-1.5-flash-002"),
            ("v1beta", "gemini-1.5-flash"),
        ]:
            try:
                url = (f"https://generativelanguage.googleapis.com/"
                       f"{api_version}/models/{model}:generateContent")
                headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
                }
                async with aiohttp.ClientSession() as s:
                    async with s.post(url, headers=headers, json=data,
                                      timeout=aiohttp.ClientTimeout(total=60)) as r:
                        if r.status == 200:
                            result = await r.json()
                            parts  = (result.get("candidates", [{}])[0]
                                      .get("content", {}).get("parts", []))
                            if parts:
                                self.model_name = model
                                self.base_url = (
                                    f"https://generativelanguage.googleapis.com/{api_version}/models"
                                )
                                print(f"✅ Switched to {model}")
                                return parts[0].get("text", "")
            except Exception:
                pass
        return ""

    # ── BATCH PROJECT EXTRACTION ───────────────────────────────────────────────

    async def batch_extract_project(
        self,
        files: List[Dict[str, Any]],
        extraction_mode: str = "hybrid",  # 'hybrid' | 'llm_only'
    ) -> Dict[str, List[ExtractedConcept]]:
        """
        Extract concepts from ALL files in ONE Gemini API call.
        extraction_mode:
          'hybrid'   — includes AST structural metadata in the prompt (default)
          'llm_only' — sends raw code only, no AST context
        """
        if not files:
            return {}

        print(f"🚀 Batch extracting {len(files)} files (mode={extraction_mode})")

        max_chars = max(600, 10000 // len(files))
        file_blocks = []

        for f in files:
            code_excerpt = f["code"][:max_chars]
            if len(f["code"]) > max_chars:
                code_excerpt += f"\n# ... [truncated]"

            if extraction_mode == "hybrid":
                # Include AST-derived metadata — this is the key differentiator
                summary   = f.get("structural_summary", {})
                structure = summary.get("structure", {})
                funcs     = structure.get("functions", [])[:5]
                clses     = structure.get("classes",   [])[:3]
                meta_parts = []
                if funcs: meta_parts.append(f"functions: {', '.join(funcs)}")
                if clses: meta_parts.append(f"classes: {', '.join(clses)}")
                meta_line = ("# AST metadata: " + " | ".join(meta_parts) + "\n") if meta_parts else ""
            else:
                meta_line = ""   # LLM-only: no structural hints

            file_blocks.append(
                f"### FILE: {f['filename']} ({f['language']})\n"
                f"{meta_line}"
                f"```{f['language']}\n{code_excerpt}\n```"
            )

        files_section = "\n\n".join(file_blocks)

        prompt = f"""You are a precise computer science educator analyzing a software project.

## TASK
Analyze these {len(files)} source files and extract ALL theoretical CS concepts present.
Only extract concepts CLEARLY evidenced in the code.

## FILES
{files_section}

## RULES
- name: specific concept (e.g. "Binary Search", "Singleton Pattern", "Recursion")
- category: exactly one of: data_structure | algorithm | design_pattern | architecture | paradigm | programming_concept
- description: HOW this specific code implements it (1-2 sentences, concrete)
- confidence: 0.0-1.0 (>0.8 only if unambiguous)
- evidence: copy 1-3 EXACT verbatim lines from the code
- filename: exact filename as listed above
- Do NOT extract generic concepts like "variables" or "functions"
- Recursion: only if a function literally calls itself by name

Return ONLY valid JSON, no markdown fences:
{{
  "project_concepts": [
    {{
      "filename": "exact filename",
      "name": "concept name",
      "category": "category",
      "description": "specific description",
      "confidence": 0.0,
      "evidence": "exact copied code lines",
      "related_concepts": ["name1"]
    }}
  ],
  "project_summary": "2-3 sentence description of this project"
}}"""

        try:
            print("🤖 Calling Gemini API (batch)...")
            response_text = await self._call_gemini_api(prompt, max_tokens=6000)

            if response_text:
                print(f"✅ Batch response ({len(response_text)} chars)")
                return self._parse_batch_response(response_text, files)
            else:
                print("⚠️  Batch Gemini call failed — AST fallback")
                return self._ast_fallback_all_files(files)

        except Exception as e:
            print(f"❌ Batch error: {e}")
            return self._ast_fallback_all_files(files)

    def _parse_batch_response(
        self, response_text: str, files: List[Dict]
    ) -> Dict[str, List[ExtractedConcept]]:
        result       = {f["filename"]: [] for f in files}
        all_filenames = list(result.keys())

        try:
            cleaned = response_text.strip()
            if "```" in cleaned:
                m       = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
                cleaned = m.group(1).strip() if m else cleaned

            data     = json.loads(cleaned)
            concepts = data.get("project_concepts", [])

            for c in concepts:
                raw_fname  = c.get("filename", "")
                matched_key = raw_fname if raw_fname in result else None

                if not matched_key:
                    for key in all_filenames:
                        if (raw_fname in key or key.endswith(raw_fname) or
                                raw_fname.endswith(key.split("/")[-1].split("\\")[-1])):
                            matched_key = key
                            break
                    if not matched_key:
                        matched_key = all_filenames[0]

                if matched_key not in result:
                    result[matched_key] = []

                result[matched_key].append(ExtractedConcept(
                    name=str(c.get("name", "")).strip(),
                    category=self._normalize_category(c.get("category", "programming_concept")),
                    description=str(c.get("description", "")).strip(),
                    confidence=min(1.0, max(0.0, float(c.get("confidence", 0.7)))),
                    evidence=str(c.get("evidence", "")).strip(),
                    related_concepts=[str(r).strip() for r in c.get("related_concepts", [])
                                      if isinstance(r, str)],
                    source="gemini",
                ))

            total = sum(len(v) for v in result.values())
            print(f"✅ Parsed {total} concepts across {len(files)} files")

        except Exception as e:
            print(f"❌ Batch parse error: {e}\n   Preview: {response_text[:300]}")
            return self._ast_fallback_all_files(files)

        return result

    @staticmethod
    def _normalize_category(cat: str) -> str:
        cat   = str(cat).lower().strip().replace(" ", "_").replace("-", "_")
        valid = {"data_structure", "algorithm", "design_pattern",
                 "architecture", "paradigm", "programming_concept"}
        aliases = {
            "data_structures": "data_structure", "algorithms": "algorithm",
            "design_patterns": "design_pattern", "architectures": "architecture",
            "paradigms": "paradigm", "programming_concepts": "programming_concept",
            "pattern": "design_pattern", "concept": "programming_concept",
        }
        return aliases.get(cat, cat) if cat not in valid else cat

    def _ast_fallback_all_files(self, files: List[Dict]) -> Dict[str, List[ExtractedConcept]]:
        return {
            f["filename"]: self._get_intelligent_fallback(
                f["code"], f["language"], f.get("pre_detected_patterns", {})
            )
            for f in files
        }

    # ── Single-file extraction (paste mode) ───────────────────────────────────

    async def extract_concepts(
        self,
        code: str,
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]],
        extraction_mode: str = "hybrid",
    ) -> List[ExtractedConcept]:
        print(f"🎯 Extracting concepts from {language} code (mode={extraction_mode})")

        if extraction_mode == "llm_only":
            prompt = self._build_llm_only_prompt(code, language)
        else:
            prompt = self._build_hybrid_prompt(code, language, structural_summary, pre_detected_patterns)

        try:
            print("🤖 Calling Gemini API...")
            response_text = await self._call_gemini_api(prompt)

            if response_text:
                concepts = self._parse_single_response(response_text)
                if concepts:
                    if extraction_mode == "hybrid":
                        concepts = self._merge_with_ast(concepts, pre_detected_patterns)
                    for c in concepts:
                        if not c.source:
                            c.source = "gemini"
                    return concepts

            print("⚠️  Using intelligent fallback")
            if extraction_mode == "llm_only":
                return []  # LLM-only genuinely has no result
            return self._get_intelligent_fallback(code, language, pre_detected_patterns)

        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return self._get_intelligent_fallback(code, language, pre_detected_patterns)

    def _build_llm_only_prompt(self, code: str, language: str) -> str:
        """Minimal prompt — no AST context. This is the research baseline."""
        return f"""List the computer science concepts in this {language} code.

```{language}
{code[:6000]}
```

Return ONLY valid JSON:
{{
  "concepts": [
    {{
      "name": "concept name",
      "category": "data_structure|algorithm|design_pattern|architecture|paradigm|programming_concept",
      "description": "how it appears in this code",
      "confidence": 0.0,
      "evidence": "exact code lines",
      "related_concepts": []
    }}
  ]
}}"""

    def _build_hybrid_prompt(
        self, code: str, language: str,
        structural_summary: Dict, pre_detected_patterns: Dict[str, List[str]]
    ) -> str:
        structure  = structural_summary.get("structure", {})
        funcs      = ", ".join(structure.get("functions", [])[:8]) or "none"
        clses      = ", ".join(structure.get("classes",   [])[:5]) or "none"
        pre_str    = ""
        for cat, patterns in pre_detected_patterns.items():
            if patterns:
                pre_str += f"  - {cat.replace('_',' ').title()}: {', '.join(patterns)}\n"

        return f"""You are an expert CS educator extracting theoretical concepts from code.

## CODE ({language})
```{language}
{code[:6000]}
```

## STRUCTURAL FACTS (from AST — ground truth)
- Functions: {funcs}
- Classes:   {clses}
- Pre-detected patterns:
{pre_str or "  none"}

Return ONLY valid JSON:
{{
  "concepts": [
    {{
      "name": "string",
      "category": "data_structure|algorithm|design_pattern|architecture|paradigm|programming_concept",
      "description": "specific to this code",
      "confidence": 0.0,
      "evidence": "exact verbatim code lines",
      "related_concepts": []
    }}
  ]
}}"""

    def _parse_single_response(self, response_text: str) -> List[ExtractedConcept]:
        if not response_text:
            return []
        try:
            cleaned = response_text.strip()
            if "```" in cleaned:
                m       = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned, re.DOTALL)
                cleaned = m.group(1).strip() if m else cleaned
            data     = json.loads(cleaned)
            raw_list = data.get("concepts", [])
            if not raw_list and isinstance(data, list):
                raw_list = data
            return [
                ExtractedConcept(
                    name=str(c["name"]).strip(),
                    category=self._normalize_category(c.get("category", "programming_concept")),
                    description=str(c.get("description", "")).strip(),
                    confidence=min(1.0, max(0.0, float(c.get("confidence", 0.7)))),
                    evidence=str(c.get("evidence", "")).strip(),
                    related_concepts=[str(r).strip() for r in c.get("related_concepts", [])
                                      if isinstance(r, str)],
                )
                for c in raw_list if isinstance(c, dict) and c.get("name")
            ]
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return []

    # ── Intelligent fallback ───────────────────────────────────────────────────

    def _get_intelligent_fallback(
        self, code: str, language: str, pre_detected_patterns: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        print("🔄 Using intelligent fallback with AST analysis")
        concepts: List[ExtractedConcept] = []
        cat_map = {
            "data_structures":      "data_structure",
            "algorithms":           "algorithm",
            "design_patterns":      "design_pattern",
            "architectures":        "architecture",
            "paradigms":            "paradigm",
            "programming_concepts": "programming_concept",
        }

        if language == "python":
            try:
                from app.services.IT22601360.ast_analyzer import ASTAnalyzer
                analysis     = ASTAnalyzer.analyze_python(code)
                ast_concepts = ASTAnalyzer.convert_to_concepts(analysis)

                for category, names in ast_concepts.items():
                    for name in names:
                        concepts.append(ExtractedConcept(
                            name=name.replace("_", " ").title(),
                            category=cat_map.get(category, "programming_concept"),
                            description=f"Detected via AST: {name}",
                            confidence=0.75,
                            evidence=_build_ast_evidence(name, analysis),
                            related_concepts=[],
                            source="ast_analysis",
                        ))
                # Boost recursion confidence — AST is definitive
                for c in concepts:
                    if "recursion" in c.name.lower() and analysis.recursive_functions:
                        c.confidence = 0.92
                        c.evidence = f"{analysis.recursive_functions[0]} calls itself recursively"

            except Exception as e:
                print(f"⚠️  AST fallback error: {e}")

        existing = {c.name.lower() for c in concepts}
        for category, patterns in pre_detected_patterns.items():
            for pattern in patterns:
                display = pattern.replace("_", " ").title()
                if display.lower() not in existing:
                    concepts.append(ExtractedConcept(
                        name=display,
                        category=cat_map.get(category, "programming_concept"),
                        description=f"Pattern detected: {pattern.replace('_', ' ')}",
                        confidence=0.60,
                        evidence=f"Pattern matched: {pattern}",
                        related_concepts=[],
                        source="rule_based",
                    ))
        return concepts

    def _merge_with_ast(
        self, llm_concepts: List[ExtractedConcept],
        pre_detected: Dict[str, List[str]]
    ) -> List[ExtractedConcept]:
        cat_map = {
            "data_structures":      "data_structure",
            "algorithms":           "algorithm",
            "design_patterns":      "design_pattern",
            "architectures":        "architecture",
            "paradigms":            "paradigm",
            "programming_concepts": "programming_concept",
        }
        for category, patterns in pre_detected.items():
            for pattern in patterns:
                norm_p = pattern.lower().replace("_", " ")
                matched = False
                for c in llm_concepts:
                    norm_n = c.name.lower().replace("_", " ")
                    if norm_p in norm_n or norm_n in norm_p:
                        c.confidence = min(1.0, c.confidence + 0.10)
                        c.source     = "hybrid"
                        matched      = True
                        break
                if not matched:
                    llm_concepts.append(ExtractedConcept(
                        name=pattern.replace("_", " ").title(),
                        category=cat_map.get(category, "programming_concept"),
                        description=f"AST/rule detection: {pattern.replace('_', ' ')}",
                        confidence=0.60,
                        evidence=f"Pattern matched: {pattern}",
                        related_concepts=[],
                        source="rule_based",
                    ))
        return llm_concepts

    # ── Concept explanation ────────────────────────────────────────────────────

    async def get_concept_explanation(
        self, concept_name: str, code_context: str, detail_level: str = "intermediate"
    ) -> Dict:
        prompt = f"""Explain "{concept_name}" as used in this code:
```
{code_context[:2000]}
```
Return ONLY valid JSON:
{{
  "concept_name": "{concept_name}",
  "definition": "clear definition",
  "how_used_in_code": "specific to this code",
  "time_complexity": "e.g. O(log n) or N/A",
  "space_complexity": "e.g. O(1) or N/A",
  "related_concepts": [],
  "real_world_examples": []
}}"""
        try:
            text = await self._call_gemini_api(prompt, max_tokens=1000)
            if not text:
                return self._fallback_explanation(concept_name)
            cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned)
            return json.loads(cleaned)
        except Exception:
            return self._fallback_explanation(concept_name)

    @staticmethod
    def _fallback_explanation(name: str) -> Dict:
        return {
            "concept_name": name,
            "definition": f"{name} is a fundamental CS concept.",
            "how_used_in_code": "Implementation detected in the provided code.",
            "time_complexity": "Varies", "space_complexity": "Varies",
            "related_concepts": [], "real_world_examples": [],
        }


def _build_ast_evidence(concept_name: str, analysis) -> str:
    n = concept_name.lower().replace("_", " ")
    if "recursion" in n and analysis.recursive_functions:
        return f"{analysis.recursive_functions[0]} calls itself recursively"
    if n in ("oop", "object oriented programming") and analysis.classes:
        return f"class {analysis.classes[0]}:"
    if "inheritance" in n and analysis.inheritance_chains:
        cls, bases = next(iter(analysis.inheritance_chains.items()))
        return f"class {cls}({', '.join(bases)}):"
    if "singleton" in n:
        return "_instance = None  # Singleton class variable"
    if "decorator" in n and analysis.decorators:
        return f"@{analysis.decorators[0]}"
    if "iteration" in n:
        return f"Loop detected ({analysis.control_flow.get('loops', 0)} loop(s))"
    if analysis.classes:
        return f"class {analysis.classes[0]}:"
    if analysis.functions:
        return f"def {analysis.functions[0]}(...):"
    return f"Pattern detected: {concept_name}"