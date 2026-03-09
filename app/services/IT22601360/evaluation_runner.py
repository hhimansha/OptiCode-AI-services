"""
Evaluation Runner — IT22601360

Runs 3 extraction modes on all 15 dataset samples and computes
precision, recall, F1, and confidence calibration.

This file is STANDALONE — it does NOT import from the app package.
Place it alongside evaluation_dataset.py, concept_matcher.py,
and baseline_extractor.py in a folder like:
  app/services/IT22601360/evaluation/

Modes
─────
  ast_only  — regex + Python AST, no Gemini API calls (run first, always free)
  baseline  — LLM only, minimal prompt, no AST pipeline (requires GEMINI_API_KEY)
  hybrid    — AST pre-detection + LLM + confidence fusion (requires GEMINI_API_KEY)

Usage
─────
  # Free, no API key needed:
  python evaluation_runner.py --mode ast_only

  # Full comparison (uses ~30 API calls, do once):
  python evaluation_runner.py --mode all

  # Quick test on specific sample:
  python evaluation_runner.py --mode hybrid --sample DS01,DS02

Output: results/evaluation_results.json
"""

import asyncio
import json
import os
import sys
import time
import argparse
from typing import List, Dict, Optional
import ast as python_ast
import re

# Local imports — all files live in the same directory
from evaluation_dataset import EVALUATION_DATASET, EvalSample, norm
from concept_matcher import match_concepts
from baseline_extractor import BaselineExtractor


# ── Self-contained AST extractor for evaluation ────────────────────────────────
# This deliberately reimplements the key logic without importing from the app.
# That way the evaluation can run on any machine without the full uvicorn stack.

def _ast_only_extract(code: str, language: str) -> List[Dict]:
    """
    Pure static analysis: Python AST + regex.
    No LLM calls. Mirrors what CodePreprocessor + ASTAnalyzer do in production.
    """
    concepts = []
    if language != "python":
        return []

    try:
        tree = python_ast.parse(code)
    except SyntaxError:
        return []

    classes   = []
    functions = []
    rec_funcs = []

    for node in python_ast.walk(tree):
        if isinstance(node, python_ast.ClassDef):
            classes.append(node.name)
        if isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)):
            functions.append(node.name)

    # Check recursion
    for node in python_ast.walk(tree):
        if isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)):
            for child in python_ast.walk(node):
                if isinstance(child, python_ast.Call):
                    func = child.func
                    if isinstance(func, python_ast.Name) and func.id == node.name:
                        rec_funcs.append(node.name)
                        break

    code_lower = code.lower()

    # Regex pattern → (concept name, category, confidence)
    patterns = [
        (r'\bleft\b.*\bright\b.*\bmid\b|\bmid\b.*=.*\bleft\b.*\bright\b',
            "Binary Search",          "algorithm",          0.85),
        (r'merge_sort|def merge\s*\(',
            "Merge Sort",             "algorithm",          0.88),
        (r'bubble_sort|swapped\s*=\s*False',
            "Bubble Sort",            "algorithm",          0.85),
        (r'quick_sort|def partition\s*\(',
            "Quick Sort",             "algorithm",          0.85),
        (r'_instance\s*=\s*None',
            "Singleton",              "design_pattern",     0.80),
        (r'def on\s*\(|self\._listeners|def emit\s*\(',
            "Observer",               "design_pattern",     0.80),
        (r'factory|def create\s*\(',
            "Factory",                "design_pattern",     0.75),
        (r'def push\s*\(|def pop\s*\(|def peek\s*\(',
            "Stack",                  "data_structure",     0.88),
        (r'self\.next\s*=|\.next\s*=\s*None',
            "Linked List",            "data_structure",     0.85),
        (r'node\.left\s*=|node\.right\s*=',
            "Binary Search Tree",     "data_structure",     0.82),
        (r'deque\s*\[|queue\.popleft\s*\(',
            "Breadth-First Search",   "algorithm",          0.85),
        (r'def dfs\s*\(',
            "Depth-First Search",     "algorithm",          0.85),
        (r'lru_cache|@memoize|\bdp\s*=\s*\[',
            "Dynamic Programming",    "algorithm",          0.82),
        (r'lru_cache|cache\s*:\s*Dict|cache\s*=\s*{}',
            "Memoization",            "programming_concept",0.85),
        (r'seen\s*=\s*{}|groups\s*=\s*{}',
            "Hash Map",               "data_structure",     0.80),
        (r'@functools\.wraps|def wrapper\s*\(',
            "Decorator Pattern",      "design_pattern",     0.80),
        (r'def.*\(.*func.*\):|return\s+wrapper',
            "Higher-Order Function",  "programming_concept",0.75),
        (r'functools\.wraps|def wrapper\s*\(',
            "Closure",                "programming_concept",0.72),
    ]

    found_names = set()
    for pattern, name, category, confidence in patterns:
        if re.search(pattern, code_lower):
            if name not in found_names:
                found_names.add(name)
                concepts.append({
                    "name": name, "category": category,
                    "confidence": confidence, "evidence": f"Pattern matched: {name}"
                })

    # OOP
    if classes:
        concepts.append({
            "name": "Object-Oriented Programming", "category": "paradigm",
            "confidence": 0.88, "evidence": f"class {classes[0]}:"
        })
        # Encapsulation — if any attribute starts with _
        if re.search(r'self\._\w+', code):
            concepts.append({
                "name": "Encapsulation", "category": "programming_concept",
                "confidence": 0.72, "evidence": "Private attributes with _ prefix"
            })

    # Recursion
    if rec_funcs:
        concepts.append({
            "name": "Recursion", "category": "algorithm",
            "confidence": 0.92, "evidence": f"{rec_funcs[0]} calls itself"
        })

    # Polymorphism — overridden abstract methods
    if re.search(r'@abstractmethod|ABC\b', code):
        concepts.append({
            "name": "Abstraction", "category": "programming_concept",
            "confidence": 0.82, "evidence": "@abstractmethod / ABC"
        })
    if classes and len(classes) > 1 and re.search(r'def area\b|def speak\b|def move\b', code_lower):
        concepts.append({
            "name": "Polymorphism", "category": "programming_concept",
            "confidence": 0.75, "evidence": "Same method name overridden in subclasses"
        })

    # Event-driven programming
    if re.search(r'def on\s*\(|def emit\s*\(|def off\s*\(', code_lower):
        concepts.append({
            "name": "Event-Driven Programming", "category": "paradigm",
            "confidence": 0.72, "evidence": "on/emit/off event handler pattern"
        })

    return concepts


