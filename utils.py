import json
import time
from google.ai.generative_v1beta import TextServiceClient

# Initialize Gemini client
def init_gemini_client():
    client = TextServiceClient()
    return client

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

def generate_analysis(client, prompt: str, max_retries: int = 2):
    last_exception = None
    for model_name in GEMINI_MODELS:
        for attempt in range(max_retries):
            try:
                resp = client.generate_text(
                    model=model_name,
                    prompt=prompt,
                    temperature=0.7,
                    max_output_tokens=1024
                )
                raw = resp.text
                try:
                    return json.loads(raw)
                except Exception:
                    cleaned = raw.strip().split("{",1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)
            except Exception as e:
                last_exception = e
                time.sleep(1)
                continue
    raise RuntimeError(f"All Gemini models failed. Last error: {last_exception}")
