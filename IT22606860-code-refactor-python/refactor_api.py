"""
Flask API for Code Refactoring using Three-Stage Hybrid Pipeline
Stage 1: Trained T5 Model (ML-based pattern recognition)
Stage 2: AST-Based Refactoring (deterministic transformations)
Stage 3: LLM Enhancement (DeepSeek API for polishing & suggestions)
Location: OPTICODE-AI-SERVICES/IT22606860-code-refactor-python/refactor_api.py

PIPELINE ARCHITECTURE:
  Input Code → [ML Model] → [AST Engine] → [LLM Polish] → Final Output
  Each stage can be independently enabled/disabled via config flags.

HOW TO ENABLE ML MODEL:
  Set ENABLE_ML_MODEL = True (line ~68)
  Ensure model exists at LOCAL_MODEL_PATH

HOW TO ENABLE LLM REFACTORING:
  Set ENABLE_LLM_REFACTORING = True (line ~69)
  Ensure valid API_KEY for DeepSeek/OpenRouter
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

# Centralized LLM configuration - change API key in llm_config.py
from llm_config import LLM_CONFIG, get_llm_client, call_llm, print_llm_config

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

# Import NEW Risk Detection & Performance Optimization modules (IT22606860)
try:
    from risk_refactor_filesystem import run_filesystem_risk_analysis
    from risk_refactor_injection import run_injection_risk_analysis
    from risk_refactor_resources import run_resource_risk_analysis
    from perf_optimizer_memory import run_memory_optimization
    from perf_optimizer_caching import run_caching_optimization
    from unified_risk_refactor import (
        refactor_risk_and_performance,
        quick_risk_scan,
        quick_perf_scan,
        get_refactored_code,
        get_issue_report
    )
    RISK_PERF_MODULES_AVAILABLE = True
    print("✅ Risk Detection & Performance Optimization modules loaded")
except ImportError as e:
    RISK_PERF_MODULES_AVAILABLE = False
    print(f"⚠️ Risk/Perf modules not available: {e}")

app = Flask(__name__)

# Configure CORS - Allow requests from frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


# Add CORS preflight support
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============================================
# CONFIGURATION - THREE-STAGE HYBRID PIPELINE
# ============================================
# 
# 🔧 HOW TO ENABLE/DISABLE EACH STAGE:
# 
#   Stage 1 - ML Model:  Set ENABLE_ML_MODEL = True
#   Stage 2 - AST:       Set ENABLE_AST_REFACTORING = True  (always recommended)
#   Stage 3 - LLM:       Set ENABLE_LLM_REFACTORING = True
#
#   LLM Suggestions:     Set ENABLE_LLM_SUGGESTIONS = True
#                        (separate from LLM refactoring - provides explanations/tips)
#
# Current: AST-only mode (ML + LLM disabled)
# ============================================

# ── Stage 1: Trained ML Model ──────────────────────────────────────────
# Your fine-tuned T5 model for code refactoring pattern recognition.
# The model pre-processes code before AST transformations.
# TO ENABLE: Change ENABLE_ML_MODEL to True
ENABLE_ML_MODEL = False          # ⬅️ SET True TO ENABLE ML MODEL

# ── Stage 2: AST-Based Refactoring ─────────────────────────────────────
# Deterministic AST transformations (100+ patterns). Always recommended.
ENABLE_AST_REFACTORING = True    # ✅ Primary refactoring engine (keep enabled)

# ── Stage 3: LLM Refactoring (DeepSeek) ───────────────────────────────
# LLM polishes the AST output for final improvements.
# TO ENABLE: Change ENABLE_LLM_REFACTORING to True
ENABLE_LLM_REFACTORING = False   # ⬅️ SET True TO ENABLE LLM REFACTORING

# ── LLM Suggestions (separate from refactoring) ───────────────────────
# When enabled, LLM provides explanations, tips, and risk analysis
# for the refactored code. Does NOT modify the code itself.
# TO ENABLE: Change ENABLE_LLM_SUGGESTIONS to True
ENABLE_LLM_SUGGESTIONS = False   # ⬅️ SET True TO ENABLE LLM SUGGESTIONS

# Legacy aliases (for backward compatibility)
USE_AST_REFACTORING = ENABLE_AST_REFACTORING
USE_LLM_FOR_SUGGESTIONS = ENABLE_LLM_SUGGESTIONS
LOCAL_MODEL_ENABLED = ENABLE_ML_MODEL

# ── ML Model Configuration ────────────────────────────────────────────
# Path to your trained T5 model (relative to this file)
LOCAL_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "model", "final-code-refactor-model"
)

# Model inference parameters
MAX_INPUT_LENGTH = 512
MAX_OUTPUT_LENGTH = 768
NUM_BEAMS = 3
LENGTH_PENALTY = 1.0
NO_REPEAT_NGRAM = 2

# ── LLM Configuration (from centralized llm_config.py) ────────────────
# API key, base URL, model name are all in llm_config.py
# To change the API key, edit llm_config.py ONLY
MODEL_NAME = LLM_CONFIG['model_name']
API_TIMEOUT = LLM_CONFIG['timeout']

# ============================================
# INITIALIZE AI CLIENTS
# ============================================

# Initialize LLM client from centralized config (only if LLM features enabled)
deepseek_client = None
if ENABLE_LLM_REFACTORING or ENABLE_LLM_SUGGESTIONS:
    deepseek_client = get_llm_client()
    if deepseek_client:
        print("✅ LLM client loaded from llm_config.py")
    else:
        print("⚠️ LLM client failed. AST refactoring will still work.")
else:
    print("ℹ️  LLM client skipped (ENABLE_LLM_REFACTORING and ENABLE_LLM_SUGGESTIONS both False)")

print_llm_config()

# Initialize Local Model
local_model = None
local_tokenizer = None
device = None

def load_local_model():
    """Load the trained T5 model for ML-based refactoring (Stage 1)"""
    global local_model, local_tokenizer, device
    
    if not ENABLE_ML_MODEL:
        print("[STARTUP] ML Model is DISABLED (set ENABLE_ML_MODEL = True to enable)")
        return False
    
    if not LOCAL_MODEL_PATH:
        print("[WARNING] LOCAL_MODEL_PATH not set. ML model will be skipped.")
        return False
    
    if not os.path.exists(LOCAL_MODEL_PATH):
        print(f"[ERROR] Model path does not exist: {LOCAL_MODEL_PATH}")
        print(f"[HINT]  Expected model at: model/final-code-refactor-model/")
        return False
    
    try:
        if not TRANSFORMERS_AVAILABLE:
            print("[STARTUP] transformers library not installed - skipping ML model")
            print("[HINT]  Run: pip install transformers torch")
            return False
            
        print(f"[STARTUP] Loading trained T5 model from: {LOCAL_MODEL_PATH}")
        
        local_tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)
        local_model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_PATH)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        local_model = local_model.to(device)
        local_model.eval()
        
        if hasattr(torch, 'inference_mode'):
            torch.set_grad_enabled(False)
        
        print(f"[STARTUP] ✅ Trained T5 model loaded successfully")
        print(f"[STARTUP] Device: {device.upper()}")
        print(f"[STARTUP] Config: {NUM_BEAMS} beams, max_len={MAX_OUTPUT_LENGTH}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load ML model: {str(e)}")
        traceback.print_exc()
        return False

# Load ML model on startup (only if enabled)
local_model_loaded = load_local_model()

# ── Startup Summary ──
print(f"\n{'='*60}")
print(f"[STARTUP] Hybrid Pipeline Configuration:")
print(f"  Stage 1 - ML Model (T5):    {'✅ LOADED' if local_model_loaded else '❌ DISABLED'}")
print(f"  Stage 2 - AST Engine:        {'✅ ENABLED' if ENABLE_AST_REFACTORING else '❌ DISABLED'}")
print(f"  Stage 3 - LLM Refactoring:   {'✅ ENABLED' if ENABLE_LLM_REFACTORING else '❌ DISABLED'}")
print(f"  LLM Suggestions:             {'✅ ENABLED' if ENABLE_LLM_SUGGESTIONS else '❌ DISABLED'}")
print(f"{'='*60}")
if not ENABLE_ML_MODEL:
    print(f"  💡 To enable ML Model:  Set ENABLE_ML_MODEL = True")
if not ENABLE_LLM_REFACTORING:
    print(f"  💡 To enable LLM:       Set ENABLE_LLM_REFACTORING = True")
if not ENABLE_LLM_SUGGESTIONS:
    print(f"  💡 To enable Suggestions: Set ENABLE_LLM_SUGGESTIONS = True")
print(f"{'='*60}\n")

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
# STAGE 1: ML MODEL REFACTORING (Trained T5)
# ============================================

def refactor_with_ml_model(code: str, instruction: str = "Refactor this code") -> Dict:
    """
    Stage 1: Refactor code using the trained T5 model.
    The model recognizes refactoring patterns from training data and
    produces an initial refactored version that AST can further improve.
    
    Returns: Dictionary with refactored code and analysis
    """
    
    if not ENABLE_ML_MODEL:
        return {
            'success': False,
            'error': 'ML model is disabled (set ENABLE_ML_MODEL = True)',
            'refactored_code': code,
            'skipped': True
        }
    
    if not local_model_loaded or local_model is None or local_tokenizer is None:
        return {
            'success': False,
            'error': 'ML model not loaded',
            'refactored_code': code,
            'skipped': True
        }
    
    try:
        print(f"[STAGE 1 - ML MODEL] Processing with trained T5 model...")
        
        # Create prompt matching training format
        prompt = f"refactor: {code}"
        
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
        
        # Generate with trained model
        with torch.inference_mode() if hasattr(torch, 'inference_mode') else torch.no_grad():
            outputs = local_model.generate(
                **inputs,
                max_length=MAX_OUTPUT_LENGTH,
                min_length=10,
                num_beams=NUM_BEAMS,
                length_penalty=LENGTH_PENALTY,
                no_repeat_ngram_size=NO_REPEAT_NGRAM,
                early_stopping=True,
                do_sample=False
            )
        
        # Decode
        refactored_raw = local_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Post-process to fix common model output issues
        refactored = post_process_refactored(code, refactored_raw)
        
        # Validate syntax
        is_valid, syntax_msg = validate_syntax(refactored)
        
        # Fallback attempt for invalid syntax on short code
        if not is_valid and len(code) < 300:
            with torch.inference_mode() if hasattr(torch, 'inference_mode') else torch.no_grad():
                outputs_fallback = local_model.generate(
                    **inputs,
                    max_length=MAX_OUTPUT_LENGTH,
                    num_beams=2,
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
                syntax_msg = "Valid syntax (fallback generation)"
        
        print(f"[STAGE 1 - ML MODEL] ✅ Complete - Valid: {is_valid}")
        
        return {
            'success': True,
            'refactored_code': refactored,
            'is_valid_syntax': is_valid,
            'syntax_message': syntax_msg,
            'post_processed': refactored != refactored_raw,
            'skipped': False,
            'model_info': {
                'type': 'T5ForConditionalGeneration',
                'path': LOCAL_MODEL_PATH,
                'device': device
            }
        }
        
    except Exception as e:
        print(f"[STAGE 1 - ML MODEL ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'refactored_code': code,
            'skipped': False
        }


# ============================================
# STAGE 2: AST-BASED REFACTORING
# ============================================

def refactor_with_ast(code: str, options: Dict = None) -> Dict:
    """
    Stage 2: Apply deterministic AST-based refactoring patterns (100+ patterns).
    This is the core refactoring engine that applies rule-based transformations.
    
    Returns: Dictionary with refactored code and detailed changes
    """
    
    if not ENABLE_AST_REFACTORING:
        return {
            'success': False,
            'error': 'AST refactoring is disabled (set ENABLE_AST_REFACTORING = True)',
            'refactored_code': code,
            'skipped': True
        }
    
    if options is None:
        options = {
            'apply_basic': True,
            'apply_priority': True,
            'apply_advanced': True,
            'apply_performance': True,
            'categories': None
        }
    
    try:
        print(f"[STAGE 2 - AST] Applying AST refactoring patterns...")
        
        result = refactor_complete(code, options)
        
        if result.get('success'):
            refactored = result.get('refactored_code', code)
            print(f"[STAGE 2 - AST] ✅ Complete - {len(result.get('all_changes', []))} changes applied")
            return {
                'success': True,
                'refactored_code': refactored,
                'summary': result.get('summary', {}),
                'stages': result.get('stages', {}),
                'analysis': result.get('analysis', {}),
                'changes': result.get('all_changes', []),
                'suggestions': result.get('all_suggestions', []),
                'skipped': False
            }
        else:
            print(f"[STAGE 2 - AST] ⚠️ Failed: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'AST refactoring failed'),
                'refactored_code': code,
                'skipped': False
            }
    
    except Exception as e:
        print(f"[STAGE 2 - AST ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'refactored_code': code,
            'skipped': False
        }


# ============================================
# STAGE 3: LLM REFACTORING (DeepSeek)
# ============================================

def refactor_with_deepseek(code: str, instruction: str = "Refactor this code") -> str:
    """
    Stage 3: Polish/enhance refactored code using DeepSeek LLM.
    Takes the output from Stages 1+2 and applies LLM-based improvements.
    
    Returns: Refactored code string
    """
    
    if not ENABLE_LLM_REFACTORING:
        return code  # Pass through unchanged when disabled
    
    system_prompt = (
        "You are a Python refactoring expert. Refactor the given Python code to improve it.\n"
        "Preserve functionality. Follow PEP8. Improve readability and efficiency.\n"
        "Output ONLY valid Python code without explanations."
    )
    
    user_prompt = f"{instruction}\n\n{code}"

    try:
        if not deepseek_client:
            print("[STAGE 3 - LLM] Client not available, passing through")
            return code
        
        print(f"[STAGE 3 - LLM] Polishing with DeepSeek...")
        
        raw_content = call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7,
            client=deepseek_client
        )
        
        if not raw_content or not raw_content.strip():
            print(f"[STAGE 3 - LLM WARNING] Empty response, using input")
            return code
        
        cleaned = clean_ai_output(raw_content)
        
        print(f"[STAGE 3 - LLM] ✅ Complete - {len(cleaned)} chars")
        
        return cleaned
        
    except Exception as e:
        print(f"[STAGE 3 - LLM ERROR] {str(e)}")
        raise e

# ============================================
# THREE-STAGE HYBRID REFACTORING PIPELINE
# ============================================

def refactor_code_hybrid(code: str, instruction: str = "Refactor this code", ast_options: Dict = None) -> Dict:
    """
    🚀 THREE-STAGE HYBRID REFACTORING PIPELINE
    
    Pipeline: Input → [Stage 1: ML Model] → [Stage 2: AST] → [Stage 3: LLM] → Output
    
    Each stage is independently toggleable:
      - ENABLE_ML_MODEL        → Stage 1 (Trained T5 model)
      - ENABLE_AST_REFACTORING → Stage 2 (100+ AST patterns)  
      - ENABLE_LLM_REFACTORING → Stage 3 (DeepSeek LLM polish)
    
    Disabled stages are simply skipped — the code passes through unchanged.
    The final output is always compared against the ORIGINAL input code.
    
    Args:
        code: Python source code to refactor
        instruction: Refactoring instruction/context
        ast_options: Options for AST stage (apply_basic, apply_priority, etc.)
    
    Returns:
        Complete result with pipeline info, metrics, and all stage outputs
    """
    
    original_code = code
    current_code = code
    
    pipeline_info = {
        'pipeline_type': 'hybrid_three_stage',
        'stage1_ml_model': {'enabled': ENABLE_ML_MODEL, 'used': False, 'result': None},
        'stage2_ast': {'enabled': ENABLE_AST_REFACTORING, 'used': False, 'result': None},
        'stage3_llm': {'enabled': ENABLE_LLM_REFACTORING, 'used': False, 'result': None},
        'original_code': original_code,
        'stages_executed': []
    }
    
    ast_result_data = {}  # Store AST stage data for response
    
    # ── STAGE 1: ML Model ──────────────────────────────────────────
    if ENABLE_ML_MODEL:
        print(f"\n{'─'*50}")
        print(f"[PIPELINE] Stage 1/3: ML Model (Trained T5)")
        print(f"{'─'*50}")
        
        stage1_result = refactor_with_ml_model(current_code, instruction)
        pipeline_info['stage1_ml_model']['used'] = True
        pipeline_info['stage1_ml_model']['result'] = {
            'success': stage1_result.get('success'),
            'valid_syntax': stage1_result.get('is_valid_syntax'),
            'skipped': stage1_result.get('skipped', False)
        }
        
        if stage1_result['success'] and stage1_result.get('is_valid_syntax'):
            current_code = stage1_result['refactored_code']
            pipeline_info['stages_executed'].append('ml_model')
            print(f"[PIPELINE] ✅ Stage 1 → code updated, passing to Stage 2")
        else:
            print(f"[PIPELINE] ⚠️ Stage 1 skipped/failed → using original for Stage 2")
    else:
        print(f"[PIPELINE] Stage 1 DISABLED (ML Model)")
    
    # ── STAGE 2: AST Refactoring ──────────────────────────────────
    if ENABLE_AST_REFACTORING:
        print(f"\n{'─'*50}")
        print(f"[PIPELINE] Stage 2/3: AST Refactoring (100+ patterns)")
        print(f"{'─'*50}")
        
        stage2_result = refactor_with_ast(current_code, ast_options)
        pipeline_info['stage2_ast']['used'] = True
        pipeline_info['stage2_ast']['result'] = {
            'success': stage2_result.get('success'),
            'changes_count': len(stage2_result.get('changes', [])),
            'skipped': stage2_result.get('skipped', False)
        }
        
        if stage2_result['success']:
            current_code = stage2_result['refactored_code']
            ast_result_data = stage2_result  # Save for response
            pipeline_info['stages_executed'].append('ast')
            print(f"[PIPELINE] ✅ Stage 2 → {len(stage2_result.get('changes', []))} changes applied")
        else:
            print(f"[PIPELINE] ⚠️ Stage 2 failed → continuing with current code")
    else:
        print(f"[PIPELINE] Stage 2 DISABLED (AST)")
    
    # ── STAGE 3: LLM Polish ──────────────────────────────────────
    if ENABLE_LLM_REFACTORING:
        print(f"\n{'─'*50}")
        print(f"[PIPELINE] Stage 3/3: LLM Polish (DeepSeek)")
        print(f"{'─'*50}")
        
        try:
            llm_result = refactor_with_deepseek(current_code, instruction)
            pipeline_info['stage3_llm']['used'] = True
            
            if llm_result and llm_result.strip() and llm_result != current_code:
                current_code = llm_result
                pipeline_info['stage3_llm']['result'] = {
                    'success': True,
                    'output_length': len(llm_result)
                }
                pipeline_info['stages_executed'].append('llm')
                print(f"[PIPELINE] ✅ Stage 3 → LLM polished ({len(llm_result)} chars)")
            else:
                pipeline_info['stage3_llm']['result'] = {
                    'success': True,
                    'note': 'LLM returned same code (no further improvements)'
                }
                print(f"[PIPELINE] ℹ️ Stage 3 → No additional changes from LLM")
                
        except Exception as e:
            print(f"[PIPELINE] ⚠️ Stage 3 failed: {str(e)} → using Stage 2 output")
            pipeline_info['stage3_llm']['result'] = {
                'success': False,
                'error': str(e)
            }
    else:
        print(f"[PIPELINE] Stage 3 DISABLED (LLM)")
    
    # ── Build Final Response ──────────────────────────────────────
    final_code = current_code
    
    comparison_info = {
        'original_length': len(original_code),
        'final_length': len(final_code),
        'character_change': len(final_code) - len(original_code),
        'original_lines': len(original_code.splitlines()),
        'final_lines': len(final_code.splitlines()),
        'line_change': len(final_code.splitlines()) - len(original_code.splitlines()),
        'stages_applied': len(pipeline_info['stages_executed']),
        'stages_list': pipeline_info['stages_executed']
    }
    
    active_method = ' + '.join([
        s.replace('ml_model', 'ML Model').replace('ast', 'AST').replace('llm', 'LLM')
        for s in pipeline_info['stages_executed']
    ]) or 'No stages executed'
    
    print(f"\n{'='*50}")
    print(f"[PIPELINE] ✅ Complete: {active_method}")
    print(f"[PIPELINE] Original: {len(original_code)} chars → Final: {len(final_code)} chars")
    print(f"{'='*50}\n")
    
    return {
        'success': True,
        'final_code': final_code,
        'original_code': original_code,
        'pipeline_info': pipeline_info,
        'comparison': comparison_info,
        'method': active_method,
        # Include AST details if available
        'summary': ast_result_data.get('summary', {}),
        'stages': ast_result_data.get('stages', {}),
        'analysis': ast_result_data.get('analysis', {}),
        'changes': ast_result_data.get('changes', []),
        'suggestions': ast_result_data.get('suggestions', [])
    }

# ============================================
# LLM SUGGESTIONS HELPER
# ============================================

def get_llm_suggestions(original_code: str, refactored_code: str) -> Dict:
    """Get AI-powered suggestions and explanations for refactored code.
    Only active when ENABLE_LLM_SUGGESTIONS = True."""
    
    if not ENABLE_LLM_SUGGESTIONS:
        return {
            'success': False, 
            'suggestions': 'LLM suggestions disabled (set ENABLE_LLM_SUGGESTIONS = True to enable)'
        }
    
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
        
        response_text = call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7,
            client=deepseek_client
        )
        
        if response_text:
            return {
                'success': True,
                'suggestions': response_text
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
    """Health check endpoint with full pipeline status"""
    return jsonify({
        'status': 'healthy',
        'pipeline': {
            'type': 'three_stage_hybrid',
            'description': 'ML Model → AST Engine → LLM Polish',
            'stage1_ml_model': {
                'enabled': ENABLE_ML_MODEL,
                'loaded': local_model_loaded,
                'model_type': 'T5ForConditionalGeneration',
                'path': LOCAL_MODEL_PATH if local_model_loaded else None,
                'device': device if local_model_loaded else None,
                'how_to_enable': 'Set ENABLE_ML_MODEL = True in refactor_api.py'
            },
            'stage2_ast': {
                'enabled': ENABLE_AST_REFACTORING,
                'patterns': '100+ refactoring patterns',
                'features': [
                    'Simplify conditionals',
                    'Extract complex expressions',
                    'Improve loops',
                    'Refactor magic numbers',
                    'Performance optimization',
                    'Code structure analysis'
                ]
            },
            'stage3_llm': {
                'enabled': ENABLE_LLM_REFACTORING,
                'model': MODEL_NAME,
                'timeout': API_TIMEOUT,
                'how_to_enable': 'Set ENABLE_LLM_REFACTORING = True in refactor_api.py'
            },
            'llm_suggestions': {
                'enabled': ENABLE_LLM_SUGGESTIONS,
                'purpose': 'Explanations, tips, and risk analysis (does not modify code)',
                'how_to_enable': 'Set ENABLE_LLM_SUGGESTIONS = True in refactor_api.py'
            }
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
            '/api/refactor': 'POST - Refactor code (hybrid pipeline)',
            '/api/refactor-complete': 'POST - Unified comprehensive refactoring',
            '/api/refactor-full': 'POST - Unified refactor + all analyses',
            '/api/analyze': 'POST - Comprehensive code analysis',
            '/api/best-practices': 'POST - Best practices checking',
            '/api/ethical-analysis': 'POST - Ethical coding analysis',
            '/api/suggest-refactorings': 'POST - Get refactoring suggestions',
            '/api/code-structure': 'POST - Analyze code structure',
            '/api/execute': 'POST - Execute Python code',
            '/api/architecture-analyze': 'POST - Architecture analysis',
            '/health': 'GET - Health check'
        }
    })

@app.route('/api/refactor', methods=['POST'])
def refactor():
    """
    Main refactoring endpoint - Three-Stage Hybrid Pipeline
    
    Pipeline: Input → [ML Model] → [AST] → [LLM] → Output
    
    Each stage can be toggled via config flags or per-request overrides:
      - use_ml: Override ENABLE_ML_MODEL for this request
      - use_ast: Override ENABLE_AST_REFACTORING for this request  
      - use_llm: Override ENABLE_LLM_REFACTORING for this request
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        instruction = data.get('instruction', 'Refactor this code')
        get_suggestions = data.get('get_suggestions', True)
        
        # Per-request stage overrides (optional)
        # These let the frontend toggle stages without changing server config
        use_ml_override = data.get('use_ml', None)
        use_ast_override = data.get('use_ast', None)
        use_llm_override = data.get('use_llm', None)
        
        # Validate
        if not code:
            return jsonify({
                'success': False,
                'message': 'No code provided'
            }), 400
        
        if language.lower() != 'python':
            return jsonify({
                'success': False,
                'message': 'Only Python is currently supported'
            }), 400
        
        # Temporarily apply per-request overrides if provided
        global ENABLE_ML_MODEL, ENABLE_AST_REFACTORING, ENABLE_LLM_REFACTORING
        original_ml = ENABLE_ML_MODEL
        original_ast = ENABLE_AST_REFACTORING
        original_llm = ENABLE_LLM_REFACTORING
        
        if use_ml_override is not None:
            ENABLE_ML_MODEL = bool(use_ml_override)
        if use_ast_override is not None:
            ENABLE_AST_REFACTORING = bool(use_ast_override)
        if use_llm_override is not None:
            ENABLE_LLM_REFACTORING = bool(use_llm_override)
        
        active_stages = []
        if ENABLE_ML_MODEL: active_stages.append('ML')
        if ENABLE_AST_REFACTORING: active_stages.append('AST')
        if ENABLE_LLM_REFACTORING: active_stages.append('LLM')
        
        print(f"\n[REFACTOR] Starting ({len(code)} chars) - Pipeline: {' → '.join(active_stages) or 'NONE'}")

        try:
            # AST options from request
            ast_options = {
                'apply_basic': True,
                'apply_priority': True,
                'apply_advanced': True,
                'apply_performance': True,
                'categories': data.get('categories')
            }

            # Run the hybrid pipeline
            result = refactor_code_hybrid(code, instruction, ast_options)

            if not result.get('success'):
                return jsonify({
                    'success': False,
                    'message': f'Refactoring failed: {result.get("error")}',
                    'original_code': code
                }), 500

            refactored = result.get('final_code', code)

            # Get AI suggestions if enabled
            ai_suggestions = None
            if get_suggestions and ENABLE_LLM_SUGGESTIONS:
                try:
                    print("[REFACTOR] Getting LLM suggestions...")
                    ai_suggestions = get_llm_suggestions(code, refactored)
                except Exception as e:
                    print(f"[WARNING] LLM suggestions failed: {str(e)}")
                    ai_suggestions = None

            processing_time = (time.time() - start_time) * 1000

            response = {
                'success': True,
                'refactored_code': refactored,
                'original_code': code,
                'processing_time': processing_time,
                'method': result.get('method', 'AST'),
                'pipeline_info': result.get('pipeline_info', {}),
                'summary': result.get('summary', {}),
                'stages': result.get('stages', {}),
                'analysis': result.get('analysis', {}),
                'changes': result.get('changes', []),
                'suggestions': result.get('suggestions', []),
                'ai_suggestions': ai_suggestions,
                'comparison': result.get('comparison', {}),
                'message': f'Code refactored successfully using: {result.get("method", "hybrid pipeline")}'
            }

            print(f"[COMPLETE] {processing_time:.0f}ms - {result.get('method', 'hybrid')}")

            return jsonify(response)
        
        finally:
            # Restore original config after per-request overrides
            ENABLE_ML_MODEL = original_ml
            ENABLE_AST_REFACTORING = original_ast
            ENABLE_LLM_REFACTORING = original_llm
    
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
    print("[THREE-STAGE HYBRID PIPELINE]")
    print(f"  Stage 1 - ML Model (T5):  {'✅ ENABLED' if ENABLE_ML_MODEL else '❌ DISABLED'}")
    print(f"  Stage 2 - AST Engine:     {'✅ ENABLED' if ENABLE_AST_REFACTORING else '❌ DISABLED'}")
    print(f"  Stage 3 - LLM (DeepSeek): {'✅ ENABLED' if ENABLE_LLM_REFACTORING else '❌ DISABLED'}")
    print(f"  LLM Suggestions:          {'✅ ENABLED' if ENABLE_LLM_SUGGESTIONS else '❌ DISABLED'}")
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


