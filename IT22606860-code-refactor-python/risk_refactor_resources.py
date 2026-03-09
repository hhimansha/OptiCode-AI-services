"""
risk_refactor_resources.py
===========================
OptiCode - Resource Leak, Concurrency & Memory Safety Refactoring
Author: IT22606860

Detects and refactors:
- Thread lock acquire without release (deadlock / leak)
- Database connections not in context managers
- Circular reference memory leaks
- Race conditions on global state
- Bare except clauses that swallow errors silently
- Missing timeout on blocking calls
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
    severity: str
    line: int
    description: str
    before_code: str
    after_suggestion: str


# ─────────────────────────────────────────────
# DETECTOR 1: Lock Acquire Without With
# ─────────────────────────────────────────────

class LockAcquireDetector(ast.NodeVisitor):
    """
    Detects threading.Lock().acquire() called outside a 'with' block.
    Supports both regular variables (lock.acquire()) and instance attributes (self.lock.acquire()).

    BEFORE (risky):
        self.lock = threading.Lock()
        self.lock.acquire()
        shared_resource.update()   # If this raises, lock NEVER released!
        self.lock.release()

    AFTER (safe):
        self.lock = threading.Lock()
        with self.lock:
            shared_resource.update()  # Lock always released via __exit__
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []
        self._inside_with = False
        self._lock_names: set[str] = set()  # Simple names like 'lock'
        self._lock_attrs: set[str] = set()  # Attribute names like 'lock' in self.lock

    def visit_Assign(self, node: ast.Assign):
        """Track variable names assigned to threading.Lock()."""
        if (isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Attribute) and
                node.value.func.attr in {"Lock", "RLock", "Semaphore", "Event"}):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._lock_names.add(target.id)
                # Handle self.lock = threading.Lock()
                elif isinstance(target, ast.Attribute):
                    self._lock_attrs.add(target.attr)
        self.generic_visit(node)

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
        
        # Check for lock.acquire() - simple variable
        if (isinstance(func, ast.Attribute) and
                func.attr == "acquire" and
                isinstance(func.value, ast.Name) and
                func.value.id in self._lock_names):
            lock_name = func.value.id
            self.issues.append(RiskIssue(
                risk_type="LOCK_NOT_RELEASED",
                severity="HIGH",
                line=node.lineno,
                description=(
                    f"'{lock_name}.acquire()' called outside 'with' block. "
                    "Lock may never be released if an exception occurs (deadlock risk)."
                ),
                before_code=f"{lock_name}.acquire() at line {node.lineno}",
                after_suggestion=(
                    f"with {lock_name}:\n"
                    "    # critical section here\n"
                    "    # lock automatically released even on exception"
                )
            ))
        
        # Check for self.lock.acquire() - instance attribute
        elif (isinstance(func, ast.Attribute) and
                func.attr == "acquire" and
                isinstance(func.value, ast.Attribute) and
                func.value.attr in self._lock_attrs):
            # Get the full attribute chain (e.g., "self.lock")
            if isinstance(func.value.value, ast.Name):
                obj_name = func.value.value.id
                lock_attr = func.value.attr
                full_name = f"{obj_name}.{lock_attr}"
                self.issues.append(RiskIssue(
                    risk_type="LOCK_NOT_RELEASED",
                    severity="HIGH",
                    line=node.lineno,
                    description=(
                        f"'{full_name}.acquire()' called outside 'with' block. "
                        "Lock may never be released if an exception occurs (deadlock risk)."
                    ),
                    before_code=f"{full_name}.acquire() at line {node.lineno}",
                    after_suggestion=(
                        f"with {full_name}:\n"
                        "    # critical section here\n"
                        "    # lock automatically released even on exception"
                    )
                ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 1: Convert lock.acquire/release to with block
# ─────────────────────────────────────────────

class ConvertLockToWith(ast.NodeTransformer):
    """
    Transforms lock.acquire() ... lock.release() patterns into with-blocks.
    Supports both simple variables (lock) and instance attributes (self.lock).

    BEFORE:
        self.lock.acquire()
        do_work()
        self.lock.release()

    AFTER:
        with self.lock:
            do_work()
    """

    def __init__(self):
        self.changes: list[dict] = []
        self._lock_names: set[str] = set()  # Simple: 'lock'
        self._lock_attrs: set[str] = set()  # Attribute: 'lock' from self.lock

    def visit_Module(self, node: ast.Module):
        # First pass: collect lock variable names
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                if (isinstance(stmt.value, ast.Call) and
                        isinstance(stmt.value.func, ast.Attribute) and
                        stmt.value.func.attr in {"Lock", "RLock", "Semaphore"}):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            self._lock_names.add(t.id)
                        # Handle self.lock = threading.Lock()
                        elif isinstance(t, ast.Attribute):
                            self._lock_attrs.add(t.attr)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self._rewrite_body(node.body)
        self.generic_visit(node)
        return node

    def _get_lock_expr(self, stmt):
        """
        Check if stmt is an acquire() call. Returns (lock_ast_node, lock_name_str) or (None, None).
        Handles both 'lock.acquire()' and 'self.lock.acquire()'.
        """
        if not (isinstance(stmt, ast.Expr) and
                isinstance(stmt.value, ast.Call) and
                isinstance(stmt.value.func, ast.Attribute) and
                stmt.value.func.attr == "acquire"):
            return None, None
        
        func_value = stmt.value.func.value
        
        # Simple variable: lock.acquire()
        if isinstance(func_value, ast.Name) and func_value.id in self._lock_names:
            return func_value, func_value.id
        
        # Instance attribute: self.lock.acquire()
        if (isinstance(func_value, ast.Attribute) and
                func_value.attr in self._lock_attrs and
                isinstance(func_value.value, ast.Name)):
            return func_value, f"{func_value.value.id}.{func_value.attr}"
        
        return None, None

    def _is_release(self, stmt, lock_expr) -> bool:
        """Check if stmt is release() for the given lock expression."""
        if not (isinstance(stmt, ast.Expr) and
                isinstance(stmt.value, ast.Call) and
                isinstance(stmt.value.func, ast.Attribute) and
                stmt.value.func.attr == "release"):
            return False
        
        func_value = stmt.value.func.value
        
        # Simple variable: lock.release()
        if isinstance(lock_expr, ast.Name):
            return (isinstance(func_value, ast.Name) and
                    func_value.id == lock_expr.id)
        
        # Instance attribute: self.lock.release()
        if isinstance(lock_expr, ast.Attribute):
            return (isinstance(func_value, ast.Attribute) and
                    func_value.attr == lock_expr.attr and
                    isinstance(func_value.value, ast.Name) and
                    isinstance(lock_expr.value, ast.Name) and
                    func_value.value.id == lock_expr.value.id)
        
        return False

    def _rewrite_body(self, stmts: list) -> list:
        new_stmts = []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            lock_expr, lock_name = self._get_lock_expr(stmt)

            if lock_expr is not None:
                body = []
                j = i + 1
                while j < len(stmts):
                    if self._is_release(stmts[j], lock_expr):
                        j += 1
                        break
                    body.append(stmts[j])
                    j += 1

                # Create the context_expr for the with statement
                if isinstance(lock_expr, ast.Name):
                    context_expr = ast.Name(id=lock_expr.id, ctx=ast.Load())
                else:  # ast.Attribute (self.lock)
                    context_expr = ast.Attribute(
                        value=ast.Name(id=lock_expr.value.id, ctx=ast.Load()),
                        attr=lock_expr.attr,
                        ctx=ast.Load()
                    )
                
                with_node = ast.With(
                    items=[ast.withitem(
                        context_expr=context_expr,
                        optional_vars=None
                    )],
                    body=body if body else [ast.Pass()]
                )
                ast.copy_location(with_node, stmt)
                ast.fix_missing_locations(with_node)
                new_stmts.append(with_node)
                self.changes.append({
                    "pattern": "LOCK_TO_WITH_BLOCK",
                    "line": stmt.lineno,
                    "before": f"{lock_name}.acquire() ... {lock_name}.release()",
                    "after": f"with {lock_name}: ..."
                })
                i = j
            else:
                new_stmts.append(stmt)
                i += 1

        return new_stmts


# ─────────────────────────────────────────────
# DETECTOR 2: Race Condition on Global State
# ─────────────────────────────────────────────

class RaceConditionDetector(ast.NodeVisitor):
    """
    Detects global variable mutation inside functions (without locks).

    BEFORE (risky):
        counter = 0
        def increment():
            global counter
            counter += 1     # Race condition in multi-threaded code!

    AFTER (safe):
        class ThreadSafeCounter:
            def __init__(self):
                self._value = 0
                self._lock = threading.Lock()
            def increment(self):
                with self._lock:
                    self._value += 1
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []
        self._global_vars: set[str] = set()

    def visit_Global(self, node: ast.Global):
        for name in node.names:
            self._global_vars.add(name)
        self.issues.append(RiskIssue(
            risk_type="RACE_CONDITION",
            severity="MEDIUM",
            line=node.lineno,
            description=(
                f"Global variable(s) {node.names} mutated inside function. "
                "This is NOT thread-safe — use threading.Lock() or a thread-safe class."
            ),
            before_code=f"global {', '.join(node.names)} at line {node.lineno}",
            after_suggestion=(
                "class ThreadSafeCounter:\n"
                "    def __init__(self):\n"
                "        self._value = 0\n"
                "        self._lock = threading.Lock()\n"
                "    def increment(self):\n"
                "        with self._lock:\n"
                "            self._value += 1\n"
                "            return self._value"
            )
        ))
        self.generic_visit(node)


# ─────────────────────────────────────────────
# DETECTOR 3: Bare Except Clause
# ─────────────────────────────────────────────

class BareExceptDetector(ast.NodeVisitor):
    """
    Detects bare 'except:' or 'except Exception:' with just 'pass' body.

    BEFORE (risky):
        try:
            risky_operation()
        except:
            pass    # Silently swallows ALL errors including KeyboardInterrupt!

    AFTER (safe):
        try:
            risky_operation()
        except SpecificError as e:
            logger.error(f"Operation failed: {e}")
            raise  # Or handle appropriately
    """

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        is_bare = node.type is None
        is_pass_only = (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))

        if is_bare:
            self.issues.append(RiskIssue(
                risk_type="BARE_EXCEPT",
                severity="HIGH",
                line=node.lineno,
                description=(
                    "Bare 'except:' clause catches ALL exceptions including "
                    "KeyboardInterrupt and SystemExit — hides real errors."
                ),
                before_code=f"except: at line {node.lineno}",
                after_suggestion=(
                    "except (ValueError, TypeError) as e:\n"
                    "    logger.error(f'Specific error: {e}')\n"
                    "    # Handle or re-raise appropriately"
                )
            ))
        elif is_pass_only:
            exc_name = getattr(node.type, "id", "Exception") if isinstance(node.type, ast.Name) else "Exception"
            self.issues.append(RiskIssue(
                risk_type="SILENT_EXCEPTION",
                severity="MEDIUM",
                line=node.lineno,
                description=(
                    f"'except {exc_name}: pass' silently swallows errors. "
                    "Errors should be logged at minimum."
                ),
                before_code=f"except {exc_name}: pass at line {node.lineno}",
                after_suggestion=(
                    f"except {exc_name} as e:\n"
                    "    logger.warning(f'Caught error: {e}')\n"
                    "    # Add appropriate handling"
                )
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 2: Replace bare except with specific
# ─────────────────────────────────────────────

class FixBareExcept(ast.NodeTransformer):
    """
    Converts bare 'except:' to 'except Exception as e:' with a logging placeholder.

    BEFORE:
        except:
            pass

    AFTER:
        except Exception as e:
            # TODO: Add proper error handling
            raise
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            node.type = ast.Name(id="Exception", ctx=ast.Load())
            node.name = "e"
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                node.body = [
                    ast.Expr(value=ast.Constant(value="# TODO: Add proper error handling")),
                    ast.Raise()
                ]
            ast.fix_missing_locations(node)
            self.changes.append({
                "pattern": "FIX_BARE_EXCEPT",
                "line": node.lineno,
                "before": "except:",
                "after": "except Exception as e: raise"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 4: DB Connection Outside Context Manager
# ─────────────────────────────────────────────

class DBConnectionLeakDetector(ast.NodeVisitor):
    """
    Detects database connections not wrapped in context managers.

    BEFORE (risky):
        conn = psycopg2.connect(dsn)
        data = conn.execute("SELECT ...").fetchall()
        # If exception occurs, conn is never closed!

    AFTER (safe):
        with psycopg2.connect(dsn) as conn:
            data = conn.execute("SELECT ...").fetchall()
    """

    DB_CONNECT_CALLS = {
        ("psycopg2", "connect"),
        ("sqlite3", "connect"),
        ("pymysql", "connect"),
        ("pyodbc", "connect"),
        ("cx_Oracle", "connect"),
        ("motor", "AsyncIOMotorClient"),
        ("pymongo", "MongoClient"),
    }

    def __init__(self):
        self.issues: list[RiskIssue] = []
        self._inside_with = False

    def visit_With(self, node: ast.With):
        old = self._inside_with
        self._inside_with = True
        self.generic_visit(node)
        self._inside_with = old

    def visit_Assign(self, node: ast.Assign):
        if self._inside_with:
            self.generic_visit(node)
            return

        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if (func.value.id, func.attr) in self.DB_CONNECT_CALLS:
                    self.issues.append(RiskIssue(
                        risk_type="DB_CONNECTION_LEAK",
                        severity="HIGH",
                        line=node.lineno,
                        description=(
                            f"{func.value.id}.{func.attr}() assigned outside context manager. "
                            "Connection may never be closed if exception occurs."
                        ),
                        before_code=f"conn = {func.value.id}.{func.attr}(...) at line {node.lineno}",
                        after_suggestion=(
                            f"with {func.value.id}.{func.attr}(...) as conn:\n"
                            "    # all DB operations here\n"
                            "    # connection auto-closed on exit"
                        )
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 4: Wrap DB connection in with-block
# ─────────────────────────────────────────────

class WrapDBConnectionInWith(ast.NodeTransformer):
    """
    Transforms db.connect() assignments into with-blocks.

    BEFORE:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    AFTER:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
    """

    DB_CONNECT_CALLS = {
        ("psycopg2", "connect"),
        ("sqlite3", "connect"),
        ("pymysql", "connect"),
        ("pyodbc", "connect"),
        ("cx_Oracle", "connect"),
    }

    def __init__(self):
        self.changes: list[dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self._transform_body(node.body)
        self.generic_visit(node)
        return node

    def _transform_body(self, stmts: list) -> list:
        new_stmts = []
        i = 0
        while i < len(stmts):
            stmt = stmts[i]

            # Pattern: conn = db.connect(...) - only for local variables, NOT self.conn
            if (isinstance(stmt, ast.Assign) and
                    len(stmt.targets) == 1 and
                    isinstance(stmt.targets[0], ast.Name) and  # Only local vars (not self.conn)
                    isinstance(stmt.value, ast.Call) and
                    isinstance(stmt.value.func, ast.Attribute) and
                    isinstance(stmt.value.func.value, ast.Name)):
                
                func = stmt.value.func
                if (func.value.id, func.attr) in self.DB_CONNECT_CALLS:
                    varname = stmt.targets[0]
                    connect_call = stmt.value
                    db_module = func.value.id

                    # Collect remaining statements until conn.close() or end of function
                    body_stmts = []
                    j = i + 1
                    while j < len(stmts):
                        s = stmts[j]
                        # Detect conn.close()
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
                                context_expr=connect_call,
                                optional_vars=varname
                            )],
                            body=body_stmts
                        )
                        ast.copy_location(with_node, stmt)
                        ast.fix_missing_locations(with_node)
                        new_stmts.append(with_node)
                        self.changes.append({
                            "pattern": "DB_CONN_TO_WITH_BLOCK",
                            "line": stmt.lineno,
                            "before": f"conn = {db_module}.{func.attr}(...)",
                            "after": f"with {db_module}.{func.attr}(...) as conn: ..."
                        })
                        i = j
                        continue

            new_stmts.append(stmt)
            i += 1

        return new_stmts


# ─────────────────────────────────────────────
# DETECTOR 5: Missing Timeout on Blocking Calls
# ─────────────────────────────────────────────

class MissingTimeoutDetector(ast.NodeVisitor):
    """
    Detects blocking calls that don't specify a timeout parameter.

    BEFORE (risky):
        requests.get("https://api.example.com/data")    # Blocks forever!
        subprocess.run(["cmd"])                          # Blocks forever!
        socket.recv(1024)                                # Blocks forever!

    AFTER (safe):
        requests.get("https://api.example.com/data", timeout=10)
        subprocess.run(["cmd"], timeout=30)
    """

    CALLS_NEEDING_TIMEOUT = {
        ("requests", "get"),
        ("requests", "post"),
        ("requests", "put"),
        ("requests", "delete"),
        ("requests", "patch"),
        ("requests", "head"),
        ("subprocess", "run"),
        ("subprocess", "call"),
        ("subprocess", "check_output"),
    }

    def __init__(self):
        self.issues: list[RiskIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            key = (func.value.id, func.attr)
            if key in self.CALLS_NEEDING_TIMEOUT:
                has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
                if not has_timeout:
                    self.issues.append(RiskIssue(
                        risk_type="MISSING_TIMEOUT",
                        severity="MEDIUM",
                        line=node.lineno,
                        description=(
                            f"{func.value.id}.{func.attr}() called without timeout — "
                            "can block forever if remote server hangs."
                        ),
                        before_code=f"{func.value.id}.{func.attr}(...) at line {node.lineno}",
                        after_suggestion=(
                            f"{func.value.id}.{func.attr}(..., timeout=30)  "
                            "# Always set a timeout!"
                        )
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 3: Add timeout to requests calls
# ─────────────────────────────────────────────

class AddTimeoutToRequests(ast.NodeTransformer):
    """
    Adds timeout=10 to requests.get/post/etc. calls that lack it.

    BEFORE:
        response = requests.get("https://example.com/api")

    AFTER:
        response = requests.get("https://example.com/api", timeout=10)
    """

    DEFAULT_TIMEOUT = 10

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if (isinstance(func, ast.Attribute) and
                isinstance(func.value, ast.Name) and
                func.value.id == "requests" and
                func.attr in {"get", "post", "put", "delete", "patch", "head"}):

            has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
            if not has_timeout:
                node.keywords.append(
                    ast.keyword(
                        arg="timeout",
                        value=ast.Constant(value=self.DEFAULT_TIMEOUT)
                    )
                )
                ast.fix_missing_locations(node)
                self.changes.append({
                    "pattern": "ADD_REQUEST_TIMEOUT",
                    "line": node.lineno,
                    "before": f"requests.{func.attr}(url)",
                    "after": f"requests.{func.attr}(url, timeout={self.DEFAULT_TIMEOUT})"
                })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# MAIN: run_resource_risk_analysis
# ─────────────────────────────────────────────

def run_resource_risk_analysis(source_code: str) -> dict:
    """
    Run all resource/concurrency risk detectors on source code.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": str(e), "issues": [], "risk_score": 0}

    all_issues: list[RiskIssue] = []

    detectors = [
        LockAcquireDetector(),
        RaceConditionDetector(),
        BareExceptDetector(),
        DBConnectionLeakDetector(),
        MissingTimeoutDetector(),
    ]

    for d in detectors:
        d.visit(tree)
        all_issues.extend(d.issues)

    # Apply transformations
    tree = ast.parse(source_code)
    transformers = [
        ConvertLockToWith(),
        FixBareExcept(),
        AddTimeoutToRequests(),
        WrapDBConnectionInWith(),
    ]

    all_changes = []
    for t in transformers:
        tree = t.visit(tree)
        ast.fix_missing_locations(tree)
        all_changes.extend(t.changes)

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
import threading
import sqlite3
import requests

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
'''

    result = run_resource_risk_analysis(SAMPLE_CODE)
    print("=" * 60)
    print("RESOURCE RISK ANALYSIS RESULTS")
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
