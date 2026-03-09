"""
Test script to verify if the API key is working
"""
import sys
from llm_config import get_llm_client, LLM_CONFIG, call_llm

def test_api_key():
    """Test if the API key is valid and working"""
    print("=" * 70)
    print("🔑 Testing API Key Configuration")
    print("=" * 70)
    
    # Display current configuration
    api_key = LLM_CONFIG['api_key']
    base_url = LLM_CONFIG['base_url']
    model = LLM_CONFIG['model_name']
    
    print(f"\n📋 Current Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else ''}")
    print()
    
    # Try to initialize the client
    print("🔄 Initializing LLM client...")
    client = get_llm_client()
    
    if client is None:
        print("❌ Failed to initialize the client. Check your API key configuration.")
        return False
    
    print("✅ Client initialized successfully")
    
    # Try to make a simple API call
    print("\n🔄 Testing API call with a simple request...")
    try:
        messages = [
            {"role": "user", "content": "Say 'Hello, API is working!' in exactly 5 words."}
        ]
        
        response = call_llm(
            messages=messages,
            model=model,
            max_tokens=50,
            temperature=0.3,
            client=client
        )
        
        if response:
            print(f"\n✅ API KEY IS WORKING!")
            print(f"\n📨 Response from API:")
            print(f"   {response}")
            print("\n" + "=" * 70)
            print("✅ Your API key is VALID and ACTIVE")
            print("=" * 70)
            return True
        else:
            print("\n❌ API call returned no response")
            return False
            
    except Exception as e:
        error_message = str(e)
        print(f"\n❌ API KEY TEST FAILED!")
        print(f"\n🔍 Error Details:")
        print(f"   {error_message}")
        
        # Check for common error types
        if "401" in error_message or "authentication" in error_message.lower():
            print("\n" + "=" * 70)
            print("❌ API KEY IS EXPIRED OR INVALID")
            print("=" * 70)
            print("\n💡 Solution:")
            print("   1. Go to https://openrouter.ai/ and log in")
            print("   2. Generate a new API key")
            print("   3. Update the key in llm_config.py or set LLM_API_KEY environment variable")
            
        elif "402" in error_message or "insufficient" in error_message.lower():
            print("\n" + "=" * 70)
            print("💰 INSUFFICIENT CREDITS")
            print("=" * 70)
            print("\n💡 Solution:")
            print("   1. Add credits to your OpenRouter account")
            print("   2. Or switch to a free model (e.g., deepseek/deepseek-r1-0528:free)")
            
        elif "429" in error_message or "rate limit" in error_message.lower():
            print("\n" + "=" * 70)
            print("⏰ RATE LIMIT EXCEEDED")
            print("=" * 70)
            print("\n💡 Solution:")
            print("   Wait a few minutes and try again")
            
        else:
            print("\n" + "=" * 70)
            print("⚠️ UNKNOWN ERROR")
            print("=" * 70)
            print("\n💡 Suggestions:")
            print("   1. Check your internet connection")
            print("   2. Verify the base URL is correct")
            print("   3. Try a different model")
        
        print()
        return False

if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)
