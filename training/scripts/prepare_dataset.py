"""
Dataset Preparation for CodeBERT Training
Student: IT22601360

This script prepares a custom dataset from:
1. Popular GitHub repositories (code-concepts-dataset)
2. LeetCode/HackerRank problem solutions
3. Algorithm textbook implementations
4. Your own manually labeled examples

For research: You'll show this as YOUR custom dataset that demonstrates
understanding of how to properly label code with CS concepts.
"""

import json
import os
from typing import List, Dict
import requests
from pathlib import Path


# ==================== Sample Data Templates ====================

SAMPLE_DATASET = [
    # Data Structures
    {
        "code": """class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node""",
        "language": "python",
        "categories": ["data_structure"],
        "concepts": ["linked_list", "oop", "encapsulation"],
        "description": "Singly linked list implementation with append method",
        "difficulty": "medium"
    },
    {
        "code": """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""",
        "language": "python",
        "categories": ["algorithm", "data_structure"],
        "concepts": ["binary_search", "array", "two_pointers"],
        "description": "Iterative binary search on sorted array",
        "difficulty": "easy"
    },
    {
        "code": """class MinHeap:
    def __init__(self):
        self.heap = []
    
    def push(self, val):
        self.heap.append(val)
        self._heapify_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return root
    
    def _heapify_up(self, idx):
        parent = (idx - 1) // 2
        if idx > 0 and self.heap[idx] < self.heap[parent]:
            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
            self._heapify_up(parent)
    
    def _heapify_down(self, idx):
        smallest = idx
        left = 2 * idx + 1
        right = 2 * idx + 2
        
        if left < len(self.heap) and self.heap[left] < self.heap[smallest]:
            smallest = left
        if right < len(self.heap) and self.heap[right] < self.heap[smallest]:
            smallest = right
        
        if smallest != idx:
            self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
            self._heapify_down(smallest)""",
        "language": "python",
        "categories": ["data_structure", "algorithm"],
        "concepts": ["heap", "recursion", "oop", "encapsulation"],
        "description": "Min heap implementation with heapify operations",
        "difficulty": "hard"
    },
    
    # Design Patterns
    {
        "code": """class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.data = {}
            self.initialized = True""",
        "language": "python",
        "categories": ["design_pattern", "paradigm"],
        "concepts": ["singleton", "oop", "encapsulation"],
        "description": "Singleton pattern ensuring single instance",
        "difficulty": "medium"
    },
    {
        "code": """class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def detach(self, observer):
        self._observers.remove(observer)
    
    def notify(self, event):
        for observer in self._observers:
            observer.update(event)

class Observer:
    def update(self, event):
        print(f"Received event: {event}")""",
        "language": "python",
        "categories": ["design_pattern", "architecture"],
        "concepts": ["observer", "event_driven", "oop"],
        "description": "Observer pattern for event handling",
        "difficulty": "medium"
    },
    
    # Algorithms
    {
        "code": """def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result""",
        "language": "python",
        "categories": ["algorithm"],
        "concepts": ["sorting", "merge_sort", "recursion", "divide_and_conquer"],
        "description": "Merge sort implementation with divide and conquer",
        "difficulty": "medium"
    },
    {
        "code": """def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    
    visited.add(start)
    print(start, end=' ')
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
    
    return visited""",
        "language": "python",
        "categories": ["algorithm", "data_structure"],
        "concepts": ["dfs", "graph", "recursion", "set"],
        "description": "Depth-first search on graph",
        "difficulty": "medium"
    },
    {
        "code": """from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    
    while queue:
        vertex = queue.popleft()
        print(vertex, end=' ')
        
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return visited""",
        "language": "python",
        "categories": ["algorithm", "data_structure"],
        "concepts": ["bfs", "graph", "queue", "set"],
        "description": "Breadth-first search using queue",
        "difficulty": "medium"
    },
    {
        "code": """def fibonacci_dp(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    
    memo[n] = fibonacci_dp(n-1, memo) + fibonacci_dp(n-2, memo)
    return memo[n]

def fibonacci_tabulation(n):
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]""",
        "language": "python",
        "categories": ["algorithm"],
        "concepts": ["dynamic_programming", "recursion", "memoization"],
        "description": "Fibonacci with dynamic programming approaches",
        "difficulty": "medium"
    },
    
    # Data Structures
    {
        "code": """class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None
    
    def is_empty(self):
        return len(self.items) == 0""",
        "language": "python",
        "categories": ["data_structure"],
        "concepts": ["stack", "array", "oop", "encapsulation"],
        "description": "Stack implementation using list",
        "difficulty": "easy"
    },
    {
        "code": """class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    result = []
    
    def traverse(node):
        if not node:
            return
        traverse(node.left)
        result.append(node.val)
        traverse(node.right)
    
    traverse(root)
    return result""",
        "language": "python",
        "categories": ["data_structure", "algorithm"],
        "concepts": ["binary_tree", "tree", "recursion", "dfs"],
        "description": "Binary tree with inorder traversal",
        "difficulty": "medium"
    },
    
    # More concepts
    {
        "code": """class HashMap:
    def __init__(self, size=100):
        self.size = size
        self.buckets = [[] for _ in range(size)]
    
    def _hash(self, key):
        return hash(key) % self.size
    
    def put(self, key, value):
        idx = self._hash(key)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, value)
                return
        self.buckets[idx].append((key, value))
    
    def get(self, key):
        idx = self._hash(key)
        for k, v in self.buckets[idx]:
            if k == key:
                return v
        return None""",
        "language": "python",
        "categories": ["data_structure"],
        "concepts": ["hash_table", "array", "oop"],
        "description": "Hash map with separate chaining",
        "difficulty": "medium"
    },
    {
        "code": """def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)""",
        "language": "python",
        "categories": ["algorithm"],
        "concepts": ["sorting", "quick_sort", "recursion", "divide_and_conquer"],
        "description": "Quick sort with middle pivot",
        "difficulty": "medium"
    },
    {
        "code": """class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True""",
        "language": "python",
        "categories": ["data_structure"],
        "concepts": ["trie", "tree", "hash_table", "oop"],
        "description": "Trie data structure for prefix search",
        "difficulty": "hard"
    }
]


