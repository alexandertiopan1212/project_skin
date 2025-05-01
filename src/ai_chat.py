import requests
import json

def get_chat_response_streaming(api_key: str, prompt: str):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": "Kamu adalah beauty advisor AI. Jawab berdasarkan produk yang direkomendasikan."},
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True
        )

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                if line.strip() == "data: [DONE]":
                    break
                try:
                    data = json.loads(line.lstrip("data: ").strip())
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except Exception as e:
                    yield f"⚠️ Error parsing stream chunk: {e}"

    except Exception as e:
        yield f"⚠️ Request failed: {e}"
