"""
unified_risk_refactor.py
========================
OptiCode - Unified Risk Detection & Performance Optimization Pipeline
Author: IT22606860

This module combines all risk and performance analyzers into a single
unified API for comprehensive code analysis and automatic refactoring.

Modules integrated:
1. risk_refactor_filesystem  - File system security risks
2. risk_refactor_injection   - Injection vulnerabilities
3. risk_refactor_resources   - Resource leaks & concurrency
4. perf_optimizer_memory     - Memory optimization
5. perf_optimizer_caching    - Caching & algorithmic optimization
"""

import ast
import astor
from dataclasses import dataclass, field
from typing import Optional

# Import all specialized modules
from risk_refactor_filesystem import run_filesystem_risk_analysis
from risk_refactor_injection import run_injection_risk_analysis
from risk_refactor_resources import run_resource_risk_analysis
from perf_optimizer_memory import run_memory_optimization
from perf_optimizer_caching import run_caching_optimization


# ─────────────────────────────────────────────
# Unified Data Classes
# ─────────────────────────────────────────────

@dataclass
class UnifiedIssue:
    """Universal issue representation across all analyzers."""
    category: str           # SECURITY, PERFORMANCE, RESOURCE, etc.
    issue_type: str         # Specific issue type
    severity: str           # CRITICAL, HIGH, MEDIUM, LOW
    line: int
    description: str
    fix_suggestion: str
    expected_improvement: str = ""


@dataclass
class UnifiedResult:
    """Complete analysis result from all modules."""
    overall_risk_score: int
    overall_perf_score: int
    total_issues: int
    issues: list[UnifiedIssue]
    refactored_code: str
    all_changes: list[dict]
    category_breakdown: dict


# ─────────────────────────────────────────────
# Unified Analysis Pipeline
# ─────────────────────────────────────────────

