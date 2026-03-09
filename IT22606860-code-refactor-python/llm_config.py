"""
Centralized LLM Configuration & Client Factory
===============================================
Location: IT22606860-code-refactor-python/llm_config.py

All LLM API keys, model names, base URLs, and client initialization
are managed HERE. Every service imports from this single module.

To change the API key or model, edit ONLY this file.

Usage in other files:
    from llm_config import get_llm_client, LLM_CONFIG
    
    client = get_llm_client()          # Get shared client instance
    model = LLM_CONFIG['model_name']   # Get model name
"""

import os
from typing import Optional

# ============================================
# 🔑 CENTRALIZED LLM CONFIGURATION
# ============================================
# Change the API key here — it applies everywhere.

LLM_CONFIG = {
    # ── API Credentials ──────────────────────────────────────────
    # IMPORTANT: Set your API key in environment variable or .env file
    # Option 1: OpenRouter (supports multiple models) - Get key at https://openrouter.ai/
    # Option 2: Direct DeepSeek API - Get key at https://platform.deepseek.com/
    'api_key': os.getenv(
        'LLM_API_KEY',  # Use LLM_API_KEY for both OpenRouter and DeepSeek
        os.getenv('OPENROUTER_API_KEY', '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')  # Fallback to hardcoded key
    ),
    
    # ── API Base URL ─────────────────────────────────────────────
    # Option 1: https://openrouter.ai/api/v1 (for OpenRouter)
    # Option 2: https://api.deepseek.com/v1 (for direct DeepSeek API)
    'base_url': os.getenv(
        'LLM_BASE_URL',
        os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')
    ),
    
    # ── Model for Refactoring & Risk Analysis ────────────────────
    # For OpenRouter: deepseek/deepseek-r1-0528:free or deepseek/deepseek-chat
    # For Direct DeepSeek API: deepseek-chat or deepseek-coder
    'model_name': os.getenv(
        'LLM_MODEL',
        'deepseek/deepseek-chat'  # Changed to more reliable model
    ),
    
    # ── Model for Chat Assistant ─────────────────────────────────
    # Chat uses a different model (conversational vs code tasks)
    'chat_model_name': os.getenv(
        'LLM_CHAT_MODEL',
        'deepseek/deepseek-chat'
    ),
    
    # ── Timeout & Retry ──────────────────────────────────────────
    'timeout': float(os.getenv('LLM_TIMEOUT', '60.0')),
    'max_retries': int(os.getenv('LLM_MAX_RETRIES', '2')),
    
    # ── Default Parameters ───────────────────────────────────────
    'max_tokens': int(os.getenv('MAX_TOKENS', '2000')),
    'temperature': float(os.getenv('TEMPERATURE', '0.7')),
    
    # ── HTTP Headers (for OpenRouter) ────────────────────────────
    'extra_headers': {
        'HTTP-Referer': 'http://localhost:8000',
        'X-Title': 'Opticode Refactor API',
    }
}


# ============================================
# CLIENT MANAGEMENT
# ============================================

# Shared client instance (lazy-initialized)
_client_instance = None
_client_initialized = False


def get_llm_client(force_new: bool = False) -> Optional[object]:
    """
    Get or create the shared LLM client instance.
    
    All services share a single client configuration.
    The client is lazily initialized on first call.
    
    Args:
        force_new: If True, create a fresh client even if one exists
        
    Returns:
        OpenAI client instance, or None if initialization fails
    """
    global _client_instance, _client_initialized
    
    if _client_instance is not None and not force_new:
        return _client_instance
    
    if _client_initialized and not force_new:
        return _client_instance  # Already tried, returned None
    
    try:
        from openai import OpenAI
        
        # Validate API key is set
        if not LLM_CONFIG['api_key'] or LLM_CONFIG['api_key'] == '':
            raise ValueError(
                "\n" + "="*70 + "\n"
                "❌ API KEY NOT SET!\n"
                "\nTo fix this, create a .env file in this directory with:\n"
                "  LLM_API_KEY=your-api-key-here\n"
                "\nGet your API key from:\n"
                "  • OpenRouter: https://openrouter.ai/ (supports multiple models)\n"
                "  • DeepSeek: https://platform.deepseek.com/ (direct DeepSeek API)\n"
                "\nOr set the environment variable LLM_API_KEY\n"
                + "="*70
            )
        
        _client_instance = OpenAI(
            base_url=LLM_CONFIG['base_url'],
            api_key=LLM_CONFIG['api_key'],
            timeout=LLM_CONFIG['timeout'],
        )
        _client_initialized = True
        print(f"✅ LLM client initialized (model: {LLM_CONFIG['model_name']})")
        return _client_instance
        
    except Exception as e:
        print(f"⚠️ LLM client initialization failed: {e}")
        _client_initialized = True
        _client_instance = None
        return None


