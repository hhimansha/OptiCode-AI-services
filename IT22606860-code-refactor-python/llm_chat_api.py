"""
LLM-Powered Chat Assistant API
Port: 8001
Provides: AI chatbot, code comparison analysis, refactoring insights
Location: IT22606860-code-refactor-python/llm_chat_api.py
"""

import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from typing import List, Dict, Optional

# Centralized LLM configuration - change API key in llm_config.py
from llm_config import LLM_CONFIG, get_llm_client, print_llm_config

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration (from centralized llm_config.py)
PORT = int(os.getenv('LLM_PORT', 8001))
MODEL = LLM_CONFIG['chat_model_name']  # Chat uses a different model
MAX_TOKENS = LLM_CONFIG['max_tokens']
TEMPERATURE = LLM_CONFIG['temperature']

# Initialize LLM client from centralized config
client = get_llm_client()
if client:
    LLM_AVAILABLE = True
    print(f"[LLM] ✅ LLM client loaded from llm_config.py (chat model: {MODEL})")
else:
    LLM_AVAILABLE = False
    print("[LLM] ⚠️ WARNING: LLM client failed. Check API key in llm_config.py.")

print_llm_config()

# In-memory chat history storage (replace with database in production)
chat_history = []
start_time = time.time()

# System prompts
CHAT_SYSTEM_PROMPT = """You are an expert code refactoring assistant with deep knowledge of:
- Software design patterns and best practices
- Performance optimization techniques
- Code quality metrics and analysis
- Refactoring patterns (Extract Method, Guard Clauses, etc.)
- Memory management and optimization
- Risk assessment in code changes

You help developers:
1. Understand refactoring techniques with clear explanations
2. Identify code risks and suggest mitigations
3. Improve their refactoring skills through examples
4. Optimize code performance and memory usage
5. Learn best practices and design patterns

Provide clear, actionable advice with code examples when relevant. Be specific and quantitative in your analysis."""

COMPARISON_SYSTEM_PROMPT = """You are a code analysis expert. Analyze the provided before and after code with extreme detail:

1. **Memory Optimization:**
   - Calculate estimated memory usage (be specific with units: KB, MB)
   - Identify memory leaks or inefficiencies
   - Score complexity (0-100)
   - List specific issues and improvements

2. **Performance Analysis:**
   - Determine time complexity (Big O notation)
   - Determine space complexity (Big O notation)
   - Identify bottlenecks with line numbers
   - Quantify improvements (e.g., "50% faster")

3. **Code Quality Metrics:**
   - Lines of code count
   - Maintainability index (0-100)
   - Cyclomatic complexity
   - Code smells detected

4. **Refactoring Patterns:**
   - List all patterns applied
   - Explain why each pattern improves the code

5. **Risk Assessment:**
   - Risks resolved by the refactoring
   - Remaining risks to address
   - Edge cases to consider

Provide quantitative data whenever possible. Be precise and specific."""

INSIGHTS_SYSTEM_PROMPT = """You are a code review expert. Analyze the provided code and give actionable insights:

1. **Immediate Recommendations:** Specific changes to make right now
2. **Refactoring Patterns:** Which patterns apply and why
3. **Complexity Analysis:** Current complexity level and how to reduce it
4. **Best Practices:** What standards are violated
5. **Performance Opportunities:** Where to optimize
6. **Memory Efficiency:** How to reduce memory usage
7. **Maintainability:** How to make code more maintainable

Focus on the specified area (memory/performance/quality/general). Provide code examples for your suggestions."""


# ============================================
# HELPER FUNCTIONS
# ============================================

def call_chat_llm(messages: List[Dict], max_tokens: int = MAX_TOKENS, temperature: float = TEMPERATURE) -> str:
    """
    Call the LLM API with the given messages (using chat model)
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        
    Returns:
        str: LLM response text
    """
    if not LLM_AVAILABLE:
        return "LLM service is not available. Please check API key in llm_config.py."
    
    try:
        response = client.chat.completions.create(
            extra_headers=LLM_CONFIG['extra_headers'],
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"[LLM] Error calling LLM API: {str(e)}")
        raise