def refactor_risk_and_performance(source_code: str) -> dict:
    """
    Run comprehensive 5-stage analysis pipeline:
    
    Stage 1: Filesystem security risks
    Stage 2: Injection vulnerabilities  
    Stage 3: Resource leaks & concurrency
    Stage 4: Memory optimization
    Stage 5: Caching & algorithmic optimization
    
    Returns unified results with:
    - Combined risk score (0-100)
    - Combined performance score (0-100)
    - All issues categorized
    - Fully refactored code (all transformations applied)
    - Detailed breakdown by category
    """
    
    all_issues: list[UnifiedIssue] = []
    all_changes: list[dict] = []
    category_breakdown = {}
    
    # ───────────────────────────────────────
    # STAGE 1: Filesystem Security Risks
    # ───────────────────────────────────────
    try:
        fs_result = run_filesystem_risk_analysis(source_code)
        source_code = fs_result.get("refactored_code", source_code)
        
        for issue in fs_result.get("issues", []):
            all_issues.append(UnifiedIssue(
                category="FILESYSTEM_SECURITY",
                issue_type=issue.risk_type,
                severity=issue.severity,
                line=issue.line,
                description=issue.description,
                fix_suggestion=issue.after_suggestion,
                expected_improvement="Prevents file system vulnerabilities"
            ))
        
        all_changes.extend(fs_result.get("changes_applied", []))
        category_breakdown["filesystem"] = {
            "count": len(fs_result.get("issues", [])),
            "risk_score": fs_result.get("risk_score", 0)
        }
    except Exception as e:
        category_breakdown["filesystem"] = {"error": str(e)}

    # ───────────────────────────────────────
    # STAGE 2: Injection Vulnerabilities
    # ───────────────────────────────────────
    try:
        inj_result = run_injection_risk_analysis(source_code)
        source_code = inj_result.get("refactored_code", source_code)
        
        for issue in inj_result.get("issues", []):
            all_issues.append(UnifiedIssue(
                category="INJECTION_SECURITY",
                issue_type=issue.risk_type,
                severity=issue.severity,
                line=issue.line,
                description=issue.description,
                fix_suggestion=issue.after_suggestion,
                expected_improvement="Prevents injection attacks"
            ))
        
        all_changes.extend(inj_result.get("changes_applied", []))
        category_breakdown["injection"] = {
            "count": len(inj_result.get("issues", [])),
            "risk_score": inj_result.get("risk_score", 0)
        }
    except Exception as e:
        category_breakdown["injection"] = {"error": str(e)}

    # ───────────────────────────────────────
    # STAGE 3: Resource Leaks & Concurrency
    # ───────────────────────────────────────
    try:
        res_result = run_resource_risk_analysis(source_code)
        source_code = res_result.get("refactored_code", source_code)
        
        for issue in res_result.get("issues", []):
            all_issues.append(UnifiedIssue(
                category="RESOURCE_SAFETY",
                issue_type=issue.risk_type,
                severity=issue.severity,
                line=issue.line,
                description=issue.description,
                fix_suggestion=issue.after_suggestion,
                expected_improvement="Prevents resource leaks and deadlocks"
            ))
        
        all_changes.extend(res_result.get("changes_applied", []))
        category_breakdown["resources"] = {
            "count": len(res_result.get("issues", [])),
            "risk_score": res_result.get("risk_score", 0)
        }
    except Exception as e:
        category_breakdown["resources"] = {"error": str(e)}

    # ───────────────────────────────────────
    # STAGE 4: Memory Optimization
    # ───────────────────────────────────────
    try:
        mem_result = run_memory_optimization(source_code)
        source_code = mem_result.get("optimized_code", source_code)
        
        for issue in mem_result.get("issues", []):
            all_issues.append(UnifiedIssue(
                category="MEMORY_PERFORMANCE",
                issue_type=issue.issue_type,
                severity=issue.severity,
                line=issue.line,
                description=issue.description,
                fix_suggestion=issue.after_suggestion,
                expected_improvement=issue.expected_improvement
            ))
        
        all_changes.extend(mem_result.get("changes_applied", []))
        category_breakdown["memory"] = {
            "count": len(mem_result.get("issues", [])),
            "perf_score": mem_result.get("perf_score", 0)
        }
    except Exception as e:
        category_breakdown["memory"] = {"error": str(e)}

    # ───────────────────────────────────────
    # STAGE 5: Caching & Algorithmic Optimization
    # ───────────────────────────────────────
    try:
        cache_result = run_caching_optimization(source_code)
        source_code = cache_result.get("optimized_code", source_code)
        
        for issue in cache_result.get("issues", []):
            all_issues.append(UnifiedIssue(
                category="CACHING_PERFORMANCE",
                issue_type=issue.issue_type,
                severity=issue.severity,
                line=issue.line,
                description=issue.description,
                fix_suggestion=issue.after_suggestion,
                expected_improvement=issue.expected_improvement
            ))
        
        all_changes.extend(cache_result.get("changes_applied", []))
        category_breakdown["caching"] = {
            "count": len(cache_result.get("issues", [])),
            "perf_score": cache_result.get("perf_score", 0)
        }
    except Exception as e:
        category_breakdown["caching"] = {"error": str(e)}

    # ───────────────────────────────────────
    # Calculate Overall Scores
    # ───────────────────────────────────────
    SEVERITY_WEIGHTS = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 5}
    
    security_issues = [i for i in all_issues if "SECURITY" in i.category or "RESOURCE" in i.category]
    perf_issues = [i for i in all_issues if "PERFORMANCE" in i.category]
    
    risk_score = min(sum(SEVERITY_WEIGHTS.get(i.severity, 5) for i in security_issues), 100)
    perf_score = min(sum(SEVERITY_WEIGHTS.get(i.severity, 5) for i in perf_issues), 100)

    # ───────────────────────────────────────
    # Build Result
    # ───────────────────────────────────────
    return {
        "overall_risk_score": risk_score,
        "overall_perf_score": perf_score,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "refactored_code": source_code,
        "all_changes": all_changes,
        "category_breakdown": category_breakdown,
        "summary": {
            "critical": sum(1 for i in all_issues if i.severity == "CRITICAL"),
            "high": sum(1 for i in all_issues if i.severity == "HIGH"),
            "medium": sum(1 for i in all_issues if i.severity == "MEDIUM"),
            "low": sum(1 for i in all_issues if i.severity == "LOW"),
        },
        "categories": {
            cat: sum(1 for i in all_issues if i.category == cat)
            for cat in set(i.category for i in all_issues)
        }
    }


# ─────────────────────────────────────────────
# Quick Analysis Functions
# ─────────────────────────────────────────────

def quick_risk_scan(source_code: str) -> dict:
    """
    Run only security risk analysis (stages 1-3).
    Faster than full analysis when performance isn't a concern.
    """
    all_issues = []
    
    try:
        fs = run_filesystem_risk_analysis(source_code)
        all_issues.extend(fs.get("issues", []))
    except:
        pass
    
    try:
        inj = run_injection_risk_analysis(source_code)
        all_issues.extend(inj.get("issues", []))
    except:
        pass
    
    try:
        res = run_resource_risk_analysis(source_code)
        all_issues.extend(res.get("issues", []))
    except:
        pass
    
    SEVERITY_WEIGHTS = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 5}
    risk_score = min(sum(SEVERITY_WEIGHTS.get(getattr(i, 'severity', 'LOW'), 5) for i in all_issues), 100)
    
    return {
        "risk_score": risk_score,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "is_safe": risk_score < 25
    }


