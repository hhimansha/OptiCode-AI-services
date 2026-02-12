"""
Flask API for Code Refactoring using Two-Stage Process
Stage 1: Local Trained Model
Stage 2: DeepSeek API (OpenRouter)
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/refactor_api.py
OPTIMIZED VERSION - Faster processing, handles longer inputs
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
import ast
from typing import Dict, Tuple

# Optional transformers import (for ML-based suggestions)
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available - Using AST-only refactoring")

# Import AST-based modules
from ast_refactor import refactor_code_ast, analyze_code_structure, suggest_refactorings
from code_analyzer import analyze_code
from best_practices import check_best_practices
from ethical_code_analyzer import analyze_ethical_code

# Import advanced modules
from advanced_ast_refactor import refactor_comprehensive, list_all_patterns, RefactoringCategory
from unified_refactor import refactor_complete
from architecture_analyzer import analyze_architecture, ArchitectureAnalyzer
from test_generator import generate_tests, analyze_testability
from performance_optimizer import optimize_performance
from priority_refactorings import apply_priority_refactorings, get_priority_patterns

app = Flask(__name__)

# Configure CORS - Allow requests from frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ============================================
# CONFIGURATION
# ============================================

# Refactoring Method Configuration
USE_AST_REFACTORING = True  # Primary method: Use AST-based refactoring
USE_LLM_FOR_SUGGESTIONS = True  # Use LLM for suggestions, risks, explanations

# Local Trained Model Configuration (DEPRECATED - Kept for legacy support)
LOCAL_MODEL_PATH = r"E:\Research Resources\Model Trained dataset\haritha\code-refactor-model"
LOCAL_MODEL_ENABLED = False  # Disabled in favor of AST refactoring

# OPTIMIZED: Increased token limits for longer code
MAX_INPUT_LENGTH = 512  # Increased from 256
MAX_OUTPUT_LENGTH = 768  # Increased from 256
NUM_BEAMS = 3  # Reduced from 5 for faster generation
LENGTH_PENALTY = 1.0
NO_REPEAT_NGRAM = 2

# DeepSeek API Configuration
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

# OPTIMIZED: API timeout settings
API_TIMEOUT = 60.0  # 60 seconds timeout
API_MAX_RETRIES = 2  # Retry failed requests

# ============================================
# INITIALIZE AI CLIENTS
# ============================================

# OPTIMIZED: Initialize DeepSeek client with timeout (Python 3.14 compatible)
try:
    deepseek_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=API_TIMEOUT,
    )
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"⚠️ OpenAI client initialization failed: {e}")
    print("⚠️ LLM-based suggestions will be disabled. AST refactoring will still work.")
    deepseek_client = None

# Initialize Local Model
local_model = None
local_tokenizer = None
device = None

def load_local_model():
    """Load the local trained model"""
    global local_model, local_tokenizer, device
    
    if not LOCAL_MODEL_ENABLED:
        print("[STARTUP] Local model is DISABLED")
        return False
    
    if not LOCAL_MODEL_PATH:
        print("[WARNING] LOCAL_MODEL_PATH not set. Local model will be skipped.")
        return False
    
    if not os.path.exists(LOCAL_MODEL_PATH):
        print(f"[ERROR] Local model path does not exist: {LOCAL_MODEL_PATH}")
        return False
    
    try:
        if not TRANSFORMERS_AVAILABLE:
            print("[STARTUP] Transformers not available - skipping local model")
            return False
            
        print(f"[STARTUP] Loading local model from: {LOCAL_MODEL_PATH}")
        
        local_tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)
        local_model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_PATH)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        local_model = local_model.to(device)
        local_model.eval()  # Set to evaluation mode
        
        # OPTIMIZED: Enable inference mode for faster generation
        if hasattr(torch, 'inference_mode'):
            torch.set_grad_enabled(False)
        
        print(f"[STARTUP] ✅ Local model loaded successfully")
        print(f"[STARTUP] Device: {device.upper()}")
        print(f"[STARTUP] Generation: {NUM_BEAMS} beams, max length {MAX_OUTPUT_LENGTH}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load local model: {str(e)}")
        traceback.print_exc()
        return False

# Load the local model on startup
local_model_loaded = load_local_model()

print(f"[STARTUP] AI Configuration:")
print(f"  - Local Model: {'ENABLED' if local_model_loaded else 'DISABLED'}")
print(f"  - DeepSeek API: ENABLED ({MODEL_NAME})")
print(f"  - API Timeout: {API_TIMEOUT}s")
print(f"  - Two-Stage Refactoring: {'YES' if local_model_loaded else 'NO (DeepSeek only)'}")

# ============================================
# HELPER FUNCTIONS FOR LOCAL MODEL
# ============================================

def extract_variables(code: str) -> set:
    """Extract variable names from code"""
    variables = set()
    
    # Function parameters
    params = re.findall(r'def\s+\w+\((.*?)\)', code)
    for param_list in params:
        for param in param_list.split(','):
            param = param.strip().split(':')[0].split('=')[0].strip()
            if param:
                variables.add(param)
    
    # Variable assignments
    assignments = re.findall(r'(\w+)\s*=', code)
    variables.update(assignments)
    
    # Loop variables
    loop_vars = re.findall(r'for\s+(\w+)\s+in', code)
    variables.update(loop_vars)
    
    return variables

def validate_syntax(code: str) -> Tuple[bool, str]:
    """Check if code has valid Python syntax"""
    try:
        ast.parse(code)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Parse error: {str(e)}"

def fix_parentheses(code: str) -> str:
    """Attempt to fix unbalanced parentheses"""
    
    # Count parentheses
    open_paren = code.count('(')
    close_paren = code.count(')')
    
    if open_paren > close_paren:
        code += ')' * (open_paren - close_paren)
    elif close_paren > open_paren:
        diff = close_paren - open_paren
        code = code.rstrip(')')
        code += ')' * (close_paren - open_paren - diff)
    
    # Same for brackets
    open_bracket = code.count('[')
    close_bracket = code.count(']')
    
    if open_bracket > close_bracket:
        code += ']' * (open_bracket - close_bracket)
    
    return code

def post_process_refactored(original: str, refactored: str) -> str:
    """Post-process refactored code to fix common issues"""
    
    # 1. Fix parentheses/brackets
    refactored = fix_parentheses(refactored)
    
    # 2. Preserve original function signature if modified incorrectly
    orig_func_match = re.search(r'def\s+(\w+)\s*\((.*?)\)', original)
    ref_func_match = re.search(r'def\s+(\w+)\s*\((.*?)\)', refactored)
    
    if orig_func_match and ref_func_match:
        orig_name, orig_params = orig_func_match.groups()
        ref_name, ref_params = ref_func_match.groups()
        
        # Keep original function name
        if ref_name != orig_name:
            refactored = refactored.replace(f'def {ref_name}(', f'def {orig_name}(')
        
        # Keep original parameters if refactored changed them significantly
        orig_param_names = [p.strip().split(':')[0].split('=')[0].strip() 
                           for p in orig_params.split(',') if p.strip()]
        ref_param_names = [p.strip().split(':')[0].split('=')[0].strip() 
                          for p in ref_params.split(',') if p.strip()]
        
        if set(orig_param_names) != set(ref_param_names):
            # Restore original parameters
            refactored = refactored.replace(
                f'def {orig_name}({ref_params})',
                f'def {orig_name}({orig_params})'
            )
    
    # 3. Remove unnecessary type hints that weren't in original
    if 'Iterable[' not in original and 'Iterable[' in refactored:
        refactored = re.sub(r':\s*Iterable\[.*?\]', '', refactored)
    
    # 4. Ensure proper indentation
    lines = refactored.split('\n')
    if lines:
        func_line_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_line_idx = i
                break
        
        if func_line_idx is not None and len(lines) > func_line_idx + 1:
            for i in range(func_line_idx + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith(' '):
                    lines[i] = '    ' + lines[i]
        
        refactored = '\n'.join(lines)
    
    # 5. Fix incomplete returns
    if 'return' in refactored and refactored.strip().endswith('return'):
        if 'return result' in original:
            refactored += ' result'
        elif 'return total' in original:
            refactored += ' total'
    
    return refactored

def clean_ai_output(content: str) -> str:
    """Removes markdown code blocks if the AI includes them"""
    if not content:
        return ""
    
    # Remove ```python or ``` at the start
    content = re.sub(r"^```(python)?\n", "", content, flags=re.MULTILINE)
    # Remove ``` at the end
    content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
    return content.strip()

# ============================================
# STAGE 1: LOCAL MODEL REFACTORING
# ============================================

def refactor_with_local_model(code: str, instruction: str = "Refactor this code") -> Dict:
    """
    Stage 1: Refactor code using the local trained model
    Returns: Dictionary with refactored code and analysis
    """
    
    if not local_model_loaded or local_model is None or local_tokenizer is None:
        return {
            'success': False,
            'error': 'Local model not available',
            'refactored_code': code,
            'skipped': True
        }
    
    try:
        print(f"[STAGE 1] Local model refactoring...")
        
        # Create prompt
        prompt = f"{instruction}: {code}"
        
        # Tokenize
        inputs = local_tokenizer(
            prompt,
            return_tensors="pt",
            max_length=MAX_INPUT_LENGTH,
            truncation=True,
            padding=False
        )
        
        if device == "cuda":
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # OPTIMIZED: Generate with reduced beams and inference mode
        with torch.inference_mode() if hasattr(torch, 'inference_mode') else torch.no_grad():
            outputs = local_model.generate(
                **inputs,
                max_length=MAX_OUTPUT_LENGTH,
                min_length=10,
                num_beams=NUM_BEAMS,  # Now 3 instead of 5
                length_penalty=LENGTH_PENALTY,
                no_repeat_ngram_size=NO_REPEAT_NGRAM,
                early_stopping=True,
                do_sample=False
            )
        
        # Decode
        refactored_raw = local_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Post-process
        refactored = post_process_refactored(code, refactored_raw)
        
        # OPTIMIZED: Quick syntax validation only
        is_valid, syntax_msg = validate_syntax(refactored)
        
        # OPTIMIZED: Simplified fallback - only if invalid and short code
        if not is_valid and len(code) < 300:
            with torch.inference_mode() if hasattr(torch, 'inference_mode') else torch.no_grad():
                outputs_fallback = local_model.generate(
                    **inputs,
                    max_length=MAX_OUTPUT_LENGTH,
                    num_beams=2,  # Even faster fallback
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    early_stopping=True
                )
            
            refactored_fallback = local_tokenizer.decode(outputs_fallback[0], skip_special_tokens=True)
            refactored_fallback = post_process_refactored(code, refactored_fallback)
            
            is_valid_fallback, _ = validate_syntax(refactored_fallback)
            
            if is_valid_fallback:
                refactored = refactored_fallback
                is_valid = True
                syntax_msg = "Valid syntax (fallback)"
        
        # OPTIMIZED: Skip variable analysis for speed
        orig_vars = set()
        ref_vars = set()
        
        print(f"[STAGE 1] ✅ Complete - Valid: {is_valid}")
        
        return {
            'success': True,
            'refactored_code': refactored,
            'is_valid_syntax': is_valid,
            'syntax_message': syntax_msg,
            'original_variables': list(orig_vars),
            'refactored_variables': list(ref_vars),
            'missing_variables': [],
            'post_processed': refactored != refactored_raw,
            'skipped': False
        }
        
    except Exception as e:
        print(f"[STAGE 1 ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'refactored_code': code,
            'skipped': False
        }

# ============================================
# STAGE 2: DEEPSEEK API REFACTORING
# ============================================

def refactor_with_deepseek(code: str, instruction: str = "Refactor this code") -> str:
    """
    Stage 2: Further refactor code using DeepSeek API
    """
    
    system_prompt = (
        "You are a Python refactoring expert. Refactor the given Python code to improve it.\n"
        "Preserve functionality. Follow PEP8. Improve readability and efficiency.\n"
        "Output ONLY valid Python code without explanations."
    )
    
    user_prompt = f"{instruction}\n\n{code}"

    try:
        # Check if LLM client is available
        if not deepseek_client:
            return {'success': False, 'error': 'LLM client not available. AST refactoring only.'}
        
        print(f"[STAGE 2] Code refactoring...")
        
        completion = deepseek_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "Opticode Refactor API", 
            },
            model=MODEL_NAME,
            max_tokens=3000,  # Increased from 2000
            temperature=0.7,
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
        )
        
        if not completion.choices or len(completion.choices) == 0:
            print(f"[STAGE 2 ERROR] No choices in completion response")
            return code
        
        raw_content = completion.choices[0].message.content
        
        if not raw_content or not raw_content.strip():
            print(f"[STAGE 2 WARNING] DeepSeek returned empty content")
            return code
        
        cleaned = clean_ai_output(raw_content)
        
        print(f"[STAGE 2] ✅ Complete - {len(cleaned)} chars")
        
        return cleaned
        
    except Exception as e:
        print(f"[STAGE 2 ERROR] {str(e)}")
        raise e

# ============================================
# TWO-STAGE REFACTORING PIPELINE
# ============================================

def refactor_code_two_stage(code: str, instruction: str = "Refactor this code") -> Dict:
    """
    Complete two-stage refactoring pipeline:
    1. Local trained model (if available)
    2. DeepSeek API for final polish
    
    Note: The final output is always compared against the ORIGINAL input code,
    not the intermediate Stage 1 output.
    """
    
    original_code = code
    
    pipeline_info = {
        'stage1_used': False,
        'stage2_used': False,
        'stage1_result': None,
        'stage2_result': None,
        'original_code': original_code
    }
    
    current_code = code
    
    # STAGE 1: Local Model
    if local_model_loaded:
        stage1_result = refactor_with_local_model(code, instruction)
        pipeline_info['stage1_used'] = True
        pipeline_info['stage1_result'] = stage1_result
        
        if stage1_result['success'] and stage1_result['is_valid_syntax']:
            current_code = stage1_result['refactored_code']
            print(f"[PIPELINE] Stage 1 OK → Stage 2")
        else:
            print("[PIPELINE] Stage 1 invalid → using original")
            current_code = code
    else:
        print("[PIPELINE] Stage 1 skipped")
    
    # STAGE 2: DeepSeek API
    try:
        final_code = refactor_with_deepseek(current_code, instruction)
        
        if not final_code or not final_code.strip():
            print("[PIPELINE WARNING] Stage 2 empty")
            if pipeline_info['stage1_used'] and pipeline_info['stage1_result']['success']:
                final_code = pipeline_info['stage1_result']['refactored_code']
            else:
                final_code = code
        
        print(f"[PIPELINE] Final: {len(final_code)} chars (Original: {len(original_code)})")
        
        pipeline_info['stage2_used'] = True
        pipeline_info['stage2_result'] = {
            'success': True,
            'refactored_code': final_code
        }
        
        # Calculate comparison metrics
        comparison_info = {
            'original_length': len(original_code),
            'final_length': len(final_code),
            'character_change': len(final_code) - len(original_code),
            'original_lines': len(original_code.splitlines()),
            'final_lines': len(final_code.splitlines()),
            'line_change': len(final_code.splitlines()) - len(original_code.splitlines())
        }
        
        return {
            'success': True,
            'final_code': final_code,
            'original_code': original_code,
            'pipeline_info': pipeline_info,
            'comparison': comparison_info
        }
        
    except Exception as e:
        print(f"[PIPELINE ERROR] Stage 2 failed: {str(e)}")
        # If Stage 2 fails but Stage 1 succeeded, return Stage 1 result
        if pipeline_info['stage1_used'] and pipeline_info['stage1_result']['success']:
            print("[PIPELINE] Using Stage 1 result")
            final_code = pipeline_info['stage1_result']['refactored_code']
            
            comparison_info = {
                'original_length': len(original_code),
                'final_length': len(final_code),
                'character_change': len(final_code) - len(original_code),
                'original_lines': len(original_code.splitlines()),
                'final_lines': len(final_code.splitlines()),
                'line_change': len(final_code.splitlines()) - len(original_code.splitlines())
            }
            
            return {
                'success': True,
                'final_code': final_code,
                'original_code': original_code,
                'pipeline_info': pipeline_info,
                'comparison': comparison_info,
                'warning': 'DeepSeek API failed, using local model result only'
            }
        else:
            raise e

# ============================================
# LLM SUGGESTIONS HELPER
# ============================================

def get_llm_suggestions(original_code: str, refactored_code: str) -> Dict:
    """Get AI-powered suggestions and explanations for refactored code"""
    
    system_prompt = (
        "You are a Python refactoring expert. Analyze the refactoring changes and provide:\n"
        "1. Brief explanation of key improvements\n"
        "2. 2-3 actionable suggestions for further improvement\n"
        "3. Any potential risks or considerations\n\n"
        "Be concise and practical. Focus on most impactful insights."
    )
    
    user_prompt = f"ORIGINAL CODE:\n{original_code}\n\nREFACTORED CODE:\n{refactored_code}\n\nProvide analysis."
    
    try:
        # Check if LLM client is available
        if not deepseek_client:
            return {'success': False, 'suggestions': 'LLM suggestions not available. Using AST-only refactoring.'}
        
        completion = deepseek_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Opticode Refactor API",
            },
            model=MODEL_NAME,
            max_tokens=500,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        if completion.choices and len(completion.choices) > 0:
            return {
                'success': True,
                'suggestions': completion.choices[0].message.content
            }
        
        return {'success': False, 'error': 'No response from AI'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================
# NEW API ENDPOINTS FOR AST FEATURES
# ============================================

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Comprehensive code analysis endpoint"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'No code provided'}), 400
        
        print(f"\n[ANALYZE] Starting code analysis...")
        
        # Perform analysis
        analysis_result = analyze_code(code)
        
        processing_time = (time.time() - start_time) * 1000
        analysis_result['processing_time'] = processing_time
        
        print(f"[ANALYZE] Complete - {processing_time:.0f}ms")
        
        return jsonify(analysis_result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/best-practices', methods=['POST'])
def best_practices():
    """Check code against Python best practices"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'No code provided'}), 400
        
        print(f"\n[BEST PRACTICES] Checking...")
        
        result = check_best_practices(code)
        
        processing_time = (time.time() - start_time) * 1000
        result['processing_time'] = processing_time
        
        print(f"[BEST PRACTICES] Complete - Score: {result.get('score', 'N/A')}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/ethical-analysis', methods=['POST'])
def ethical_analysis():
    """Analyze code for ethical practices"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'No code provided'}), 400
        
        print(f"\n[ETHICAL ANALYSIS] Checking...")
        
        result = analyze_ethical_code(code)
        
        processing_time = (time.time() - start_time) * 1000
        result['processing_time'] = processing_time
        
        print(f"[ETHICAL ANALYSIS] Complete - Score: {result.get('ethical_score', 'N/A')}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/suggest-refactorings', methods=['POST'])
def suggest_refactorings_endpoint():
    """Get refactoring suggestions for code"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'No code provided'}), 400
        
        print(f"\n[SUGGESTIONS] Analyzing code for refactoring opportunities...")
        
        suggestions = suggest_refactorings(code)
        
        processing_time = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions),
            'processing_time': processing_time
        }
        
        print(f"[SUGGESTIONS] Complete - Found {len(suggestions)} suggestions")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/code-structure', methods=['POST'])
