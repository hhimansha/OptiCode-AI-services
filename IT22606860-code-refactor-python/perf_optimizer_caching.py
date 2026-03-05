"""
perf_optimizer_caching.py
=========================
OptiCode - Caching & Algorithmic Performance Optimizer
Author: IT22606860

Detects and refactors:
- Recursive functions without memoization
- Repeated expensive calls in loops
- Missing augmented assignment operators
- range(len()) anti-pattern
- Nested loop complexity (O(n²) to O(n))
"""

import ast
import astor
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────

@dataclass
class PerfIssue:
    issue_type: str
    severity: str
    line: int
    description: str
    before_code: str
    after_suggestion: str
    expected_improvement: str


# ─────────────────────────────────────────────
# DETECTOR 1: Recursive Without Cache
# ─────────────────────────────────────────────

class RecursiveWithoutCacheDetector(ast.NodeVisitor):
    """
    Detects recursive functions without @cache or @lru_cache.

    BEFORE (exponential for fib):
        def fib(n):
            if n <= 1:
                return n
            return fib(n-1) + fib(n-2)

    AFTER (O(n) with memoization):
        from functools import lru_cache

        @lru_cache(maxsize=None)
        def fib(n):
            if n <= 1:
                return n
            return fib(n-1) + fib(n-2)
    """

    CACHE_DECORATORS = {"cache", "lru_cache", "cached_property", "memoize"}

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check if already decorated with cache
        decorated = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in self.CACHE_DECORATORS:
                decorated = True
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name) and dec.func.id in self.CACHE_DECORATORS:
                    decorated = True
                elif isinstance(dec.func, ast.Attribute) and dec.func.attr in self.CACHE_DECORATORS:
                    decorated = True

        if decorated:
            self.generic_visit(node)
            return

        # Check if function calls itself (both function and method style)
        func_name = node.name
        is_recursive = False

        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                # Check for direct function call: func_name(...)
                if isinstance(sub.func, ast.Name) and sub.func.id == func_name:
                    is_recursive = True
                    break
                # Check for method call: self.func_name(...)
                if isinstance(sub.func, ast.Attribute):
                    if sub.func.attr == func_name:
                        if isinstance(sub.func.value, ast.Name) and sub.func.value.id == "self":
                            is_recursive = True
                            break

        if is_recursive:
            self.issues.append(PerfIssue(
                issue_type="RECURSIVE_NO_CACHE",
                severity="HIGH",
                line=node.lineno,
                description=(
                    f"Recursive function '{func_name}' without memoization. "
                    "May have exponential time complexity for repeated inputs."
                ),
                before_code=f"def {func_name}(...):",
                after_suggestion=(
                    "from functools import lru_cache\n\n"
                    f"@lru_cache(maxsize=128)\n"
                    f"def {func_name}(...):"
                ),
                expected_improvement="Exponential → O(n) for many recursive patterns"
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 1: Add @lru_cache to recursive functions
# ─────────────────────────────────────────────

class AddCacheDecorator(ast.NodeTransformer):
    """
    Adds @lru_cache decorator to recursive functions.

    BEFORE:
        def fib(n):
            if n <= 1: return n
            return fib(n-1) + fib(n-2)

    AFTER:
        @lru_cache(maxsize=128)
        def fib(n):
            if n <= 1: return n
            return fib(n-1) + fib(n-2)
    """

    CACHE_DECORATORS = {"cache", "lru_cache", "cached_property", "memoize"}

    def __init__(self):
        self.changes: list[dict] = []
        self._added_import = False

    def visit_Module(self, node: ast.Module):
        self.generic_visit(node)

        # Add functools import if we made changes and it's not already imported
        if self.changes and not self._has_functools_import(node):
            import_node = ast.ImportFrom(
                module="functools",
                names=[ast.alias(name="lru_cache", asname=None)],
                level=0
            )
            ast.fix_missing_locations(import_node)
            node.body.insert(0, import_node)

        return node

    def _has_functools_import(self, node: ast.Module) -> bool:
        for stmt in node.body:
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "functools":
                if any(alias.name in {"lru_cache", "cache"} for alias in stmt.names):
                    return True
            if isinstance(stmt, ast.Import):
                if any(alias.name == "functools" for alias in stmt.names):
                    return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check if already decorated
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in self.CACHE_DECORATORS:
                return node
            if isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name) and dec.func.id in self.CACHE_DECORATORS:
                    return node

        # Check if recursive (both function and method style)
        func_name = node.name
        is_recursive = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                # Check for direct function call: func_name(...)
                if isinstance(sub.func, ast.Name) and sub.func.id == func_name:
                    is_recursive = True
                    break
                # Check for method call: self.func_name(...)
                if isinstance(sub.func, ast.Attribute):
                    if sub.func.attr == func_name:
                        if isinstance(sub.func.value, ast.Name) and sub.func.value.id == "self":
                            is_recursive = True
                            break

        if is_recursive:
            decorator = ast.Call(
                func=ast.Name(id="lru_cache", ctx=ast.Load()),
                args=[],
                keywords=[ast.keyword(arg="maxsize", value=ast.Constant(value=128))]
            )
            ast.fix_missing_locations(decorator)
            node.decorator_list.insert(0, decorator)
            self.changes.append({
                "pattern": "ADD_LRU_CACHE",
                "line": node.lineno,
                "before": f"def {func_name}(...):",
                "after": f"@lru_cache(maxsize=128) def {func_name}(...):"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 2: range(len()) Anti-Pattern
# ─────────────────────────────────────────────

class RangeLenDetector(ast.NodeVisitor):
    """
    Detects 'for i in range(len(x))' patterns.

    BEFORE (unpythonic, slower):
        for i in range(len(items)):
            print(items[i])

    AFTER (pythonic, faster):
        for item in items:
            print(item)

        # Or if index needed:
        for i, item in enumerate(items):
            print(i, item)
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_For(self, node: ast.For):
        if (isinstance(node.iter, ast.Call) and
                isinstance(node.iter.func, ast.Name) and
                node.iter.func.id == "range" and
                len(node.iter.args) == 1):

            arg = node.iter.args[0]
            if (isinstance(arg, ast.Call) and
                    isinstance(arg.func, ast.Name) and
                    arg.func.id == "len"):
                if len(arg.args) == 1 and isinstance(arg.args[0], ast.Name):
                    seq_name = arg.args[0].id
                    self.issues.append(PerfIssue(
                        issue_type="RANGE_LEN_ANTIPATTERN",
                        severity="LOW",
                        line=node.lineno,
                        description=(
                            f"'for i in range(len({seq_name}))' is unpythonic. "
                            "Use direct iteration or enumerate()."
                        ),
                        before_code=f"for i in range(len({seq_name})):",
                        after_suggestion=(
                            f"for item in {seq_name}:\n"
                            "    # access item directly\n\n"
                            "# Or if index needed:\n"
                            f"for i, item in enumerate({seq_name}):"
                        ),
                        expected_improvement="More readable, slightly faster"
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 2: Convert range(len()) to enumerate
# ─────────────────────────────────────────────

class RangeLenToEnumerate(ast.NodeTransformer):
    """
    Converts 'for i in range(len(x))' to 'for i, item in enumerate(x)'.

    BEFORE:
        for i in range(len(items)):
            process(items[i])

    AFTER:
        for i, _item in enumerate(items):
            process(_item)
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_For(self, node: ast.For):
        if not (isinstance(node.iter, ast.Call) and
                isinstance(node.iter.func, ast.Name) and
                node.iter.func.id == "range" and
                len(node.iter.args) == 1):
            self.generic_visit(node)
            return node

        arg = node.iter.args[0]
        if not (isinstance(arg, ast.Call) and
                isinstance(arg.func, ast.Name) and
                arg.func.id == "len" and
                len(arg.args) == 1 and
                isinstance(arg.args[0], ast.Name)):
            self.generic_visit(node)
            return node

        seq_name = arg.args[0].id
        idx_var = node.target.id if isinstance(node.target, ast.Name) else "_i"
        item_var = f"_{seq_name}_item"

        # Transform to enumerate
        node.target = ast.Tuple(
            elts=[
                ast.Name(id=idx_var, ctx=ast.Store()),
                ast.Name(id=item_var, ctx=ast.Store())
            ],
            ctx=ast.Store()
        )
        node.iter = ast.Call(
            func=ast.Name(id="enumerate", ctx=ast.Load()),
            args=[ast.Name(id=seq_name, ctx=ast.Load())],
            keywords=[]
        )
        ast.fix_missing_locations(node)

        self.changes.append({
            "pattern": "RANGE_LEN_TO_ENUMERATE",
            "line": node.lineno,
            "before": f"for {idx_var} in range(len({seq_name})):",
            "after": f"for {idx_var}, {item_var} in enumerate({seq_name}):"
        })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 3: Missing Augmented Assignment
# ─────────────────────────────────────────────

class AugmentedAssignmentDetector(ast.NodeVisitor):
    """
    Detects 'x = x + y' patterns that should use 'x += y'.

    BEFORE:
        count = count + 1
        total = total * factor

    AFTER:
        count += 1
        total *= factor
    """

    OP_MAP = {
        ast.Add: "+=",
        ast.Sub: "-=",
        ast.Mult: "*=",
        ast.Div: "/=",
        ast.FloorDiv: "//=",
        ast.Mod: "%=",
        ast.Pow: "**=",
        ast.BitAnd: "&=",
        ast.BitOr: "|=",
        ast.BitXor: "^=",
        ast.LShift: "<<=",
        ast.RShift: ">>=",
    }

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            self.generic_visit(node)
            return

        target_name = node.targets[0].id

        if isinstance(node.value, ast.BinOp):
            left = node.value.left
            if isinstance(left, ast.Name) and left.id == target_name:
                op_type = type(node.value.op)
                if op_type in self.OP_MAP:
                    aug_op = self.OP_MAP[op_type]
                    self.issues.append(PerfIssue(
                        issue_type="MISSING_AUGMENTED_ASSIGN",
                        severity="LOW",
                        line=node.lineno,
                        description=(
                            f"'{target_name} = {target_name} op ...' can be written as "
                            f"'{target_name} {aug_op} ...'. More concise and potentially faster."
                        ),
                        before_code=f"{target_name} = {target_name} {op_type.__name__.lower()} ...",
                        after_suggestion=f"{target_name} {aug_op} ...",
                        expected_improvement="More readable, avoids redundant lookup"
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 3: Convert to augmented assignment
# ─────────────────────────────────────────────

class ConvertToAugmented(ast.NodeTransformer):
    """
    Converts 'x = x + y' to 'x += y'.

    BEFORE:
        count = count + 1

    AFTER:
        count += 1
    """

    OP_MAP = {
        ast.Add: ast.Add,
        ast.Sub: ast.Sub,
        ast.Mult: ast.Mult,
        ast.Div: ast.Div,
        ast.FloorDiv: ast.FloorDiv,
        ast.Mod: ast.Mod,
        ast.Pow: ast.Pow,
        ast.BitAnd: ast.BitAnd,
        ast.BitOr: ast.BitOr,
        ast.BitXor: ast.BitXor,
        ast.LShift: ast.LShift,
        ast.RShift: ast.RShift,
    }

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return node

        target_name = node.targets[0].id

        if isinstance(node.value, ast.BinOp):
            left = node.value.left
            if isinstance(left, ast.Name) and left.id == target_name:
                op_type = type(node.value.op)
                if op_type in self.OP_MAP:
                    aug_node = ast.AugAssign(
                        target=ast.Name(id=target_name, ctx=ast.Store()),
                        op=self.OP_MAP[op_type](),
                        value=node.value.right
                    )
                    ast.copy_location(aug_node, node)
                    ast.fix_missing_locations(aug_node)
                    self.changes.append({
                        "pattern": "TO_AUGMENTED_ASSIGN",
                        "line": node.lineno,
                        "before": f"{target_name} = {target_name} op ...",
                        "after": f"{target_name} op= ..."
                    })
                    return aug_node

        return node


# ─────────────────────────────────────────────
# DETECTOR 4: Repeated Call in Loop
# ─────────────────────────────────────────────

class RepeatedCallInLoopDetector(ast.NodeVisitor):
    """
    Detects expensive function calls repeated in loops.

    BEFORE (len called N times):
        for i in range(1000):
            if i < len(big_list):
                process(i)

    AFTER (len called once):
        list_len = len(big_list)
        for i in range(1000):
            if i < list_len:
                process(i)
    """

    EXPENSIVE_CALLS = {"len", "sorted", "list", "set", "dict", "tuple"}

    def __init__(self):
        self.issues: list[PerfIssue] = []
        self._in_loop = False

    def visit_For(self, node: ast.For):
        old = self._in_loop
        self._in_loop = True
        call_counts: dict[str, list[int]] = {}

        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                fname = sub.func.id
                if fname in self.EXPENSIVE_CALLS:
                    call_counts.setdefault(fname, []).append(sub.lineno)

        for fname, lines in call_counts.items():
            if len(lines) >= 2:
                self.issues.append(PerfIssue(
                    issue_type="REPEATED_CALL_IN_LOOP",
                    severity="MEDIUM",
                    line=lines[0],
                    description=(
                        f"'{fname}(...)' called {len(lines)} times inside loop. "
                        "Consider caching the result before the loop."
                    ),
                    before_code=f"{fname}(...) at lines {lines}",
                    after_suggestion=(
                        f"cached_{fname} = {fname}(...)\n"
                        f"for ... in ...:\n"
                        f"    # use cached_{fname} instead"
                    ),
                    expected_improvement=f"Avoid {len(lines)-1} redundant calls per iteration"
                ))

        self.generic_visit(node)
        self._in_loop = old


# ─────────────────────────────────────────────
# DETECTOR 5: Nested Loop Complexity
# ─────────────────────────────────────────────

class NestedLoopComplexityDetector(ast.NodeVisitor):
    """
    Detects deeply nested loops (O(n²) or worse).

    BEFORE (O(n²)):
        for item in list_a:
            for other in list_b:
                if item == other:
                    matches.append(item)

    AFTER (O(n)):
        set_b = set(list_b)
        for item in list_a:
            if item in set_b:
                matches.append(item)
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []
        self._loop_depth = 0
        self._max_nesting = 2

    def visit_For(self, node: ast.For):
        self._loop_depth += 1
        if self._loop_depth >= self._max_nesting:
            self.issues.append(PerfIssue(
                issue_type="NESTED_LOOP_COMPLEXITY",
                severity="MEDIUM",
                line=node.lineno,
                description=(
                    f"Nested loop at depth {self._loop_depth} — O(n^{self._loop_depth}) complexity. "
                    "Consider using sets, dicts, or algorithmic improvements."
                ),
                before_code=f"Nested for loop at line {node.lineno}",
                after_suggestion=(
                    "# Convert inner list to set for O(1) lookups:\n"
                    "set_b = set(list_b)\n"
                    "for item in list_a:\n"
                    "    if item in set_b:\n"
                    "        matches.append(item)"
                ),
                expected_improvement=f"O(n^{self._loop_depth}) → O(n) possible"
            ))
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While):
        self._loop_depth += 1
        if self._loop_depth >= self._max_nesting:
            self.issues.append(PerfIssue(
                issue_type="NESTED_LOOP_COMPLEXITY",
                severity="MEDIUM",
                line=node.lineno,
                description=(
                    f"Nested while loop at depth {self._loop_depth} — O(n^{self._loop_depth}) complexity."
                ),
                before_code=f"Nested while loop at line {node.lineno}",
                after_suggestion="Consider refactoring to reduce nesting",
                expected_improvement="Reduced time complexity"
            ))
        self.generic_visit(node)
        self._loop_depth -= 1


# ─────────────────────────────────────────────
# MAIN: run_caching_optimization
# ─────────────────────────────────────────────

def run_caching_optimization(source_code: str) -> dict:
    """
    Run all caching/algorithmic detectors on source code.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": str(e), "issues": [], "perf_score": 0}

    all_issues: list[PerfIssue] = []

    detectors = [
        RecursiveWithoutCacheDetector(),
        RangeLenDetector(),
        AugmentedAssignmentDetector(),
        RepeatedCallInLoopDetector(),
        NestedLoopComplexityDetector(),
    ]

    for d in detectors:
        d.visit(tree)
        all_issues.extend(d.issues)

    # Apply transformations
    tree = ast.parse(source_code)
    transformers = [
        AddCacheDecorator(),
        RangeLenToEnumerate(),
        ConvertToAugmented(),
    ]

    all_changes = []
    for t in transformers:
        tree = t.visit(tree)
        ast.fix_missing_locations(tree)
        all_changes.extend(t.changes)

    try:
        optimized = astor.to_source(tree)
    except Exception:
        optimized = source_code

    SEVERITY_WEIGHTS = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 10, "LOW": 5}
    perf_score = min(sum(SEVERITY_WEIGHTS.get(i.severity, 5) for i in all_issues), 100)

    return {
        "issues": all_issues,
        "perf_score": perf_score,
        "total_issues": len(all_issues),
        "optimized_code": optimized,
        "changes_applied": all_changes,
        "suggestions": [
            {
                "issue_type": i.issue_type,
                "severity": i.severity,
                "line": i.line,
                "description": i.description,
                "fix": i.after_suggestion,
                "expected_improvement": i.expected_improvement
            }
            for i in all_issues
        ]
    }


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    SAMPLE_CODE = '''
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

def process_items(items):
    for i in range(len(items)):
        print(items[i])

def counter():
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

    result = run_caching_optimization(SAMPLE_CODE)
    print("=" * 60)
    print("CACHING OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"Performance Score (issues weight): {result['perf_score']}")
    print(f"Total Issues: {result['total_issues']}")
    print()
    for issue in result["issues"]:
        print(f"[{issue.severity}] {issue.issue_type} - Line {issue.line}")
        print(f"  {issue.description}")
        print(f"  Expected Improvement: {issue.expected_improvement}")
        print()
    print("OPTIMIZED CODE:")
    print(result["optimized_code"])
