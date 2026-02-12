"""
Quick Fix: Working Range-Len Transformer
This demonstrates how transformers should actually MODIFY the AST
"""

import ast
import astor

def fix_range_len_loops(code: str) -> str:
    """
    Simple working transformer that ACTUALLY fixes range(len()) patterns
    
    Transforms:
        for i in range(len(items)):
            print(items[i])
    
    To:
        for i, item in enumerate(items):
            print(item)
    """
    
    class RangeLenFixer(ast.NodeTransformer):
        def __init__(self):
            self.changes = 0
            
        def visit_For(self, node):
            # Pattern: for i in range(len(items)):
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                    if len(node.iter.args) == 1:
                        arg = node.iter.args[0]
                        # Check if it's range(len(something))
                        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                            if len(arg.args) == 1:
                                list_name = arg.args[0]
                                
                                # Get the index variable name
                                if isinstance(node.target, ast.Name):
                                    index_var = node.target.id
                                    
                                    # Create new item variable name
                                    if isinstance(list_name, ast.Name):
                                        item_name = list_name.id.rstrip('s')  # items -> item
                                        if item_name == list_name.id:
                                            item_name = 'item'
                                        
                                        # Transform to enumerate
                                        new_target = ast.Tuple(
                                            elts=[ast.Name(id=index_var, ctx=ast.Store()), 
                                                  ast.Name(id=item_name, ctx=ast.Store())],
                                            ctx=ast.Store()
                                        )
                                        new_iter = ast.Call(
                                            func=ast.Name(id='enumerate', ctx=ast.Load()),
                                            args=[list_name],
                                            keywords=[]
                                        )
                                        
                                        node.target = new_target
                                        node.iter = new_iter
                                        self.changes += 1
                                        print(f"✅ Fixed range(len()) pattern to enumerate()")
            
            # Continue visiting child nodes
            self.generic_visit(node)
            return node
    
    try:
        tree = ast.parse(code)
        fixer = RangeLenFixer()
        tree = fixer.visit(tree)
        ast.fix_missing_locations(tree)
        
        refactored = astor.to_source(tree)
        print(f"Total fixes applied: {fixer.changes}")
        return refactored
    except Exception as e:
        print(f"Error: {e}")
        return code


# Test it
if __name__ == "__main__":
    test_code = """
def example():
    items = [1, 2, 3, 4, 5]
    for i in range(len(items)):
        print(items[i])
"""
    
    print("ORIGINAL:")
    print(test_code)
    print("\nREFACTORED:")
    result = fix_range_len_loops(test_code)
    print(result)
