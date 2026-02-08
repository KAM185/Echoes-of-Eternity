import json
import time
from google.ai import generative
from google.ai.generative_v1beta import types

# ---------------- Initialize Gemini client ----------------
def init_gemini_client():
    """
    Initialize Google Gemini client.
    GOOGLE_APPLICATION_CREDENTIALS env var must point to your service account JSON.
    """
    client = generative.TextServiceClient()
    return client

# ---------------- Available Gemini Models ----------------
GEMINI_MODELS = [
    "gemini-3",
    "gemini-3-preview",
    "gemini-2.5",
    "gemini-2.5-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0",
    "gemini-2.0-lite"
]

# ---------------- Generate Analysis ----------------
def generate_analysis(client, prompt: str, max_retries: int = 2):
    """
    Try 8 Gemini models in order. Retry each model up to max_retries.
    Returns first successful JSON response.
    """
    last_exception = None

    for model_name in GEMINI_MODELS:
        for attempt in range(max_retries):
            try:
                response = client.generate_text(
                    model=model_name,
                    prompt=prompt,
                    temperature=0.7,
                    max_output_tokens=1024
                )
                raw = response.text

                try:
                    return json.loads(raw)
                except Exception:
                    # last-resort cleanup for partial JSON
                    cleaned = raw.strip().split("{",1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)

            except Exception as e:
                last_exception = e
                time.sleep(1)
                continue
        # If this model fails after retries, try next
        print(f"Model {model_name} failed after {max_retries} retries: {last_exception}")

    raise RuntimeError(f"All Gemini models failed. Last error: {last_exception}")

# ---------------- Draw Damage Overlay ----------------
def draw_damage_overlay(image, damages):
    # Placeholder - just return the original image
    return image.copy()

# ---------------- Chat With Monument ----------------
def chat_with_monument(analysis, chat_history, question, chat_prompt):
    """
    Ask follow-up question to monument using same Gemini models fallback.
    """
    client = init_gemini_client()
    prompt = chat_prompt + "\n" + question
    result = generate_analysis(client, prompt)
    return result.get("reply", "The monument remains silent.")

