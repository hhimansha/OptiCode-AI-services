"""
risk_refactor_injection.py
===========================
OptiCode - Injection Risk Detection and Refactoring
Author: IT22606860

Detects and refactors injection vulnerabilities:
- Shell injection via os.system / subprocess shell=True
- SQL injection via f-string or string concat in queries
- Code injection via eval() / exec() / __import__()
- YAML code execution via yaml.load (without SafeLoader)
- Pickle remote code execution via pickle.loads
"""

import ast
import astor
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────

@dataclass
class RiskIssue:
    risk_type: str
    severity: str
    line: int
    description: str
    before_code: str
    after_suggestion: str


# ─────────────────────────────────────────────
# DETECTOR 1: Shell Injection
# ─────────────────────────────────────────────

class ShellInjectionDetector(ast.NodeVisitor):
    """
    Detects dangerous shell execution patterns.

    BEFORE (risky):
        os.system("ping " + ip)           # Shell injection!
        subprocess.call(cmd, shell=True)  # Always dangerous with variables
        os.popen(f"grep {keyword} log")   # F-string = injection

    AFTER (safe):
        subprocess.run(["ping", "-c", "4", ip], shell=False, timeout=10)
    """

    # (module, method) pairs that are dangerous
    DANGEROUS_CALLS = {
        ("os", "system"),
        ("os", "popen"),
        ("os", "startfile"),
        ("commands", "getoutput"),
        ("commands", "getstatusoutput"),
    }

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def _is_dynamic(self, node) -> bool:
        """Returns True if argument is not a plain string constant."""
        return not isinstance(node, ast.Constant)

    def _check_subprocess_shell_true(self, node: ast.Call):
        """Detect subprocess.* called with shell=True."""
        func = node.func
        if not (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "subprocess"):
            return

        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                # Extra danger if first arg is dynamic
                first_arg = node.args[0] if node.args else None
                severity = "CRITICAL" if (first_arg and self._is_dynamic(first_arg)) else "HIGH"
                self.issues.append(RiskIssue(
                    risk_type="SHELL_INJECTION",
                    severity=severity,
                    line=node.lineno,
                    description=f"subprocess.{func.attr}() called with shell=True — shell injection risk.",
                    before_code=f"subprocess.{func.attr}(cmd, shell=True) at line {node.lineno}",
                    after_suggestion=(
                        "subprocess.run(\n"
                        "    ['command', 'arg1', user_input],  # List args, never string\n"
                        "    shell=False,   # Critical!\n"
                        "    timeout=30,\n"
                        "    capture_output=True\n"
                        ")"
                    )
                ))

    def visit_Call(self, node: ast.Call):
        func = node.func

        # Check os.system / os.popen etc.
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module = func.value.id
            method = func.attr
            if (module, method) in self.DANGEROUS_CALLS:
                first_arg = node.args[0] if node.args else None
                severity = "CRITICAL" if (first_arg and self._is_dynamic(first_arg)) else "HIGH"
                self.issues.append(RiskIssue(
                    risk_type="SHELL_INJECTION",
                    severity=severity,
                    line=node.lineno,
                    description=f"{module}.{method}() is dangerous — use subprocess.run() with shell=False.",
                    before_code=f"{module}.{method}(...) at line {node.lineno}",
                    after_suggestion=(
                        "import subprocess\n"
                        "subprocess.run(['cmd', arg], shell=False, timeout=10, check=True)"
                    )
                ))

        # Check subprocess shell=True
        self._check_subprocess_shell_true(node)

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 1: Replace os.system with subprocess
# ─────────────────────────────────────────────