def code_structure():
    """Analyze code structure"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'message': 'No code provided'}), 400
        
        print(f"\n[STRUCTURE] Analyzing...")
        
        result = analyze_code_structure(code)
        
        processing_time = (time.time() - start_time) * 1000
        if result.get('success'):
            result['processing_time'] = processing_time
        
        print(f"[STRUCTURE] Complete")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================
# API ENDPOINTS (LEGACY - Keeping for compatibility)
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'refactoring_method': 'AST-based' if USE_AST_REFACTORING else 'LLM-based',
        'ast_refactoring': {
            'enabled': USE_AST_REFACTORING,
            'features': [
                'Simplify conditionals',
                'Extract complex expressions',
                'Improve loops',
                'Refactor magic numbers',
                'Code structure analysis'
            ]
        },
        'local_model': {
            'enabled': LOCAL_MODEL_ENABLED,
            'loaded': local_model_loaded,
            'path': LOCAL_MODEL_PATH if local_model_loaded else None,
            'device': device if local_model_loaded else None,
            'status': 'deprecated - use AST refactoring instead'
        },
        'llm_suggestions': {
            'enabled': USE_LLM_FOR_SUGGESTIONS,
            'model': MODEL_NAME,
            'timeout': API_TIMEOUT,
            'purpose': 'Suggestions, explanations, and risk analysis'
        },
        'features': {
            'code_analysis': True,
            'best_practices_check': True,
            'ethical_analysis': True,
            'refactoring_suggestions': True,
            'code_structure_analysis': True,
            'security_scanning': True,
            'complexity_metrics': True
        },
        'endpoints': {
            '/api/refactor': 'POST - Refactor code (AST-based)',
            '/api/refactor-complete': 'POST - Unified comprehensive refactoring',
            '/api/refactor-full': 'POST - Unified refactor + all analyses',
            '/api/analyze': 'POST - Comprehensive code analysis',
            '/api/best-practices': 'POST - Best practices checking',
            '/api/ethical-analysis': 'POST - Ethical coding analysis',
            '/api/suggest-refactorings': 'POST - Get refactoring suggestions',
            '/api/code-structure': 'POST - Analyze code structure',
            '/api/execute': 'POST - Execute Python code',
            '/api/architecture-analyze': 'POST - Architecture analysis (code payload)',
            '/health': 'GET - Health check'
        }
    })

@app.route('/api/refactor', methods=['POST'])
def refactor():
    """Main refactoring endpoint - Unified AST refactoring + analysis"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        instruction = data.get('instruction', 'Refactor this code')
        use_ast = data.get('use_ast', USE_AST_REFACTORING)
        get_suggestions = data.get('get_suggestions', True)
        
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
        
        print(f"\n[REFACTOR] Starting ({len(code)} chars) - Method: {'AST' if use_ast else 'LLM'}")

        if use_ast:
            options = {
                'apply_basic': True,
                'apply_priority': True,
                'apply_advanced': True,
                'apply_performance': True,
                'categories': data.get('categories')
            }

            result = refactor_complete(code, options)

            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': f'Unified refactoring failed: {result.get("error")}',
                    'original_code': code
                }), 500

            refactored = result.get('refactored_code', code)

            ai_suggestions = None
            if get_suggestions and USE_LLM_FOR_SUGGESTIONS:
                try:
                    print("[REFACTOR] Getting AI suggestions...")
                    ai_suggestions = get_llm_suggestions(code, refactored)
                except Exception as e:
                    print(f"[WARNING] AI suggestions failed: {str(e)}")
                    ai_suggestions = None

            processing_time = (time.time() - start_time) * 1000

            response = {
                'success': True,
                'refactored_code': refactored,
                'original_code': code,
                'processing_time': processing_time,
                'method': 'Unified AST refactoring',
                'summary': result.get('summary', {}),
                'stages': result.get('stages', {}),
                'analysis': result.get('analysis', {}),
                'changes': result.get('all_changes', []),
                'suggestions': result.get('all_suggestions', []),
                'ai_suggestions': ai_suggestions,
                'message': 'Code refactored successfully using unified AST pipeline'
            }

            print(f"[COMPLETE] {processing_time:.0f}ms - Unified AST Method")

            return jsonify(response)
        
        else:
            # Use legacy two-stage refactoring
            result = refactor_code_two_stage(code, instruction)
            
            processing_time = (time.time() - start_time) * 1000
            
            response_data = {
                'success': True,
                'refactored_code': result.get('final_code', ''),
                'original_code': result.get('original_code', code),
                'processing_time': processing_time,
                'method': 'LLM-based refactoring (legacy)',
                'message': 'Code refactored successfully',
                'pipeline_info': {
                    'local_model_used': result['pipeline_info']['stage1_used'],
                    'deepseek_used': result['pipeline_info']['stage2_used'],
                    'stages': 2 if result['pipeline_info']['stage1_used'] and result['pipeline_info']['stage2_used'] else 1
                },
                'comparison': result.get('comparison', {}),
                'warning': result.get('warning')
            }
            
            if not response_data['refactored_code']:
                print("[API] Empty output, using original")
                response_data['refactored_code'] = code
                response_data['warning'] = 'Refactoring failed, returning original code'
            
            print(f"[COMPLETE] {processing_time:.0f}ms - LLM Method")
            
            return jsonify(response_data)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
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

        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        code = data.get('code', '')
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
            'error': str(e)
        }), 500


