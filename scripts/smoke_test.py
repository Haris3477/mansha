"""Smoke test: confirms .env loads and both FreeLLMAPI chains answer.

Run from the project root:  python scripts/smoke_test.py
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # finds .env by walking up from this file's folder

base_url = os.environ["FREELLMAPI_BASE_URL"]
api_key = os.environ["FREELLMAPI_KEY"]

# Show only the public prefix and length, never the full key.
print(f"Key loaded: {api_key[:11]}... ({len(api_key)} chars, expected 59)")
print(f"Base URL:   {base_url}\n")

client = OpenAI(base_url=base_url, api_key=api_key)

for chain in ["auto:qa", "auto:long"]:
    raw = client.chat.completions.with_raw_response.create(
        model=chain,
        max_tokens=200,  # room for reasoning models; still under Groq's 1000 cap
        messages=[{"role": "user", "content": "Reply with exactly one word: OK"}],
    )
    resp = raw.parse()
    choice = resp.choices[0]
    print(f"[{chain}]")
    print(f"  Served by:     {raw.headers.get('x-routed-via')}")
    print(f"  Finish reason: {choice.finish_reason}")
    print(f"  Reply:         {(choice.message.content or '').strip()!r}\n")