"""
Smart Recommendations Engine
Provides contextual Python best practices recommendations
"""

from typing import List, Dict

class RecommendationsEngine:
    
    def get_recommendations(self, violations: List[dict]) -> List[Dict]:
        """Generate smart recommendations based on violations"""
        
        recommendations = []
        
        # Group violations by category
        by_category = {}
        for v in violations:
            category = v.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(v)
        
        # Generate recommendations for each category
        if 'pythonic' in by_category:
            recommendations.append(self._pythonic_recommendation(by_category['pythonic']))
        
        if 'pep8' in by_category:
            recommendations.append(self._pep8_recommendation(by_category['pep8']))
        
        if 'anti-pattern' in by_category:
            recommendations.append(self._antipattern_recommendation(by_category['anti-pattern']))
        
        return recommendations
    
    def _pythonic_recommendation(self, violations: List[dict]) -> Dict:
        """Pythonic patterns recommendation"""
        return {
            'title': '🐍 Make Your Code More Pythonic',
            'summary': f'Found {len(violations)} opportunities to write more idiomatic Python',
            'priority': 'medium',
            'tips': [
                'Use list comprehensions instead of loops with append()',
                'Prefer enumerate() over range(len())',
                'Use f-strings for string formatting (Python 3.6+)',
                'Context managers (with) for resource handling',
                'Dictionary get() method with defaults instead of if-else'
            ],
            'example': {
                'bad': 'result = []\nfor i in range(len(items)):\n    result.append(items[i] * 2)',
                'good': 'result = [item * 2 for item in items]',
                'explanation': 'List comprehensions are more readable, faster, and Pythonic'
            },
            'resources': [
                {'title': 'PEP 8 Style Guide', 'url': 'https://pep8.org'},
                {'title': 'The Zen of Python', 'url': 'https://www.python.org/dev/peps/pep-0020/'},
                {'title': 'Effective Python', 'url': 'https://effectivepython.com/'}
            ]
        }
    
    def _pep8_recommendation(self, violations: List[dict]) -> Dict:
        """PEP 8 style recommendation"""
        return {
            'title': '📐 PEP 8 Style Guide Compliance',
            'summary': f'Found {len(violations)} style guide violations',
            'priority': 'low',
            'tips': [
                'Use snake_case for functions and variables',
                'Use PascalCase for class names',
                'Use UPPER_SNAKE_CASE for constants',
                'Limit lines to 79 characters (or 99 for code)',
                'Add docstrings to public functions and classes',
                'Two blank lines between top-level definitions'
            ],
            'example': {
                'bad': 'def calculateTotal():\n    pass',
                'good': 'def calculate_total():\n    """Calculate the total sum."""\n    pass',
                'explanation': 'Follow PEP 8 naming conventions and add docstrings for clarity'
            },
            'resources': [
                {'title': 'PEP 8', 'url': 'https://pep8.org'},
                {'title': 'PEP 257 Docstrings', 'url': 'https://pep257.readthedocs.io/'},
                {'title': 'Black Formatter', 'url': 'https://black.readthedocs.io/'}
            ]
        }
    
    def _antipattern_recommendation(self, violations: List[dict]) -> Dict:
        """Anti-patterns recommendation"""
        return {
            'title': '⚠️ Avoid Common Anti-Patterns',
            'summary': f'Found {len(violations)} anti-patterns to fix',
            'priority': 'high',
            'tips': [
                'Never use mutable default arguments ([], {}, etc.)',
                'Avoid bare except clauses - use specific exceptions',
                'Don\'t modify a list while iterating over it',
                'Close files properly using context managers (with)',
                'Use "is None" instead of "== None" for comparisons'
            ],
            'example': {
                'bad': 'def add_item(item, items=[]):\n    items.append(item)\n    return items',
                'good': 'def add_item(item, items=None):\n    if items is None:\n        items = []\n    items.append(item)\n    return items',
                'explanation': 'Mutable default arguments are shared across function calls - common bug!'
            },
            'resources': [
                {'title': 'Common Pitfalls', 'url': 'https://docs.python-guide.org/writing/gotchas/'},
                {'title': 'Python Anti-Patterns', 'url': 'https://docs.quantifiedcode.com/python-anti-patterns/'}
            ]
        }