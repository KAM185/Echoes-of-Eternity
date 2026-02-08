import json
import time
from openai import OpenAI

# ---------------- Initialize 8 Gemini models ----------------
def init_gemini_models(api_key: str):
    client = OpenAI(api_key=api_key)
    models = [
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-preview-09-2025",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite"
    ]
    return client, models

# ---------------- Generate Analysis ----------------
def generate_analysis(client, models, prompt: str, max_retries: int = 2):
    last_exception = None

    for model_name in models:
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "<image uploaded>"}
                    ]
                )
                raw = resp.choices[0].message["content"]
                try:
                    return json.loads(raw)
                except Exception:
                    # last-resort cleanup
                    cleaned = raw.strip().split("{",1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    continue
                print(f"Model {model_name} attempt {attempt+1} failed: {e}")
                break

    raise RuntimeError(f"All Gemini models failed after retries. Last error: {last_exception}")

# ---------------- Draw Damage Overlay ----------------
def draw_damage_overlay(image, damages):
    return image.copy()  # simple placeholder

# ---------------- Chat with Monument ----------------
def chat_with_monument(analysis, chat_history, question, chat_prompt):
    client, models = init_gemini_models("<YOUR_API_KEY_HERE>")
    prompt = chat_prompt + "\n" + question
    result = generate_analysis(client, models, prompt)
    return result.get("reply", "The monument remains silent.")
