# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 134.68 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 4.93 | google/gemini-3.7-flash | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 13.3 | google/gemini-3.7-flash | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 67.47 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Document Builder | OK | 48.98 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 7 in (6 mandatory, verbatim) -> 6 in the report |
| 7 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by google/gemini-3.7-flash (4.88 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by google/gemini-3.7-flash (13.29 s)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by groq/openai/gpt-oss-120b (3.57 s)
- served by groq/openai/gpt-oss-120b (3.85 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '032845f3-f552-44a0-b5f5-9b3cc19d4c99'} -> waited 30 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '51e3760a-b8e5-4223-ad32-b3895605d1bb'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 3.85 s OK

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (3.57 s)
- part 2/2: steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (3.85 s)

### 6. Document Builder: OK

LLM prose passed the checks | notes: 7 in (6 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (48.97 s)

### 7. Report check: OK

0 problem(s), 0 warning(s)