# ── Per-sample evaluation ───────────────────────────────────────────────────────

async def evaluate_sample(
    sample: EvalSample,
    mode: str,
    baseline_extractor: Optional[BaselineExtractor],
    rate_delay: float = 14.0,
) -> Dict:
    print(f"  [{sample.id}] {sample.title:<45} ({mode})", end=" ", flush=True)
    start = time.time()

    if mode == "ast_only":
        raw = _ast_only_extract(sample.code, sample.language)
        extracted_names      = [norm(c["name"]) for c in raw]
        extracted_with_conf  = [(norm(c["name"]), c["confidence"]) for c in raw]

    elif mode == "baseline":
        if not baseline_extractor:
            print("→ skipped (no API key)")
            return _empty_result(sample, mode, "No GEMINI_API_KEY")
        await asyncio.sleep(rate_delay)
        raw = await baseline_extractor.extract(sample.code, sample.language)
        extracted_names     = [norm(c.name) for c in raw if c.name]
        extracted_with_conf = [(norm(c.name), c.confidence) for c in raw if c.name]

    elif mode == "hybrid":
        # Step 1: AST
        ast_raw   = _ast_only_extract(sample.code, sample.language)
        ast_names = {norm(c["name"]) for c in ast_raw}

        # Step 2: LLM
        if baseline_extractor:
            await asyncio.sleep(rate_delay)
            llm_raw = await baseline_extractor.extract(sample.code, sample.language)
        else:
            llm_raw = []

        # Step 3: Merge — boost confidence when both agree
        merged: Dict[str, float] = {}
        for c in llm_raw:
            n      = norm(c.name)
            in_ast = any(n in an or an in n for an in ast_names)
            merged[n] = min(1.0, c.confidence + (0.10 if in_ast else 0.0))

        for c in ast_raw:
            n = norm(c["name"])
            if n not in merged:
                merged[n] = c["confidence"]

        extracted_names     = list(merged.keys())
        extracted_with_conf = list(merged.items())

    else:
        return _empty_result(sample, mode, f"Unknown mode: {mode}")

    elapsed = time.time() - start
    match   = match_concepts(
        extracted=extracted_names,
        ground_truth=sample.ground_truth,
    )

    # Build calibration data: was each prediction correct?
    calib_data = []
    tp_norm = {norm(t[0]) for t in match["tp"]} | {norm(t[1]) for t in match["tp"]}
    for name, conf in extracted_with_conf:
        calib_data.append({
            "concept":    name,
            "confidence": conf,
            "correct":    name in tp_norm,
        })

    print(f"→ P={match['precision']:.2f}  R={match['recall']:.2f}  F1={match['f1']:.2f}"
          f"  [TP={match['tp_count']} FP={match['fp_count']} FN={match['fn_count']}]")

    return {
        "sample_id":        sample.id,
        "sample_title":     sample.title,
        "mode":             mode,
        "difficulty":       sample.difficulty,
        "ground_truth":     list(sample.ground_truth),
        "extracted":        extracted_names,
        "tp":               [(t[0], t[1]) for t in match["tp"]],
        "fp":               match["fp"],
        "fn":               match["fn"],
        "tp_count":         match["tp_count"],
        "fp_count":         match["fp_count"],
        "fn_count":         match["fn_count"],
        "precision":        match["precision"],
        "recall":           match["recall"],
        "f1":               match["f1"],
        "elapsed_s":        round(elapsed, 3),
        "calibration_data": calib_data,
    }


