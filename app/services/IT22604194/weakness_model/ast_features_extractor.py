import ast

def extract_basic_ast_features(code_text: str):
    features = {
        "loc": 0, "num_functions": 0, "num_classes": 0, "max_nesting_depth": 0,
        "num_if": 0, "num_for": 0, "num_while": 0, "num_return": 0,
        "num_try": 0, "num_recursion_calls": 0, "has_recursion": 0,
        "cyclomatic_est": 1
    }

    if not code_text:
        return features

    features["loc"] = len(code_text.splitlines())

    try:
        tree = ast.parse(code_text)
    except:
        features["syntax_error_parse"] = 1
        return features

    # count everything in the AST
    func_names = set()

    # nesting depth
    def visit(node, depth=0):
        features["max_nesting_depth"] = max(features["max_nesting_depth"], depth)
        for child in ast.iter_child_nodes(node):
            visit(child, depth+1)

    visit(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            features["num_functions"] += 1
            func_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            features["num_classes"] += 1
        elif isinstance(node, ast.If):
            features["num_if"] += 1
        elif isinstance(node, ast.For):
            features["num_for"] += 1
        elif isinstance(node, ast.While):
            features["num_while"] += 1
        elif isinstance(node, ast.Return):
            features["num_return"] += 1
        elif isinstance(node, ast.Try):
            features["num_try"] += 1
        elif isinstance(node, ast.Call):
            fn = getattr(node.func, 'id', None)
            if fn in func_names:
                features["num_recursion_calls"] += 1

    features["has_recursion"] = 1 if features["num_recursion_calls"] > 0 else 0
    features["cyclomatic_est"] = 1 + features["num_if"] + features["num_for"] + features["num_while"] + features["num_try"]

    return features
