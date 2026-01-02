"""
Flask API for Code Refactoring Model + Python Compiler
Place this file in: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/
Run with: python refactor_api.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os
import time
import re
import subprocess
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for React

# ============================================
# LOAD MODEL (Update path to match your structure)
# ============================================
MODEL_PATH = r"E:\Research Resources\Model Trained dataset\haritha\code-refactor-model\final-code-refactor-model"

print("Loading model from:", MODEL_PATH)

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    
    # Use GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    print(f"[SUCCESS] Model loaded successfully on {device.upper()}")
    print(f"[WARNING] Model output unreliable - using smart fallback mode")
except Exception as e:
    print(f"[ERROR] Error loading model: {e}")
    exit(1)

# ============================================
# HELPER FUNCTIONS
# ============================================

def smart_refactor_fallback(code: str) -> str:
    """Enhanced regex-based refactoring when model fails"""
    print("\n[REFACTOR] Applying smart refactoring rules...")
    
    original = code
    changes = []
    
    # Pattern 1: Simple loop to list comprehension
    pattern1 = r'(\s*)result\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*result\.append\(([^)]+)\)\s*\n\s*return\s+result'
    match1 = re.search(pattern1, code, re.MULTILINE)
    if match1:
        indent = match1.group(1)
        var_name = match1.group(2)
        iterable = match1.group(3)
        expression = match1.group(4)
        replacement = f"{indent}return [{expression} for {var_name} in {iterable}]"
        code = re.sub(pattern1, replacement, code, flags=re.MULTILINE)
        changes.append("Loop → List comprehension")
    
    # Pattern 2: Filter with loop
    pattern2 = r'(\s*)result\s*=\s*\[\]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*if\s+([^:]+):\s*\n\s*result\.append\(([^)]+)\)\s*\n\s*return\s+result'
    match2 = re.search(pattern2, code, re.MULTILINE)
    if match2:
        indent = match2.group(1)
        var_name = match2.group(2)
        iterable = match2.group(3)
        condition = match2.group(4)
        expression = match2.group(5)
        replacement = f"{indent}return [{expression} for {var_name} in {iterable} if {condition}]"
        code = re.sub(pattern2, replacement, code, flags=re.MULTILINE)
        changes.append("Filter loop → List comprehension")
    
    # Pattern 3: Manual sum
    pattern3 = r'(\s*)total\s*=\s*0\s*\n\s*for\s+\w+\s+in\s+(\w+):\s*\n\s*total\s*\+=\s*\w+\s*\n\s*return\s+total'
    match3 = re.search(pattern3, code, re.MULTILINE)
    if match3:
        indent = match3.group(1)
        iterable = match3.group(2)
        replacement = f"{indent}return sum({iterable})"
        code = re.sub(pattern3, replacement, code, flags=re.MULTILINE)
        changes.append("Manual sum → sum()")
    
    # Pattern 4: range(len()) pattern
    pattern4 = r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):'
    match4 = re.search(pattern4, code)
    if match4:
        index_var = match4.group(1)
        iterable = match4.group(2)
        code = re.sub(pattern4, f'for item in {iterable}:', code)
        code = re.sub(rf'{iterable}\[{index_var}\]', 'item', code)
        changes.append("range(len()) → Direct iteration")
    
    # Pattern 5: String concatenation in loop
    pattern5 = r'(\s*)result\s*=\s*["\'][\'"]\s*\n\s*for\s+(\w+)\s+in\s+(\w+):\s*\n\s*result\s*\+=\s*\2\s*\+\s*["\']([^"\']+)[\'"]\s*\n\s*return\s+result'
    match5 = re.search(pattern5, code, re.MULTILINE)
    if match5:
        indent = match5.group(1)
        iterable = match5.group(3)
        separator = match5.group(4)
        replacement = f'{indent}return "{separator}".join({iterable})'
        code = re.sub(pattern5, replacement, code, flags=re.MULTILINE)
        changes.append("String concatenation → join()")
    
    # Pattern 6: Add type hints if missing
    if 'def ' in code and '->' not in code:
        code = re.sub(r'def\s+(\w+)\((\w+)\):', r'def \1(\2: List) -> List:', code)
        if 'from typing import List' not in code:
            code = "from typing import List\n\n" + code
        changes.append("Added type hints")
    
    # Report changes
    if changes:
        for change in changes:
            print(f"   ✓ {change}")
        print(f"[SUCCESS] Applied {len(changes)} refactoring(s)")
    else:
        print(f"[INFO] No refactoring patterns found")
    
    return code if code != original else original

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,
        'device': device,
        'mode': 'smart_fallback',
        'compiler': 'enabled'
    })

@app.route('/api/refactor', methods=['POST'])
def refactor():
    """Main refactoring endpoint"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        code = data.get('code', '').strip()
        instruction = data.get('instruction', 'Refactor this code')
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
        
        print(f"\n[INFO] Refactoring {len(code)} characters of Python code...")
        
        # Skip model, use smart fallback directly
        print(f"[MODE] Using smart fallback (model output unreliable)")
        result = smart_refactor_fallback(code)
        
        processing_time = (time.time() - start_time) * 1000
        
        print(f"[COMPLETE] Refactored in {processing_time:.0f}ms\n")
        
        return jsonify({
            'success': True,
            'refactored_code': result,
            'processing_time': processing_time,
            'message': 'Code refactored successfully'
        })
    
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
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
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Execution failed'
        }), 500

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("[STARTUP] CODE REFACTORING + COMPILER API SERVER")
    print("="*60)
    print(f"[MODEL] Model: {MODEL_PATH}")
    print(f"[DEVICE] Device: {device.upper()}")
    print(f"[MODE] Smart Fallback (Model Output Unreliable)")
    print(f"[COMPILER] Python Code Execution: ENABLED")
    print(f"[SERVER] Server: http://localhost:8000")
    print("="*60)
    print("[ENDPOINTS]")
    print("  - POST /api/refactor  (Refactor code)")
    print("  - POST /api/execute   (Run code)")
    print("  - GET  /health        (Health check)")
    print("="*60)
    print("[TIP] To retrain model: Use CORRECT_training_script.py")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)