def add_to_history(role: str, content: str) -> Dict:
    """Add a message to chat history"""
    message = {
        'id': len(chat_history) + 1,
        'role': role,
        'content': content,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    chat_history.append(message)
    return message


def get_history_context(limit: int = 10) -> List[Dict]:
    """Get recent chat history for context"""
    recent = chat_history[-limit:] if len(chat_history) > limit else chat_history
    return [{'role': msg['role'], 'content': msg['content']} for msg in recent]


# ============================================
# CHAT ENDPOINTS
# ============================================

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the AI assistant
    
    Request:
        {
            "message": "How can I optimize this code?",
            "history": [optional previous messages]
        }
        
    Response:
        {
            "response": "Here are some ways...",
            "metadata": {
                "analysisType": "general",
                "tokensUsed": 150,
                "timestamp": "2026-02-09T10:00:00Z"
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message in request'}), 400
        
        user_message = data['message']
        provided_history = data.get('history', [])
        
        print(f"[LLM] Received chat message: {user_message[:100]}...")
        
        # Build messages for LLM
        messages = [{'role': 'system', 'content': CHAT_SYSTEM_PROMPT}]
        
        # Add provided history or use stored history
        if provided_history:
            messages.extend(provided_history[-10:])  # Last 10 messages
        else:
            messages.extend(get_history_context())
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})
        
        # Call LLM
        response_text = call_chat_llm(messages)
        
        # Determine analysis type from message content
        analysis_type = 'general'
        lower_msg = user_message.lower()
        if any(word in lower_msg for word in ['risk', 'danger', 'safe', 'security']):
            analysis_type = 'risk'
        elif any(word in lower_msg for word in ['performance', 'speed', 'optimize', 'fast']):
            analysis_type = 'performance'
        elif any(word in lower_msg for word in ['memory', 'leak', 'ram', 'allocation']):
            analysis_type = 'memory'
        elif any(word in lower_msg for word in ['skill', 'learn', 'improve', 'practice']):
            analysis_type = 'learning'
        elif any(word in lower_msg for word in ['refactor', 'pattern', 'clean']):
            analysis_type = 'refactoring'
        
        # Store in history
        add_to_history('user', user_message)
        add_to_history('assistant', response_text)
        
        # Calculate approximate tokens (rough estimate)
        tokens_used = len(' '.join([m['content'] for m in messages])) // 4
        
        result = {
            'response': response_text,
            'metadata': {
                'analysisType': analysis_type,
                'tokensUsed': tokens_used,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'model': MODEL
            }
        }
        
        print(f"[LLM] Chat response sent (type: {analysis_type})")
        return jsonify(result)
        
    except Exception as e:
        print(f"[LLM] Chat error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to process chat message',
            'details': str(e)
        }), 500


