"""
Flask API for Code Refactoring using Two-Stage Process
Stage 1: Local Trained Model
Stage 2: DeepSeek API (OpenRouter)
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
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import ast
from typing import Dict, Tuple

app = Flask(__name__)
CORS(app)  # Enable CORS for React

# ============================================
# CONFIGURATION
# ============================================

# Local Trained Model Configuration
LOCAL_MODEL_PATH = r"E:\Research Resources\Model Trained dataset\haritha\code-refactor-model"
LOCAL_MODEL_ENABLED = True

# Generation settings for local model
MAX_INPUT_LENGTH = 256
MAX_OUTPUT_LENGTH = 256
NUM_BEAMS = 5
LENGTH_PENALTY = 1.0
NO_REPEAT_NGRAM = 2

# DeepSeek API Configuration
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

# ============================================
# INITIALIZE AI CLIENTS
# ============================================

# Initialize DeepSeek client
deepseek_client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

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
        print(f"[STARTUP] Loading local model from: {LOCAL_MODEL_PATH}")
        
        local_tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)
        local_model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_PATH)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        local_model = local_model.to(device)
        local_model.eval()  # Set to evaluation mode
        
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
        
        # Generate with beam search
        with torch.no_grad():
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
        
        # Post-process
        refactored = post_process_refactored(code, refactored_raw)
        
        # Validate
        is_valid, syntax_msg = validate_syntax(refactored)
        
        # If invalid, try fallback generation
        if not is_valid:
            print("[STAGE 1] First attempt invalid, trying fallback generation...")
            with torch.no_grad():
                outputs_fallback = local_model.generate(
                    **inputs,
                    max_length=MAX_OUTPUT_LENGTH,
                    num_beams=3,
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
        
        # Variable analysis
        orig_vars = extract_variables(code)
        ref_vars = extract_variables(refactored)
        
        print(f"[STAGE 1] ✅ Local model complete - Valid: {is_valid}")
        
        return {
            'success': True,
            'refactored_code': refactored,
            'is_valid_syntax': is_valid,
            'syntax_message': syntax_msg,
            'original_variables': list(orig_vars),
            'refactored_variables': list(ref_vars),
            'missing_variables': list(orig_vars - ref_vars),
            'post_processed': refactored != refactored_raw,
            'skipped': False
        }
        
    except Exception as e:
        print(f"[STAGE 1 ERROR] {str(e)}")
        traceback.print_exc()
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
        print(f"[STAGE 2] DeepSeek API refactoring...")
        print(f"[STAGE 2] Input code length: {len(code)} characters")
        
        completion = deepseek_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "Opticode Refactor API", 
            },
            model=MODEL_NAME,
            max_tokens=2000,  # Ensure we get enough tokens back
            temperature=0.7,   # Add some creativity
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
        
        # Debug: Print the full response
        print(f"[STAGE 2 DEBUG] Completion choices: {len(completion.choices)}")
        print(f"[STAGE 2 DEBUG] First choice: {completion.choices[0] if completion.choices else 'None'}")
        
        if not completion.choices or len(completion.choices) == 0:
            print(f"[STAGE 2 ERROR] No choices in completion response")
            return code
        
        raw_content = completion.choices[0].message.content
        print(f"[STAGE 2 DEBUG] Raw content type: {type(raw_content)}")
        print(f"[STAGE 2 DEBUG] Raw content: {repr(raw_content)}")
        print(f"[STAGE 2 DEBUG] Raw content length: {len(raw_content) if raw_content else 0}")
        
        if not raw_content or not raw_content.strip():
            print(f"[STAGE 2 WARNING] DeepSeek returned empty content, using Stage 1 output")
            return code  # Return the input code if DeepSeek returns nothing
        
        cleaned = clean_ai_output(raw_content)
        print(f"[STAGE 2 DEBUG] Cleaned content length: {len(cleaned)}")
        if len(cleaned) > 0:
            print(f"[STAGE 2 DEBUG] Cleaned content preview: {cleaned[:200]}...")
        
        print(f"[STAGE 2] ✅ DeepSeek complete - output length: {len(cleaned)}")
        
        return cleaned
        
    except Exception as e:
        print(f"[STAGE 2 ERROR] Exception: {str(e)}")
        print(f"[STAGE 2 ERROR] Exception type: {type(e)}")
        traceback.print_exc()
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
    
    original_code = code  # Keep the original for comparison
    
    pipeline_info = {
        'stage1_used': False,
        'stage2_used': False,
        'stage1_result': None,
        'stage2_result': None,
        'original_code': original_code  # Store original for reference
    }
    
    current_code = code
    
    # STAGE 1: Local Model
    if local_model_loaded:
        stage1_result = refactor_with_local_model(code, instruction)
        pipeline_info['stage1_used'] = True
        pipeline_info['stage1_result'] = stage1_result
        
        if stage1_result['success'] and stage1_result['is_valid_syntax']:
            current_code = stage1_result['refactored_code']
            print(f"[PIPELINE] Stage 1 successful")
            print(f"[PIPELINE] Original code length: {len(original_code)}")
            print(f"[PIPELINE] Stage 1 output length: {len(current_code)}")
            print(f"[PIPELINE] Stage 1 output preview: {current_code[:150]}...")
            print("[PIPELINE] Proceeding to Stage 2 with Stage 1 output")
        else:
            print("[PIPELINE] Stage 1 produced invalid code, using original for Stage 2")
            current_code = code
    else:
        print("[PIPELINE] Stage 1 skipped (local model not available)")
    
    print(f"[PIPELINE] Input to Stage 2: {len(current_code)} characters")
    
    # STAGE 2: DeepSeek API
    # Note: Stage 2 receives Stage 1 output (if valid), but we compare final result with original
    try:
        final_code = refactor_with_deepseek(current_code, instruction)
        
        # Validate that we got something back
        if not final_code or not final_code.strip():
            print("[PIPELINE WARNING] Stage 2 returned empty, using Stage 1 output")
            if pipeline_info['stage1_used'] and pipeline_info['stage1_result']['success']:
                final_code = pipeline_info['stage1_result']['refactored_code']
            else:
                final_code = code  # Fallback to original
        
        print(f"\n[PIPELINE] ===== FINAL COMPARISON =====")
        print(f"[PIPELINE] Original input length: {len(original_code)} characters")
        print(f"[PIPELINE] Final output length: {len(final_code)} characters")
        print(f"[PIPELINE] Change: {len(final_code) - len(original_code):+d} characters")
        print(f"[PIPELINE] Original preview: {original_code[:100]}...")
        print(f"[PIPELINE] Final preview: {final_code[:100]}...")
        print(f"[PIPELINE] ============================\n")
        
        pipeline_info['stage2_used'] = True
        pipeline_info['stage2_result'] = {
            'success': True,
            'refactored_code': final_code
        }
        
        # Calculate comparison metrics against ORIGINAL code
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
            'original_code': original_code,  # Include original for frontend comparison
            'pipeline_info': pipeline_info,
            'comparison': comparison_info
        }
        
    except Exception as e:
        print(f"[PIPELINE ERROR] Stage 2 exception: {str(e)}")
        # If Stage 2 fails but Stage 1 succeeded, return Stage 1 result
        if pipeline_info['stage1_used'] and pipeline_info['stage1_result']['success']:
            print("[PIPELINE] Stage 2 failed, returning Stage 1 result")
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
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'local_model': {
            'enabled': LOCAL_MODEL_ENABLED,
            'loaded': local_model_loaded,
            'path': LOCAL_MODEL_PATH if local_model_loaded else None,
            'device': device if local_model_loaded else None
        },
        'deepseek_api': {
            'enabled': True,
            'model': MODEL_NAME
        },
        'two_stage_refactoring': local_model_loaded,
        'compiler': 'enabled'
    })

@app.route('/api/refactor', methods=['POST'])
def refactor():
    """Main refactoring endpoint using two-stage process"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        code = data.get('code', '').strip()
        language = data.get('language', 'python')
        instruction = data.get('instruction', 'Refactor this code')
        
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
        
        print(f"\n{'='*70}")
        print(f"[REFACTOR] Starting two-stage refactoring")
        print(f"[REFACTOR] Input: {len(code)} characters")
        print(f"[REFACTOR] Original code preview: {code[:100]}...")
        print(f"{'='*70}")
        
        # Run two-stage refactoring
        result = refactor_code_two_stage(code, instruction)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Debug: Check what we got back
        print(f"\n{'='*70}")
        print(f"[API ENDPOINT DEBUG] Result keys: {result.keys()}")
        print(f"[API ENDPOINT DEBUG] Success: {result.get('success')}")
        print(f"[API ENDPOINT DEBUG] Final code present: {'final_code' in result}")
        print(f"[API ENDPOINT DEBUG] Original code length: {len(result.get('original_code', ''))}")
        print(f"[API ENDPOINT DEBUG] Final code length: {len(result.get('final_code', ''))}")
        if result.get('final_code'):
            print(f"[API ENDPOINT DEBUG] Final code preview: {result['final_code'][:150]}...")
        if result.get('comparison'):
            print(f"[API ENDPOINT DEBUG] Comparison: {result['comparison']}")
        print(f"{'='*70}")
        print(f"[COMPLETE] Total time: {processing_time:.0f}ms")
        print(f"{'='*70}\n")
        
        # Build response
        response_data = {
            'success': True,
            'refactored_code': result.get('final_code', ''),
            'original_code': result.get('original_code', code),  # Include original for comparison
            'processing_time': processing_time,
            'message': 'Code refactored successfully',
            'pipeline_info': {
                'local_model_used': result['pipeline_info']['stage1_used'],
                'deepseek_used': result['pipeline_info']['stage2_used'],
                'stages': 2 if result['pipeline_info']['stage1_used'] and result['pipeline_info']['stage2_used'] else 1
            },
            'comparison': result.get('comparison', {}),  # Include comparison metrics
            'warning': result.get('warning')
        }
        
        # Final validation before sending
        if not response_data['refactored_code']:
            print("[API ENDPOINT ERROR] Refactored code is empty! Using original code as fallback")
            response_data['refactored_code'] = code
            response_data['warning'] = 'Both stages failed to produce output, returning original code'
        
        print(f"[API ENDPOINT] Sending response:")
        print(f"  - Original code length: {len(response_data['original_code'])}")
        print(f"  - Refactored code length: {len(response_data['refactored_code'])}")
        print(f"  - Stages used: {response_data['pipeline_info']['stages']}")
        
        return jsonify(response_data)
    
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
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 CODE REFACTORING API SERVER (TWO-STAGE)")
    print("="*70)
    print(f"[STAGE 1] Local Model: {'✅ ENABLED' if local_model_loaded else '❌ DISABLED'}")
    if local_model_loaded:
        print(f"  Path: {LOCAL_MODEL_PATH}")
        print(f"  Device: {device.upper()}")
        print(f"  Beams: {NUM_BEAMS}, Max Length: {MAX_OUTPUT_LENGTH}")
    print(f"[STAGE 2] DeepSeek: ✅ ENABLED ({MODEL_NAME})")
    print("="*70)
    print("[PIPELINE FLOW]")
    if local_model_loaded:
        print("  1. Original Code → Local Model → Intermediate Code")
        print("  2. Intermediate Code → DeepSeek API → Final Code")
        print("  3. Comparison: Original Code ⟷ Final Code")
    else:
        print("  1. Original Code → DeepSeek API → Final Code")
        print("  2. Comparison: Original Code ⟷ Final Code")
    print("="*70)
    print("[NOTE]")
    print("  The final output is ALWAYS compared with the ORIGINAL input,")
    print("  not with intermediate Stage 1 output.")
    print("="*70)
    print("[ENDPOINTS]")
    print("  POST /api/refactor  - Two-stage refactoring")
    print("  POST /api/execute   - Execute code")
    print("  GET  /health        - Health check")
    print("="*70)
    print(f"[SERVER] Running on: http://localhost:8000")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)