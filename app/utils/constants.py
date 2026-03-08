"""
Constants and Configuration for Code Concept Extractor
"""

# Supported programming languages
SUPPORTED_LANGUAGES = {
    "python": {
        "extensions": [".py"],
        "comment_single": "#",
        "comment_multi_start": '"""',
        "comment_multi_end": '"""'
    },
    "javascript": {
        "extensions": [".js", ".jsx"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "java": {
        "extensions": [".java"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "cpp": {
        "extensions": [".cpp", ".cc", ".cxx", ".c++", ".h", ".hpp"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "c": {
        "extensions": [".c", ".h"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "csharp": {
        "extensions": [".cs"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "go": {
        "extensions": [".go"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "rust": {
        "extensions": [".rs"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "php": {
        "extensions": [".php"],
        "comment_single": "//",
        "comment_multi_start": "/*",
        "comment_multi_end": "*/"
    },
    "ruby": {
        "extensions": [".rb"],
        "comment_single": "#",
        "comment_multi_start": "=begin",
        "comment_multi_end": "=end"
    }
}

# Concept categories
CONCEPT_CATEGORIES = [
    "data_structure",
    "algorithm",
    "design_pattern",
    "architecture",
    "paradigm",
    "programming_concept"
]

# Known concepts for pattern matching (used before LLM)
# More precise patterns using regex-compatible strings
KNOWN_CONCEPTS = {
    "data_structures": {
        "array": [r"\barray\b", r"\blist\s*=", r"\[\s*\]", r"Array\("],
        "linked_list": [r"LinkedList", r"ListNode", r"\.next\s*=", r"self\.next", r"this\.next"],
        "stack": [r"\bstack\b", r"\.push\(", r"\.pop\(", r"LIFO", r"Stack\("],
        "queue": [r"\bqueue\b", r"\.enqueue\(", r"\.dequeue\(", r"FIFO", r"Queue\(", r"from collections import deque"],
        "tree": [r"TreeNode", r"\.root\b", r"\.left\b", r"\.right\b", r"\.children\b"],
        "binary_tree": [r"BinaryTree", r"left_child", r"right_child", r"inorder", r"preorder", r"postorder"],
        "binary_search_tree": [r"\bBST\b", r"BinarySearchTree"],
        "heap": [r"\bheap\b", r"heapify", r"heappush", r"heappop", r"MinHeap", r"MaxHeap"],
        "hash_table": [r"\bhash\b.*table", r"HashMap", r"HashSet", r"\bdict\s*=", r"dictionary"],
        "graph": [r"\bGraph\b", r"vertex", r"\.edge\b", r"adjacent", r"neighbors", r"addEdge"],
        "trie": [r"\bTrie\b", r"TrieNode", r"\.prefix\b", r"startsWith"],
        "set": [r"\bSet\(", r"set\(\)", r"HashSet", r"TreeSet"]
    },
    
    "algorithms": {
        "sorting": [r"\.sort\(", r"sorted\(", r"bubble.*sort", r"quick.*sort", r"merge.*sort"],
        "binary_search": [r"binary_search", r"\bleft\b.*\bright\b.*\bmid\b", r"\blow\b.*\bhigh\b"],
        "linear_search": [r"linear_search", r"for\s+\w+\s+in.*if.*=="],
        "recursion": [r"def\s+(\w+)\(.*\):.*\n.*\1\("],  # Function calls itself
        "dynamic_programming": [r"\bdp\b", r"\bmemo\b", r"@cache", r"@lru_cache", r"memoization"],
        "greedy": [r"greedy", r"local.*optimal"],
        "backtracking": [r"backtrack", r"backtracking"],
        "divide_and_conquer": [r"divide.*conquer"],
        "bfs": [r"\bBFS\b", r"breadth.*first", r"from collections import deque.*queue"],
        "dfs": [r"\bDFS\b", r"depth.*first"],
        "two_pointers": [r"two.*pointer", r"\bleft\b.*=.*0.*\bright\b.*=.*len"],
        "sliding_window": [r"sliding.*window"]
    },
    
    "design_patterns": {
        "singleton": [r"_instance\s*=\s*None", r"__new__", r"getInstance"],
        "factory": [r"Factory", r"create_\w+", r"factory_method"],
        "observer": [r"Observer", r"\.subscribe\(", r"\.notify\(", r"\.emit\("],
        "strategy": [r"Strategy", r"set_strategy", r"execute.*algorithm"],
        "decorator": [r"@\w+\s*\n\s*def", r"wrapper.*def"],  # Only actual decorators
        "adapter": [r"Adapter", r"class.*Adapter"],
        "facade": [r"Facade"],
        "builder": [r"Builder", r"\.build\("],
        "prototype": [r"Prototype", r"\.clone\(", r"deepcopy"],
        "command": [r"Command", r"\.execute\(", r"\.undo\("],
        "mvc": [r"Model.*View.*Controller", r"\bMVC\b"],
        "repository": [r"Repository", r"findAll", r"findById"]
    },
    
    "architectures": {
        "layered": [r"layer.*architecture", r"service.*layer.*repository"],
        "microservices": [r"microservice"],
        "event_driven": [r"event.*driven", r"EventEmitter"],
        "rest_api": [r"@app\.", r"@router\.", r"@get\(", r"@post\(", r"GET.*POST.*PUT"],
        "mvc_architecture": [r"render.*template"]
    },
    
    "paradigms": {
        "oop": [r"class\s+\w+.*:", r"self\.", r"this\.", r"__init__"],  # Must have class
        "functional": [r"\blambda\b", r"map\(", r"filter\(", r"reduce\("],
        "procedural": [r"^def\s+\w+\(.*\):(?!.*class)"],  # Function but no class context
        "reactive": [r"Observable", r"\.subscribe\(", r"async.*await"]
    },
    
    "programming_concepts": {
        # ⚠️ FIX: Only match REAL encapsulation (class + private members)
        "encapsulation": [
            r"class\s+\w+:.*\n.*self\.__\w+",  # Private attributes
            r"@property",  # Property decorators
            r"def\s+get_\w+\(self\)",  # Getter methods
            r"def\s+set_\w+\(self"  # Setter methods
        ],
        "inheritance": [r"class\s+\w+\([^)]+\):", r"super\(\)\."],
        "polymorphism": [r"@override", r"@abstractmethod", r"def.*override"],
        "abstraction": [r"from abc import", r"ABC", r"@abstractmethod"],
        "exception_handling": [r"\btry\b:\s*\n.*except", r"\braise\b"],
        "async_programming": [r"\basync\s+def\b", r"\bawait\b"],
        "generics": [r"<T>", r"Generic\[", r"TypeVar"],
        "closures": [r"def\s+\w+\(.*\):.*\n.*def\s+\w+\("],  # Nested function
        "iterators": [r"__iter__", r"__next__", r"\byield\b"],
        # ⚠️ FIX: Only match REAL type hints
        "type_hints": [
            r"def\s+\w+\([^)]*:\s*\w+[,\)]",  # Argument with type
            r"->\s*\w+:",  # Return type
            r":\s*List\[", r":\s*Dict\[", r":\s*Optional\["
        ],
        "loop": [r"\bfor\b", r"\bwhile\b"],
        "conditional": [r"\bif\b", r"\belse\b", r"\belif\b"]
    }
}
# Concept descriptions for explanations
CONCEPT_DESCRIPTIONS = {
    "array": "A collection of elements stored at contiguous memory locations, accessed by index.",
    "linked_list": "A linear data structure where elements are linked using pointers.",
    "stack": "A LIFO (Last In First Out) data structure supporting push and pop operations.",
    "queue": "A FIFO (First In First Out) data structure supporting enqueue and dequeue operations.",
    "tree": "A hierarchical data structure with nodes connected by edges, having a root and children.",
    "binary_tree": "A tree where each node has at most two children (left and right).",
    "binary_search_tree": "A binary tree maintaining sorted order for efficient searching.",
    "heap": "A tree-based structure satisfying the heap property (min-heap or max-heap).",
    "hash_table": "A data structure mapping keys to values using a hash function.",
    "graph": "A non-linear structure consisting of vertices connected by edges.",
    "trie": "A tree-like structure for storing strings, optimized for prefix searches.",
    "sorting": "Algorithms that arrange elements in a specific order (ascending/descending).",
    "binary_search": "An efficient O(log n) search algorithm for sorted arrays.",
    "recursion": "A technique where a function calls itself to solve smaller subproblems.",
    "dynamic_programming": "Optimization technique breaking problems into overlapping subproblems.",
    "bfs": "Breadth-First Search: explores all neighbors at current depth before going deeper.",
    "dfs": "Depth-First Search: explores as far as possible along each branch before backtracking.",
    "singleton": "A design pattern ensuring a class has only one instance.",
    "factory": "A pattern for creating objects without specifying their exact class.",
    "observer": "A pattern where objects subscribe to events and get notified of changes.",
    "decorator": "A pattern that adds behavior to objects dynamically.",
    "oop": "Object-Oriented Programming: organizing code into objects with state and behavior.",
    "functional": "Programming paradigm treating computation as evaluation of mathematical functions."
}

# Colors for visualization
CATEGORY_COLORS = {
    "data_structure": "#4CAF50",    # Green
    "algorithm": "#2196F3",          # Blue
    "design_pattern": "#9C27B0",     # Purple
    "architecture": "#FF9800",       # Orange
    "paradigm": "#E91E63",           # Pink
    "programming_concept": "#00BCD4" # Cyan
}