class ReplaceOsSystem(ast.NodeTransformer):
    """
    Transforms os.system(string) calls to subprocess.run() with shell=False.
    Only transforms calls with constant string arguments (safe to split).

    BEFORE:
        os.system("ls -la /tmp")

    AFTER:
        subprocess.run(['ls', '-la', '/tmp'], shell=False, check=True)
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "os" and
                func.attr == "system" and
                node.args and
                isinstance(node.args[0], ast.Constant)):

            cmd_str = node.args[0].value
            parts = cmd_str.split()
            list_node = ast.List(
                elts=[ast.Constant(value=p) for p in parts],
                ctx=ast.Load()
            )

            new_call = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="subprocess", ctx=ast.Load()),
                    attr="run",
                    ctx=ast.Load()
                ),
                args=[list_node],
                keywords=[
                    ast.keyword(arg="shell", value=ast.Constant(value=False)),
                    ast.keyword(arg="check", value=ast.Constant(value=True)),
                ]
            )
            ast.copy_location(new_call, node)
            ast.fix_missing_locations(new_call)
            self.changes.append({
                "pattern": "REPLACE_OS_SYSTEM",
                "line": node.lineno,
                "before": f"os.system('{cmd_str}')",
                "after": f"subprocess.run({parts}, shell=False, check=True)"
            })
            return new_call

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 2: SQL Injection
# ─────────────────────────────────────────────

class SQLInjectionDetector(ast.NodeVisitor):
    """
    Detects SQL queries built via f-strings or string concatenation.

    BEFORE (risky):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute("DELETE FROM " + table + " WHERE id = " + str(record_id))

    AFTER (safe):
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    """

    SQL_KEYWORDS = {"SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"}

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def _contains_sql(self, value: str) -> bool:
        upper = value.upper()
        return any(kw in upper for kw in self.SQL_KEYWORDS)

    def _check_fstring_sql(self, node: ast.JoinedStr, lineno: int):
        """Check f-strings that look like SQL queries."""
        parts = [p.value for p in node.values if isinstance(p, ast.Constant) and isinstance(p.value, str)]
        combined = "".join(parts)
        if self._contains_sql(combined):
            self.issues.append(RiskIssue(
                risk_type="SQL_INJECTION",
                severity="CRITICAL",
                line=lineno,
                description="SQL query built using f-string with variable substitution — SQL injection risk!",
                before_code=f'f"SELECT ... {{user_var}}" at line {lineno}',
                after_suggestion=(
                    '# Use parameterized queries:\n'
                    'cursor.execute("SELECT * FROM table WHERE id = ?", (user_id,))\n'
                    '# OR with psycopg2:\n'
                    'cursor.execute("SELECT * FROM table WHERE id = %s", (user_id,))'
                )
            ))

    def _check_concat_sql(self, node: ast.BinOp, lineno: int):
        """Check string concatenation that looks like SQL."""
        if isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                if self._contains_sql(node.left.value):
                    self.issues.append(RiskIssue(
                        risk_type="SQL_INJECTION",
                        severity="CRITICAL",
                        line=lineno,
                        description="SQL query built via string concatenation — SQL injection risk!",
                        before_code=f'"SELECT ... " + variable at line {lineno}',
                        after_suggestion='cursor.execute("SELECT ... WHERE col = ?", (value,))'
                    ))

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.JoinedStr):
            self._check_fstring_sql(node.value, node.lineno)
        elif isinstance(node.value, ast.BinOp):
            self._check_concat_sql(node.value, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Also check when SQL is passed directly to execute()."""
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"execute", "executemany"}:
            if node.args:
                first = node.args[0]
                if isinstance(first, ast.JoinedStr):
                    self._check_fstring_sql(first, node.lineno)
                elif isinstance(first, ast.BinOp):
                    self._check_concat_sql(first, node.lineno)
        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 2: Remove shell=True from subprocess
# ─────────────────────────────────────────────

