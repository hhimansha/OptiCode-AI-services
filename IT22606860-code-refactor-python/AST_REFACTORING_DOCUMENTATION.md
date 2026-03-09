# OptiCode AST-Based Python Code Refactoring Documentation

## Author: IT22606860
## Project: Comprehensive Python Code Refactoring Research

---

## 📋 Overview

This documentation describes all AST (Abstract Syntax Tree) refactoring methods implemented in the OptiCode Python backend. The system provides **100+ refactoring patterns** across **12 categories** for professional Python code transformation.

### Core Files
| File | Purpose |
|------|---------|
| `ast_refactor.py` | Basic AST transformations (foundational patterns) |
| `priority_refactorings.py` | Top 20 priority refactoring patterns |
| `advanced_ast_refactor.py` | 100+ comprehensive patterns across 12 categories |
| `performance_optimizer.py` | Performance-specific optimizations |
| `unified_refactor.py` | Orchestrator combining all refactoring stages |

---

## 🔧 AST Module Used

The refactoring engine uses Python's built-in `ast` module along with:
- **`ast.parse()`** - Parse source code into AST
- **`ast.NodeTransformer`** - Transform AST nodes (modify code)
- **`ast.NodeVisitor`** - Visit AST nodes (analyze code)
- **`ast.walk()`** - Iterate over all nodes in AST
- **`ast.unparse()`** - Convert AST back to source code (Python 3.9+)
- **`astor.to_source()`** - Convert AST to source code (fallback)
- **`ast.fix_missing_locations()`** - Fix line/column info after transformations

---

## 📦 CATEGORY 1: NAMING & READABILITY REFACTORINGS

### Class: `NamingRefactorer`
Improves code readability through better naming conventions.

| Pattern | Description | Before | After |
|---------|-------------|--------|-------|
| **Rename Variable** | Single-letter variables to descriptive names | `x = 5` | `count = 5` |
| **Rename Function** | Unclear function names to verb-noun pattern | `def func():` | `def calculate_total():` |
| **Suggest Better Names** | Detect common abbreviations | `tmp`, `cnt`, `idx` | `temporary`, `count`, `index` |
| **snake_case Enforcement** | Enforce Python naming conventions | `myFunction` | `my_function` |
| **PascalCase for Classes** | Enforce class naming conventions | `class myclass:` | `class MyClass:` |

**AST Nodes Used:**
- `ast.Name` - Variable names
- `ast.FunctionDef` - Function definitions
- `ast.ClassDef` - Class definitions
- `ast.arg` - Function arguments

---

## 📦 CATEGORY 2: FUNCTION/METHOD REFACTORINGS

### Class: `FunctionRefactorer`
Advanced function restructuring patterns.

| Pattern | Description | Trigger Condition |
|---------|-------------|-------------------|
| **Extract Function** | Break large functions into smaller ones | Function body > 10 statements |
| **Inline Function** | Replace single-statement functions with expression | Function has only `return` statement |
| **Split Function** | Separate functions with multiple concerns | Multiple I/O, database, network operations |
| **Extract Method** | Extract long function bodies | Function body > 15 statements |

**AST Methods:**
```python
def visit_FunctionDef(self, node):
    # Analyze function body length
    if len(node.body) > 15:
        # Suggest extraction
```

---

## 📦 CATEGORY 3: CONDITIONAL LOGIC REFACTORINGS

### Class: `ConditionalRefactorer` & `SimplifyConditionals`

| Pattern | Before | After | Impact |
|---------|--------|-------|--------|
| **Simplify Boolean Return** | `if cond: return True else: return False` | `return cond` | Cleaner code |
| **Remove Negated Boolean** | `if cond == True:` | `if cond:` | Pythonic style |
| **Guard Clauses** | Nested `if` statements | Early `return` statements | Reduces nesting |
| **Decompose Conditional** | Complex boolean expressions | Extract to method | Testable logic |
| **Remove Control Flag** | `while found:` pattern | `while True: ... break` | Clearer intent |
| **Consolidate Conditionals** | Duplicate code in if/else branches | Move common code outside | DRY principle |
| **Dictionary Dispatch** | Long if-elif chains (>3 branches) | Dictionary lookup | Cleaner, O(1) |

**AST Pattern - Simplify Boolean Return:**
```python
class SimplifyConditionals(ast.NodeTransformer):
    def visit_If(self, node):
        # Pattern: if cond: return True else: return False
        if (len(node.body) == 1 and len(node.orelse) == 1 and
            isinstance(node.body[0], ast.Return) and 
            isinstance(node.orelse[0], ast.Return)):
            
            body_val = node.body[0].value
            else_val = node.orelse[0].value
            
            if body_val.value is True and else_val.value is False:
                return ast.Return(value=node.test)  # return cond
```

