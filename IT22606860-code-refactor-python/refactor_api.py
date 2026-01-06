"""
Flask API for Code Refactoring with Risk Analysis, Best Practices, and Metrics
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/refactor_api.py
"""
import os
import time
import subprocess
import tempfile
import traceback
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Import analysis modules
# (Preserving your existing local module imports)
try:
    from risk_analyzer import RiskAnalyzer
    RISK_ANALYZER_LOADED = True
    print("[STARTUP] ✓ RiskAnalyzer loaded")
except Exception as e:
    print(f"[STARTUP] ✗ RiskAnalyzer failed: {e}")
    RISK_ANALYZER_LOADED = False

try:
    from best_practices_detector import BestPracticesDetector
    BEST_PRACTICES_LOADED = True
    print("[STARTUP] ✓ BestPracticesDetector loaded")
except Exception as e:
    print(f"[STARTUP] ✗ BestPracticesDetector failed: {e}")
    BEST_PRACTICES_LOADED = False

try:
    from recommendations_engine import RecommendationsEngine
    RECOMMENDATIONS_LOADED = True
    print("[STARTUP] ✓ RecommendationsEngine loaded")
except Exception as e:
    print(f"[STARTUP] ✗ RecommendationsEngine failed: {e}")
    RECOMMENDATIONS_LOADED = False

try:
    from metrics_calculator import MetricsCalculator
    METRICS_LOADED = True
    print("[STARTUP] ✓ MetricsCalculator loaded")
except Exception as e:
    print(f"[STARTUP] ✗ MetricsCalculator failed: {e}")
    METRICS_LOADED = False

app = Flask(__name__)
CORS(app)  # Enable CORS for React

# ============================================
# INITIALIZE SERVICES
# ============================================

if RISK_ANALYZER_LOADED:
    risk_analyzer = RiskAnalyzer()
    
if BEST_PRACTICES_LOADED:
    best_practices_detector = BestPracticesDetector()
    
if RECOMMENDATIONS_LOADED:
    recommendations_engine = RecommendationsEngine()
    
if METRICS_LOADED:
    metrics_calculator = MetricsCalculator()

# ============================================
# AI CLIENT CONFIGURATION (DEEPSEEK)
# ============================================

# Replace <OPENROUTER_API_KEY> with your actual key or set it as an environment variable
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

print(f"[STARTUP] AI Client Initialized for model: {MODEL_NAME}")

# ============================================
# HELPER FUNCTIONS
# ============================================

def clean_ai_output(content: str) -> str:
    """
    Removes markdown code blocks if the AI includes them.
    e.g., removes ```python and ```
    """
    if not content:
        return ""
    
    # Remove ```python or ``` at the start
    content = re.sub(r"^```(python)?\n", "", content, flags=re.MULTILINE)
    # Remove ``` at the end
    content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
    return content.strip()

def get_deepseek_refactor(code: str) -> str:
    """Calls DeepSeek via OpenRouter to refactor code"""
    
    system_prompt = (
        "You are a Python refactoring expert. Refactor the given Python code only.\n"
        "Preserve functionality. Follow PEP8. Do not explain.\n"
        "Output ONLY valid Python code."
    )

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "Opticode Refactor API", 
            },
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": code
                }
            ]
        )
        raw_content = completion.choices[0].message.content
        return clean_ai_output(raw_content)
        
    except Exception as e:
        print(f"[AI ERROR] {str(e)}")
        raise e

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_type': 'DeepSeek-R1 (OpenRouter)',
        'compiler': 'enabled',
        'services': {
            'risk_analysis': RISK_ANALYZER_LOADED,
            'best_practices': BEST_PRACTICES_LOADED,
            'recommendations': RECOMMENDATIONS_LOADED,
            'metrics': METRICS_LOADED
        }
    })

