import requests
import time
from backend.core.config import GEMINI_API_KEY

def generate_deepseek_response(prompt: str, temperature=0.3, max_tokens=2000) -> str:
    """
    Refined Gemini API call via REST (requests)
    """
    try:
        print(f"📤 Sending Gemini API request... Prompt length: {len(prompt)} chars")
        
        # 1. Use the stable or latest flash model
        model_name = "gemini-2.5-flash-lite"
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        # 2. Structure the payload according to Google's Generative AI schema
        payload = {
    "contents": [{
        "parts": [{
            "text": f"""
            Return a JSON object with a key 'results' containing an array of candidate summaries.
            Each summary MUST be exactly 3-4 full sentences.
            
            IMPORTANT: Return ONLY raw JSON code. Do not include markdown formatting like ```json.
            
            Data: {prompt}
            """
        }]
    }],
    "generationConfig": {
        "temperature": 0.1,
        "maxOutputTokens": 4000,
        "topP": 0.8,
        "topK": 40
        # Notice: response_mime_type is REMOVED to avoid the 400 error
    }
}
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 3. Robust parsing: Check for candidates and content parts
            try:
                candidate = data["candidates"][0]
                
                # Check if the model stopped because of safety or other reasons
                if "content" in candidate and "parts" in candidate["content"]:
                    result = candidate["content"]["parts"][0]["text"].strip()
                    print(f"✅ Gemini API Success: '{result[:50]}...'")
                    return result
                else:
                    finish_reason = candidate.get("finishReason", "UNKNOWN")
                    print(f"⚠️ Gemini blocked response. Reason: {finish_reason}")
                    return f"Error: Content blocked by safety filters (Reason: {finish_reason})"
                    
            except (KeyError, IndexError):
                print(f"⚠️ Gemini response format unexpected: {data}")
                return ""
        else:
            print(f"❌ Gemini API Error {response.status_code}: {response.text[:200]}")
            return ""
            
    except Exception as e:
        print(f"❌ Gemini API Exception: {type(e).__name__}: {e}")
        return ""
