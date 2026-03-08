import google.genai as genai
import os
from dotenv import load_dotenv
import json
from typing import Dict, Any

load_dotenv()

# Configure the API
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    print("✅ Gemini AI client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Gemini AI client: {e}")
    client = None

def extract_concepts(code: str) -> Dict[str, Any]:
    """
    Extract concepts from code using Gemini AI
    """
    if not client:
        return {"error": "Gemini AI client not initialized", "concepts": ""}
    
    if not code or len(code.strip()) == 0:
        return {"error": "Empty code provided", "concepts": ""}
    
    prompt = f"""
    Extract theory concepts, data structures, algorithms, and 
    generate a graph-ready JSON structure from the following code:
    
    {code}
    
    Please respond with valid JSON only.
    """
    
    try:
        # Generate content
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 1000,
            }
        )
        
        # Try to parse as JSON if possible
        text = response.text.strip()
        try:
            concepts_json = json.loads(text)
            return {"concepts": concepts_json}
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {"concepts": text}
            
    except Exception as e:
        return {"error": str(e), "concepts": ""}