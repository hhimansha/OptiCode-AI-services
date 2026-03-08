"""
Learning API - Educational Content Server
Provides educational content about refactoring, best practices, code analysis, etc.
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/learning_api.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, List

app = Flask(__name__)
CORS(app)  # Enable CORS for React


# ============================================
# EDUCATIONAL CONTENT DATABASE
# ============================================

LEARNING_CONTENT = {
    'refactoring': {
        'title': 'Code Refactoring Methods',
        'description': 'Learn various code refactoring techniques to improve code quality',
        'topics': {
            'extract_method': {
                'name': 'Extract Method',
                'description': 'Extract a code fragment into a new method to improve readability and reusability',
                'when_to_use': 'When you have a code fragment that can be grouped together',
                'benefits': ['Improves readability', 'Reduces duplication', 'Easier to test'],
                'example': {
                    'before': '''def process_order(order):
    # Validate order
    if not order.customer:
        raise ValueError("No customer")
    if not order.items:
        raise ValueError("No items")
    
    # Calculate total
    total = 0
    for item in order.items:
        total += item.price * item.quantity
    
    # Apply discount
    if order.customer.is_vip:
        total *= 0.9
    
    return total''',
                    'after': '''def process_order(order):
    validate_order(order)
    total = calculate_total(order.items)
    total = apply_discount(total, order.customer)
    return total

def validate_order(order):
    if not order.customer:
        raise ValueError("No customer")
    if not order.items:
        raise ValueError("No items")

def calculate_total(items):
    return sum(item.price * item.quantity for item in items)

def apply_discount(total, customer):
    return total * 0.9 if customer.is_vip else total'''
                }
            },
            'rename_variable': {
                'name': 'Rename Variable',
                'description': 'Give variables more meaningful names',
                'when_to_use': 'When variable names are unclear or misleading',
                'benefits': ['Improves code clarity', 'Self-documenting code', 'Easier maintenance'],
                'example': {
                    'before': 'def calc(a, b, c):\n    x = a * b\n    y = x + c\n    return y',
                    'after': 'def calculate_total_price(unit_price, quantity, shipping_cost):\n    subtotal = unit_price * quantity\n    total = subtotal + shipping_cost\n    return total'
                }
            },
            'simplify_conditional': {
                'name': 'Simplify Conditional',
                'description': 'Make complex conditionals easier to understand',
                'when_to_use': 'When you have complicated conditional logic',
                'benefits': ['Easier to read', 'Fewer bugs', 'Better testability'],
                'example': {
                    'before': 'if status == "active":\n    return True\nelse:\n    return False',
                    'after': 'return status == "active"'
                }
            },
            'remove_magic_numbers': {
                'name': 'Replace Magic Numbers',
                'description': 'Replace unnamed numerical constants with named constants',
                'when_to_use': 'When you have unexplained numbers in your code',
                'benefits': ['Clearer intent', 'Easier to maintain', 'Single point of change'],
                'example': {
                    'before': 'if age >= 18 and age <= 65:\n    discount = price * 0.1',
                    'after': 'ADULT_AGE = 18\nRETIREMENT_AGE = 65\nADULT_DISCOUNT_RATE = 0.1\n\nif ADULT_AGE <= age <= RETIREMENT_AGE:\n    discount = price * ADULT_DISCOUNT_RATE'
                }
            }
        }
    },
    'best_practices': {
        'title': 'Python Best Practices',
        'description': 'Essential best practices for writing clean Python code',
        'topics': {
            'solid': {
                'name': 'SOLID Principles',
                'description': 'Five fundamental principles for object-oriented design',
                'principles': [
                    {
                        'name': 'Single Responsibility Principle (SRP)',
                        'description': 'A class should have only one reason to change',
                        'example': 'Separate data persistence logic from business logic'
                    },
                    {
                        'name': 'Open/Closed Principle (OCP)',
                        'description': 'Open for extension, closed for modification',
                        'example': 'Use inheritance and polymorphism instead of modifying existing code'
                    },
                    {
                        'name': 'Liskov Substitution Principle (LSP)',
                        'description': 'Subtypes must be substitutable for their base types',
                        'example': 'Derived classes should extend, not replace, base class behavior'
                    },
                    {
                        'name': 'Interface Segregation Principle (ISP)',
                        'description': 'Clients should not depend on interfaces they don\'t use',
                        'example': 'Create specific interfaces rather than one general-purpose interface'
                    },
                    {
                        'name': 'Dependency Inversion Principle (DIP)',
                        'description': 'Depend on abstractions, not concretions',
                        'example': 'Use dependency injection and abstract interfaces'
                    }
                ]
            },
            'dry': {
                'name': 'DRY - Don\'t Repeat Yourself',
                'description': 'Every piece of knowledge should have a single, unambiguous representation',
                'benefits': ['Easier maintenance', 'Fewer bugs', 'Consistent behavior'],
                'example': {
                    'bad': 'def get_full_name_1(first, last):\n    return f"{first} {last}"\n\ndef get_full_name_2(first, last):\n    return f"{first} {last}"',
                    'good': 'def get_full_name(first, last):\n    return f"{first} {last}"\n\n# Reuse the same function everywhere'
                }
            },
            'pep8': {
                'name': 'PEP 8 Style Guide',
                'description': 'Python\'s official style guide',
                'key_points': [
                    'Use 4 spaces for indentation',
                    'Limit lines to 79 characters',
                    'Use snake_case for functions and variables',
                    'Use PascalCase for class names',
                    'Use UPPERCASE for constants',
                    'Add docstrings to functions and classes',
                    'Use meaningful variable names'
                ]
            }
        }
    },
    'code_analysis': {
        'title': 'Code Analysis Techniques',
        'description': 'Learn how to analyze and improve code quality',
        'topics': {
            'complexity': {
                'name': 'Cyclomatic Complexity',
                'description': 'Measure of code complexity based on decision points',
                'interpretation': {
                    '1-10': 'Simple, easy to test',
                    '11-20': 'Moderate complexity, consider refactoring',
                    '21+': 'High complexity, difficult to maintain and test'
                },
                'how_to_reduce': [
                    'Extract methods',
                    'Simplify conditionals',
                    'Use early returns',
                    'Replace nested loops with helper functions'
                ]
            },
            'maintainability': {
                'name': 'Maintainability Index',
                'description': 'Measure of how maintainable code is',
                'scale': {
                    '0-9': 'Difficult to maintain',
                    '10-19': 'Moderate maintainability',
                    '20+': 'Highly maintainable'
                },
                'factors': [
                    'Cyclomatic complexity',
                    'Lines of code',
                    'Halstead volume',
                    'Comment ratio'
                ]
            },
            'code_smells': {
                'name': 'Common Code Smells',
                'description': 'Indicators of potential problems in code',
                'smells': [
                    {
                        'name': 'Long Method',
                        'description': 'Methods with too many lines',
                        'solution': 'Extract smaller methods'
                    },
                    {
                        'name': 'Large Class',
                        'description': 'Classes doing too much',
                        'solution': 'Split into focused classes'
                    },
                    {
                        'name': 'Long Parameter List',
                        'description': 'Too many function parameters',
                        'solution': 'Use parameter objects or reduce parameters'
                    },
                    {
                        'name': 'Duplicate Code',
                        'description': 'Same code in multiple places',
                        'solution': 'Extract common code into functions'
                    }
                ]
            }
        }
    },
    'security': {
        'title': 'Secure Coding Practices',
        'description': 'Best practices for writing secure code',
        'topics': {
            'input_validation': {
                'name': 'Input Validation',
                'description': 'Always validate and sanitize user input',
                'practices': [
                    'Validate type, length, format, and range',
                    'Use allowlists over denylists',
                    'Escape special characters',
                    'Never trust client-side validation alone'
                ],
                'example': '''# Good practice
def process_age(age_str):
    try:
        age = int(age_str)
        if not (0 <= age <= 150):
            raise ValueError("Age out of range")
        return age
    except ValueError:
        raise ValueError("Invalid age format")'''
            },
            'sql_injection': {
                'name': 'SQL Injection Prevention',
                'description': 'Prevent SQL injection attacks',
                'practices': [
                    'Use parameterized queries',
                    'Use ORM frameworks',
                    'Never concatenate user input into SQL',
                    'Apply principle of least privilege'
                ],
                'example': '''# Bad
query = f"SELECT * FROM users WHERE username = '{username}'"

# Good
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))'''
            },
            'sensitive_data': {
                'name': 'Sensitive Data Protection',
                'description': 'Protect sensitive information',
                'practices': [
                    'Never hardcode credentials',
                    'Use environment variables',
                    'Encrypt sensitive data',
                    'Hash passwords with bcrypt or argon2',
                    'Use HTTPS for data transmission',
                    'Implement proper access controls'
                ]
            }
        }
    },
    'ethical_coding': {
        'title': 'Ethical Coding Practices',
        'description': 'Code with responsibility and inclusivity',
        'topics': {
            'inclusive_language': {
                'name': 'Inclusive Language',
                'description': 'Use inclusive terminology in code',
                'replacements': {
                    'master/slave': 'primary/replica, leader/follower',
                    'whitelist/blacklist': 'allowlist/blocklist',
                    'dummy': 'placeholder, sample, mock',
                    'sanity check': 'validation check, verification'
                },
                'importance': 'Creates welcoming environment for all developers'
            },
            'privacy': {
                'name': 'Privacy by Design',
                'description': 'Build privacy into your applications',
                'principles': [
                    'Collect only necessary data',
                    'Implement data minimization',
                    'Provide transparency about data usage',
                    'Give users control over their data',
                    'Secure data storage and transmission',
                    'Comply with privacy regulations (GDPR, CCPA)'
                ]
            },
            'accessibility': {
                'name': 'Accessibility',
                'description': 'Make code outputs accessible to all users',
                'practices': [
                    'Provide text alternatives for visual content',
                    'Don\'t rely solely on color',
                    'Support keyboard navigation',
                    'Use clear, simple language',
                    'Test with screen readers'
                ]
            }
        }
    }
}


# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'learning-api',
        'categories': list(LEARNING_CONTENT.keys()),
        'endpoints': {
            '/api/categories': 'GET - List all learning categories',
            '/api/category/<name>': 'GET - Get content for specific category',
            '/api/topic/<category>/<topic>': 'GET - Get specific topic details',
            '/api/search': 'GET - Search learning content',
            '/health': 'GET - Health check'
        }
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all learning categories"""
    
    categories = []
    for key, content in LEARNING_CONTENT.items():
        categories.append({
            'id': key,
            'title': content['title'],
            'description': content['description'],
            'topic_count': len(content['topics'])
        })
    
    return jsonify({
        'success': True,
        'categories': categories,
        'total': len(categories)
    })