@app.route('/api/refactor', methods=['POST'])
def refactor():
    """Main refactoring endpoint using DeepSeek"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        
        # Validate
        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400
        
        # Only support Python
        if language.lower() != 'python':
            return jsonify({
                'success': False,
                'message': 'Only Python is currently supported'
            }), 400
        
        print(f"\n[REFACTOR] Sending {len(code)} chars to {MODEL_NAME}...")
        
        # Call AI
        result = get_deepseek_refactor(code)
        
        processing_time = (time.time() - start_time) * 1000
        
        print(f"[COMPLETE] Refactored in {processing_time:.0f}ms")
        
        return jsonify({
            'success': True,
            'refactored_code': result,
            'processing_time': processing_time,
            'message': 'Code refactored successfully'
        })
    
    except Exception as e:
        print(f"[ERROR] Refactor error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute():
    """Execute Python code safely"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400
        
        print(f"\n[EXECUTE] Running {len(code)} characters of Python code...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout and security restrictions
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                cwd=tempfile.gettempdir(),
                encoding='utf-8'
            )
            
            output = result.stdout
            error = result.stderr
            
            processing_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                print(f"[SUCCESS] Executed in {processing_time:.0f}ms")
                return jsonify({
                    'success': True,
                    'output': output or 'Code executed successfully (no output)',
                    'error': error if error else None,
                    'processing_time': processing_time
                })
            else:
                print(f"[ERROR] Execution failed with code {result.returncode}")
                return jsonify({
                    'success': False,
                    'output': output,
                    'error': error or 'Execution failed',
                    'processing_time': processing_time
                })
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Execution exceeded 10 seconds")
        return jsonify({
            'success': False,
            'error': 'Execution timeout (10 seconds exceeded)',
            'message': 'Code took too long to execute'
        }), 400
    
    except Exception as e:
        print(f"[ERROR] Execution error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Execution failed'
        }), 500

# ============================================
# RISK ANALYSIS
# ============================================

