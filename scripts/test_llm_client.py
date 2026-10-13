"""Manual test for mansha.llm_client.

Run from the project root:  python -m scripts.test_llm_client
"""
import logging

from mansha.llm_client import LLMCallError, call_llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)  # hide the SDK's per-request HTTP lines

JSON_SYSTEM = "Return only a single JSON object. No markdown, no extra text."
JSON_USER = 'Return exactly this JSON: {"emirate": "Abu Dhabi", "language": "en"}'


def section(title: str) -> None:
    print(f"\n=== {title} ===")


section("Test 1: plain text on auto:qa")
r = call_llm("test", "auto:qa", [{"role": "user", "content": "What is the capital of the UAE? One word."}])
print("Reply:", r.text.strip())

section("Test 2: valid JSON on auto:long")
r = call_llm(
    "test", "auto:long",
    [{"role": "system", "content": JSON_SYSTEM}, {"role": "user", "content": JSON_USER}],
    expect_json=True, required_keys=("emirate", "language"),
)
print("Parsed:", r.data)

section("Test 3: forced validation failure (expect a retry, then a clear error)")
try:
    call_llm(
        "test", "auto:qa",
        [{"role": "system", "content": JSON_SYSTEM}, {"role": "user", "content": JSON_USER}],
        expect_json=True, required_keys=("emirate", "this_key_never_exists"),
    )
    print("UNEXPECTED: no error raised")
except LLMCallError as e:
    print("Raised LLMCallError as expected:", e)
    print("Attempts recorded:", len(e.attempts))

section("Test 4: plain 'auto' is blocked")
try:
    call_llm("test", "auto", [{"role": "user", "content": "hi"}])
    print("UNEXPECTED: no error raised")
except ValueError as e:
    print("Blocked as expected:", e)