@app.route('/api/category/<category_name>', methods=['GET'])
def get_category(category_name):
    """Get detailed content for a specific category"""
    
    if category_name not in LEARNING_CONTENT:
        return jsonify({
            'success': False,
            'message': f'Category "{category_name}" not found'
        }), 404
    
    content = LEARNING_CONTENT[category_name]
    
    # Format topics
    topics = []
    for topic_key, topic_data in content['topics'].items():
        topics.append({
            'id': topic_key,
            'name': topic_data.get('name', topic_key),
            'description': topic_data.get('description', ''),
            'has_example': 'example' in topic_data
        })
    
    return jsonify({
        'success': True,
        'category': {
            'id': category_name,
            'title': content['title'],
            'description': content['description'],
            'topics': topics
        }
    })


@app.route('/api/topic/<category_name>/<topic_name>', methods=['GET'])
def get_topic(category_name, topic_name):
    """Get detailed information about a specific topic"""
    
    if category_name not in LEARNING_CONTENT:
        return jsonify({
            'success': False,
            'message': f'Category "{category_name}" not found'
        }), 404
    
    category = LEARNING_CONTENT[category_name]
    
    if topic_name not in category['topics']:
        return jsonify({
            'success': False,
            'message': f'Topic "{topic_name}" not found in category "{category_name}"'
        }), 404
    
    topic = category['topics'][topic_name]
    
    return jsonify({
        'success': True,
        'topic': {
            'id': topic_name,
            'category': category_name,
            **topic
        }
    })