def _empty_result(sample: EvalSample, mode: str, reason: str) -> Dict:
    return {
        "sample_id": sample.id, "sample_title": sample.title,
        "mode": mode, "difficulty": sample.difficulty,
        "ground_truth": list(sample.ground_truth), "extracted": [],
        "tp": [], "fp": [], "fn": list(sample.ground_truth),
        "tp_count": 0, "fp_count": 0, "fn_count": len(sample.ground_truth),
        "precision": 0.0, "recall": 0.0, "f1": 0.0,
        "elapsed_s": 0.0, "calibration_data": [], "error": reason,
    }


# ── Aggregate metrics ───────────────────────────────────────────────────────────

def aggregate_results(per_sample: List[Dict]) -> Dict:
    if not per_sample:
        return {}
    n = len(per_sample)

    avg_p  = sum(r["precision"] for r in per_sample) / n
    avg_r  = sum(r["recall"]    for r in per_sample) / n
    avg_f1 = sum(r["f1"]        for r in per_sample) / n

    total_tp = sum(r["tp_count"] for r in per_sample)
    total_fp = sum(r["fp_count"] for r in per_sample)
    total_fn = sum(r["fn_count"] for r in per_sample)
    micro_p  = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r  = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        sub = [r for r in per_sample if r["difficulty"] == diff]
        if sub:
            by_difficulty[diff] = {
                "precision": round(sum(r["precision"] for r in sub) / len(sub), 4),
                "recall":    round(sum(r["recall"]    for r in sub) / len(sub), 4),
                "f1":        round(sum(r["f1"]        for r in sub) / len(sub), 4),
                "n":         len(sub),
            }

    return {
        "n_samples":        n,
        "macro_precision":  round(avg_p,    4),
        "macro_recall":     round(avg_r,    4),
        "macro_f1":         round(avg_f1,   4),
        "micro_precision":  round(micro_p,  4),
        "micro_recall":     round(micro_r,  4),
        "micro_f1":         round(micro_f1, 4),
        "total_tp": total_tp, "total_fp": total_fp, "total_fn": total_fn,
        "by_difficulty": by_difficulty,
    }


def compute_calibration(per_sample: List[Dict]) -> Dict:
    """
    Group predictions into confidence buckets.
    For each bucket: what fraction were actually correct (TP)?
    A well-calibrated system: 80% confidence bucket ≈ 80% accuracy.
    ECE = Expected Calibration Error (lower is better).
    """
    buckets = {
        "0.0-0.2": [], "0.2-0.4": [], "0.4-0.6": [],
        "0.6-0.8": [], "0.8-1.0": []
    }
    for r in per_sample:
        for cd in r.get("calibration_data", []):
            conf = cd["confidence"]
            bucket = (
                "0.0-0.2" if conf < 0.2 else
                "0.2-0.4" if conf < 0.4 else
                "0.4-0.6" if conf < 0.6 else
                "0.6-0.8" if conf < 0.8 else
                "0.8-1.0"
            )
            buckets[bucket].append(cd["correct"])

    result = []
    for bucket, correctness in buckets.items():
        lo, hi = [float(x) for x in bucket.split("-")]
        midpoint = (lo + hi) / 2
        acc = sum(correctness) / len(correctness) if correctness else None
        result.append({
            "bucket":             bucket,
            "midpoint":           midpoint,
            "n_predictions":      len(correctness),
            "n_correct":          sum(correctness) if correctness else 0,
            "actual_accuracy":    round(acc, 4) if acc is not None else None,
            "expected_accuracy":  midpoint,
            "calibration_error":  round(abs(acc - midpoint), 4) if acc is not None else None,
        })

    valid       = [r for r in result if r["n_predictions"] > 0 and r["calibration_error"] is not None]
    total_preds = sum(r["n_predictions"] for r in valid)
    ece = (
        sum((r["n_predictions"] / total_preds) * r["calibration_error"] for r in valid)
        if total_preds > 0 else None
    )

    return {"buckets": result, "ece": round(ece, 4) if ece is not None else None}