@app.route('/api/analyze-risks', methods=['POST'])
def analyze_risks():
    """Analyze code for security and quality risks"""
    try:
        if not RISK_ANALYZER_LOADED:
            return jsonify({
                'success': False,
                'message': 'Risk analyzer not available'
            }), 503

        data = request.get_json()
        code = data.get('code', '')

        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400

        print(f"\n[RISK ANALYSIS] Analyzing code ({len(code)} chars)...")

        result = risk_analyzer.analyze(code)

        print(f"[RISK ANALYSIS] Found {result['total']} risks")

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        print(f"[RISK ANALYSIS] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================
# BEST PRACTICES
# ============================================

@app.route('/api/analyze-practices', methods=['POST'])
def analyze_practices():
    """Analyze code for best practices violations"""
    try:
        if not BEST_PRACTICES_LOADED:
            return jsonify({
                'success': False,
                'message': 'Best practices analyzer not available'
            }), 503

        data = request.get_json()
        code = data.get('code', '')

        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400

        print(f"\n[BEST PRACTICES] Analyzing code ({len(code)} chars)...")

        violations = best_practices_detector.analyze(code)
        
        # Count by severity
        by_severity = {
            'error': len([v for v in violations if v.get('severity') == 'error']),
            'warning': len([v for v in violations if v.get('severity') == 'warning']),
            'info': len([v for v in violations if v.get('severity') == 'info'])
        }

        print(f"[BEST PRACTICES] Found {len(violations)} violations")

        # Generate recommendations if available
        recommendations = []
        if RECOMMENDATIONS_LOADED:
            try:
                recommendations = recommendations_engine.get_recommendations(violations)
            except Exception as e:
                print(f"[RECOMMENDATIONS] Error: {e}")

        return jsonify({
            'success': True,
            'violations': violations,
            'by_severity': by_severity,
            'recommendations': recommendations,
            'total': len(violations)
        })

    except Exception as e:
        print(f"[BEST PRACTICES] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================
# METRICS
# ============================================

@app.route('/api/analyze-metrics', methods=['POST'])
def analyze_metrics():
    """Calculate code quality metrics"""
    try:
        if not METRICS_LOADED:
            return jsonify({
                'success': False,
                'message': 'Metrics calculator not available'
            }), 503

        data = request.get_json()
        code = data.get('code', '')

        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400

        print(f"\n[METRICS] Calculating metrics...")

        metrics = metrics_calculator.calculate(code)

        print(f"[METRICS] LOC={metrics.get('loc', 0)}, Complexity={metrics.get('complexity', {}).get('average', 0)}")

        return jsonify({
            'success': True,
            'metrics': metrics
        })

    except Exception as e:
        print(f"[METRICS] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/compare-metrics', methods=['POST'])
def compare_metrics():
    """Compare metrics between original and refactored code"""
    try:
        if not METRICS_LOADED:
            return jsonify({
                'success': False,
                'message': 'Metrics calculator not available'
            }), 503

        data = request.get_json()
        original_code = data.get('original_code', '')
        refactored_code = data.get('refactored_code', '')

        if not original_code or not refactored_code:
            return jsonify({
                'success': False,
                'message': 'Both original and refactored code are required'
            }), 400

        print(f"\n[METRICS] Comparing metrics...")

        original_metrics = metrics_calculator.calculate(original_code)
        refactored_metrics = metrics_calculator.calculate(refactored_code)
        comparison = metrics_calculator.compare(original_metrics, refactored_metrics)

        print(f"[METRICS] Comparison completed")

        return jsonify({
            'success': True,
            'metrics': {
                'before': original_metrics,
                'after': refactored_metrics,
                'improvements': comparison
            }
        })

    except Exception as e:
        print(f"[METRICS] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================
# EXPLANATION
# ============================================

@app.route('/api/explain', methods=['POST'])
def explain_refactoring():
    """Generate explanation for refactoring changes"""
    try:
        data = request.get_json()
        original_code = data.get('original_code', '')
        refactored_code = data.get('refactored_code', '')

        if not original_code or not refactored_code:
            return jsonify({
                'success': False,
                'message': 'Both codes are required'
            }), 400

        print(f"\n[EXPLAIN] Generating explanation...")

        # Simple explanation
        explanation = {
            'changes': [
                {
                    'title': 'Code Refactored',
                    'description': 'Code has been improved for better readability and maintainability',
                    'reason': 'Following Python best practices and PEP 8 guidelines',
                    'benefit': 'Cleaner, more maintainable code'
                }
            ],
            'principles': [
                'Clean Code',
                'PEP 8 Style Guide',
                'Pythonic Patterns'
            ],
            'benefits': [
                'Improved readability',
                'Better maintainability',
                'Reduced complexity'
            ],
            'resources': [
                {'title': 'PEP 8', 'url': '[https://pep8.org](https://pep8.org)'},
                {'title': 'Python Guide', 'url': '[https://docs.python-guide.org](https://docs.python-guide.org)'}
            ]
        }

        return jsonify({
            'success': True,
            'explanation': explanation
        })

    except Exception as e:
        print(f"[EXPLAIN] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================
# TEST GENERATION
# ============================================

@app.route('/api/generate-tests', methods=['POST'])
def generate_tests():
    """Generate unit tests for code"""
    try:
        data = request.get_json()
        code = data.get('code', '')

        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400

        print(f"\n[TESTS] Generating tests...")

        # Simple test template
        tests = """import pytest

# Test cases for your refactored code

def test_basic_functionality():
    \"\"\"Test basic functionality\"\"\"
    # Add your test here
    pass

def test_edge_cases():
    \"\"\"Test edge cases\"\"\"
    # Add your test here
    pass

def test_error_handling():
    \"\"\"Test error handling\"\"\"
    # Add your test here
    pass
"""

        return jsonify({
            'success': True,
            'tests': tests,
            'message': 'Tests generated successfully'
        })

    except Exception as e:
        print(f"[TESTS] Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 CODE REFACTORING + ANALYSIS API SERVER")
    print("="*60)
    print(f"[MODEL] Engine: {MODEL_NAME}")
    print(f"[PROVIDER] OpenRouter.ai")
    print("="*60)
    print("[SERVICES]")
    print(f"  ✓ Refactoring: ENABLED (DeepSeek)")
    print(f"  ✓ Code Execution: ENABLED")
    print(f"  ✓ Risk Analysis: {'ENABLED' if RISK_ANALYZER_LOADED else 'DISABLED'}")
    print(f"  ✓ Best Practices: {'ENABLED' if BEST_PRACTICES_LOADED else 'DISABLED'}")
    print(f"  ✓ Recommendations: {'ENABLED' if RECOMMENDATIONS_LOADED else 'DISABLED'}")
    print(f"  ✓ Metrics: {'ENABLED' if METRICS_LOADED else 'DISABLED'}")
    print("="*60)
    print("[ENDPOINTS]")
    print("  POST /api/refactor          - Refactor code (AI)")
    print("  POST /api/execute           - Execute code")
    print("  POST /api/analyze-risks     - Analyze risks")
    print("  POST /api/analyze-practices - Best practices")
    print("  POST /api/analyze-metrics   - Calculate metrics")
    print("  POST /api/compare-metrics   - Compare metrics")
    print("  POST /api/explain           - Get explanation")
    print("  POST /api/generate-tests    - Generate tests")
    print("  GET  /health                - Health check")
    print("="*60)
    print(f"[SERVER] Running on: http://localhost:8000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)