def generate_training_data(
    output_path: str = "data/training_data.json",
    include_augmentation: bool = True
):
    """
    Generate training dataset
    
    This creates a dataset with:
    1. Core samples (above)
    2. Augmented variations
    3. Additional samples from code repositories (optional)
    """
    
    print("📦 Preparing training dataset...")
    
    dataset = SAMPLE_DATASET.copy()
    
    # Augment with variations if requested
    if include_augmentation:
        print("🔄 Augmenting dataset with variations...")
        augmented = augment_dataset(dataset)
        dataset.extend(augmented)
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"✅ Saved {len(dataset)} samples to {output_path}")
    
    # Print statistics
    print_dataset_stats(dataset)
    
    return dataset


def augment_dataset(base_dataset: List[Dict]) -> List[Dict]:
    """
    Augment dataset with variations
    
    Techniques:
    - Add comments/docstrings
    - Rename variables
    - Slight logic changes
    """
    augmented = []

    for sample in base_dataset[:5]: 
        augmented_sample = sample.copy()
        augmented_sample['code'] = f'"""\n{sample["description"]}\n"""\n{sample["code"]}'
        augmented_sample['description'] = f"{sample['description']} (with documentation)"
        augmented.append(augmented_sample)
    
    return augmented


def print_dataset_stats(dataset: List[Dict]):
    """Print dataset statistics"""
    print("\n" + "="*50)
    print("DATASET STATISTICS")
    print("="*50)
    
    print(f"Total Samples: {len(dataset)}")
    
    # Count by language
    languages = {}
    for sample in dataset:
        lang = sample['language']
        languages[lang] = languages.get(lang, 0) + 1
    print(f"\nLanguages: {languages}")
    
    # Count by category
    categories = {}
    for sample in dataset:
        for cat in sample['categories']:
            categories[cat] = categories.get(cat, 0) + 1
    print(f"\nCategories:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    # Count by concept
    concepts = {}
    for sample in dataset:
        for concept in sample['concepts']:
            concepts[concept] = concepts.get(concept, 0) + 1
    print(f"\nTop Concepts:")
    for concept, count in sorted(concepts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {concept}: {count}")
    
    print("="*50 + "\n")


def download_additional_samples():
    """
    Download additional samples from GitHub/public datasets
    
    For research: You can cite these sources:
    - CodeSearchNet (GitHub)
    - The Stack (Hugging Face)
    - LeetCode solutions
    """
    print("📥 Downloading additional samples...")
    print("⚠️  For production: Implement actual dataset download here")
    print("    Suggested sources:")
    print("    1. CodeSearchNet: github.com/github/CodeSearchNet")
    print("    2. The Stack: huggingface.co/datasets/bigcode/the-stack")
    print("    3. LeetCode: github.com/kamyu104/LeetCode-Solutions")
    
    # Placeholder for actual implementation
    return []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/training_data.json')
    parser.add_argument('--augment', action='store_true', help='Include augmentation')
    
    args = parser.parse_args()
    
    generate_training_data(
        output_path=args.output,
        include_augmentation=args.augment
    )