@app.route('/api/search', methods=['GET'])
def search():
    """Search learning content"""
    
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'No search query provided'
        }), 400
    
    results = []
    
    # Search through all content
    for category_key, category in LEARNING_CONTENT.items():
        # Check category title and description
        if query in category['title'].lower() or query in category['description'].lower():
            results.append({
                'type': 'category',
                'id': category_key,
                'title': category['title'],
                'description': category['description']
            })
        
        # Check topics
        for topic_key, topic in category['topics'].items():
            topic_name = topic.get('name', topic_key)
            topic_desc = topic.get('description', '')
            
            if query in topic_name.lower() or query in topic_desc.lower():
                results.append({
                    'type': 'topic',
                    'id': topic_key,
                    'category': category_key,
                    'name': topic_name,
                    'description': topic_desc
                })
    
    return jsonify({
        'success': True,
        'query': query,
        'results': results,
        'count': len(results)
    })


@app.route('/api/random-tip', methods=['GET'])
def random_tip():
    """Get a random coding tip"""
    
    import random
    
    tips = [
        {
            'category': 'Refactoring',
            'tip': 'Extract methods when a function does more than one thing',
            'example': 'Split complex functions into smaller, focused ones'
        },
        {
            'category': 'Best Practice',
            'tip': 'Use meaningful variable names that explain their purpose',
            'example': 'user_age instead of x, is_valid instead of flag'
        },
        {
            'category': 'Security',
            'tip': 'Never hardcode credentials - use environment variables',
            'example': 'api_key = os.getenv("API_KEY")'
        },
        {
            'category': 'Performance',
            'tip': 'Use list comprehensions instead of loops when appropriate',
            'example': 'squares = [x**2 for x in range(10)]'
        },
        {
            'category': 'Ethical',
            'tip': 'Use inclusive language: prefer "primary/replica" over "master/slave"',
            'example': 'Creates a welcoming environment for all developers'
        },
        {
            'category': 'Code Quality',
            'tip': 'Keep functions under 20 lines when possible',
            'example': 'Smaller functions are easier to test and maintain'
        },
        {
            'category': 'Documentation',
            'tip': 'Write docstrings for all public functions and classes',
            'example': 'Helps others (and future you) understand the code'
        }
    ]
    
    tip = random.choice(tips)
    
    return jsonify({
        'success': True,
        'tip': tip
    })


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("📚 OPTICODE LEARNING API - EDUCATIONAL CONTENT SERVER")
    print("="*70)
    print("[CATEGORIES]")
    for key, content in LEARNING_CONTENT.items():
        print(f"  • {content['title']} ({len(content['topics'])} topics)")
    print()
    print("[ENDPOINTS]")
    print("  GET  /api/categories              - List all categories")
    print("  GET  /api/category/<name>         - Get category details")
    print("  GET  /api/topic/<cat>/<topic>     - Get topic details")
    print("  GET  /api/search?q=<query>        - Search content")
    print("  GET  /api/random-tip              - Get random tip")
    print("  GET  /health                      - Health check")
    print("="*70)
    print(f"[SERVER] Running on: http://localhost:8002")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=8002, debug=True)