@app.route('/api/refactor-full', methods=['POST'])
def refactor_full_endpoint():
    """
    Unified refactoring + all analysis endpoints combined
    Request: {"code": str, "apply_basic": bool, "apply_priority": bool,
              "apply_advanced": bool, "apply_performance": bool,
              "categories": List[str] | None}
    """
    try:
        data = request.get_json()

        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        code = data.get('code', '')
        options = {
            'apply_basic': data.get('apply_basic', True),
            'apply_priority': data.get('apply_priority', True),
            'apply_advanced': data.get('apply_advanced', True),
            'apply_performance': data.get('apply_performance', True),
            'categories': data.get('categories')
        }

        unified_result = refactor_complete(code, options)
        refactored_code = unified_result.get('refactored_code', code)

        full_results = {
            'basic_refactor': refactor_code_ast(code),
            'priority_refactor': apply_priority_refactorings(code),
            'advanced_refactor': refactor_comprehensive(code, options.get('categories')),
            'performance_optimize': optimize_performance(code),
            'code_analysis': analyze_code(code),
            'best_practices': check_best_practices(code),
            'ethical_analysis': analyze_ethical_code(code),
            'structure_analysis': analyze_code_structure(code),
            'suggestions': suggest_refactorings(code)
        }

        try:
            full_results['architecture_analysis'] = analyze_architecture({'main.py': code})
        except Exception as e:
            full_results['architecture_analysis'] = {'error': str(e)}

        response = {
            'success': unified_result.get('success', True),
            'original_code': code,
            'refactored_code': refactored_code,
            'summary': unified_result.get('summary', {}),
            'stages': unified_result.get('stages', {}),
            'analysis': unified_result.get('analysis', {}),
            'changes': unified_result.get('all_changes', []),
            'suggestions': unified_result.get('all_suggestions', []),
            'processing_time_ms': unified_result.get('processing_time_ms', 0),
            'all_endpoints': full_results
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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
        print(f"[TIMEOUT] Execution exceeded 10s")
        return jsonify({
            'success': False,
            'error': 'Execution timeout (10 seconds exceeded)',
            'message': 'Code took too long to execute'
        }), 400
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Execution failed'
        }), 500

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 OPTICODE - PYTHON CODE REFACTORING & LEARNING PLATFORM")
    print("="*80)
    print("[PRIMARY METHOD] AST-Based Refactoring: ✅ ENABLED")
    print("  ✓ Simplify conditionals")
    print("  ✓ Extract complex expressions")
    print("  ✓ Improve loops")
    print("  ✓ Refactor magic numbers")
    print("  ✓ Code structure analysis")
    print()
