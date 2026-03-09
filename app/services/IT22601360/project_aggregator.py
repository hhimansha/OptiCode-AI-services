"""
Project Aggregator Service
Merges concept extraction results from multiple files into a unified project-level view.
Student: IT22601360
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from app.services.IT22601360.gemini_extractor import ExtractedConcept


@dataclass
class AggregatedConcept:
    """A concept aggregated across multiple files"""
    name: str
    category: str
    description: str
    confidence: float           # max confidence seen across files
    evidence: str               # best evidence snippet
    related_concepts: List[str]
    frequency: int = 1          # how many files contained this concept
    source_files: List[str] = field(default_factory=list)


@dataclass
class ProjectSummary:
    """High-level summary of an analyzed project"""
    total_files_scanned: int
    total_files_processed: int
    total_files_skipped: int
    total_lines_of_code: int
    languages_detected: List[str]
    total_concepts_extracted: int
    unique_concepts: int
    top_categories: List[Dict[str, Any]]


class ProjectAggregator:
    """
    Aggregates concept extraction results across multiple files.

    - Deduplicates concepts by name (case-insensitive)
    - Tracks frequency (how many files contain this concept)
    - Keeps the highest confidence value
    - Ranks concepts by frequency desc, confidence desc
    """

    def aggregate(
        self,
        per_file_results: List[Dict[str, Any]],
    ) -> List[AggregatedConcept]:
        """
        Merge per-file concept lists into a ranked aggregated list.

        Args:
            per_file_results: List of dicts with keys:
                'filename', 'language', 'concepts' (list of ExtractedConcept or dicts)

        Returns:
            Sorted list of AggregatedConcept objects
        """
        # key: normalized concept name -> AggregatedConcept
        bucket: Dict[str, AggregatedConcept] = {}

        for file_result in per_file_results:
            filename = file_result.get("filename", "unknown")
            concepts = file_result.get("concepts", [])

            for concept in concepts:
                # Handle both ExtractedConcept dataclass and plain dicts
                if isinstance(concept, ExtractedConcept):
                    name = concept.name
                    category = concept.category
                    description = concept.description
                    confidence = concept.confidence
                    evidence = concept.evidence
                    related = concept.related_concepts or []
                else:
                    name = concept.get("name", "Unknown")
                    category = concept.get("category", "programming_concept")
                    description = concept.get("description", "")
                    confidence = float(concept.get("confidence", 0.5))
                    evidence = concept.get("evidence", "")
                    related = concept.get("relatedConcepts", concept.get("related_concepts", []))

                key = name.lower().strip()

                if key in bucket:
                    existing = bucket[key]
                    existing.frequency += 1
                    # Keep highest confidence
                    if confidence > existing.confidence:
                        existing.confidence = confidence
                        existing.description = description
                        existing.evidence = evidence
                    # Merge related concepts (deduplicate)
                    for r in related:
                        if r not in existing.related_concepts:
                            existing.related_concepts.append(r)
                    if filename not in existing.source_files:
                        existing.source_files.append(filename)
                else:
                    bucket[key] = AggregatedConcept(
                        name=name,
                        category=category,
                        description=description,
                        confidence=confidence,
                        evidence=evidence,
                        related_concepts=list(related),
                        frequency=1,
                        source_files=[filename],
                    )

        # Sort: frequency desc, confidence desc
        aggregated = sorted(
            bucket.values(),
            key=lambda c: (-c.frequency, -c.confidence)
        )

        return aggregated

    def build_project_summary(
        self,
        per_file_results: List[Dict[str, Any]],
        aggregated_concepts: List[AggregatedConcept],
        total_files_scanned: int,
        total_files_skipped: int,
    ) -> ProjectSummary:
        """Build a high-level project summary"""
        languages = list({r.get("language", "unknown") for r in per_file_results})
        total_loc = sum(r.get("metrics", {}).get("linesOfCode", 0) for r in per_file_results)
        total_concepts = sum(len(r.get("concepts", [])) for r in per_file_results)

        # Category breakdown
        category_counts: Dict[str, int] = defaultdict(int)
        for c in aggregated_concepts:
            category_counts[c.category] += 1

        top_categories = sorted(
            [{"category": cat, "count": cnt} for cat, cnt in category_counts.items()],
            key=lambda x: -x["count"]
        )

        return ProjectSummary(
            total_files_scanned=total_files_scanned,
            total_files_processed=len(per_file_results),
            total_files_skipped=total_files_skipped,
            total_lines_of_code=total_loc,
            languages_detected=sorted(languages),
            total_concepts_extracted=total_concepts,
            unique_concepts=len(aggregated_concepts),
            top_categories=top_categories,
        )

    def to_response_dict(
        self,
        aggregated: List[AggregatedConcept],
        summary: ProjectSummary,
    ) -> Dict[str, Any]:
        """Convert aggregated data to a JSON-serializable dict"""
        return {
            "aggregated_concepts": [
                {
                    "name": c.name,
                    "category": c.category,
                    "description": c.description,
                    "confidence": round(c.confidence, 3),
                    "evidence": c.evidence,
                    "relatedConcepts": c.related_concepts,
                    "frequency": c.frequency,
                    "sourceFiles": c.source_files,
                }
                for c in aggregated
            ],
            "project_summary": {
                "totalFilesScanned": summary.total_files_scanned,
                "totalFilesProcessed": summary.total_files_processed,
                "totalFilesSkipped": summary.total_files_skipped,
                "totalLinesOfCode": summary.total_lines_of_code,
                "languagesDetected": summary.languages_detected,
                "totalConceptsExtracted": summary.total_concepts_extracted,
                "uniqueConcepts": summary.unique_concepts,
                "topCategories": summary.top_categories,
            }
        }