def get_llm_client_with_http_client(force_new: bool = False) -> Optional[object]:
    """
    Get LLM client with custom HTTP client (for Python 3.14+ compatibility).
    Used by risk_analysis_api.py which needs DefaultHttpxClient.
    
    Falls back to standard client if DefaultHttpxClient is not available.
    
    Args:
        force_new: If True, create a fresh client
        
    Returns:
        OpenAI client instance, or None if initialization fails
    """
    try:
        from openai import OpenAI, DefaultHttpxClient
        
        http_client = DefaultHttpxClient(timeout=LLM_CONFIG['timeout'])
        client = OpenAI(
            base_url=LLM_CONFIG['base_url'],
            api_key=LLM_CONFIG['api_key'],
            http_client=http_client
        )
        print(f"✅ LLM client initialized with custom HTTP client")
        return client
        
    except ImportError:
        # DefaultHttpxClient not available, use standard client
        print("ℹ️  DefaultHttpxClient not available, using standard client")
        return get_llm_client(force_new=force_new)
        
    except Exception as e:
        print(f"⚠️ LLM client (with http_client) failed: {e}")
        # Try fallback
        return get_llm_client(force_new=force_new)


def call_llm(
    messages: list,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    extra_headers: Optional[dict] = None,
    client: Optional[object] = None
) -> Optional[str]:
    """
    Unified LLM call function used across all services.
    
    Args:
        messages: List of {"role": ..., "content": ...} message dicts
        model: Override model name (defaults to LLM_CONFIG['model_name'])
        max_tokens: Override max tokens (defaults to LLM_CONFIG['max_tokens'])
        temperature: Override temperature (defaults to LLM_CONFIG['temperature'])
        extra_headers: Override HTTP headers for OpenRouter
        client: Use a specific client instance instead of the shared one
        
    Returns:
        Response text string, or None if the call fails
        
    Raises:
        Exception: If the LLM call fails (caller should handle)
    """
    llm_client = client or get_llm_client()
    
    if not llm_client:
        raise ConnectionError("LLM client not available. Check API key in llm_config.py")
    
    completion = llm_client.chat.completions.create(
        extra_headers=extra_headers or LLM_CONFIG['extra_headers'],
        model=model or LLM_CONFIG['model_name'],
        max_tokens=max_tokens or LLM_CONFIG['max_tokens'],
        temperature=temperature if temperature is not None else LLM_CONFIG['temperature'],
        messages=messages
    )
    
    if not completion.choices or len(completion.choices) == 0:
        return None
    
    return completion.choices[0].message.content


# ============================================
# STARTUP INFO
# ============================================

def print_llm_config():
    """Print current LLM configuration (for startup logs)"""
    print(f"\n{'─'*50}")
    print(f"[LLM CONFIG] Centralized Configuration (llm_config.py)")
    print(f"  API Key:     ...{LLM_CONFIG['api_key'][-12:]}")
    print(f"  Base URL:    {LLM_CONFIG['base_url']}")
    print(f"  Model:       {LLM_CONFIG['model_name']}")
    print(f"  Chat Model:  {LLM_CONFIG['chat_model_name']}")
    print(f"  Timeout:     {LLM_CONFIG['timeout']}s")
    print(f"{'─'*50}\n")