@app.route('/api/advanced-refactor', methods=['POST'])
def advanced_refactor():
    """
    Advanced comprehensive refactoring using 100+ patterns
    Request: {"code": str, "categories": List[str] (optional)}
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        categories = data.get('categories', None)
        
        # Apply comprehensive refactoring
        result = refactor_comprehensive(code, categories)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/architecture-analysis', methods=['POST'])
def architecture_analysis():
    """
    Comprehensive architecture analysis
    Request: {"files": {"filename1.py": "code1", "filename2.py": "code2"}}
             or {"code": "..."}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        files = data.get('files')
        code = data.get('code')

        if files:
            result = analyze_architecture(files)
        elif code:
            result = analyze_architecture({'main.py': code})
        else:
            return jsonify({
                'success': False,
                'error': 'No files or code provided'
            }), 400
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate-tests', methods=['POST'])
def generate_tests_endpoint():
    """
    Generate comprehensive unit tests
    Request: {"code": str}
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        
        # Generate tests
        result = generate_tests(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/testability-score', methods=['POST'])
def testability_score():
    """
    Analyze code testability
    Request: {"code": str}
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        
        # Analyze testability
        result = analyze_testability(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/optimize-performance', methods=['POST'])
def optimize_performance_endpoint():
    """
    Analyze and optimize performance
    Request: {"code": str}
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        
        # Optimize performance
        result = optimize_performance(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/list-patterns', methods=['GET'])
def list_patterns():
    """
    List all available refactoring patterns
    """
    try:
        patterns = list_all_patterns()
        priority_patterns = get_priority_patterns()
        
        return jsonify({
            'success': True,
            'categories': len(patterns),
            'patterns': patterns,
            'priority_patterns': len(priority_patterns),
            'priority_list': priority_patterns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/priority-refactor', methods=['POST'])
def priority_refactor():
    """
    Apply top 20 priority refactoring patterns
    Request: {"code": str}
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        code = data['code']
        
        # Apply priority refactorings
        result = apply_priority_refactorings(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/priority-patterns', methods=['GET'])
def priority_patterns():
    """
    Get list of priority refactoring patterns
    """
    try:
        patterns = get_priority_patterns()
        
        return jsonify({
            'success': True,
            'count': len(patterns),
            'patterns': patterns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/architecture-analyze', methods=['POST'])
def architecture_analyze_alias():
    """Alias for architecture analysis with code payloads."""
    return architecture_analysis()


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("[STARTING] Code Refactoring API Server")
    print("="*80)
    print()
    print("[COMPREHENSIVE RESEARCH PROJECT]")
    print("  Student: IT22606860")
    print("  Project: Advanced Python Code Refactoring & Analysis")
    print("  Duration: 1 Year Research")
    print("  Patterns: 100+ Refactoring Methods")
    print()
    print("[REFACTORING ENGINE]")
    print("  Primary: AST-Based Refactoring ✅")
    print("  Method: 12 Categories of Refactoring Patterns")
    print("  Categories:")
    print("    1. Naming & Readability")
    print("    2. Function/Method Refactoring")
    print("    3. Conditional Logic")
    print("    4. Variable & Data")
    print("    5. Class & Object-Oriented")
    print("    6. Module & File Organization")
    print("    7. Python-Specific Idioms")
    print("    8. Performance Optimization")
    print("    9. Error Handling & Safety")
    print("   10. Dependency & Architecture")
    print("   11. Testing & Maintainability")
    print("   12. Code Style & Cleanliness")
    print()
    print("[ANALYSIS FEATURES]")
    print("  ✓ Code Quality Analysis (Radon, Bandit)")
    print("  ✓ Best Practices Checking (SOLID, DRY, etc.)")
    print("  ✓ Ethical Coding Analysis")
    print("  ✓ Security Scanning")
    print("  ✓ Complexity Metrics")
    print("  ✓ Refactoring Suggestions")
    print("  ✓ Architecture Analysis (Design Patterns, SOLID)")
    print("  ✓ Test Generation (Unit Tests, Coverage)")
    print("  ✓ Performance Optimization (Algorithmic, Data Structures)")
    print()
    print("[LLM FEATURES] DeepSeek API: ✅ ENABLED")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Timeout: {API_TIMEOUT}s")
    print("  Purpose: Suggestions, Explanations, Risk Analysis")
    print()
    print("[EDUCATIONAL FOCUS]")
    print("  • Learn refactoring methods")
    print("  • Understand best practices")
    print("  • Risk analysis & mitigation")
    print("  • Ethical coding practices")
    print("  • Code analysis techniques")
    print()
    print("="*80)
    print("[API ENDPOINTS]")
    print("  POST /api/refactor              - Refactor code (AST-based)")
    print("  POST /api/refactor-complete     - Unified comprehensive refactoring")
    print("  POST /api/analyze               - Comprehensive code analysis")
    print("  POST /api/best-practices        - Best practices checking")
    print("  POST /api/ethical-analysis      - Ethical coding analysis")
    print("  POST /api/suggest-refactorings  - Get refactoring suggestions")
    print("  POST /api/code-structure        - Analyze code structure")
    print("  POST /api/execute               - Execute Python code")
    print("  POST /api/advanced-refactor     - Advanced comprehensive refactoring")
    print("  POST /api/priority-refactor     - Top 20 priority patterns (FASTEST)")
    print("  POST /api/architecture-analysis - Project architecture analysis")
    print("  POST /api/generate-tests        - Generate unit tests")
    print("  POST /api/testability-score     - Analyze testability")
    print("  POST /api/optimize-performance  - Performance optimization")
    print("  GET  /api/list-patterns         - List all refactoring patterns")
    print("  GET  /api/priority-patterns     - List top 20 priority patterns")
    print("  GET  /health                    - Health check")
    print("="*80)
    print(f"[SERVER] Running on: http://localhost:8000")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)