@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """
    Retrieve chat history
    
    Response:
        {
            "history": [...],
            "count": 10
        }
    """
    try:
        return jsonify({
            'history': chat_history,
            'count': len(chat_history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat/history', methods=['DELETE'])
def clear_chat_history():
    """
    Clear chat history
    
    Response:
        {
            "success": true,
            "message": "Chat history cleared"
        }
    """
    try:
        global chat_history
        cleared_count = len(chat_history)
        chat_history = []
        
        print(f"[LLM] Cleared {cleared_count} messages from history")
        
        return jsonify({
            'success': True,
            'message': f'Chat history cleared ({cleared_count} messages)',
            'clearedCount': cleared_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# CODE ANALYSIS ENDPOINTS
# ============================================

@app.route('/analyze/comparison', methods=['POST'])
def analyze_comparison():
    """
    Analyze code comparison with advanced memory/performance metrics
    
    Request:
        {
            "before": "code before refactoring",
            "after": "code after refactoring",
            "language": "python"
        }
        
    Response:
        {
            "analysis": {
                "memoryOptimization": {...},
                "performance": {...},
                "codeQuality": {...},
                "refactoringPatterns": [...],
                "risks": {...}
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'before' not in data or 'after' not in data:
            return jsonify({'error': 'Missing before/after code in request'}), 400
        
        before_code = data['before']
        after_code = data['after']
        language = data.get('language', 'python')
        
        print(f"[LLM] Analyzing code comparison ({language})...")
        print(f"[LLM] Before: {len(before_code)} chars, After: {len(after_code)} chars")
        
        # Build comprehensive analysis prompt
        analysis_prompt = f"""Analyze this code refactoring in {language}.

BEFORE CODE:
```{language}
{before_code}
```

AFTER CODE:
```{language}
{after_code}
```

Provide a detailed JSON analysis with these sections:

1. memoryOptimization:
   - before: {{estimatedMemory: "X KB", complexityScore: 0-100, issues: []}}
   - after: {{estimatedMemory: "X KB", complexityScore: 0-100, improvements: []}}
   - improvement: "X%" (percentage improvement)

2. performance:
   - before: {{timeComplexity: "O(n)", spaceComplexity: "O(n)", bottlenecks: []}}
   - after: {{timeComplexity: "O(n)", spaceComplexity: "O(n)", optimizations: []}}
   - improvement: "X% faster" or description

3. codeQuality:
   - before: {{linesOfCode: X, maintainabilityIndex: 0-100, cyclomaticComplexity: X}}
   - after: {{linesOfCode: X, maintainabilityIndex: 0-100, cyclomaticComplexity: X}}

4. refactoringPatterns: [list of patterns applied]

5. risks:
   - resolved: [list of risks fixed]
   - remaining: [list of risks still present]

Be specific with numbers and measurements. Respond with valid JSON only."""

        # Call LLM
        messages = [
            {'role': 'system', 'content': COMPARISON_SYSTEM_PROMPT},
            {'role': 'user', 'content': analysis_prompt}
        ]
        
        response_text = call_chat_llm(messages, max_tokens=3000, temperature=0.3)
        
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            json_text = json_match.group(0) if json_match else response_text
        
        try:
            analysis = json.loads(json_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, structure the response manually
            analysis = {
                'memoryOptimization': {
                    'before': {'estimatedMemory': 'N/A', 'complexityScore': 50, 'issues': ['Unable to parse']},
                    'after': {'estimatedMemory': 'N/A', 'complexityScore': 50, 'improvements': []},
                    'improvement': 'N/A'
                },
                'performance': {
                    'before': {'timeComplexity': 'N/A', 'spaceComplexity': 'N/A', 'bottlenecks': []},
                    'after': {'timeComplexity': 'N/A', 'spaceComplexity': 'N/A', 'optimizations': []},
                    'improvement': 'N/A'
                },
                'codeQuality': {
                    'before': {'linesOfCode': len(before_code.split('\n')), 'maintainabilityIndex': 50, 'cyclomaticComplexity': 1},
                    'after': {'linesOfCode': len(after_code.split('\n')), 'maintainabilityIndex': 50, 'cyclomaticComplexity': 1}
                },
                'refactoringPatterns': ['Analysis incomplete'],
                'risks': {
                    'resolved': [],
                    'remaining': ['Manual review recommended']
                },
                'rawResponse': response_text
            }
        
        print(f"[LLM] Comparison analysis complete")
        
        return jsonify({
            'analysis': analysis,
            'metadata': {
                'language': language,
                'beforeLines': len(before_code.split('\n')),
                'afterLines': len(after_code.split('\n')),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        })
        
    except Exception as e:
        print(f"[LLM] Comparison analysis error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to analyze code comparison',
            'details': str(e)
        }), 500


@app.route('/insights', methods=['POST'])
def get_insights():
    """
    Get refactoring insights and recommendations
    
    Request:
        {
            "code": "function processData(items) {...}",
            "focus": "memory|performance|quality|general"
        }
        
    Response:
        {
            "insights": {
                "recommendations": [...],
                "patterns": [...],
                "complexity": {...}
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Missing code in request'}), 400
        
        code = data['code']
        focus = data.get('focus', 'general')
        
        print(f"[LLM] Generating insights (focus: {focus})...")
        
        # Build insights prompt
        focus_instruction = {
            'memory': 'Focus on memory optimization: reduce allocations, prevent leaks, efficient data structures',
            'performance': 'Focus on performance: time complexity, algorithm efficiency, bottleneck elimination',
            'quality': 'Focus on code quality: readability, maintainability, best practices, design patterns',
            'general': 'Provide comprehensive analysis covering all aspects: memory, performance, quality, patterns'
        }.get(focus, 'Provide general refactoring recommendations')
        
        insights_prompt = f"""{focus_instruction}

CODE TO ANALYZE:
```
{code}
```

Provide detailed insights in this structure:

1. recommendations: [List 3-7 specific, actionable recommendations with code examples]

2. patterns: [List refactoring patterns that should be applied, e.g., "Extract Method", "Guard Clause"]

3. complexity:
   - current: "Low|Medium|High|Very High"
   - score: 0-100
   - suggestions: "How to reduce complexity"

4. memoryOptimization: [Specific memory improvements if focus is memory or general]

5. performanceOpportunities: [Specific performance improvements if focus is performance or general]

6. codeSmells: [List any code smells detected]

Provide practical, actionable advice with code examples."""

        # Call LLM
        messages = [
            {'role': 'system', 'content': INSIGHTS_SYSTEM_PROMPT},
            {'role': 'user', 'content': insights_prompt}
        ]
        
        response_text = call_chat_llm(messages, max_tokens=2500, temperature=0.4)
        
        print(f"[LLM] Insights generated")
        
        return jsonify({
            'insights': {
                'analysis': response_text,
                'focus': focus,
                'codeLength': len(code),
                'linesOfCode': len(code.split('\n'))
            },
            'metadata': {
                'focus': focus,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'model': MODEL
            }
        })
        
    except Exception as e:
        print(f"[LLM] Insights error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to generate insights',
            'details': str(e)
        }), 500


# ============================================
# HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    
    Response:
        {
            "status": "healthy",
            "model": MODEL,
            "version": "1.0.0",
            "uptime": 3600,
            "llmAvailable": true
        }
    """
    uptime = int(time.time() - start_time)
    
    return jsonify({
        'status': 'healthy' if LLM_AVAILABLE else 'degraded',
        'service': 'LLM Chat Assistant',
        'model': MODEL if LLM_AVAILABLE else 'Not configured',
        'version': '1.0.0',
        'port': PORT,
        'uptime': uptime,
        'llmAvailable': LLM_AVAILABLE,
        'features': [
            'AI Chat Assistant',
            'Code Comparison Analysis',
            'Refactoring Insights',
            'Memory Optimization Analysis',
            'Performance Analysis'
        ],
        'chatHistory': {
            'messages': len(chat_history),
            'stored': True
        }
    })


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# STARTUP
# ============================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print(" 🤖 LLM CHAT ASSISTANT API")
    print("="*80)
    print(f" 📍 Port: {PORT}")
    print(f" 🧠 Model: {MODEL}")
    print(f" ✅ LLM Available: {LLM_AVAILABLE}")
    print("="*80)
    print("\n 🎯 AVAILABLE ENDPOINTS:")
    print("="*80)
    print(f"  POST   /chat                    - AI chat assistant")
    print(f"  GET    /chat/history            - Get chat history")
    print(f"  DELETE /chat/history            - Clear chat history")
    print(f"  POST   /analyze/comparison      - Advanced code comparison")
    print(f"  POST   /insights                - Get refactoring insights")
    print(f"  GET    /health                  - Health check")
    print("="*80)
    
    if not LLM_AVAILABLE:
        print("\n ⚠️  WARNING: LLM is not configured!")
        print(" Set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable")
        print(" Example: export OPENROUTER_API_KEY='your-key-here'")
        print()
    
    print(f"\n 🚀 Starting server on http://localhost:{PORT}")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
