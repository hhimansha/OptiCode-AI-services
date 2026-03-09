"""
End-to-end test of Risk Analysis API with LLM
"""
import requests
import json

API_URL = "http://localhost:8001/api/risk-analyze"

print("Testing Risk Analysis API - Full End-to-End Test")
print("="*70)

# Test data
original_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price']
    return total
"""

refactored_code = """
def calculate_total(items: list[dict]) -> float:
    '''Calculate the total price of all items.
    
    Args:
        items: List of item dictionaries with 'price' key
        
    Returns:
        Total price as float
    '''
    return sum(item['price'] for item in items)
"""

payload = {
    "original_code": original_code,
    "refactored_code": refactored_code,
    "language": "python",
    "include_ast_analysis": False  # Disable AST for faster test
}

print(f"Sending request to: {API_URL}")
print(f"Original code: {len(original_code)} chars")
print(f"Refactored code: {len(refactored_code)} chars")
print("\nWaiting for LLM response (may take 10-20 seconds)...")
print("-"*70)

try:
    response = requests.post(API_URL, json=payload, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            risk_data = result['risk_analysis']
            
            print("\n✅ RISK ANALYSIS COMPLETED!")
            print("="*70)
            print(f"Risk Score:        {risk_data['risk_score']}/100")
            print(f"Risk Level:        {risk_data['risk_level']}")
            print(f"Processing Time:   {risk_data.get('processing_time', 0):.0f}ms")
            print(f"\nRecommendation:")
            print(f"  {risk_data.get('recommendation', 'N/A')}")
            
            if risk_data.get('risk_factors'):
                print(f"\nRisk Factors:")
                for factor in risk_data['risk_factors'][:3]:  # Show first 3
                    print(f"  • {factor['factor']}: {factor['score']}/100")
                    print(f"    {factor['description'][:80]}...")
            
            print("\n" + "="*70)
            print("✅ LLM INTEGRATION IS FULLY WORKING!")
            print("✅ Ready to use from frontend code editor!")
            print("="*70)
        else:
            print(f"❌ Analysis failed: {result}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out (LLM took too long)")
    print("   Note: Free tier models can be slow, try again")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*70)