@app.route('/api/patterns/all', methods=['GET'])
def all_patterns():
    """Get ALL available refactoring patterns from all modules"""
    try:
        advanced_patterns = list_all_patterns()
        priority_pattern_list = get_priority_patterns()

        return jsonify({
            'success': True,
            'advanced_patterns': advanced_patterns,
            'priority_patterns': priority_pattern_list,
            'total_advanced': len(advanced_patterns) if isinstance(advanced_patterns, list) else 0,
            'total_priority': len(priority_pattern_list)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# NEW: RISK DETECTION & PERFORMANCE OPTIMIZATION ENDPOINTS
# Author: IT22606860
# ============================================

@app.route('/api/risk/filesystem', methods=['POST'])
def risk_filesystem():
    """Analyze filesystem security risks (unclosed files, path traversal, etc.)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_filesystem_risk_analysis(code)
        return jsonify({
            'success': True,
            'category': 'FILESYSTEM_SECURITY',
            'risk_score': result.get('risk_score', 0),
            'total_issues': result.get('total_issues', 0),
            'issues': [{
                'type': i.risk_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.after_suggestion
            } for i in result.get('issues', [])],
            'refactored_code': result.get('refactored_code', code),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/risk/injection', methods=['POST'])
def risk_injection():
    """Analyze injection vulnerabilities (shell, SQL, eval, yaml, pickle)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_injection_risk_analysis(code)
        return jsonify({
            'success': True,
            'category': 'INJECTION_SECURITY',
            'risk_score': result.get('risk_score', 0),
            'total_issues': result.get('total_issues', 0),
            'issues': [{
                'type': i.risk_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.after_suggestion
            } for i in result.get('issues', [])],
            'refactored_code': result.get('refactored_code', code),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/risk/resources', methods=['POST'])
def risk_resources():
    """Analyze resource leaks & concurrency issues (locks, DB connections, timeouts)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_resource_risk_analysis(code)
        return jsonify({
            'success': True,
            'category': 'RESOURCE_SAFETY',
            'risk_score': result.get('risk_score', 0),
            'total_issues': result.get('total_issues', 0),
            'issues': [{
                'type': i.risk_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.after_suggestion
            } for i in result.get('issues', [])],
            'refactored_code': result.get('refactored_code', code),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/perf/memory', methods=['POST'])
def perf_memory():
    """Optimize memory usage (__slots__, string concat, readlines, list membership)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Perf modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_memory_optimization(code)
        return jsonify({
            'success': True,
            'category': 'MEMORY_PERFORMANCE',
            'perf_score': result.get('perf_score', 0),
            'total_issues': result.get('total_issues', 0),
            'issues': [{
                'type': i.issue_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.after_suggestion,
                'expected_improvement': i.expected_improvement
            } for i in result.get('issues', [])],
            'optimized_code': result.get('optimized_code', code),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/perf/caching', methods=['POST'])
def perf_caching():
    """Optimize caching & algorithms (lru_cache, range(len), augmented assignment)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Perf modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_caching_optimization(code)
        return jsonify({
            'success': True,
            'category': 'CACHING_PERFORMANCE',
            'perf_score': result.get('perf_score', 0),
            'total_issues': result.get('total_issues', 0),
            'issues': [{
                'type': i.issue_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.after_suggestion,
                'expected_improvement': i.expected_improvement
            } for i in result.get('issues', [])],
            'optimized_code': result.get('optimized_code', code),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/unified-risk-perf', methods=['POST'])
def unified_risk_perf():
    """Run FULL 5-stage risk detection & performance optimization pipeline"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk/Perf modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = refactor_risk_and_performance(code)
        return jsonify({
            'success': True,
            'overall_risk_score': result.get('overall_risk_score', 0),
            'overall_perf_score': result.get('overall_perf_score', 0),
            'total_issues': result.get('total_issues', 0),
            'summary': result.get('summary', {}),
            'categories': result.get('categories', {}),
            'category_breakdown': result.get('category_breakdown', {}),
            'issues': [{
                'category': i.category,
                'type': i.issue_type,
                'severity': i.severity,
                'line': i.line,
                'description': i.description,
                'fix': i.fix_suggestion,
                'expected_improvement': i.expected_improvement
            } for i in result.get('issues', [])],
            'refactored_code': result.get('refactored_code', code),
            'all_changes': result.get('all_changes', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


# =============================================================================
# SECURITY AST REFACTORING ENDPOINT (20 Bandit Patterns)
# =============================================================================

@app.route('/api/security-refactor', methods=['POST'])
def security_refactor_endpoint():
    """Comprehensive AST-based security vulnerability detection & auto-fix (20 patterns)."""
    try:
        from security_ast_refactor import run_security_refactoring
    except ImportError:
        return jsonify({'success': False, 'error': 'security_ast_refactor module not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = run_security_refactoring(code)
        return jsonify({
            'success': True,
            'refactored_code': result.get('refactored_code', code),
            'total_issues': result.get('total_issues', 0),
            'total_fixes': result.get('total_fixes', 0),
            'risk_score': result.get('risk_score', 0),
            'vulnerability_summary': result.get('vulnerability_summary', {}),
            'suggestions': result.get('suggestions', []),
            'changes_applied': result.get('changes_applied', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/quick-risk-scan', methods=['POST'])
def quick_risk_scan_endpoint():
    """Quick security-only scan (stages 1-3: filesystem, injection, resources)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = quick_risk_scan(code)
        return jsonify({
            'success': True,
            'risk_score': result.get('risk_score', 0),
            'total_issues': result.get('total_issues', 0),
            'is_safe': result.get('is_safe', False),
            'issues': [{
                'type': getattr(i, 'risk_type', 'UNKNOWN'),
                'severity': getattr(i, 'severity', 'LOW'),
                'line': getattr(i, 'line', 0),
                'description': getattr(i, 'description', '')
            } for i in result.get('issues', [])]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/quick-perf-scan', methods=['POST'])
def quick_perf_scan_endpoint():
    """Quick performance-only scan (stages 4-5: memory, caching)"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Perf modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        result = quick_perf_scan(code)
        return jsonify({
            'success': True,
            'perf_score': result.get('perf_score', 0),
            'total_issues': result.get('total_issues', 0),
            'is_optimized': result.get('is_optimized', False),
            'issues': [{
                'type': getattr(i, 'issue_type', 'UNKNOWN'),
                'severity': getattr(i, 'severity', 'LOW'),
                'line': getattr(i, 'line', 0),
                'description': getattr(i, 'description', '')
            } for i in result.get('issues', [])]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/risk-report', methods=['POST'])
def risk_report():
    """Generate human-readable risk & performance report"""
    if not RISK_PERF_MODULES_AVAILABLE:
        return jsonify({'success': False, 'error': 'Risk/Perf modules not available'}), 503

    try:
        data = request.get_json()
        code = data.get('code', '')
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400

        report = get_issue_report(code)
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


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
    print("[THREE-STAGE HYBRID REFACTORING PIPELINE]")
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  Input Code                                        │")
    print("  │    ↓                                               │")
    print(f"  │  Stage 1: ML Model (T5)     {'✅ ENABLED' if ENABLE_ML_MODEL else '❌ DISABLED':>12}         │")
    print("  │    ↓                                               │")
    print(f"  │  Stage 2: AST Engine         {'✅ ENABLED' if ENABLE_AST_REFACTORING else '❌ DISABLED':>12}         │")
    print("  │    ↓                                               │")
    print(f"  │  Stage 3: LLM (DeepSeek)    {'✅ ENABLED' if ENABLE_LLM_REFACTORING else '❌ DISABLED':>12}         │")
    print("  │    ↓                                               │")
    print("  │  Refactored Output                                 │")
    print("  └─────────────────────────────────────────────────────┘")
    print()
    print("  HOW TO ENABLE DISABLED STAGES:")
    if not ENABLE_ML_MODEL:
        print("    ML Model:  Set ENABLE_ML_MODEL = True       (line ~68)")
    if not ENABLE_LLM_REFACTORING:
        print("    LLM:       Set ENABLE_LLM_REFACTORING = True (line ~78)")
    if not ENABLE_LLM_SUGGESTIONS:
        print("    Suggestions: Set ENABLE_LLM_SUGGESTIONS = True (line ~84)")
    print()
    print("[AST REFACTORING ENGINE - 12 Categories]")
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
    print("  ✓ Security AST Refactoring (20 Bandit Patterns - NEW)")
    print("  ✓ Complexity Metrics")
    print("  ✓ Refactoring Suggestions")
    print("  ✓ Architecture Analysis (Design Patterns, SOLID)")
    print("  ✓ Test Generation (Unit Tests, Coverage)")
    print("  ✓ Performance Optimization (Algorithmic, Data Structures)")
    print()
    print("[RISK DETECTION & PERFORMANCE OPTIMIZATION - NEW]")
    print(f"  Status: {'✅ ENABLED' if RISK_PERF_MODULES_AVAILABLE else '❌ NOT AVAILABLE'}")
    if RISK_PERF_MODULES_AVAILABLE:
        print("  ✓ Filesystem Security (unclosed files, path traversal, unsafe rmtree)")
        print("  ✓ Injection Vulnerabilities (shell, SQL, eval, yaml, pickle)")
        print("  ✓ Resource Safety (locks, DB connections, bare except, timeouts)")
        print("  ✓ Memory Optimization (__slots__, string concat, readlines)")
        print("  ✓ Caching & Algorithms (lru_cache, range(len), nested loops)")
        print("  ✓ Unified 5-Stage Pipeline (risk + performance combined)")
    print()
    print("[ML MODEL]")
    print(f"  Type: T5ForConditionalGeneration")
    print(f"  Path: {LOCAL_MODEL_PATH}")
    print(f"  Status: {'✅ LOADED' if local_model_loaded else '❌ DISABLED'}")
    print()
    if ENABLE_LLM_REFACTORING or ENABLE_LLM_SUGGESTIONS:
        print(f"[LLM] DeepSeek API: ✅ ENABLED")
        print(f"  Model: {MODEL_NAME}")
        print(f"  Timeout: {API_TIMEOUT}s")
        print(f"  Refactoring: {'✅' if ENABLE_LLM_REFACTORING else '❌'}")
        print(f"  Suggestions: {'✅' if ENABLE_LLM_SUGGESTIONS else '❌'}")
    else:
        print("[LLM] DeepSeek API: ❌ DISABLED")
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
    print("  POST /api/refactor              - Refactor code (hybrid pipeline)")
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
    print("  GET  /api/patterns/all          - All patterns from all modules")
    print("  GET  /health                    - Health check + pipeline status")
    print()
    print("  [RISK DETECTION & PERFORMANCE ENDPOINTS - NEW]")
    print("  POST /api/risk/filesystem       - Filesystem security risks")
    print("  POST /api/risk/injection        - Injection vulnerabilities")
    print("  POST /api/risk/resources        - Resource leaks & concurrency")
    print("  POST /api/perf/memory           - Memory optimization")
    print("  POST /api/perf/caching          - Caching & algorithmic optimization")
    print("  POST /api/unified-risk-perf     - FULL 5-stage pipeline")
    print("  POST /api/quick-risk-scan       - Quick security-only scan")
    print("  POST /api/security-refactor     - 20-pattern AST security refactoring (NEW)")
    print("  POST /api/quick-perf-scan       - Quick performance-only scan")
    print("  POST /api/risk-report           - Human-readable report")
    print("="*80)
    print(f"[SERVER] Running on: http://localhost:8000")
    print("="*80 + "\n")
    
    # Check if running under run_backend.py (FLASK_DEBUG=0 disables debug/reloader)
    debug_mode = os.environ.get('FLASK_DEBUG', '1') != '0'
    # Never use reloader when started via subprocess to avoid FD issues
    use_reloader = debug_mode and os.environ.get('WERKZEUG_RUN_MAIN') != 'true'
    app.run(host='0.0.0.0', port=8000, debug=debug_mode, use_reloader=False)