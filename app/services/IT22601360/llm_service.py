import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_concepts(code: str):
    prompt = f"""
    Extract theory concepts, data structures, algorithms, and 
    generate a graph-ready JSON structure from the following code:
    
    {code}
    """

    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return {"concepts": response.text}