def quick_perf_scan(source_code: str) -> dict:
    """
    Run only performance analysis (stages 4-5).
    Faster than full analysis when security isn't a concern.
    """
    all_issues = []
    
    try:
        mem = run_memory_optimization(source_code)
        all_issues.extend(mem.get("issues", []))
    except:
        pass
    
    try:
        cache = run_caching_optimization(source_code)
        all_issues.extend(cache.get("issues", []))
    except:
        pass
    
    SEVERITY_WEIGHTS = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 5}
    perf_score = min(sum(SEVERITY_WEIGHTS.get(getattr(i, 'severity', 'LOW'), 5) for i in all_issues), 100)
    
    return {
        "perf_score": perf_score,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "is_optimized": perf_score < 25
    }


def get_refactored_code(source_code: str) -> str:
    """
    Run full pipeline and return only the refactored code.
    Convenience function for integration.
    """
    result = refactor_risk_and_performance(source_code)
    return result["refactored_code"]


def get_issue_report(source_code: str) -> str:
    """
    Generate a human-readable report of all issues.
    """
    result = refactor_risk_and_performance(source_code)
    
    lines = [
        "=" * 70,
        "UNIFIED CODE ANALYSIS REPORT",
        "=" * 70,
        "",
        f"Overall Risk Score: {result['overall_risk_score']}/100",
        f"Overall Performance Score: {result['overall_perf_score']}/100",
        f"Total Issues Found: {result['total_issues']}",
        "",
        "SEVERITY BREAKDOWN:",
        f"  CRITICAL: {result['summary']['critical']}",
        f"  HIGH:     {result['summary']['high']}",
        f"  MEDIUM:   {result['summary']['medium']}",
        f"  LOW:      {result['summary']['low']}",
        "",
        "CATEGORY BREAKDOWN:",
    ]
    
    for cat, count in result["categories"].items():
        lines.append(f"  {cat}: {count}")
    
    lines.append("")
    lines.append("-" * 70)
    lines.append("DETAILED ISSUES:")
    lines.append("-" * 70)
    
    for i, issue in enumerate(result["issues"], 1):
        lines.extend([
            f"\n[{i}] [{issue.severity}] {issue.issue_type}",
            f"    Category: {issue.category}",
            f"    Line: {issue.line}",
            f"    Description: {issue.description}",
            f"    Fix: {issue.fix_suggestion[:100]}..." if len(issue.fix_suggestion) > 100 else f"    Fix: {issue.fix_suggestion}",
        ])
        if issue.expected_improvement:
            lines.append(f"    Expected Improvement: {issue.expected_improvement}")
    
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    SAMPLE_CODE = '''
import os
import subprocess
import threading
import sqlite3
import requests
import yaml
import pickle

# Security risks
def delete_file(user_path):
    full_path = "/var/data/" + user_path
    os.remove(full_path)

def run_command(cmd):
    os.system(cmd)
    subprocess.run(cmd, shell=True)

def load_config(path):
    with open(path) as f:
        return yaml.load(f)

def load_user(data):
    return pickle.loads(data)

# Resource risks
counter = 0
lock = threading.Lock()

def increment():
    global counter
    lock.acquire()
    counter += 1
    if counter > 100:
        raise ValueError("Too high!")
    lock.release()

def get_data(url):
    response = requests.get(url)
    return response.json()

def query_db(user_id):
    conn = sqlite3.connect("app.db")
    result = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return result.fetchall()

def risky_op():
    try:
        do_something()
    except:
        pass

# Performance issues
class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

def build_csv(items):
    result = ""
    for item in items:
        result += str(item) + ","
    return result

def process_file(path):
    with open(path) as f:
        for line in f.readlines():
            print(line.strip())

valid_codes = [100, 200, 300, 400, 500]

def is_valid(code):
    return code in valid_codes

def total_squares(n):
    return sum([x**2 for x in range(n)])

def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

def process_items(items):
    for i in range(len(items)):
        print(items[i])

def counter_func():
    count = 0
    for x in range(100):
        count = count + 1
    return count

def find_common(list_a, list_b):
    result = []
    for item in list_a:
        for other in list_b:
            if item == other:
                result.append(item)
    return result
'''

    print(get_issue_report(SAMPLE_CODE))
    print("\n\nREFACTORED CODE:")
    print("=" * 70)
    result = refactor_risk_and_performance(SAMPLE_CODE)
    print(result["refactored_code"])
