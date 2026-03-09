"""
Code Concept Extractor API Router
Student: IT22601360

Supports:
- Single code paste extraction
- Multi-file folder upload (webkitdirectory)
- Project purpose generation via Gemini
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import traceback
import asyncio

from app.services.IT22601360.preprocessor import CodePreprocessor
from app.services.IT22601360.gemini_extractor import GeminiExtractor, ExtractedConcept
from app.services.IT22601360.visualizer import VisualizationGenerator
from app.services.IT22601360.enhanced_extractor import EnhancedExtractor
from app.services.IT22601360.file_processor import FileProcessor
from app.services.IT22601360.project_aggregator import ProjectAggregator

router = APIRouter()

preprocessor = CodePreprocessor()
visualizer = VisualizationGenerator()
file_processor = FileProcessor()
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
    """Request to generate project purpose from aggregated data"""
    filenames: List[str]
    conceptNames: List[str]
    languageDistribution: Optional[Dict[str, int]] = {}


# ── Project Purpose Generation ────────────────────────────────────────────────

async def _generate_project_purpose(
    file_results: List[Dict],
    extractor: Optional[GeminiExtractor]
) -> str:
    """
    Use Gemini to generate a natural language description of the project's purpose.
    Falls back to a template-based description if Gemini is unavailable.
    """
    filenames = [r["filename"] for r in file_results if r.get("success")]
    all_concept_names = []
    for r in file_results:
        if r.get("success"):
            for c in r.get("concepts", []):
                all_concept_names.append(c.get("name", ""))

    unique_concepts = list(dict.fromkeys(all_concept_names))[:20]

    if not extractor or not filenames:
        return _fallback_project_purpose(filenames, unique_concepts)

    prompt = f"""You are analyzing a software project. Based on the following file names and detected computer science concepts, write a clear 3-4 sentence description of:
1. What this project does (its main purpose)
2. The key technical approaches and patterns used
3. The likely domain or application area

Files analyzed ({len(filenames)} total):
{chr(10).join(f"  - {f}" for f in filenames[:15])}
{"  ... and more" if len(filenames) > 15 else ""}

Key CS concepts detected: {', '.join(unique_concepts[:20])}

