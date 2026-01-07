import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_with_fallback(prompt: str) -> str:
    # If key is missing, safe local fallback
    if not GEMINI_API_KEY:
        return "Write a Python function that returns the sum of two numbers."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 80,
            }
        )

        text = (response.text or "").strip()
        if not text:
            return "Write a Python program that prints numbers from 1 to 10."

        return text

    except Exception as e:
        print("Gemini fallback error:", e)
        return "Write a Python function that returns the sum of two numbers."