class RemoveShellTrue(ast.NodeTransformer):
    """
    Transforms subprocess calls to use shell=False (where the command is a constant).

    BEFORE:
        subprocess.run("ls -la", shell=True)

    AFTER:
        subprocess.run(['ls', '-la'], shell=False)
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if not (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "subprocess"):
            self.generic_visit(node)
            return node

        has_shell_true = any(
            kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
        )

        if has_shell_true and node.args and isinstance(node.args[0], ast.Constant):
            # Convert string command to list
            cmd_str = node.args[0].value
            parts = cmd_str.split()
            node.args[0] = ast.List(
                elts=[ast.Constant(value=p) for p in parts],
                ctx=ast.Load()
            )

            # Change shell=True to shell=False
            for kw in node.keywords:
                if kw.arg == "shell":
                    kw.value = ast.Constant(value=False)

            ast.fix_missing_locations(node)
            self.changes.append({
                "pattern": "REMOVE_SHELL_TRUE",
                "line": node.lineno,
                "before": f"subprocess.{func.attr}('{cmd_str}', shell=True)",
                "after": f"subprocess.{func.attr}({parts}, shell=False)"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 3: eval / exec / __import__
# ─────────────────────────────────────────────

class EvalExecDetector(ast.NodeVisitor):
    """
    Detects usage of eval(), exec(), and __import__() with variable arguments.

    BEFORE (risky):
        result = eval(user_input)
        exec(user_code)
        mod = __import__(user_module)

    AFTER (safe):
        # Use ast.literal_eval for safe expression evaluation
        import ast as ast_safe
        result = ast_safe.literal_eval(user_input)
    """

    DANGEROUS_BUILTINS = {"eval", "exec", "__import__", "compile"}

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func

        if isinstance(func, ast.Name) and func.id in self.DANGEROUS_BUILTINS:
            first_arg = node.args[0] if node.args else None
            is_dynamic = first_arg and not isinstance(first_arg, ast.Constant)
            severity = "CRITICAL" if is_dynamic else "HIGH"

            self.issues.append(RiskIssue(
                risk_type="CODE_INJECTION",
                severity=severity,
                line=node.lineno,
                description=f"{func.id}() can execute arbitrary code — code injection risk!",
                before_code=f"{func.id}(user_input) at line {node.lineno}",
                after_suggestion=(
                    "# For math expressions:\n"
                    "import ast as ast_safe\n"
                    "result = ast_safe.literal_eval(expr)  # Only allows literals\n\n"
                    "# For configuration: use json.loads() instead of eval()"
                )
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# DETECTOR 4: Unsafe yaml.load
# ─────────────────────────────────────────────

class UnsafeYamlDetector(ast.NodeVisitor):
    """
    Detects yaml.load() without Loader=yaml.SafeLoader.

    BEFORE (risky):
        config = yaml.load(file_obj)           # Can execute arbitrary code!
        config = yaml.load(f, Loader=yaml.Loader)  # Also unsafe!

    AFTER (safe):
        config = yaml.safe_load(file_obj)
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "yaml" and
                func.attr == "load"):

            # Check if it uses SafeLoader
            uses_safe_loader = False
            for kw in node.keywords:
                if kw.arg == "Loader":
                    if (isinstance(kw.value, ast.Attribute) and
                            kw.value.attr in {"SafeLoader", "BaseLoader"}):
                        uses_safe_loader = True

            if not uses_safe_loader:
                self.issues.append(RiskIssue(
                    risk_type="UNSAFE_YAML_LOAD",
                    severity="HIGH",
                    line=node.lineno,
                    description="yaml.load() without SafeLoader can execute arbitrary Python code via YAML tags.",
                    before_code=f"yaml.load(data) at line {node.lineno}",
                    after_suggestion="yaml.safe_load(data)  # safe_load disables dangerous YAML tags"
                ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 3: Replace yaml.load with yaml.safe_load
# ─────────────────────────────────────────────

class ReplaceUnsafeYaml(ast.NodeTransformer):
    """
    Replaces yaml.load() with yaml.safe_load().

    BEFORE:
        config = yaml.load(f)

    AFTER:
        config = yaml.safe_load(f)
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "yaml" and
                func.attr == "load"):

            # Check not already safe
            for kw in node.keywords:
                if kw.arg == "Loader":
                    if (isinstance(kw.value, ast.Attribute) and
                            kw.value.attr in {"SafeLoader", "BaseLoader"}):
                        self.generic_visit(node)
                        return node

            # Replace with safe_load and remove Loader kwarg
            func.attr = "safe_load"
            node.keywords = [kw for kw in node.keywords if kw.arg != "Loader"]
            ast.fix_missing_locations(node)
            self.changes.append({
                "pattern": "REPLACE_YAML_LOAD",
                "line": node.lineno,
                "before": "yaml.load(data)",
                "after": "yaml.safe_load(data)"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 5: Unsafe pickle.loads
# ─────────────────────────────────────────────

class PickleDetector(ast.NodeVisitor):
    """
    Detects pickle.loads() usage — can execute arbitrary code on deserialize.

    BEFORE (risky):
        obj = pickle.loads(untrusted_data)   # Remote code execution!

    AFTER (safe):
        import json
        obj = json.loads(untrusted_data)     # Safe alternative
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id in {"pickle", "cPickle", "marshal"} and
                func.attr in {"loads", "load"}):
            self.issues.append(RiskIssue(
                risk_type="UNSAFE_DESERIALIZATION",
                severity="CRITICAL",
                line=node.lineno,
                description=f"{func.value.id}.{func.attr}() on untrusted data allows remote code execution.",
                before_code=f"{func.value.id}.{func.attr}(data) at line {node.lineno}",
                after_suggestion=(
                    "# Use JSON for safe serialization:\n"
                    "import json\n"
                    "obj = json.loads(data)  # Safe — no code execution\n\n"
                    "# If pickle MUST be used, verify HMAC signature first:\n"
                    "import hmac, hashlib\n"
                    "expected_sig = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()\n"
                    "if not hmac.compare_digest(expected_sig, received_sig):\n"
                    "    raise ValueError('Invalid signature!')\n"
                    "obj = pickle.loads(data)"
                )
            ))
        self.generic_visit(node)


# ─────────────────────────────────────────────
# MAIN: run_injection_risk_analysis
# ─────────────────────────────────────────────

def run_injection_risk_analysis(source_code: str) -> dict:
    """
    Run all injection risk detectors and transformers on source code.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": str(e), "issues": [], "risk_score": 0}

    all_issues: list[RiskIssue] = []

    detectors = [
        ShellInjectionDetector(),
        SQLInjectionDetector(),
        EvalExecDetector(),
        UnsafeYamlDetector(),
        PickleDetector(),
    ]

    for d in detectors:
        d.visit(tree)
        all_issues.extend(d.issues)

    # Apply safe transformations
    tree = ast.parse(source_code)
    transformers = [
        ReplaceOsSystem(),
        RemoveShellTrue(),
        ReplaceUnsafeYaml(),
    ]

    all_changes = []
    for transformer in transformers:
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)
        all_changes.extend(transformer.changes)

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
        "changes_applied": all_changes,
        "suggestions": [
            {
                "risk_type": i.risk_type,
                "severity": i.severity,
                "line": i.line,
                "description": i.description,
                "fix": i.after_suggestion
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
import subprocess
import yaml
import pickle

def run_scan(ip_address):
    os.system("ping " + ip_address)

def search_logs(keyword):
    cmd = f"grep {keyword} /var/log/app.log"
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return result.communicate()[0]

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

def load_config(path):
    with open(path) as f:
        return yaml.load(f)

def load_session(data):
    return pickle.loads(data)

def run_expr(user_input):
    return eval(user_input)
'''

    result = run_injection_risk_analysis(SAMPLE_CODE)
    print("=" * 60)
    print("INJECTION RISK ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Total Issues: {result['total_issues']}")
    print()
    for issue in result["issues"]:
        print(f"[{issue.severity}] {issue.risk_type} - Line {issue.line}")
        print(f"  {issue.description}")
        print()
    print("REFACTORED CODE:")
    print(result["refactored_code"])