Write ONLY a natural language paragraph. No JSON, no bullet points, no headers. Be specific and technical."""

    try:
        response = await extractor._call_gemini_api(prompt)
        if response and len(response.strip()) > 20:
            return response.strip()
        return _fallback_project_purpose(filenames, unique_concepts)
    except Exception as e:
        print(f"⚠️ Purpose generation failed: {e}")
        return _fallback_project_purpose(filenames, unique_concepts)


def _fallback_project_purpose(filenames: List[str], concepts: List[str]) -> str:
    """Template-based project purpose when Gemini is unavailable."""
    file_count = len(filenames)
    top_concepts = concepts[:4] if concepts else ["general programming patterns"]

    # Try to guess domain from filenames
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

    domain_str = f" with {', '.join(domain_hints)}" if domain_hints else ""
    concepts_str = ", ".join(top_concepts)

    return (
        f"This project consists of {file_count} source file(s){domain_str}. "
        f"The codebase demonstrates key computer science concepts including {concepts_str}. "
        f"Analysis identified patterns across the files that reflect structured software "
        f"development practices and established architectural approaches."
    )


# ── Internal Helpers ──────────────────────────────────────────────────────────

async def _extract_single_file(
    filename: str,
    language: str,
    code: str,
) -> Dict[str, Any]:
    """Run the full extraction pipeline on a single file."""
    start = time.time()
    try:
        preprocessed = preprocessor.preprocess(code=code, language=language)

        if gemini_extractor:
            concepts = await gemini_extractor.extract_concepts(
                code=code,
                language=language,
                structural_summary=preprocessed.structural_summary,
                pre_detected_patterns=preprocessed.detected_patterns,
            )
        else:
            concepts = _convert_patterns_to_concepts(preprocessed.detected_patterns)

        concepts_response = [
            {
                "name": c.name,
                "category": c.category,
                "description": c.description,
                "confidence": c.confidence,
                "evidence": c.evidence,
                "relatedConcepts": c.related_concepts,
                "source": getattr(c, "source", "gemini"),
            }
            for c in concepts
        ]

        return {
            "filename": filename,
            "language": language,
            "success": True,
            "concepts": concepts_response,
            "metrics": {
                "linesOfCode": preprocessed.metrics.lines_of_code,
                "functionsFound": len(preprocessed.metrics.functions),
                "classesFound": len(preprocessed.metrics.classes),
                "importsFound": len(preprocessed.metrics.imports),
                "conceptsExtracted": len(concepts),
                "language": language,
            },
            "processingTimeMs": round((time.time() - start) * 1000, 2),
            "skipped": False,
            "skipReason": None,
        }

    except Exception as exc:
        return {
            "filename": filename,
            "language": language,
            "success": False,
            "concepts": [],
            "metrics": {},
            "processingTimeMs": round((time.time() - start) * 1000, 2),
            "skipped": True,
            "skipReason": str(exc),
        }


async def _build_project_response(
    file_results: List[Dict],
    skipped_files: List[Dict],
    total_files_scanned: int,
    start_time: float,
) -> Dict[str, Any]:
    """Build the complete project response with purpose generation."""
    all_results = file_results + skipped_files

    try:
        aggregated = project_aggregator.aggregate(file_results)
        summary = project_aggregator.build_project_summary(
            per_file_results=file_results,
            aggregated_concepts=aggregated,
            total_files_scanned=total_files_scanned,
            total_files_skipped=len(skipped_files),
        )
        agg_dict = project_aggregator.to_response_dict(aggregated, summary)
    except Exception as e:
        print(f"⚠️ Aggregator error (using fallback): {e}")
        agg_dict = {
            "aggregated_concepts": [],
            "project_summary": {
                "total_files": total_files_scanned,
                "successful_files": len(file_results),
                "skipped_files": len(skipped_files),
            },
        }

    # Generate project purpose via Gemini
    project_purpose = await _generate_project_purpose(file_results, gemini_extractor)
    agg_dict["project_summary"]["project_purpose"] = project_purpose

    return {
        "success": True,
        "files": all_results,
        "aggregated_concepts": agg_dict.get("aggregated_concepts", []),
        "project_summary": agg_dict.get("project_summary", {}),
        "totalProcessingTime": round(time.time() - start_time, 3),
    }


def _convert_patterns_to_concepts(patterns: Dict[str, List[str]]) -> List[ExtractedConcept]:
    category_map = {
        "data_structures": "data_structure",
        "algorithms": "algorithm",
        "design_patterns": "design_pattern",
        "architectures": "architecture",
        "paradigms": "paradigm",
        "programming_concepts": "programming_concept",
    }
    concepts = []
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            concepts.append(ExtractedConcept(
                name=pattern.replace("_", " ").title(),
                category=category_map.get(category, "programming_concept"),
                description=f"Detected {pattern.replace('_', ' ')} pattern in code",
                confidence=0.5,
                evidence="Pattern matched by rule-based detection",
                related_concepts=[],
            ))
    return concepts


# ── API Endpoints ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "component": "Code Concept Extractor",
        "student_id": "IT22601360",
        "gemini_available": gemini_extractor is not None,
    }


@router.post("/extract", response_model=ExtractionResponse)
async def extract_concepts(input_data: CodeInput):
    """Extract concepts from a single code snippet."""
    start_time = time.time()
    try:
        preprocessed = preprocessor.preprocess(
            code=input_data.code,
            language=input_data.language or "python",
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

        visualizations = visualizer.generate_all_visualizations(concepts)

        concepts_response = [
            ConceptResponse(
                name=c.name,
                category=c.category,
                description=c.description,
                confidence=c.confidence,
                evidence=c.evidence,
                relatedConcepts=c.related_concepts,
            )
            for c in concepts
        ]

        return ExtractionResponse(
            success=True,
            concepts=concepts_response,
            visualizations=visualizations,
            metrics={
                "linesOfCode": preprocessed.metrics.lines_of_code,
                "functionsFound": len(preprocessed.metrics.functions),
                "classesFound": len(preprocessed.metrics.classes),
                "importsFound": len(preprocessed.metrics.imports),
                "conceptsExtracted": len(concepts),
                "language": input_data.language or "python",
            },
            processingTime=round(time.time() - start_time, 3),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract-enhanced")
async def extract_concepts_enhanced(request: Request):
    """Extract concepts with AST enhancement (used by frontend)."""
    data = await request.json()
    code = data.get("code", "")
    language = data.get("language", "python")

    preprocessed = preprocessor.preprocess(code, language)
    extractor = EnhancedExtractor(use_codebert=False)

    concepts = await extractor.extract_concepts(
        code=code,
        language=language,
        structural_summary=preprocessed.structural_summary,
        pre_detected_patterns=preprocessed.detected_patterns,
    )

    return {
        "success": True,
        "concepts": [
            {
                "name": c.name,
                "category": c.category,
                "description": c.description,
                "confidence": c.confidence,
                "evidence": c.evidence,
                "relatedConcepts": c.related_concepts,
            }
            for c in concepts
        ],
        "metrics": {
            "linesOfCode": preprocessed.metrics.lines_of_code,
            "functionsFound": len(preprocessed.metrics.functions),
            "classesFound": len(preprocessed.metrics.classes),
            "importsFound": len(preprocessed.metrics.imports),
            "conceptsExtracted": len(concepts),
            "language": language,
        },
    }


@router.post("/classify")
async def quick_classify(input_data: QuickClassifyInput):
    """Fast rule-based classification without LLM."""
    start_time = time.time()
    try:
        preprocessed = preprocessor.preprocess(
            code=input_data.code,
            language=input_data.language or "python",
        )
        patterns = preprocessed.detected_patterns
        category_counts = {k: len(v) for k, v in patterns.items() if v}

        primary_category = None
        confidence = 0.0
        if category_counts:
            primary_category = max(category_counts, key=category_counts.get)
            total_patterns = sum(category_counts.values())
            confidence = min(0.9, 0.3 + (total_patterns * 0.1))

        return {
            "detectedPatterns": patterns,
            "primaryCategory": primary_category,
            "confidence": confidence,
            "processingTimeMs": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/concept-details")
async def get_concept_details(input_data: ConceptDetailInput):
    """Get AI-generated educational explanation for a concept."""
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
        raise HTTPException(status_code=500, detail=f"Failed to get concept details: {str(e)}")


@router.post("/visualize")
async def generate_visualization(input_data: VisualizationInput):
    """Generate a specific visualization type from concept data."""
    try:
        concepts = [
            ExtractedConcept(
                name=c.get("name", ""),
                category=c.get("category", ""),
                description=c.get("description", ""),
                confidence=c.get("confidence", 0.8),
                evidence=c.get("evidence", ""),
                related_concepts=c.get("relatedConcepts", []),
            )
            for c in input_data.concepts
        ]

        viz_type = input_data.type.lower()
        if viz_type == "graph":
            result = visualizer.generate_concept_graph(concepts)
        elif viz_type == "distribution":
            result = visualizer.generate_category_distribution(concepts)
        elif viz_type == "cards":
            result = visualizer.generate_concept_cards(concepts)
        elif viz_type == "mermaid":
            result = {"diagram": visualizer.generate_mermaid_diagram(concepts)}
        else:
            result = visualizer.generate_all_visualizations(concepts)

        return {"success": True, "type": viz_type, "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.post("/project-purpose")
async def generate_project_purpose(input_data: ProjectPurposeInput):
    """
    Standalone endpoint to generate project purpose from metadata.
    Called after multi-file extraction completes.
    """
    fake_results = [
        {"filename": f, "success": True, "concepts": [{"name": n} for n in input_data.conceptNames]}
        for f in input_data.filenames
    ]
    purpose = await _generate_project_purpose(fake_results, gemini_extractor)
    return {"success": True, "purpose": purpose}


@router.get("/supported-languages")
async def get_supported_languages():
    from app.utils.constants import SUPPORTED_LANGUAGES
    return {"languages": list(SUPPORTED_LANGUAGES.keys()), "details": SUPPORTED_LANGUAGES}


@router.get("/model-info")
async def get_model_info():
    return {
        "current_model": {
            "name": "Google Gemini 2.0 Flash",
            "provider": "Google AI",
            "type": "Large Language Model",
            "use_case": "Concept extraction and explanation",
        },
        "pipeline": [
            "1. Code Preprocessing (AST + tokenization)",
            "2. Rule-based Pattern Detection",
            "3. Gemini AI Extraction",
            "4. Confidence Fusion",
            "5. Visualization Generation",
        ],
        "student_id": "IT22601360",
    }


# ── Multi-File Extraction ─────────────────────────────────────────────────────

@router.post("/extract-files")
async def extract_from_files(
    files: List[UploadFile] = File(...),
    language_override: Optional[str] = None,
):
    """
    Upload a folder's files and extract CS concepts from the entire project.
    Returns per-file results, aggregated concepts, and an AI-generated project purpose.
    """
    start_time = time.time()

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    raw_files = []
    for uf in files:
        content = await uf.read()
        raw_files.append((uf.filename or "unknown", content))

    processed = file_processor.process_uploaded_files(raw_files, language_override)

    valid = [p for p in processed if not p.skipped]
    skipped = [p for p in processed if p.skipped]

    if not valid:
        reasons = [f"{p.filename}: {p.skip_reason}" for p in skipped]
        raise HTTPException(
            status_code=400,
            detail=f"No processable files found. Skipped: {reasons}",
        )

    tasks = [_extract_single_file(p.filename, p.language, p.code) for p in valid]
    file_results = list(await asyncio.gather(*tasks))

    skipped_entries = [
        {
            "filename": p.filename,
            "language": p.language,
            "success": False,
            "concepts": [],
            "metrics": {},
            "processingTimeMs": 0,
            "skipped": True,
            "skipReason": p.skip_reason,
        }
        for p in skipped
    ]

    return await _build_project_response(
        file_results=file_results,
        skipped_files=skipped_entries,
        total_files_scanned=len(processed),
        start_time=start_time,
    )