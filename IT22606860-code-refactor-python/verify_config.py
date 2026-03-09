"""Verify LLM configuration"""
from llm_config import LLM_CONFIG, get_llm_client, call_llm

print("="*70)
print("LLM CONFIGURATION VERIFICATION")
print("="*70)
print(f"API Key: ...{LLM_CONFIG['api_key'][-20:]}")
print(f"Base URL: {LLM_CONFIG['base_url']}")
print(f'Model: {LLM_CONFIG["model_name"]}')
print("="*70)

# Test client initialization
print("\nInitializing client...")
client = get_llm_client()
if client:
    print("✅ Client initialized successfully")
    
    # Test API call
    print("\nTesting API call...")
    try:
        response = call_llm(
            [{"role": "user", "content": "Say 'Hello' in 2 words"}],
            client=client,
            max_tokens=10
        )
        if response:
            print(f"✅ API call successful!")
            print(f"   Response: {response}")
            print("\n✅ LLM INTEGRATION IS WORKING!")
        else:
            print("❌ No response from API")
    except Exception as e:
        print(f"❌ API call failed: {e}")
else:
    print("❌ Client initialization failed")

print("="*70)
