"""
Risk Analysis API for Code Refactoring
Uses OpenRouter AI to analyze refactoring risks and AST for technical analysis
Enhanced with AST-based metrics and comprehensive assessment
"""

import os
import time
import json
import traceback
import ast
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import re

# Import AST analysis modules
try:
    from code_analyzer import analyze_code
    from ast_refactor import analyze_code_structure
    AST_ANALYSIS_AVAILABLE = True
except ImportError:
    AST_ANALYSIS_AVAILABLE = False
    print("[WARNING] AST analysis modules not available")

app = Flask(__name__)
CORS(app)  # Enable CORS for React

# ============================================
# CONFIGURATION
# ============================================

# OpenRouter API Configuration
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

# Initialize OpenAI client
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

# ============================================
# HELPER FUNCTIONS
# ============================================

def clean_ai_output(content: str) -> str:
    """Remove markdown code blocks from AI output"""
    if not content:
        return ""
    
    # Remove ```json or ``` at the start/end
    content = re.sub(r"^```(json)?\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
    return content.strip()

def extract_json_from_response(content: str):
    """Extract JSON object from AI response"""
    try:
        # Try to find JSON object in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        
        # If no JSON found, return None
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {str(e)}")
        print(f"[ERROR] Content: {content}")
        return None

def calculate_comparison_metrics(original_code: str, refactored_code: str) -> dict:
    """Calculate comparison metrics between original and refactored code"""
    
    # Calculate lines and characters
    original_lines = original_code.split('\n')
    refactored_lines = refactored_code.split('\n')
    
    # Calculate complexity metrics (simplified)
    # Count loops and conditionals
    original_loops = len(re.findall(r'(for\s|while\s|\.map\(|\.filter\(|\.reduce\(|list\s*comprehension)', original_code, re.IGNORECASE))
    refactored_loops = len(re.findall(r'(for\s|while\s|\.map\(|\.filter\(|\.reduce\(|list\s*comprehension)', refactored_code, re.IGNORECASE))
    
    original_conditionals = len(re.findall(r'(if\s|elif\s|else:|case\s|switch\s)', original_code, re.IGNORECASE))
    refactored_conditionals = len(re.findall(r'(if\s|elif\s|else:|case\s|switch\s)', refactored_code, re.IGNORECASE))
    
    # Calculate nesting depth (simplified)
    original_nesting = len(re.findall(r'(\s{4,}|\t)', original_code))
    refactored_nesting = len(re.findall(r'(\s{4,}|\t)', refactored_code))
    
    return {
        'line_count': {
            'original': len(original_lines),
            'refactored': len(refactored_lines),
            'change': len(refactored_lines) - len(original_lines)
        },
        'character_count': {
            'original': len(original_code),
            'refactored': len(refactored_code),
            'change': len(refactored_code) - len(original_code)
        },
        'complexity': {
            'original_loops': original_loops,
            'refactored_loops': refactored_loops,
            'original_conditionals': original_conditionals,
            'refactored_conditionals': refactored_conditionals,
            'original_nesting': original_nesting,
            'refactored_nesting': refactored_nesting
        },
        'readability_score': {
            'original': max(0, 100 - (original_loops * 5 + original_conditionals * 3 + original_nesting * 2)),
            'refactored': max(0, 100 - (refactored_loops * 5 + refactored_conditionals * 3 + refactored_nesting * 2))
        }
    }

def get_color_for_risk(risk_score: int) -> str:
    """Get color based on risk score"""
    if risk_score <= 30:
        return "#10B981"  # Green - low risk
    elif risk_score <= 60:
        return "#F59E0B"  # Yellow - medium risk
    else:
        return "#EF4444"  # Red - high risk

# ============================================
# RISK ANALYSIS FUNCTIONS
# ============================================

def analyze_refactoring_risk(original_code: str, refactored_code: str, language: str = "python") -> dict:
    """
    Analyze the risk of refactoring from original to refactored code
    Returns detailed risk assessment with scores, explanations, and suggestions
    """
    
    print(f"[RISK ANALYSIS] Analyzing risk for {len(original_code)} chars -> {len(refactored_code)} chars")
    
    # System prompt for risk analysis
    system_prompt = """You are an expert code refactoring risk analyst. Your task is to analyze the risk involved in refactoring from original code to refactored code.

Your response MUST be a valid JSON object with the following structure:
{
    "risk_score": 0-100,
    "risk_level": "low" | "medium" | "high",
    "risk_factors": [
        {
            "factor": "string",
            "score": 0-100,
            "description": "string"
        }
    ],
    "explanation": "Detailed explanation of the risk assessment",
    "suggestions": ["suggestion1", "suggestion2"],
    "potential_issues": ["issue1", "issue2"],
    "side_effects": ["effect1", "effect2"],
    "recommendation": "string describing whether to apply the refactor"
}

Risk score calculation guidelines:
- 0-30: Low risk - Refactor is safe to apply
- 31-60: Medium risk - Apply with caution, review carefully
- 61-100: High risk - Avoid or heavily test before applying

Consider these risk factors:
1. Side effects - Does the refactor introduce unintended side effects?
2. Readability - Is the refactored code easier or harder to read?
3. Performance - Will performance improve or degrade?
4. Maintainability - Is the code easier to maintain?
5. Functionality - Does functionality remain exactly the same?
6. Language idiomaticity - Does it follow language best practices?
7. Complexity - Does it reduce or increase complexity?
8. Error handling - How does it affect error handling?

Return ONLY the JSON object, no additional text."""

    # User prompt with code
    user_prompt = f"""Language: {language}

ORIGINAL CODE:
{original_code}

REFACTORED CODE:
{refactored_code}

Analyze the refactoring risk and provide a comprehensive assessment.
Consider the specific changes made, potential side effects, and whether the refactoring follows best practices."""

    try:
        print(f"[RISK ANALYSIS] Calling AI for risk assessment...")
        start_time = time.time()
        
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8001",
                "X-Title": "Opticode Risk Analysis API",
            },
            model=MODEL_NAME,
            max_tokens=2000,
            temperature=0.3,  # Lower temperature for more consistent results
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
        
        processing_time = (time.time() - start_time) * 1000
        
        if not completion.choices or len(completion.choices) == 0:
            raise Exception("No response from AI")
        
        raw_content = completion.choices[0].message.content
        cleaned = clean_ai_output(raw_content)
        
        print(f"[RISK ANALYSIS] AI response received in {processing_time:.0f}ms")
        print(f"[RISK ANALYSIS] Raw response: {cleaned[:200]}...")
        
        # Parse JSON response
        risk_data = extract_json_from_response(cleaned)
        
        if not risk_data:
            # Fallback response if JSON parsing fails
            risk_data = {
                "risk_score": 2,
                "risk_level": "low",
                "risk_factors": [
                    {
                        "factor": "AI Response Parsing",
                        "score": 2,
                        "description": "Failed to parse AI response for detailed analysis"
                    }
                ],
                "explanation": "Unable to provide detailed risk analysis due to AI response format issues.",
                "suggestions": ["Review the refactored code manually before applying"],
                "potential_issues": ["AI response format unexpected"],
                "side_effects": ["Unknown without detailed analysis"],
                "recommendation": "Apply with caution and thorough testing"
            }
        
        # Add calculated metrics
        comparison_metrics = calculate_comparison_metrics(original_code, refactored_code)
        
        # Add color coding
        risk_data['risk_color'] = get_color_for_risk(risk_data.get('risk_score', 50))
        
        # Add processing info
        risk_data['processing_time'] = processing_time
        
        # Combine all data
        response_data = {
            'success': True,
            'risk_analysis': risk_data,
            'comparison_metrics': comparison_metrics,
            'language': language
        }
        
        print(f"[RISK ANALYSIS] ✅ Complete - Risk Score: {risk_data.get('risk_score')}")
        
        return response_data
        
    except Exception as e:
        print(f"[RISK ANALYSIS ERROR] Exception: {str(e)}")
        traceback.print_exc()
        raise e

