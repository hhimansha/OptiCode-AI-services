"""
Flask API for Code Refactoring - FAST VERSION (AST-only)
No ML dependencies - Pure Python AST refactoring
Location: IT22606860-code-refactor-python/refactor_api_fast.py
"""
import os
import time
import subprocess
import tempfile
import traceback
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import ast
from typing import Dict, Tuple

# Import AST-based modules
from ast_refactor import refactor_code_ast, analyze_code_structure, suggest_refactorings
from code_analyzer import analyze_code
from best_practices import check_best_practices
from ethical_code_analyzer import analyze_ethical_code

# Import advanced modules
from advanced_ast_refactor import refactor_comprehensive, list_all_patterns, RefactoringCategory
from unified_refactor import refactor_complete
from architecture_analyzer import analyze_architecture, ArchitectureAnalyzer
from test_generator import TestGenerator
from performance_optimizer import PerformanceOptimizer, optimize_performance

# Import priority refactorings
from priority_refactorings import apply_priority_refactorings, get_priority_patterns

# Initialize Flask app
app = Flask(__name__)

# Configure CORS - Allow requests from frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Environment configuration
PORT = int(os.getenv('PORT', 8000))

print("="*80)
print(" 🚀 FAST REFACTORING API - AST-only Version")
print("="*80)
print(" ✅ All imports loaded successfully!")
print(f" 📍 Port: {PORT}")
print("="*80)


# Add CORS preflight support
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '4.0-FAST',
        'mode': 'AST-only (No ML)',
        'port': PORT
    })


@app.route('/api/refactor', methods=['POST'])
def refactor():
    """Basic AST refactoring endpoint"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Apply AST refactoring
        result = refactor_code_ast(code)
        
        return jsonify({
            'success': True,
            'original_code': code,
            'refactored_code': result.get('refactored_code', code),
            'suggestions': result.get('suggestions', [])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/refactor-complete', methods=['POST'])
def refactor_complete_endpoint():
    """
    Unified comprehensive refactoring endpoint
    Request: {"code": str, "apply_basic": bool, "apply_priority": bool,
              "apply_advanced": bool, "apply_performance": bool,
              "categories": List[str] | None}
    """
    try:
        data = request.get_json()
        code = data.get('code', '') if data else ''

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        options = {
            'apply_basic': data.get('apply_basic', True),
            'apply_priority': data.get('apply_priority', True),
            'apply_advanced': data.get('apply_advanced', True),
            'apply_performance': data.get('apply_performance', True),
            'categories': data.get('categories')
        }

        result = refactor_complete(code, options)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Code analysis endpoint"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Analyze code
        analysis = analyze_code(code)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/best-practices', methods=['POST'])
def best_practices():
    """Check best practices endpoint"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Check best practices
        result = check_best_practices(code)
        
        return jsonify({
            'success': True,
            'best_practices': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/advanced-refactor', methods=['POST'])
def advanced_refactor():
    """
    Advanced comprehensive refactoring with 100+ patterns
    Categories: Naming, Function, Conditional, Variable, Class, Module,
               Python-Specific, Performance, Error Handling, Architecture,
               Testing, Style
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        categories = data.get('categories', [])  # Optional: filter by categories
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Apply comprehensive refactoring
        if categories:
            # Convert string categories to enum
            category_enums = []
            for cat in categories:
                try:
                    category_enums.append(RefactoringCategory[cat.upper().replace(' ', '_').replace('-', '_')])
                except KeyError:
                    pass
            
            result = refactor_comprehensive(code, categories=category_enums)
        else:
            result = refactor_comprehensive(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/list-patterns', methods=['GET'])
def list_patterns():
    """List all available refactoring patterns"""
    try:
        patterns = list_all_patterns()
        
        # Add priority patterns
        priority_patterns = get_priority_patterns()
        
        return jsonify({
            'success': True,
            'total_patterns': len(patterns),
            'priority_patterns': len(priority_patterns),
            'patterns': patterns,
            'priority_list': priority_patterns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/architecture-analyze', methods=['POST'])
def architecture_analyze():
    """Analyze architecture and suggest improvements"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        result = analyze_architecture(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/generate-tests', methods=['POST'])
def generate_tests():
    """Generate unit tests for code"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Generate tests using TestGenerator
        generator = TestGenerator()
        result = generator.generate_tests(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/optimize-performance', methods=['POST'])
def optimize_performance_endpoint():
    """Optimize code performance"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        result = optimize_performance(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/execute', methods=['POST', 'OPTIONS'])
def execute():
    """Execute Python code safely"""
    if request.method == 'OPTIONS':
        return '', 204
    
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400
        
        print(f"\n[EXECUTE] Running code...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=tempfile.gettempdir(),
                encoding='utf-8'
            )
            
            output = result.stdout
            error = result.stderr
            
            processing_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                print(f"[SUCCESS] {processing_time:.0f}ms")
                return jsonify({
                    'success': True,
                    'output': output or 'Code executed successfully (no output)',
                    'error': error if error else None,
                    'processing_time': processing_time
                })
            else:
                print(f"[ERROR] Exit code {result.returncode}")
                return jsonify({
                    'success': False,
                    'output': output,
                    'error': error or 'Execution failed',
                    'processing_time': processing_time
                })
        
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Code execution timeout (10 seconds limit)'
        }), 408
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/priority-refactor', methods=['POST'])
def priority_refactor():
    """
    Apply top 20 priority refactoring patterns (FASTEST)
    Focused on most common and impactful issues:
    - Dead code removal
    - Duplicate code detection
    - Loop → comprehension
    - Guard clauses
    - Method extraction
    - Variable management
    And 14 more critical patterns!
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        result = apply_priority_refactorings(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/priority-patterns', methods=['GET'])
def priority_patterns():
    """Get list of top 20 priority patterns"""
    try:
        patterns = get_priority_patterns()
        
        return jsonify({
            'success': True,
            'count': len(patterns),
            'patterns': patterns,
            'description': 'Top 20 most important refactoring patterns for immediate code improvement'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*80)
    print(" 🎯 AVAILABLE ENDPOINTS:")
    print("="*80)
    print(f"  GET  /health                    - Health check")
    print(f"  POST /api/refactor              - Basic AST refactoring")
    print(f"  POST /api/analyze               - Code analysis")
    print(f"  POST /api/best-practices        - Best practices check")
    print(f"  POST /api/advanced-refactor     - 100+ refactoring patterns")
    print(f"  POST /api/priority-refactor     - Top 20 priority patterns (FASTEST)")
    print(f"  GET  /api/list-patterns         - List all patterns")
    print(f"  GET  /api/priority-patterns     - List priority patterns")
    print(f"  POST /api/architecture-analyze  - Architecture analysis")
    print(f"  POST /api/generate-tests        - Generate unit tests")
    print(f"  POST /api/optimize-performance  - Performance optimization")
    print("="*80)
    print(f" 🚀 Starting server on http://localhost:{PORT}")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