---

## 📦 CATEGORY 4: VARIABLE & DATA REFACTORINGS

### Class: `VariableRefactorer`

| Pattern | Description | Example |
|---------|-------------|---------|
| **Replace Magic Number** | Named constants for literals | `60` → `SECONDS_PER_MINUTE` |
| **Encapsulate Variable** | Convert to property with getter/setter | `obj.x` → `obj.get_x()` |
| **Inline Temp Variable** | Remove single-use temporaries | `temp = x; use(temp)` → `use(x)` |
| **Introduce Explaining Variable** | Break complex expressions | Long boolean → `is_valid = ...` |
| **Split Temporary Variable** | Separate multi-purpose variables | Single var assigned 3+ times |

**Magic Number Detection:**
```python
# Automatic mapping
60 → SECONDS_PER_MINUTE
24 → HOURS_PER_DAY
100 → PERCENTAGE_MAX
365 → DAYS_PER_YEAR
```

---

## 📦 CATEGORY 5: CLASS & OBJECT REFACTORINGS

### Class: `ClassRefactorer`

| Pattern | Trigger | Suggestion |
|---------|---------|------------|
| **Extract Class** | Class has >20 methods | Split into helper class |
| **God Class Detection** | Class >300 lines | Violates Single Responsibility |
| **Multiple Inheritance Warning** | >1 base class | Consider composition |
| **Move Method** | Method uses another class's data more | Move to appropriate class |
| **Introduce Dataclass** | Class has only `__init__` and data | Use `@dataclass` decorator |

---

## 📦 CATEGORY 6: PYTHON-SPECIFIC REFACTORINGS

### Class: `PythonSpecificRefactorer`

| Pattern | Before | After | Performance |
|---------|--------|-------|-------------|
| **List Comprehension** | `for x in items: result.append(f(x))` | `result = [f(x) for x in items]` | 30-40% faster |
| **Generator Expression** | `sum([x*2 for x in items])` | `sum(x*2 for x in items)` | Memory efficient |
| **enumerate()** | `for i in range(len(x)):` | `for i, val in enumerate(x):` | Pythonic |
| **zip()** | Manual index iteration | `for a, b in zip(list1, list2):` | Cleaner |
| **F-Strings** | `print("val:", x)` | `print(f"val: {x}")` | Modern Python |
| **Context Manager** | Manual open/close | `with open() as f:` | Safe resources |
| **Augmented Assignment** | `x = x + 1` | `x += 1` | Slightly faster |

### AST Pattern - Loop to Comprehension:
```python
class OptimizeListAppendLoops(ast.NodeTransformer):
    def _try_rewrite_append_loop(self, assign_node, loop_node):
        # Detect: result = []; for x in items: result.append(expr)
        # Transform to: result = [expr for x in items]
        
        comp = ast.ListComp(
            elt=append_expr,
            generators=[
                ast.comprehension(
                    target=iter_target,
                    iter=iter_expr,
                    ifs=[if_test] if if_test else [],
                    is_async=0
                )
            ]
        )
```

### AST Pattern - Sum Replacement:
```python
class OptimizeSumLoops(ast.NodeTransformer):
    # Detect:
    #   total = 0
    #   for x in items:
    #       if x > 0:
    #           total += x
    
    # Transform to:
    #   total = sum(x for x in items if x > 0)
```

---

## 📦 CATEGORY 7: LOOP OPTIMIZATIONS

### Classes: `ImproveLoops`, `OptimizeSumLoops`, `OptimizeListAppendLoops`

| Pattern | Before | After |
|---------|--------|-------|
| **Accumulation to sum()** | `total = 0; for i in range(len(nums)): total = total + nums[i]` | `total = sum(nums)` |
| **Append Loop to Comprehension** | `result = []; for x in items: result.append(x*2)` | `result = [x*2 for x in items]` |
| **Conditional Append** | `for x in items: if x > 0: result.append(x)` | `result = [x for x in items if x > 0]` |
| **range(len()) Pattern** | `for i in range(len(items)):` | `for i, item in enumerate(items):` |

---

## 📦 CATEGORY 8: PERFORMANCE OPTIMIZATIONS

### Class: `PerformanceOptimizer`

| Category | Issue | Solution | Complexity Change |
|----------|-------|----------|-------------------|
| **Algorithmic** | Nested loops for lookup | Use set/dict | O(n*m) → O(n+m) |
| **Data Structure** | List for membership testing | Use set | O(n) → O(1) |
| **Memory** | Large list in memory | Use generator | O(n) → O(1) space |
| **String** | String concatenation in loop | Use `join()` | O(n²) → O(n) |
| **Caching** | Repeated expensive calls | Use `@lru_cache` | Memoization |

