import requests

def get_ai_response(api_key: str, user_prompt: str, system_prompt: str = None) -> str:
    """
    Kirim prompt ke OpenRouter API dan ambil respons-nya.
    """
    default_system = "Kamu adalah asisten skincare yang ramah dan profesional. Jawabanmu harus singkat, jelas, dan sesuai konteks produk."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt or default_system},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 512
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
