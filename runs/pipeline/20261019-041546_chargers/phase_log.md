# Mansha run: CHECKS_FAILED

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 390.89 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 49.71 | google/gemini-3.7-flash | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 135.24 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 78.35 | groq/openai/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | OK | 30.83 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 96.75 | groq/openai/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by google/gemini-3.7-flash (49.67 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (135.24 s)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by groq/openai/gpt-oss-120b (4.12 s)
- served by groq/openai/gpt-oss-120b (2.48 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~11s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792369146323}, 'execution_id': 'f28fea74-cd51-453b-b019-4d040785c76a'} (router cooldown, no model tried) -> waited 11.6 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '766322bc-ca7f-4006-86e5-002f31b052db'} -> waited 30 s | #3 router 0.04 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '781a71e9-66f9-44f4-afd8-2ff3cd89f5cc'} -> waited 30 s | #4 groq/openai/gpt-oss-120b 2.48 s OK

Problems:
- caveats[11].note: The note cites the wrong website for the India-specific service page. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically; the India-specific service page is still on moet.gov.ae. (see P-UAE-ISSUER)

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (4.12 s)
- part 2/2: steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (2.48 s)

### 6. Researcher (round 2): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: caveats[11].note: The note cites the wrong website for the India-specific service page. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically; the India-specific service page is still on moet.gov.ae. (see P-UAE-ISSUER)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (30.82 s)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by groq/openai/gpt-oss-120b (4.45 s); attempts: #1 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '3baca015-0cf3-4962-a28d-8e2db9c5c667'} -> waited 30 s | #2 groq/openai/gpt-oss-120b 4.45 s OK
- served by groq/openai/gpt-oss-120b (2.22 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'b1062fc8-8d7c-4ecc-9b31-591cfb4bd8ae'} -> waited 30 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '0f44d2fe-f836-4390-8989-4343ae59db1e'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 2.22 s OK

Problems:
- caveats[11].note: The note cites the wrong website (doit.gov.ae) which is not supported by the evidence. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically; the India-specific service page is still on moet.gov.ae. (see P-UAE-ISSUER)

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (4.45 s)
- part 2/2: steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (2.22 s)