def get_chart_data(risk_score: int, risk_factors: list) -> dict:
    """Generate chart data for visualization"""
    
    # Gauge chart data
    gauge_data = [
        {"name": "Low Risk", "value": 30, "color": "#10B981"},
        {"name": "Medium Risk", "value": 30, "color": "#F59E0B"},
        {"name": "High Risk", "value": 40, "color": "#EF4444"},
        {"name": "Current Risk", "value": risk_score, "color": get_color_for_risk(risk_score)}
    ]
    
    # Pie chart data for risk factors
    pie_data = []
    if risk_factors:
        for factor in risk_factors:
            pie_data.append({
                "name": factor.get("factor", "Unknown"),
                "value": factor.get("score", 0),
                "color": get_color_for_risk(factor.get("score", 0))
            })
    
    # Bar chart data for comparison
    bar_data = [
        {"name": "Original", "lines": 0, "complexity": 0, "readability": 0},
        {"name": "Refactored", "lines": 0, "complexity": 0, "readability": 0}
    ]
    
    return {
        "gauge_chart": gauge_data,
        "pie_chart": pie_data,
        "bar_chart": bar_data
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'risk-analysis-api',
        'ai_model': MODEL_NAME,
        'endpoints': {
            '/api/risk-analyze': 'POST - Analyze refactoring risk',
            '/health': 'GET - Health check'
        }
    })

