import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com"


def _get_working_model() -> str | None:
    """
    Dynamically fetch a Gemini model that supports generateContent
    """
    url = f"{BASE_URL}/v1beta/models?key={GEMINI_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print("❌ Gemini model list failed:", resp.text)
            return None

        models = resp.json().get("models", [])
        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                return m["name"]

        return None

    except Exception as e:
        print("❌ Gemini list exception:", e)
        return None


def generate_answer(context: str, question: str) -> str:
    """
    Generate answer using Gemini API
    """

    model = _get_working_model()
    if not model:
        return (
            "Gemini text generation is not enabled for this API key. "
            "The chatbot architecture is correct, but the API access is restricted."
        )

    url = f"{BASE_URL}/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
You are an intelligent HR and recruitment assistant.

Rules:
- Always answer in at least 5 to 6 detailed sentences.
- Explain clearly and professionally.
- Use the provided context if available.

Context:
{context if context else "General HR and technical knowledge."}

Question:
{question}

Answer:
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)

        if resp.status_code != 200:
            print("❌ Gemini generate error:", resp.text)
            return "Unable to generate response at the moment."

        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except Exception as e:
        print("❌ Gemini exception:", e)
        return "Unable to generate response at the moment."
