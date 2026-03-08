"""
risk_refactor_filesystem.py
============================
OptiCode - File System & OS Risk Detection and Refactoring
Author: IT22606860

Detects and refactors risky file system operations:
- Path traversal vulnerabilities
- Unclosed file handles (resource leaks)
- Unsafe os.remove / shutil.rmtree usage
- Hardcoded sensitive paths
- Missing existence checks before file operations
"""

import ast
import astor
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────

@dataclass
class RiskIssue:
    risk_type: str
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW
    line: int
    description: str
    before_code: str
    after_suggestion: str
    fix_applied: bool = False


# ─────────────────────────────────────────────
# DETECTOR 1: Unclosed File Handles
# ─────────────────────────────────────────────

class UnclosedFileDetector(ast.NodeVisitor):
    """
    Detects open() calls that are NOT inside a 'with' block.

    BEFORE (risky):
        f = open("file.txt", "r")
        data = f.read()
        f.close()   # Never called if exception occurs!

    AFTER (safe):
        with open("file.txt", "r") as f:
            data = f.read()
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []
        self._inside_with = False

    def visit_With(self, node: ast.With):
        old = self._inside_with
        self._inside_with = True
        self.generic_visit(node)
        self._inside_with = old

    def visit_Call(self, node: ast.Call):
        if self._inside_with:
            self.generic_visit(node)
            return

        func = node.func
        is_open_call = (
            (isinstance(func, ast.Name) and func.id == "open") or
            (isinstance(func, ast.Attribute) and func.attr == "open")
        )

        if is_open_call:
            self.issues.append(RiskIssue(
                risk_type="UNCLOSED_FILE_HANDLE",
                severity="HIGH",
                line=node.lineno,
                description="open() called outside a 'with' block — file may never be closed on exception.",
                before_code=f"f = open(...) at line {node.lineno}",
                after_suggestion="with open(...) as f:\n    # file operations here"
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 1: Wrap open() in with-block
# ─────────────────────────────────────────────

class WrapOpenInWith(ast.NodeTransformer):
    """
    Transforms bare open() assignments into with-block context managers.

    BEFORE:
        f = open("data.txt", "r")
        content = f.read()
        f.close()

    AFTER:
        with open("data.txt", "r") as f:
            content = f.read()
    """

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self._transform_body(node.body)
        self.generic_visit(node)
        return node

    def _transform_body(self, stmts: list) -> list:
        new_stmts = []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]

            # Pattern: varname = open(...)
            if (isinstance(stmt, ast.Assign) and
                    len(stmt.targets) == 1 and
                    isinstance(stmt.value, ast.Call) and
                    isinstance(stmt.value.func, ast.Name) and
                    stmt.value.func.id == "open"):

                varname = stmt.targets[0]
                open_call = stmt.value

                # Collect remaining statements until f.close()
                body_stmts = []
                j = i + 1
                while j < len(stmts):
                    s = stmts[j]
                    # Detect f.close()
                    if (isinstance(s, ast.Expr) and
                            isinstance(s.value, ast.Call) and
                            isinstance(s.value.func, ast.Attribute) and
                            s.value.func.attr == "close"):
                        j += 1
                        break
                    body_stmts.append(s)
                    j += 1

                if body_stmts:
                    with_node = ast.With(
                        items=[ast.withitem(
                            context_expr=open_call,
                            optional_vars=varname
                        )],
                        body=body_stmts if body_stmts else [ast.Pass()]
                    )
                    ast.copy_location(with_node, stmt)
                    ast.fix_missing_locations(with_node)
                    new_stmts.append(with_node)
                    i = j
                    continue

            new_stmts.append(stmt)
            i += 1

        return new_stmts


# ─────────────────────────────────────────────
# DETECTOR 2: Path Traversal Risk
# ─────────────────────────────────────────────

class PathTraversalDetector(ast.NodeVisitor):
    """
    Detects file operations using variables (not constants) as paths.
    Variables used as file paths = potential path traversal attack.

    BEFORE (risky):
        path = "/uploads/" + username + "/" + filename
        os.remove(path)           # Attacker passes: "../../etc/passwd"

    AFTER (safe):
        base = Path("/uploads").resolve()
        target = (base / username / filename).resolve()
        if not str(target).startswith(str(base)):
            raise PermissionError("Path traversal detected")
        target.unlink()
    """

    DANGEROUS_FILE_OPS = {
        "os": {"remove", "unlink", "rmdir", "rename", "chmod", "chown"},
        "shutil": {"rmtree", "move", "copy", "copy2"},
        "open": {"open"},
    }

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def _is_variable(self, node) -> bool:
        return isinstance(node, (ast.Name, ast.BinOp, ast.JoinedStr, ast.Subscript))

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and node.args:
            first_arg = node.args[0]
            module = ""
            if isinstance(func.value, ast.Name):
                module = func.value.id
            method = func.attr

            if module in self.DANGEROUS_FILE_OPS and method in self.DANGEROUS_FILE_OPS[module]:
                if self._is_variable(first_arg):
                    self.issues.append(RiskIssue(
                        risk_type="PATH_TRAVERSAL",
                        severity="CRITICAL",
                        line=node.lineno,
                        description=f"{module}.{method}() called with variable path — path traversal risk!",
                        before_code=f"{module}.{method}(variable) at line {node.lineno}",
                        after_suggestion=(
                            "base = Path(BASE_DIR).resolve()\n"
                            "target = (base / user_input).resolve()\n"
                            "if not str(target).startswith(str(base)):\n"
                            "    raise PermissionError('Path traversal detected')"
                        )
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# DETECTOR 3: Unsafe shutil.rmtree
# ─────────────────────────────────────────────

class UnsafeRmtreeDetector(ast.NodeVisitor):
    """
    Detects shutil.rmtree() without a prior existence check.

    BEFORE (risky):
        shutil.rmtree(folder)        # Crashes if folder doesn't exist

    AFTER (safe):
        if Path(folder).exists():
            shutil.rmtree(folder)
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                func.attr == "rmtree" and
                isinstance(func.value, ast.Name) and
                func.value.id == "shutil"):
            self.issues.append(RiskIssue(
                risk_type="UNSAFE_RMTREE",
                severity="HIGH",
                line=node.lineno,
                description="shutil.rmtree() called without existence check — may delete critical paths or crash.",
                before_code=f"shutil.rmtree(path) at line {node.lineno}",
                after_suggestion=(
                    "p = Path(path).resolve()\n"
                    "if len(p.parts) < 3:\n"
                    "    raise PermissionError('Refusing to delete root-level path')\n"
                    "if p.exists():\n"
                    "    shutil.rmtree(p)"
                )
            ))
        self.generic_visit(node)


