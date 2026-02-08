import json
import time
import streamlit as st
from openai import OpenAI

# ---------------- Initialize client and 8 models ----------------
def init_gemini_models():
    """
    Initialize OpenAI client with GEMINI_API_KEY from Streamlit secrets.
    Returns client and list of 8 Gemini model names.
    """
    api_key = st.secrets["GEMINI_API_KEY"]
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
    """
    Tries 8 Gemini models in order with retries.
    Returns JSON-parsed result from first successful model.
    """
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

                # Try parsing JSON
                try:
                    return json.loads(raw)
                except Exception:
                    # Last-resort cleanup
                    cleaned = raw.strip().split("{",1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                break  # Try next model

    raise RuntimeError(f"All Gemini models failed after retries. Last error: {last_exception}")

# ---------------- Draw Damage Overlay ----------------
def draw_damage_overlay(image, damages):
    """
    Simple placeholder function to return original image.
    """
    return image.copy()

# ---------------- Chat With Monument ----------------
def chat_with_monument(analysis, chat_history, question, chat_prompt):
    """
    Ask the monument a follow-up question.
    """
    client, models = init_gemini_models()
    prompt = chat_prompt + "\n" + question
    result = generate_analysis(client, models, prompt)
    return result.get("reply", "The monument remains silent.")