---

## 📦 CATEGORY 9: ERROR HANDLING

| Pattern | Description |
|---------|-------------|
| **Introduce Exception** | Convert return codes to exceptions |
| **Result Objects** | Use Result pattern for error handling |
| **Narrow Exception Scope** | Catch specific exceptions, not bare `except:` |
| **Remove Empty Handlers** | Detect `except: pass` antipattern |

---

## 📦 CATEGORY 10: CODE STYLE & CLEANLINESS

### Class: `ExtractComplexExpressions`

| Pattern | Before | After |
|---------|--------|-------|
| **Extract Complex Return** | `return a + b * c - d / e` | `result = a + b * c - d / e; return result` |
| **If/Else to Ternary** | `if cond: x = 1 else: x = 2` | `x = 1 if cond else 2` |
| **Remove Dead Code** | Code after `return` statement | Removed |
| **Remove Unused Variables** | Assigned but never used variables | Warning/Removal |

---

## 📦 CATEGORY 11: DEAD CODE REMOVAL

### Pattern Detection:

| Pattern | Description | Action |
|---------|-------------|--------|
| **Unreachable Code** | Code after `return/raise` | Remove |
| **Always True** | `if True: body` | Keep only body |
| **Always False** | `if False: body else: other` | Keep only else |
| **Unused Variables** | Assigned but never read | Warning |

**AST Implementation:**
```python
class DeadCodeRemover(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        new_body = []
        found_return = False
        
        for stmt in node.body:
            if found_return:
                # This code is unreachable - skip it
                continue
            new_body.append(stmt)
            if isinstance(stmt, (ast.Return, ast.Raise)):
                found_return = True
        
        node.body = new_body
        return node
```

---

## 📦 CATEGORY 12: ARCHITECTURE & TESTING

| Pattern | Description |
|---------|-------------|
| **Dependency Injection** | Remove hard-coded dependencies |
| **Separate I/O** | Isolate I/O from business logic |
| **Single Responsibility** | One class/function = one purpose |
| **Add Type Hints** | Missing type annotations |
| **Remove Duplicates** | Identical function bodies |

---

## 🎯 TOP 20 PRIORITY PATTERNS (PriorityRefactorer)

These are the most impactful patterns applied in order:

| # | Pattern | Impact |
|---|---------|--------|
| 1 | Remove Dead Code | Cleaner code, no confusion |
| 2 | Remove Duplicate Code | DRY principle, easier maintenance |
| 3 | Replace Loop with Comprehension | More Pythonic, 30-40% faster |
| 4 | Replace Accumulation with sum() | More Pythonic, optimized |
| 5 | Convert to Augmented Assignment | Cleaner syntax |
| 6 | Convert Print to F-String | Modern Python style |
| 7 | Introduce Explaining Variable | Better readability |
| 8 | Decompose Conditional | Clearer intent, testable |
| 9 | Replace Nested with Guard Clauses | Reduces nesting |
| 10 | Remove Control Flag | Simpler logic |
| 11 | Consolidate Duplicate Conditionals | DRY principle |
| 12 | Inline Temp Variable | Fewer variables |
| 13 | Extract Method | Single responsibility |
| 14 | Introduce Assertion | Fail fast, clearer contracts |
| 15 | Replace Temp with Query | Reusable logic |
| 16 | Rename Variable | Self-documenting code |
| 17 | Remove Assignments to Parameters | No side effects |
| 18 | Split Temporary Variable | Single purpose variables |
| 19 | Replace Magic Number | Named constants |
| 20 | Use Context Manager | Safe resource handling |

---

## 🔄 Unified Refactoring Pipeline

The `unified_refactor.py` orchestrates all stages:

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT CODE                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Basic AST Refactoring (ast_refactor.py)       │
│  - Simplify conditionals                                 │
│  - Extract complex expressions                           │
│  - Optimize loops                                        │
│  - Magic numbers & duplicates                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: Priority Patterns (priority_refactorings.py)  │
│  - Top 20 critical transformations                       │
│  - Dead code removal                                     │
│  - Comprehensions & f-strings                            │
│  - Guard clauses                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 3: Advanced (advanced_ast_refactor.py)           │
│  - 100+ patterns across 12 categories                    │
│  - Naming, functions, classes                            │
│  - Python-specific idioms                                │
│  - Architecture improvements                             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 4: Performance (performance_optimizer.py)        │
│  - Algorithmic complexity                                │
│  - Data structure optimization                           │
│  - Caching opportunities                                 │
│  - Memory efficiency                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    OUTPUT CODE                           │
│         + Changes + Metrics + Suggestions                │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Code Quality Metrics Calculated

