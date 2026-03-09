"""
Test script to verify risk analysis LLM integration is working
"""
from risk_analysis_api import analyze_refactoring_risk
import json

# Simple test case
original_code = """def add(a, b):
    return a + b"""

refactored_code = """def add(a: int, b: int) -> int:
    '''Add two integers and return the result.'''
    return a + b"""

print("Testing Risk Analysis LLM Integration...")
print("="*70)

try:
    result = analyze_refactoring_risk(original_code, refactored_code, "python")
    
    if result['success']:
        risk_data = result['risk_analysis']
        print(f"✅ Risk Analysis Successful!")
        print(f"   Risk Score: {risk_data['risk_score']}/100")
        print(f"   Risk Level: {risk_data['risk_level']}")
        print(f"   Processing Time: {risk_data.get('processing_time', 0):.0f}ms")
        print(f"\n   Recommendation: {risk_data.get('recommendation', 'N/A')}")
        print(f"\n✅ LLM Integration is WORKING!")
    else:
        print("❌ Risk analysis failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*70)
