# adaptive_task_generator/gemini_client.py
import os
import requests
import json
from typing import Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # set in .env when ready
# If you prefer a specific model set here:
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # change if needed
# Google generative API base - note: exact endpoint version may change
GEN_API_BASE = "https://generativelanguage.googleapis.com/v1beta2"

def call_gemini_prompt(prompt: str, max_tokens: int = 700, temperature: float = 0.7) -> Optional[str]:
    """
    Call Gemini via REST; requires GEMINI_API_KEY in environment.
    If no API key present, returns None.
    NOTE: endpoint path and request fields may need updates; replace with Google SDK if preferred.
    """
    if not GEMINI_API_KEY:
        return None

    url = f"{GEN_API_BASE}/models/{GEMINI_MODEL}:generateText"
    headers = {"Content-Type": "application/json"}
    body = {
        "prompt": {
            "text": prompt
        },
        "temperature": temperature,
        "maxOutputTokens": max_tokens
    }
    params = {"key": GEMINI_API_KEY}
    # Use requests to call the API
    resp = requests.post(url, headers=headers, params=params, json=body, timeout=30)
    if resp.status_code != 200:
        # return the text body to help debugging
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
    j = resp.json()
    # Try to parse returned text
    # NOTE: different endpoints/sdks return different keys; adapt if you use SDK
    # Here we attempt common places:
    if "candidates" in j:
        return j["candidates"][0].get("content", {}).get("text", "")
    if "output" in j:
        return j["output"].get("text", "")
    # fallback: full JSON string
    return json.dumps(j)

def generate_with_fallback(prompt: str) -> str:
    """
    If GEMINI_API_KEY set we attempt remote call, otherwise create a local fallback.
    """
    remote = call_gemini_prompt(prompt)
    if remote:
        return remote

    # Local fallback = simple rule-based generator for testing
    # Keep it short and safe
    return local_fallback_generator(prompt)

def local_fallback_generator(prompt: str) -> str:
    """
    Create a simple task derived from the prompt (only for local testing).
    """
    # Very simple: return a small template
    task = {
        "title": "Sum of Two Numbers (practice)",
        "description": "Write a function `sum_two` that returns the sum of two integers.",
        "starter_code": "def sum_two(a, b):\n    # TODO: implement\n    return None",
        "testcases": [
            {"input": "sum_two(1, 2)", "output": "3"},
            {"input": "sum_two(0, 0)", "output": "0"},
            {"input": "sum_two(-1, 5)", "output": "4"}
        ],
        "notes": "This is a fallback generated task (local). Replace with Gemini output when API key is configured."
    }
    return json.dumps(task, indent=2)