@app.route('/api/risk-analyze', methods=['POST'])
def risk_analyze():
    """Enhanced risk analysis endpoint with AST-based metrics"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Get input
        original_code = data.get('original_code', '').strip()
        refactored_code = data.get('refactored_code', '').strip()
        language = data.get('language', 'python')
        include_ast_analysis = data.get('include_ast_analysis', AST_ANALYSIS_AVAILABLE)
        
        # Validate
        if not original_code:
            return jsonify({
                'success': False,
                'message': 'No original code provided'
            }), 400
        
        if not refactored_code:
            return jsonify({
                'success': False,
                'message': 'No refactored code provided'
            }), 400
        
        print(f"\n{'='*70}")
        print(f"[RISK ANALYSIS] Starting risk analysis")
        print(f"[RISK ANALYSIS] Original: {len(original_code)} chars")
        print(f"[RISK ANALYSIS] Refactored: {len(refactored_code)} chars")
        print(f"[RISK ANALYSIS] AST Analysis: {'Enabled' if include_ast_analysis else 'Disabled'}")
        print(f"{'='*70}")
        
        # Perform AI-based risk analysis
        result = analyze_refactoring_risk(original_code, refactored_code, language)
        
        # Add AST-based technical analysis if available
        if include_ast_analysis and AST_ANALYSIS_AVAILABLE:
            print("[RISK ANALYSIS] Adding AST-based technical analysis...")
            
            try:
                # Analyze both code versions
                original_analysis = analyze_code(original_code)
                refactored_analysis = analyze_code(refactored_code)
                
                result['technical_analysis'] = {
                    'original': {
                        'complexity': original_analysis.get('complexity', {}),
                        'metrics': original_analysis.get('metrics', {}),
                        'overall_score': original_analysis.get('overall_score', {})
                    },
                    'refactored': {
                        'complexity': refactored_analysis.get('complexity', {}),
                        'metrics': refactored_analysis.get('metrics', {}),
                        'overall_score': refactored_analysis.get('overall_score', {})
                    },
                    'improvements': calculate_improvements(original_analysis, refactored_analysis)
                }
                
                print("[RISK ANALYSIS] AST analysis complete")
            except Exception as e:
                print(f"[WARNING] AST analysis failed: {str(e)}")
                result['technical_analysis_error'] = str(e)
        
        # Generate chart data
        risk_score = result['risk_analysis'].get('risk_score', 50)
        risk_factors = result['risk_analysis'].get('risk_factors', [])
        chart_data = get_chart_data(risk_score, risk_factors)
        
        # Add chart data to response
        result['chart_data'] = chart_data
        
        # Calculate total time
        total_time = (time.time() - start_time) * 1000
        
        # Add timing info
        result['total_processing_time'] = total_time
        
        print(f"[RISK ANALYSIS] Total time: {total_time:.0f}ms")
        print(f"[RISK ANALYSIS] Risk Score: {risk_score}")
        print(f"{'='*70}\n")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] Risk analysis error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error during risk analysis: {str(e)}'
        }), 500


def calculate_improvements(original: Dict, refactored: Dict) -> Dict:
    """Calculate improvements between original and refactored code"""
    
    improvements = {}
    
    # Complexity improvements
    if 'complexity' in original and 'complexity' in refactored:
        orig_complexity = original['complexity'].get('average_complexity', 0)
        ref_complexity = refactored['complexity'].get('average_complexity', 0)
        
        if orig_complexity > 0:
            complexity_improvement = ((orig_complexity - ref_complexity) / orig_complexity) * 100
            improvements['complexity_reduction'] = round(complexity_improvement, 2)
    
    # Code quality improvements
    if 'overall_score' in original and 'overall_score' in refactored:
        orig_score = original['overall_score'].get('score', 50)
        ref_score = refactored['overall_score'].get('score', 50)
        
        improvements['quality_improvement'] = round(ref_score - orig_score, 2)
    
    # Lines of code change
    if 'metrics' in original and 'metrics' in refactored:
        orig_loc = original['metrics'].get('loc', 0)
        ref_loc = refactored['metrics'].get('loc', 0)
        
        if orig_loc > 0:
            loc_change = ((ref_loc - orig_loc) / orig_loc) * 100
            improvements['loc_change_percent'] = round(loc_change, 2)
    
    return improvements

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔍 CODE REFACTORING RISK ANALYSIS API")
    print("="*70)
    print(f"[AI MODEL] {MODEL_NAME}")
    print("[FEATURES]")
    print("  1. Risk Score (0-100)")
    print("  2. Risk Level (Low/Medium/High)")
    print("  3. Detailed Risk Factors")
    print("  4. Side Effects Analysis")
    print("  5. Chart Data Generation")
    print("="*70)
    print("[ENDPOINTS]")
    print("  POST /api/risk-analyze  - Analyze refactoring risk")
    print("  GET  /health           - Health check")
    print("="*70)
    print(f"[SERVER] Running on: http://localhost:8001")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=8001, debug=True)