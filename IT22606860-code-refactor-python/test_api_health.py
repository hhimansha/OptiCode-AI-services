"""
Quick test to verify Risk Analysis API is accessible
"""
import requests
import time

print("Testing Risk Analysis API endpoint...")
print("="*70)

# Wait a moment for server to fully start
time.sleep(2)

# Test health endpoint
try:
    response = requests.get("http://localhost:8001/health", timeout=5)
    if response.status_code == 200:
        print("✅ Health check passed!")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Could not connect to API: {e}")
    print("   Make sure the server is running on port 8001")

print("="*70)
