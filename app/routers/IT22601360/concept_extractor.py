"""
Code Concept Extractor API Router
Student: IT22601360

Changes from original:
  /extract-enhanced — now accepts extraction_mode ('hybrid' | 'llm_only')
  /extract-files    — now uses batch_extract_project() instead of one call
                      per file. Also accepts extraction_mode query param.
                      N files: was N API calls → now 2 total.
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import traceback

from app.services.IT22601360.preprocessor import CodePreprocessor
from app.services.IT22601360.gemini_extractor import GeminiExtractor, ExtractedConcept
from app.services.IT22601360.visualizer import VisualizationGenerator
from app.services.IT22601360.enhanced_extractor import EnhancedExtractor
from app.services.IT22601360.file_processor import FileProcessor
from app.services.IT22601360.project_aggregator import ProjectAggregator

router = APIRouter()

preprocessor       = CodePreprocessor()
visualizer         = VisualizationGenerator()
file_processor     = FileProcessor()
project_aggregator = ProjectAggregator()

try:
    gemini_extractor = GeminiExtractor()
except ValueError as e:
    print(f"⚠️ Gemini not initialized: {e}")
    gemini_extractor = None


# ── Request / Response Models ─────────────────────────────────────────────────

class CodeInput(BaseModel):
    code: str = Field(..., min_length=1)
    language: Optional[str] = Field(default="python")


class ConceptResponse(BaseModel):
    name: str
    category: str
    description: str
    confidence: float
    evidence: str
    relatedConcepts: List[str]


class ExtractionResponse(BaseModel):
    success: bool
    concepts: List[ConceptResponse]
    visualizations: Dict[str, Any]
    metrics: Dict[str, Any]
    processingTime: float


class QuickClassifyInput(BaseModel):
    code: str = Field(..., min_length=1)
    language: Optional[str] = "python"


class ConceptDetailInput(BaseModel):
    conceptName: str
    codeContext: Optional[str] = ""
    detailLevel: Optional[str] = "intermediate"


class VisualizationInput(BaseModel):
    concepts: List[Dict[str, Any]]
    type: str = Field(default="all")


class ProjectPurposeInput(BaseModel):
    filenames: List[str]
    conceptNames: List[str]
    languageDistribution: Optional[Dict[str, int]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _concept_to_dict(c: ExtractedConcept) -> Dict:
    return {
        "name": c.name,
        "category": c.category,
        "description": c.description,
        "confidence": c.confidence,
        "evidence": c.evidence,
        "relatedConcepts": c.related_concepts,
        "source": getattr(c, "source", "gemini"),
    }


def _convert_patterns_to_concepts(patterns: Dict[str, List[str]]) -> List[ExtractedConcept]:
    category_map = {
        "data_structures":      "data_structure",
        "algorithms":           "algorithm",
        "design_patterns":      "design_pattern",
        "architectures":        "architecture",
        "paradigms":            "paradigm",
        "programming_concepts": "programming_concept",
    }
    concepts = []
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            concepts.append(ExtractedConcept(
                name=pattern.replace("_", " ").title(),
                category=category_map.get(category, "programming_concept"),
                description=f"Detected {pattern.replace('_', ' ')} pattern in code",
                confidence=0.50,
                evidence="Pattern matched by rule-based detection",
                related_concepts=[],
                source="rule_based",
            ))
    return concepts


async def _generate_project_purpose(
    file_results: List[Dict],
    extractor: Optional[GeminiExtractor],
) -> str:
    filenames = [r["filename"] for r in file_results if r.get("success")]
    all_concept_names = []
    for r in file_results:
        if r.get("success"):
            for c in r.get("concepts", []):
                all_concept_names.append(c.get("name", ""))
    unique_concepts = list(dict.fromkeys(all_concept_names))[:20]

    if not extractor or not filenames:
        return _fallback_project_purpose(filenames, unique_concepts)

    prompt = (
        f"You are analyzing a software project. Write a clear 3-4 sentence description of: "
        f"(1) what this project does, (2) key technical approaches, (3) likely domain.\n\n"
        f"Files ({len(filenames)}): {', '.join(filenames[:15])}"
        + ("..." if len(filenames) > 15 else "") + "\n"
        f"CS concepts: {', '.join(unique_concepts[:20])}\n\n"
        f"Write ONLY a plain English paragraph. No JSON, no bullets."
    )

    try:
        response = await extractor._call_gemini_api(prompt, max_tokens=300)
        if response and len(response.strip()) > 20:
            return response.strip()
    except Exception as e:
        print(f"⚠️ Purpose generation failed: {e}")

    return _fallback_project_purpose(filenames, unique_concepts)


def _fallback_project_purpose(filenames: List[str], concepts: List[str]) -> str:
    domain_hints = []
    all_names = " ".join(filenames).lower()
    if any(k in all_names for k in ["api", "router", "endpoint", "controller"]):
        domain_hints.append("API or backend service")
    if any(k in all_names for k in ["model", "schema", "db", "database"]):
        domain_hints.append("data modeling")
    if any(k in all_names for k in ["test", "spec"]):
        domain_hints.append("includes test coverage")
    if any(k in all_names for k in ["ui", "component", "view", "frontend"]):
        domain_hints.append("frontend interface")
    domain_str   = f" with {', '.join(domain_hints)}" if domain_hints else ""
    concepts_str = ", ".join(concepts[:4]) if concepts else "general programming patterns"
    return (
        f"This project consists of {len(filenames)} source file(s){domain_str}. "
        f"The codebase demonstrates key CS concepts including {concepts_str}. "
        f"Analysis identified patterns reflecting structured software development practices."
    )


def _build_project_response(
    file_results: List[Dict],
    skipped_files: List[Dict],
    total_files_scanned: int,
    start_time: float,
    project_purpose: str,
) -> Dict[str, Any]:
    try:
        aggregated = project_aggregator.aggregate(file_results)
        summary    = project_aggregator.build_project_summary(
            per_file_results=file_results,
            aggregated_concepts=aggregated,
            total_files_scanned=total_files_scanned,
            total_files_skipped=len(skipped_files),
        )
        agg_dict = project_aggregator.to_response_dict(aggregated, summary)
    except Exception as e:
        print(f"⚠️ Aggregator error: {e}")
        traceback.print_exc()
        agg_dict = {
            "aggregated_concepts": [],
            "project_summary": {
                "total_files":       total_files_scanned,
                "successful_files":  len(file_results),
                "skipped_files":     len(skipped_files),
            },
        }

    agg_dict["project_summary"]["project_purpose"] = project_purpose

    return {
        "success":             True,
        "files":               file_results + skipped_files,
        "aggregated_concepts": agg_dict.get("aggregated_concepts", []),
        "project_summary":     agg_dict.get("project_summary", {}),
        "totalProcessingTime": round(time.time() - start_time, 3),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {
        "status":           "healthy",
        "component":        "Code Concept Extractor",
        "student_id":       "IT22601360",
        "gemini_available": gemini_extractor is not None,
        "batch_mode":       True,
    }


@router.post("/extract", response_model=ExtractionResponse)
async def extract_concepts(input_data: CodeInput):
    """Extract concepts from a single code snippet."""
    start_time = time.time()
    try:
        preprocessed = preprocessor.preprocess(
            code=input_data.code, language=input_data.language or "python"
        )
        if gemini_extractor:
            concepts = await gemini_extractor.extract_concepts(
                code=input_data.code,
                language=input_data.language or "python",
                structural_summary=preprocessed.structural_summary,
                pre_detected_patterns=preprocessed.detected_patterns,
            )
        else:
            concepts = _convert_patterns_to_concepts(preprocessed.detected_patterns)

        return ExtractionResponse(
            success=True,
            concepts=[ConceptResponse(
                name=c.name, category=c.category, description=c.description,
                confidence=c.confidence, evidence=c.evidence,
                relatedConcepts=c.related_concepts,
            ) for c in concepts],
            visualizations=visualizer.generate_all_visualizations(concepts),
            metrics={
                "linesOfCode":    preprocessed.metrics.lines_of_code,
                "functionsFound": len(preprocessed.metrics.functions),
                "classesFound":   len(preprocessed.metrics.classes),
                "importsFound":   len(preprocessed.metrics.imports),
                "conceptsExtracted": len(concepts),
                "language":       input_data.language or "python",
            },
            processingTime=round(time.time() - start_time, 3),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract-enhanced")
async def extract_concepts_enhanced(request: Request):
    """
    Extract concepts with AST enhancement.
    Accepts extraction_mode: 'hybrid' (default) | 'llm_only'
    """
    data            = await request.json()
    code            = data.get("code", "")
    language        = data.get("language", "python")
    extraction_mode = data.get("extraction_mode", "hybrid")

    preprocessed = preprocessor.preprocess(code, language)
    quota_exhausted = False

    if extraction_mode == "llm_only":
        # LLM-only: send raw code to Gemini, no AST metadata in prompt
        if gemini_extractor:
            concepts = await gemini_extractor.extract_concepts(
                code=code,
                language=language,
                structural_summary={},
                pre_detected_patterns={},
                extraction_mode="llm_only",
            )
            # Gemini returned nothing — likely quota exhausted
            # Return AST fallback so frontend isn't empty, but flag it clearly
            if not concepts:
                quota_exhausted = True
                concepts = gemini_extractor._get_intelligent_fallback(
                    code, language, preprocessed.detected_patterns
                )
                print("ℹ️  LLM-only returned no results — serving AST fallback with quota_exhausted flag")
        else:
            quota_exhausted = True
            concepts = []
    else:
        # Hybrid: use EnhancedExtractor (AST + Gemini)
        extractor = EnhancedExtractor(use_codebert=False)
        concepts  = await extractor.extract_concepts(
            code=code,
            language=language,
            structural_summary=preprocessed.structural_summary,
            pre_detected_patterns=preprocessed.detected_patterns,
        )

    return {
        "success":         True,
        "extraction_mode": extraction_mode,
        "quota_exhausted": quota_exhausted,
        "concepts":        [_concept_to_dict(c) for c in concepts],
        "metrics": {
            "linesOfCode":       preprocessed.metrics.lines_of_code,
            "functionsFound":    len(preprocessed.metrics.functions),
            "classesFound":      len(preprocessed.metrics.classes),
            "importsFound":      len(preprocessed.metrics.imports),
            "conceptsExtracted": len(concepts),
            "language":          language,
        },
    }


@router.post("/classify")
async def quick_classify(input_data: QuickClassifyInput):
    start_time = time.time()
    try:
        preprocessed = preprocessor.preprocess(
            code=input_data.code, language=input_data.language or "python"
        )
        patterns       = preprocessed.detected_patterns
        category_counts = {k: len(v) for k, v in patterns.items() if v}
        primary        = max(category_counts, key=category_counts.get) if category_counts else None
        confidence     = min(0.9, 0.3 + sum(category_counts.values()) * 0.1) if category_counts else 0.0
        return {
            "detectedPatterns": patterns,
            "primaryCategory":  primary,
            "confidence":       confidence,
            "processingTimeMs": round((time.time() - start_time) * 1000, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/concept-details")
async def get_concept_details(input_data: ConceptDetailInput):
    if not gemini_extractor:
        raise HTTPException(status_code=503, detail="Gemini API not configured")
    try:
        details = await gemini_extractor.get_concept_explanation(
            concept_name=input_data.conceptName,
            code_context=input_data.codeContext or "",
            detail_level=input_data.detailLevel or "intermediate",
        )
        return {"success": True, "details": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.post("/visualize")
async def generate_visualization(input_data: VisualizationInput):
    try:
        concepts = [ExtractedConcept(
            name=c.get("name", ""), category=c.get("category", ""),
            description=c.get("description", ""), confidence=c.get("confidence", 0.8),
            evidence=c.get("evidence", ""), related_concepts=c.get("relatedConcepts", []),
        ) for c in input_data.concepts]
        vt     = input_data.type.lower()
        result = (
            visualizer.generate_concept_graph(concepts)         if vt == "graph"        else
            visualizer.generate_category_distribution(concepts) if vt == "distribution" else
            visualizer.generate_concept_cards(concepts)         if vt == "cards"        else
            {"diagram": visualizer.generate_mermaid_diagram(concepts)} if vt == "mermaid" else
            visualizer.generate_all_visualizations(concepts)
        )
        return {"success": True, "type": vt, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/project-purpose")
async def generate_project_purpose(input_data: ProjectPurposeInput):
    fake = [
        {"filename": f, "success": True,
         "concepts": [{"name": n} for n in input_data.conceptNames]}
        for f in input_data.filenames
    ]
    purpose = await _generate_project_purpose(fake, gemini_extractor)
    return {"success": True, "purpose": purpose}


@router.get("/supported-languages")
async def get_supported_languages():
    from app.utils.constants import SUPPORTED_LANGUAGES
    return {"languages": list(SUPPORTED_LANGUAGES.keys()), "details": SUPPORTED_LANGUAGES}


@router.get("/model-info")
async def get_model_info():
    return {
        "current_model": {
            "name": "Google Gemini 2.0 Flash", "provider": "Google AI",
            "type": "Large Language Model", "use_case": "Concept extraction",
        },
        "pipeline": [
            "1. AST Preprocessing", "2. Rule-based Detection",
            "3. Gemini AI Batch (1 call for all files)", "4. Confidence Fusion",
        ],
        "student_id": "IT22601360",
        "extraction_modes": ["hybrid (AST + LLM)", "llm_only (LLM baseline)"],
    }


# ── Multi-File Extraction ─────────────────────────────────────────────────────

@router.post("/extract-files")
async def extract_from_files(
    files: List[UploadFile] = File(...),
    language_override: Optional[str] = None,
    extraction_mode: str = Query(default="hybrid", pattern="^(hybrid|llm_only)$"),
):
    """
    Upload a folder and extract CS concepts from the whole project.

    extraction_mode:
      hybrid   — AST preprocessing + batch Gemini + confidence boost (default)
      llm_only — batch Gemini with raw code only (research baseline)

    Both use ONE batch API call. Total: 2 API calls regardless of file count.
    Previous behaviour was N API calls (one per file) → caused the 429 storm.
    """
    start_time = time.time()
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    raw_files = [(uf.filename or "unknown", await uf.read()) for uf in files]
    processed = file_processor.process_uploaded_files(raw_files, language_override)
    valid     = [p for p in processed if not p.skipped]
    skipped   = [p for p in processed if p.skipped]

    if not valid:
        raise HTTPException(
            status_code=400,
            detail=f"No processable files. Skipped: {[p.filename for p in skipped]}"
        )

    # ── Step 1: Preprocess all files (AST + rules, zero API calls) ────────
    print(f"📦 Preprocessing {len(valid)} files (mode={extraction_mode})...")
    preprocessed_files = []
    for p in valid:
        try:
            pre = preprocessor.preprocess(p.code, p.language)
            preprocessed_files.append({
                "filename":              p.filename,
                "language":              p.language,
                "code":                  p.code,
                "structural_summary":    pre.structural_summary,
                "pre_detected_patterns": pre.detected_patterns,
                "metrics": {
                    "linesOfCode":    pre.metrics.lines_of_code,
                    "functionsFound": len(pre.metrics.functions),
                    "classesFound":   len(pre.metrics.classes),
                    "importsFound":   len(pre.metrics.imports),
                    "language":       p.language,
                },
            })
        except Exception as e:
            print(f"⚠️ Preprocess failed {p.filename}: {e}")
            preprocessed_files.append({
                "filename": p.filename, "language": p.language, "code": p.code,
                "structural_summary": {}, "pre_detected_patterns": {},
                "metrics": {"linesOfCode": 0, "functionsFound": 0,
                            "classesFound": 0, "importsFound": 0, "language": p.language},
            })

    # ── Step 2: ONE batch Gemini call for all files ────────────────────────
    if gemini_extractor:
        batch_results = await gemini_extractor.batch_extract_project(
            preprocessed_files, extraction_mode=extraction_mode
        )
    else:
        batch_results = {
            pf["filename"]: _convert_patterns_to_concepts(pf["pre_detected_patterns"])
            for pf in preprocessed_files
        }

    # ── Step 3: Build per-file result dicts ───────────────────────────────
    file_results = []
    for pf in preprocessed_files:
        fname    = pf["filename"]
        concepts = list(batch_results.get(fname, []))

        # Hybrid: fill gaps with AST/rule-based concepts Gemini missed
        if extraction_mode == "hybrid":
            existing = {c.name.lower() for c in concepts}
            for ac in _convert_patterns_to_concepts(pf["pre_detected_patterns"]):
                if ac.name.lower() not in existing:
                    ac.source = "rule_based"
                    concepts.append(ac)

        file_results.append({
            "filename":        fname,
            "language":        pf["language"],
            "success":         True,
            "extraction_mode": extraction_mode,
            "concepts":        [_concept_to_dict(c) for c in concepts],
            "metrics":         {**pf["metrics"], "conceptsExtracted": len(concepts)},
            "processingTimeMs": round((time.time() - start_time) * 1000, 2),
            "skipped":         False,
            "skipReason":      None,
        })

    skipped_entries = [{
        "filename": p.filename, "language": p.language, "success": False,
        "concepts": [], "metrics": {}, "processingTimeMs": 0,
        "skipped": True, "skipReason": p.skip_reason,
    } for p in skipped]

    # ── Step 4: Project purpose (second API call) ──────────────────────────
    project_purpose = await _generate_project_purpose(file_results, gemini_extractor)

    total_c = sum(len(r["concepts"]) for r in file_results)
    print(
        f"✅ Done: {len(file_results)} files · {total_c} concepts · "
        f"mode={extraction_mode} · {round(time.time()-start_time, 2)}s"
    )

    return _build_project_response(
        file_results, skipped_entries, len(processed), start_time, project_purpose
    )