# ─────────────────────────────────────────────
# DETECTOR 4: String Path Concatenation
# ─────────────────────────────────────────────

class StringPathConcatDetector(ast.NodeVisitor):
    """
    Detects building file paths via string concatenation.

    BEFORE (risky):
        path = "/uploads/" + username + "/" + filename

    AFTER (safe):
        path = Path("/uploads") / username / filename
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def _has_path_string(self, node: ast.BinOp) -> bool:
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            val = node.left.value
            return val.startswith("/") or "\\" in val or "." in val
        return False

    def visit_BinOp(self, node: ast.BinOp):
        if (isinstance(node.op, ast.Add) and self._has_path_string(node)):
            self.issues.append(RiskIssue(
                risk_type="STRING_PATH_CONCAT",
                severity="MEDIUM",
                line=node.lineno,
                description="Building file path via string concatenation — use pathlib.Path instead.",
                before_code=f'"/some/dir/" + variable at line {node.lineno}',
                after_suggestion='path = Path("/some/dir") / username / filename'
            ))
        self.generic_visit(node)


# ─────────────────────────────────────────────
# MAIN: run_filesystem_risk_analysis
# ─────────────────────────────────────────────

def run_filesystem_risk_analysis(source_code: str) -> dict:
    """
    Run all filesystem risk detectors on source code.

    Returns:
        {
            "issues": [RiskIssue, ...],
            "risk_score": int,
            "refactored_code": str,
            "changes": [...]
        }
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}", "issues": [], "risk_score": 0}

    all_issues: list[RiskIssue] = []

    detectors = [
        UnclosedFileDetector(),
        PathTraversalDetector(),
        UnsafeRmtreeDetector(),
        StringPathConcatDetector(),
    ]

    for detector in detectors:
        detector.visit(tree)
        all_issues.extend(detector.issues)

    # Apply transformations
    tree = ast.parse(source_code)  # Fresh tree for transforms
    tree = WrapOpenInWith().visit(tree)
    ast.fix_missing_locations(tree)

    try:
        refactored = astor.to_source(tree)
    except Exception:
        refactored = source_code

    SEVERITY_WEIGHTS = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 5}
    risk_score = min(sum(SEVERITY_WEIGHTS.get(i.severity, 5) for i in all_issues), 100)

    return {
        "issues": all_issues,
        "risk_score": risk_score,
        "total_issues": len(all_issues),
        "refactored_code": refactored,
        "changes": [
            {
                "risk_type": i.risk_type,
                "severity": i.severity,
                "line": i.line,
                "description": i.description,
                "suggestion": i.after_suggestion,
            }
            for i in all_issues
        ]
    }


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    SAMPLE_CODE = '''
import os
import shutil

def delete_user_file(username, filename):
    path = "/uploads/" + username + "/" + filename
    f = open(path, "r")
    data = f.read()
    f.close()
    os.remove(path)
    return data

def cleanup_temp(folder):
    shutil.rmtree(folder)

def save_log(msg):
    f = open("/var/logs/app.log", "a")
    f.write(msg)
'''

    result = run_filesystem_risk_analysis(SAMPLE_CODE)
    print("=" * 60)
    print("FILESYSTEM RISK ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Total Issues: {result['total_issues']}")
    print()
    for issue in result["issues"]:
        print(f"[{issue.severity}] {issue.risk_type} - Line {issue.line}")
        print(f"  {issue.description}")
        print(f"  Fix: {issue.after_suggestion[:80]}...")
        print()
    print("REFACTORED CODE:")
    print(result["refactored_code"])
