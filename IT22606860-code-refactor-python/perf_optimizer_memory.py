"""
perf_optimizer_memory.py
========================
OptiCode - Memory & Object Performance Optimizer
Author: IT22606860

Detects and refactors:
- Missing __slots__ in data classes (memory bloat)
- String concatenation in loops (quadratic memory)
- Using .readlines() when iterating (full file in memory)
- Using 'in' on lists for membership checks (O(n) vs O(1))
- Large list comprehensions that could be generators
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
# DETECTOR 1: Missing __slots__ in Classes
# ─────────────────────────────────────────────

class SlotsSuggester(ast.NodeVisitor):
    """
    Detects data-holding classes without __slots__.

    BEFORE (memory-heavy):
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

    AFTER (30-50% less memory per instance):
        class Point:
            __slots__ = ('x', 'y')
            def __init__(self, x, y):
                self.x = x
                self.y = y
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        # Check if __slots__ already defined
        has_slots = any(
            isinstance(stmt, ast.Assign) and
            any(
                isinstance(t, ast.Name) and t.id == "__slots__"
                for t in stmt.targets
            )
            for stmt in node.body
        )

        if has_slots:
            self.generic_visit(node)
            return

        # Find __init__ and extract self.attr assignments
        attrs = set()
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                for sub in ast.walk(stmt):
                    if (isinstance(sub, ast.Assign) and
                            len(sub.targets) == 1 and
                            isinstance(sub.targets[0], ast.Attribute) and
                            isinstance(sub.targets[0].value, ast.Name) and
                            sub.targets[0].value.id == "self"):
                        attrs.add(sub.targets[0].attr)

        if len(attrs) >= 2:
            slots_tuple = f"__slots__ = {tuple(sorted(attrs))}"
            self.issues.append(PerfIssue(
                issue_type="MISSING_SLOTS",
                severity="LOW",
                line=node.lineno,
                description=(
                    f"Class '{node.name}' defines {len(attrs)} instance attributes "
                    "but lacks __slots__. Each instance carries a __dict__ overhead."
                ),
                before_code=f"class {node.name}: (without __slots__)",
                after_suggestion=(
                    f"class {node.name}:\n"
                    f"    {slots_tuple}\n"
                    "    # ... rest of class"
                ),
                expected_improvement="30-50% memory reduction per instance"
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 1: Add __slots__ to classes
# ─────────────────────────────────────────────

class AddSlots(ast.NodeTransformer):
    """
    Auto-adds __slots__ to classes without it.

    BEFORE:
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

    AFTER:
        class Point:
            __slots__ = ('x', 'y')
            def __init__(self, x, y):
                self.x = x
                self.y = y
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        # Check if __slots__ already exists
        has_slots = any(
            isinstance(stmt, ast.Assign) and
            any(
                isinstance(t, ast.Name) and t.id == "__slots__"
                for t in stmt.targets
            )
            for stmt in node.body
        )

        if has_slots:
            self.generic_visit(node)
            return node

        # Find instance attributes from __init__
        attrs = set()
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                for sub in ast.walk(stmt):
                    if (isinstance(sub, ast.Assign) and
                            len(sub.targets) == 1 and
                            isinstance(sub.targets[0], ast.Attribute) and
                            isinstance(sub.targets[0].value, ast.Name) and
                            sub.targets[0].value.id == "self"):
                        attrs.add(sub.targets[0].attr)

        if len(attrs) >= 2:
            slots_assign = ast.Assign(
                targets=[ast.Name(id="__slots__", ctx=ast.Store())],
                value=ast.Tuple(
                    elts=[ast.Constant(value=a) for a in sorted(attrs)],
                    ctx=ast.Load()
                )
            )
            ast.copy_location(slots_assign, node)
            ast.fix_missing_locations(slots_assign)
            node.body.insert(0, slots_assign)
            self.changes.append({
                "pattern": "ADD_SLOTS",
                "line": node.lineno,
                "before": f"class {node.name}:",
                "after": f"class {node.name}: __slots__ = {tuple(sorted(attrs))}"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 2: String Concatenation in Loop
# ─────────────────────────────────────────────

class StringConcatInLoopDetector(ast.NodeVisitor):
    """
    Detects string += concatenation inside loops (O(n²) behavior).

    BEFORE (quadratic time/memory):
        result = ""
        for item in items:
            result += str(item) + ", "

    AFTER (linear):
        result = ", ".join(str(item) for item in items)
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []
        self._loop_depth = 0
        self._string_vars: set[str] = set()

    def visit_Assign(self, node: ast.Assign):
        # Track variables initialized to empty string
        if (isinstance(node.value, ast.Constant) and
                isinstance(node.value.value, str) and
                node.value.value == ""):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self._string_vars.add(t.id)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While):
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_AugAssign(self, node: ast.AugAssign):
        if self._loop_depth > 0:
            if (isinstance(node.op, ast.Add) and
                    isinstance(node.target, ast.Name) and
                    node.target.id in self._string_vars):
                self.issues.append(PerfIssue(
                    issue_type="STRING_CONCAT_IN_LOOP",
                    severity="HIGH",
                    line=node.lineno,
                    description=(
                        f"'{node.target.id} +=' inside loop creates new string each iteration. "
                        "Causes O(n²) time complexity for n iterations."
                    ),
                    before_code=f"{node.target.id} += ... at line {node.lineno}",
                    after_suggestion=(
                        "# Use list.append() + ''.join() pattern:\n"
                        "parts = []\n"
                        "for item in items:\n"
                        "    parts.append(str(item))\n"
                        "result = ', '.join(parts)\n"
                        "\n# Or generator expression:\n"
                        "result = ', '.join(str(item) for item in items)"
                    ),
                    expected_improvement="O(n²) → O(n) time complexity"
                ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# DETECTOR 3: readlines() Memory Hog
# ─────────────────────────────────────────────

class ReadlinesDetector(ast.NodeVisitor):
    """
    Detects file.readlines() usage (loads entire file to memory).

    BEFORE (memory hog):
        with open('huge.txt') as f:
            for line in f.readlines():
                process(line)

    AFTER (streaming, O(1) memory):
        with open('huge.txt') as f:
            for line in f:
                process(line)
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_Call(self, node: ast.Call):
        if (isinstance(node.func, ast.Attribute) and
                node.func.attr == "readlines"):
            self.issues.append(PerfIssue(
                issue_type="READLINES_MEMORY",
                severity="MEDIUM",
                line=node.lineno,
                description=(
                    ".readlines() loads entire file into memory as a list. "
                    "For large files, this can exhaust available RAM."
                ),
                before_code=f"f.readlines() at line {node.lineno}",
                after_suggestion=(
                    "# Iterate file directly (streaming):\n"
                    "with open('file.txt') as f:\n"
                    "    for line in f:   # O(1) memory\n"
                    "        process(line)"
                ),
                expected_improvement="O(n) → O(1) memory usage"
            ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 2: Replace readlines() with direct iteration
# ─────────────────────────────────────────────

class ReplaceReadlines(ast.NodeTransformer):
    """
    Replaces 'for line in f.readlines():' with 'for line in f:'.

    BEFORE:
        for line in f.readlines():
            process(line)

    AFTER:
        for line in f:
            process(line)
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_For(self, node: ast.For):
        if (isinstance(node.iter, ast.Call) and
                isinstance(node.iter.func, ast.Attribute) and
                node.iter.func.attr == "readlines"):
            file_obj = node.iter.func.value
            node.iter = file_obj
            self.changes.append({
                "pattern": "REMOVE_READLINES",
                "line": node.lineno,
                "before": "for line in f.readlines():",
                "after": "for line in f:"
            })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 4: 'in' on List for Membership
# ─────────────────────────────────────────────

class ListMembershipDetector(ast.NodeVisitor):
    """
    Detects 'x in some_list' patterns that should use a set.
    Supports both simple variables and instance attributes (self.var).

    BEFORE (O(n) per lookup):
        self.valid_ids = [1, 2, 3, 4, 5]
        if user_id in self.valid_ids:
            allow()

    AFTER (O(1) per lookup):
        self.valid_ids = {1, 2, 3, 4, 5}
        if user_id in self.valid_ids:
            allow()
    """

    def __init__(self):
        self.issues: list[PerfIssue] = []
        self._list_vars: set[str] = set()       # Simple: 'valid_ids'
        self._list_attrs: set[str] = set()      # Instance attrs: 'valid_ids' from self.valid_ids

    def visit_Assign(self, node: ast.Assign):
        # Track variables assigned to list literals
        if isinstance(node.value, ast.List):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self._list_vars.add(t.id)
                # Handle self.valid_ids = [...]
                elif isinstance(t, ast.Attribute):
                    self._list_attrs.add(t.attr)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        for i, (op, comp) in enumerate(zip(node.ops, node.comparators)):
            if isinstance(op, ast.In):
                var_name = None
                
                # Simple variable: x in valid_ids
                if isinstance(comp, ast.Name) and comp.id in self._list_vars:
                    var_name = comp.id
                # Instance attribute: x in self.valid_ids
                elif (isinstance(comp, ast.Attribute) and 
                      comp.attr in self._list_attrs and
                      isinstance(comp.value, ast.Name)):
                    var_name = f"{comp.value.id}.{comp.attr}"
                
                if var_name:
                    self.issues.append(PerfIssue(
                        issue_type="LIST_MEMBERSHIP_CHECK",
                        severity="MEDIUM",
                        line=node.lineno,
                        description=(
                            f"'in {var_name}' operates on a list — O(n) lookup. "
                            "Convert to set for O(1) membership checks."
                        ),
                        before_code=f"x in {var_name} (list) at line {node.lineno}",
                        after_suggestion=(
                            f"# Change list to set:\n"
                            f"{var_name} = {{{var_name.split('.')[-1]}_elements...}}\n"
                            f"if x in {var_name}:  # O(1)"
                        ),
                        expected_improvement="O(n) → O(1) lookup per check"
                    ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 3: Convert list to set for membership
# ─────────────────────────────────────────────

class ConvertListToSet(ast.NodeTransformer):
    """
    Converts list literals used for membership to sets.
    Supports both simple variables and instance attributes (self.var).

    BEFORE:
        self.valid_ids = [1, 2, 3, 4, 5]
        if user_id in self.valid_ids:

    AFTER:
        self.valid_ids = {1, 2, 3, 4, 5}
        if user_id in self.valid_ids:
    """

    def __init__(self):
        self.changes: list[dict] = []
        self._list_vars_used_for_membership: set[str] = set()   # Simple vars
        self._list_attrs_used_for_membership: set[str] = set()  # Instance attrs
        self._list_definitions: dict[str, ast.Assign] = {}      # Simple vars
        self._attr_definitions: dict[str, ast.Assign] = {}      # Instance attrs

    def visit_Module(self, node: ast.Module):
        # First pass: find lists used in membership checks
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.List):
                for t in stmt.targets:
                    if isinstance(t, ast.Name):
                        self._list_definitions[t.id] = stmt
                    # Handle self.valid_ids = [...]
                    elif isinstance(t, ast.Attribute):
                        self._attr_definitions[t.attr] = stmt

            if isinstance(stmt, ast.Compare):
                for op, comp in zip(stmt.ops, stmt.comparators):
                    if isinstance(op, ast.In):
                        # Simple variable: x in valid_ids
                        if isinstance(comp, ast.Name) and comp.id in self._list_definitions:
                            self._list_vars_used_for_membership.add(comp.id)
                        # Instance attribute: x in self.valid_ids
                        elif isinstance(comp, ast.Attribute) and comp.attr in self._attr_definitions:
                            self._list_attrs_used_for_membership.add(comp.attr)

        self.generic_visit(node)
        return node

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.List):
            for t in node.targets:
                # Handle simple variable: valid_ids = [...]
                if isinstance(t, ast.Name) and t.id in self._list_vars_used_for_membership:
                    node.value = ast.Set(elts=node.value.elts)
                    ast.fix_missing_locations(node)
                    self.changes.append({
                        "pattern": "LIST_TO_SET",
                        "line": node.lineno,
                        "before": f"{t.id} = [...]",
                        "after": f"{t.id} = {{...}}"
                    })
                # Handle instance attribute: self.valid_ids = [...]
                elif isinstance(t, ast.Attribute) and t.attr in self._list_attrs_used_for_membership:
                    node.value = ast.Set(elts=node.value.elts)
                    ast.fix_missing_locations(node)
                    full_name = f"{t.value.id}.{t.attr}" if isinstance(t.value, ast.Name) else t.attr
                    self.changes.append({
                        "pattern": "LIST_TO_SET",
                        "line": node.lineno,
                        "before": f"{full_name} = [...]",
                        "after": f"{full_name} = {{...}}"
                    })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# DETECTOR 5: Large List Comprehension
# ─────────────────────────────────────────────

class LargeListComprehensionDetector(ast.NodeVisitor):
    """
    Detects large list comprehensions that could be generators.

    BEFORE (materializes entire list in memory):
        result = sum([x**2 for x in range(1000000)])

    AFTER (lazy, O(1) memory):
        result = sum(x**2 for x in range(1000000))
    """

    CONSUMING_FUNCS = {"sum", "min", "max", "all", "any", "sorted", "list", "set", "tuple", "frozenset"}

    def __init__(self):
        self.issues: list[PerfIssue] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in self.CONSUMING_FUNCS:
            if len(node.args) >= 1 and isinstance(node.args[0], ast.ListComp):
                self.issues.append(PerfIssue(
                    issue_type="LISTCOMP_INSTEAD_OF_GENEXP",
                    severity="LOW",
                    line=node.lineno,
                    description=(
                        f"{func.id}([...]) creates an intermediate list. "
                        f"Use {func.id}(...) with a generator expression instead."
                    ),
                    before_code=f"{func.id}([x for x in ...]) at line {node.lineno}",
                    after_suggestion=(
                        f"{func.id}(x for x in ...)  # No intermediate list"
                    ),
                    expected_improvement="O(n) → O(1) memory for intermediate storage"
                ))

        self.generic_visit(node)


# ─────────────────────────────────────────────
# TRANSFORMER 4: Replace list comprehension with generator
# ─────────────────────────────────────────────

class ListCompToGenerator(ast.NodeTransformer):
    """
    Converts sum([x for x in ...]) to sum(x for x in ...).

    BEFORE:
        result = sum([x**2 for x in range(1000000)])

    AFTER:
        result = sum(x**2 for x in range(1000000))
    """

    CONSUMING_FUNCS = {"sum", "min", "max", "all", "any", "sorted"}

    def __init__(self):
        self.changes: list[dict] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in self.CONSUMING_FUNCS:
            if len(node.args) >= 1 and isinstance(node.args[0], ast.ListComp):
                listcomp = node.args[0]
                genexp = ast.GeneratorExp(
                    elt=listcomp.elt,
                    generators=listcomp.generators
                )
                ast.copy_location(genexp, listcomp)
                ast.fix_missing_locations(genexp)
                node.args[0] = genexp
                self.changes.append({
                    "pattern": "LISTCOMP_TO_GENEXP",
                    "line": node.lineno,
                    "before": f"{func.id}([expr for ...])",
                    "after": f"{func.id}(expr for ...)"
                })

        self.generic_visit(node)
        return node


# ─────────────────────────────────────────────
# TRANSFORMER 5: Convert simple for-append loop to list comprehension
# ─────────────────────────────────────────────

class ForAppendToListComp(ast.NodeTransformer):
    """
    Converts simple for-append loops to list comprehensions.

    BEFORE:
        result = []
        for item in items:
            result.append(item * 2)

    AFTER:
        result = [item * 2 for item in items]
    """

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
            # Look for pattern: result = []; for x in y: result.append(expr)
            if (i + 1 < len(stmts) and
                isinstance(stmts[i], ast.Assign) and
                len(stmts[i].targets) == 1 and
                isinstance(stmts[i].targets[0], ast.Name) and
                isinstance(stmts[i].value, ast.List) and
                len(stmts[i].value.elts) == 0):
                
                list_var = stmts[i].targets[0].id
                for_stmt = stmts[i + 1]
                
                if (isinstance(for_stmt, ast.For) and
                    len(for_stmt.body) == 1 and
                    isinstance(for_stmt.body[0], ast.Expr) and
                    isinstance(for_stmt.body[0].value, ast.Call) and
                    isinstance(for_stmt.body[0].value.func, ast.Attribute) and
                    for_stmt.body[0].value.func.attr == "append"):
                    
                    call = for_stmt.body[0].value
                    if (isinstance(call.func.value, ast.Name) and
                        call.func.value.id == list_var and
                        len(call.args) == 1):
                        
                        # Create list comprehension
                        listcomp = ast.ListComp(
                            elt=call.args[0],
                            generators=[ast.comprehension(
                                target=for_stmt.target,
                                iter=for_stmt.iter,
                                ifs=[],
                                is_async=0
                            )]
                        )
                        new_assign = ast.Assign(
                            targets=[ast.Name(id=list_var, ctx=ast.Store())],
                            value=listcomp
                        )
                        ast.copy_location(new_assign, stmts[i])
                        ast.fix_missing_locations(new_assign)
                        
                        self.changes.append({
                            "pattern": "FOR_APPEND_TO_LISTCOMP",
                            "line": stmts[i].lineno,
                            "before": f"{list_var} = []; for ...: {list_var}.append(...)",
                            "after": f"{list_var} = [expr for ... in ...]"
                        })
                        
                        new_stmts.append(new_assign)
                        i += 2
                        continue
            
            new_stmts.append(stmts[i])
            i += 1
        
        return new_stmts


# ─────────────────────────────────────────────
# TRANSFORMER 6: Convert % formatting to f-string
# ─────────────────────────────────────────────

class PercentToFString(ast.NodeTransformer):
    """
    Converts % string formatting to f-strings.

    BEFORE:
        message = "Hello %s, you are %d years old" % (name, age)

    AFTER:
        message = f"Hello {name}, you are {age} years old"
    """

    def __init__(self):
        self.changes: list[dict] = []

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        
        if not isinstance(node.op, ast.Mod):
            return node
        
        if not isinstance(node.left, ast.Constant):
            return node
        
        if not isinstance(node.left.value, str):
            return node
        
        format_str = node.left.value
        
        # Get the values to substitute
        if isinstance(node.right, ast.Tuple):
            values = node.right.elts
        else:
            values = [node.right]
        
        # Convert % placeholders to f-string format
        import re
        placeholders = re.findall(r'%[sd]', format_str)
        
        if len(placeholders) != len(values):
            return node  # Mismatch, don't transform
        
        # Build f-string
        fstring_parts = []
        remaining = format_str
        value_idx = 0
        
        for placeholder in placeholders:
            idx = remaining.find(placeholder)
            if idx > 0:
                fstring_parts.append(ast.Constant(value=remaining[:idx]))
            fstring_parts.append(ast.FormattedValue(
                value=values[value_idx],
                conversion=-1,
                format_spec=None
            ))
            remaining = remaining[idx + len(placeholder):]
            value_idx += 1
        
        if remaining:
            fstring_parts.append(ast.Constant(value=remaining))
        
        if not fstring_parts:
            return node
        
        fstring = ast.JoinedStr(values=fstring_parts)
        ast.copy_location(fstring, node)
        ast.fix_missing_locations(fstring)
        
        self.changes.append({
            "pattern": "PERCENT_TO_FSTRING",
            "line": node.lineno,
            "before": '"..." % (...)',
            "after": 'f"..."'
        })
        
        return fstring


# ─────────────────────────────────────────────
# MAIN: run_memory_optimization
# ─────────────────────────────────────────────

def run_memory_optimization(source_code: str) -> dict:
    """
    Run all memory/performance detectors on source code.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": str(e), "issues": [], "perf_score": 0}

    all_issues: list[PerfIssue] = []

    detectors = [
        SlotsSuggester(),
        StringConcatInLoopDetector(),
        ReadlinesDetector(),
        ListMembershipDetector(),
        LargeListComprehensionDetector(),
    ]

    for d in detectors:
        d.visit(tree)
        all_issues.extend(d.issues)

    # Apply transformations
    tree = ast.parse(source_code)
    transformers = [
        AddSlots(),
        ReplaceReadlines(),
        ConvertListToSet(),
        ListCompToGenerator(),
        ForAppendToListComp(),
        PercentToFString(),
    ]

    all_changes = []
    for t in transformers:
        tree = t.visit(tree)
        ast.fix_missing_locations(tree)
        all_changes.extend(t.changes)

    # Use ast.unparse (Python 3.9+) first as it handles f-strings properly
    # Fall back to astor.to_source for older Python versions
    try:
        optimized = ast.unparse(tree)
    except AttributeError:
        try:
            optimized = astor.to_source(tree)
        except Exception:
            optimized = source_code
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
'''

    result = run_memory_optimization(SAMPLE_CODE)
    print("=" * 60)
    print("MEMORY OPTIMIZATION RESULTS")
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