| Metric | Description | Source |
|--------|-------------|--------|
| **Cyclomatic Complexity** | Number of decision points | `radon` |
| **Lines of Code (LOC)** | Total lines | `radon.raw` |
| **Maintainability Index** | Overall maintainability score | `radon.metrics` |
| **Halstead Metrics** | Volume, difficulty, effort | `radon.metrics` |
| **Max Nesting Level** | Deepest indentation | Custom AST |
| **Improvement Score** | Before/after comparison | Custom |

---

## 🛡️ Security Analysis

Using `bandit` for security checks:
- SQL injection vulnerabilities
- Hardcoded credentials
- Unsafe deserialization
- Shell injection risks
- Weak cryptography

---

## 📝 API Usage Examples

### Basic Refactoring
```python
from ast_refactor import refactor_code_ast

result = refactor_code_ast(code, options={
    'simplify_conditionals': True,
    'extract_complex': True,
    'improve_loops': True,
    'refactor_magic_numbers': True
})

print(result['refactored_code'])
```

### Priority Patterns
```python
from priority_refactorings import apply_priority_refactorings

result = apply_priority_refactorings(code)
for change in result['changes']:
    print(f"Pattern: {change.pattern_name}")
    print(f"Line: {change.line}")
    print(f"Before: {change.before}")
    print(f"After: {change.after}")
```

### Comprehensive Refactoring
```python
from advanced_ast_refactor import refactor_comprehensive

result = refactor_comprehensive(code, categories=[
    'Naming & Readability',
    'Function/Method',
    'Python-Specific'
])
```

### Full Pipeline
```python
from unified_refactor import refactor_complete

result = refactor_complete(code, options={
    'apply_basic': True,
    'apply_priority': True,
    'apply_advanced': True,
    'apply_performance': True
})
```

---

## 📈 Supported Python Code Transformations Summary

| Category | Patterns Count | Key Transformations |
|----------|----------------|---------------------|
| Naming & Readability | 5 | Variable/function/class renaming |
| Function/Method | 9 | Extract, inline, split functions |
| Conditional Logic | 8 | Simplify, guard clauses, dict dispatch |
| Variable & Data | 9 | Magic numbers, encapsulation, inline |
| Class & Object | 9 | Extract class, god class, composition |
| Module & File | 6 | Reorganize packages |
| Python-Specific | 10 | Comprehensions, f-strings, dataclass |
| Performance | 6 | Generators, caching, algorithms |
| Error Handling | 5 | Exceptions, result objects |
| Architecture | 7 | DI, SRP, separate I/O |
| Testing | 5 | Type hints, dead code |
| Code Style | 5 | Formatting, self-documenting |
| **TOTAL** | **84+** | Core patterns |

*Note: Including sub-patterns and variations, the system handles 100+ refactoring scenarios.*

---

## 🔬 AST Node Types Used

| AST Node | Usage |
|----------|-------|
| `ast.Module` | Root of parsed code |
| `ast.FunctionDef` | Function definitions |
| `ast.AsyncFunctionDef` | Async function definitions |
| `ast.ClassDef` | Class definitions |
| `ast.Return` | Return statements |
| `ast.Assign` | Variable assignments |
| `ast.AugAssign` | Augmented assignments (+=) |
| `ast.For` | For loops |
| `ast.While` | While loops |
| `ast.If` | If statements |
| `ast.Compare` | Comparison operations |
| `ast.BoolOp` | Boolean operations (and/or) |
| `ast.BinOp` | Binary operations (+, -, *, /) |
| `ast.UnaryOp` | Unary operations (not, -) |
| `ast.Call` | Function calls |
| `ast.Name` | Variable references |
| `ast.Constant` | Literal values |
| `ast.List` | List literals |
| `ast.ListComp` | List comprehensions |
| `ast.GeneratorExp` | Generator expressions |
| `ast.JoinedStr` | F-strings |
| `ast.FormattedValue` | F-string placeholders |
| `ast.Expr` | Expression statements |
| `ast.IfExp` | Ternary expressions |

---

## 📚 References

- Python AST Documentation: https://docs.python.org/3/library/ast.html
- Radon (Code Metrics): https://radon.readthedocs.io/
- Astor (AST to Source): https://astor.readthedocs.io/
- Bandit (Security): https://bandit.readthedocs.io/
- Refactoring (Martin Fowler): https://refactoring.com/catalog/

---

*Documentation generated for OptiCode AI Services - IT22606860*
