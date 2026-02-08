import os
import time
from google.generativeai import GenerativeModel
import google.generativeai as genai


# ────────────────────────────────────────────────
# Gemini initialization
# ────────────────────────────────────────────────
def init_gemini(model_name: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    return GenerativeModel(model_name)


# ────────────────────────────────────────────────
# Multi-model fallback chain (6 models)
# ────────────────────────────────────────────────
MODEL_CHAIN = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-1.5-pro-vision",
    "gemini-1.5-flash-vision",
]


# ────────────────────────────────────────────────
# Streaming analysis
# ────────────────────────────────────────────────
def generate_analysis_stream(image, prompt):
    last_error = None

    for model_name in MODEL_CHAIN:
        try:
            model = init_gemini(model_name)

            response = model.generate_content(
                [prompt, image],
                stream=True,
            )

            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

            return

        except Exception as e:
            last_error = e
            time.sleep(0.5)
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")
