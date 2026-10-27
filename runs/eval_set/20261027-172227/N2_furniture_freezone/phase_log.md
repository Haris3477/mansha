# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 387.56 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.41 | groq/openai/gpt-oss-120b | product='wooden bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19692 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 106.54 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 2.93 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 275.55 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 16 in (11 mandatory, verbatim) -> 13 in the report; summary cautions (code): FREE_ZONE |
| 7 | Prose QA (round 1) | OK | 1.12 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='wooden bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.41 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19692 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (106.53 s)

Normalized by code:
- origin_result.basis: check names written in plain words
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm the HS code for your wooden bedroom furniture.'
- follow_up_questions[0]: free-zone question dropped, the user already said the factory is in a free zone: 'Is the manufacturing facility located in a free zone?'
- caveats[10]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.32 s)
- served by cerebras/gpt-oss-120b (0.94 s)
- served by cerebras/gpt-oss-120b (0.65 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.32 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.94 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.65 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 16 in (11 mandatory, verbatim) -> 13 in the report | summary cautions (code): FREE_ZONE

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (59.73 s); attempts: #1 router 94.76 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'Provider error (Dots3 Note Preview (free)): OpenRouter returned 200 with a non-JSON body — the endpoint is not OpenAI-compatible. Check the base URL (for Ollama use [redacted-url] for llama.cpp/vLLM/LM Studio the /v1 path).', 'type': 'provider_error'}, 'execution_id': 'cb045760-8e9c-42de-bc44-31712baceb1a'} -> waited 30 s | #2 router 0.04 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (error ×2). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: openrouter/dots-studio/dots-3-note-preview:free key1: error; google/gemini-3.6-flash key2: error. Last error: fetch failed (ENOTFOUND generativelanguage.googleapis.com)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '379ea972-fec5-4794-9d26-266a0a3bf511'} -> waited 30 s | #3 router 0.04 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.5-flash key1: error. Last error: fetch failed (ENOTFOUND generativelanguage.googleapis.com)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': 'ca54ab91-8081-457b-8b71-ed8fd7404b8c'} -> waited 30 s | #4 router 0.04 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 3 routes checked (3 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~30s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793107944243}, 'execution_id': '94915da7-449e-49ee-a384-56c36cba3421'} (router cooldown, no model tried) -> waited 30.9 s | #5 openrouter/dots-studio/dots-3-note-preview:free 59.73 s OK

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.12 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
