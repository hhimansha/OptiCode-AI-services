import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from typing import Dict, Any

load_dotenv()

# Configure the API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("✅ Gemini AI client initialized successfully")
        client = True
    else:
        print("⚠️ Gemini not initialized: Gemini API key not found. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        client = None
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={
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