# ── Main ────────────────────────────────────────────────────────────────────────

async def run_evaluation(
    modes: List[str],
    sample_ids: Optional[List[str]] = None,
    output_dir: str = "results",
) -> Dict:
    os.makedirs(output_dir, exist_ok=True)

    api_key  = os.getenv("GEMINI_API_KEY")
    baseline = None
    if api_key:
        try:
            baseline = BaselineExtractor(api_key)
        except Exception as e:
            print(f"⚠️  Could not init baseline extractor: {e}")
    else:
        print("⚠️  No GEMINI_API_KEY — LLM modes will be skipped.")
        print("    ast_only mode works without an API key.\n")

    samples = EVALUATION_DATASET
    if sample_ids:
        samples = [s for s in samples if s.id in sample_ids]
        if not samples:
            print(f"❌ No samples matched IDs: {sample_ids}")
            return {}

    print(f"🔬 Evaluation: {len(samples)} samples × {len(modes)} mode(s)\n")

    all_results   = []
    mode_results  = {m: [] for m in modes}

    for mode in modes:
        print(f"\n{'─'*60}")
        print(f"  MODE: {mode.upper()}")
        print(f"{'─'*60}")

        for sample in samples:
            result = await evaluate_sample(
                sample=sample,
                mode=mode,
                baseline_extractor=baseline,
                rate_delay=14.0,    # ~4 RPM, safely under 5 RPM free-tier limit
            )
            all_results.append(result)
            mode_results[mode].append(result)

    # ── Summary table ──────────────────────────────────────────────────────────
    summary = {}
    for mode in modes:
        agg   = aggregate_results(mode_results[mode])
        calib = compute_calibration(mode_results[mode])
        summary[mode] = {"aggregate": agg, "calibration": calib}

    print(f"\n{'='*70}")
    print(f"{'RESULTS SUMMARY':^70}")
    print(f"{'='*70}")
    print(f"{'Mode':<15} {'Macro-P':>9} {'Macro-R':>9} {'Macro-F1':>10} {'ECE':>8}  Notes")
    print(f"{'─'*70}")
    for mode in modes:
        agg   = summary[mode]["aggregate"]
        calib = summary[mode]["calibration"]
        notes = ""
        if not agg:
            notes = "(no results)"
        print(
            f"{mode:<15} "
            f"{agg.get('macro_precision', 0):>9.4f} "
            f"{agg.get('macro_recall', 0):>9.4f} "
            f"{agg.get('macro_f1', 0):>10.4f} "
            f"{str(calib.get('ece', 'N/A')):>8}  {notes}"
        )

    if "baseline" in summary and "hybrid" in summary:
        b = summary["baseline"]["aggregate"]
        h = summary["hybrid"]["aggregate"]
        if b and h:
            delta_f1 = h.get("macro_f1", 0) - b.get("macro_f1", 0)
            sign = "+" if delta_f1 > 0 else ""
            print(f"\n  Hybrid vs Baseline F1: {sign}{delta_f1*100:.1f}%")

    print(f"{'='*70}\n")

    # ── Save results ───────────────────────────────────────────────────────────
    output = {
        "metadata": {
            "n_samples":   len(samples),
            "modes":       modes,
            "dataset_ids": [s.id for s in samples],
        },
        "summary":    summary,
        "per_sample": all_results,
    }

    out_path = os.path.join(output_dir, "evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Results saved → {out_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run concept extraction evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluation_runner.py --mode ast_only
  python evaluation_runner.py --mode all
  python evaluation_runner.py --mode baseline,hybrid --sample DS01,DS07,DS10
        """
    )
    parser.add_argument(
        "--mode", default="ast_only",
        help="Modes: all | ast_only | baseline | hybrid (comma-separated, default: ast_only)"
    )
    parser.add_argument(
        "--sample", default=None,
        help="Sample IDs to run: DS01,DS02 (default: all 15)"
    )
    parser.add_argument(
        "--output", default="results",
        help="Output directory for results JSON (default: results/)"
    )
    args = parser.parse_args()

    if args.mode == "all":
        modes = ["ast_only", "baseline", "hybrid"]
    else:
        modes = [m.strip() for m in args.mode.split(",")]

    sample_ids = (
        [s.strip() for s in args.sample.split(",")]
        if args.sample else None
    )

    asyncio.run(run_evaluation(
        modes=modes,
        sample_ids=sample_ids,
        output_dir=args.output,
    ))