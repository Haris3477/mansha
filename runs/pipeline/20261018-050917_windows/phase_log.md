# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 471.05 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.24 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 142.78 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | FAILED | 270.26 | - | QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts) |
| 6 | Document Builder | OK | 56.77 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 11 in (4 mandatory, verbatim) -> 6 in the report |
| 7 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Warnings

- QA round 1: QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts)

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.19 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (142.77 s)

### 5. QA (round 1): FAILED

QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts)

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '71f9c0c6-d236-455a-b114-2e5c7f7f6c85'} -> waited 30 s | #2 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '7ccf12cd-e174-4e30-9b33-d5151fde30d8'} -> waited 30 s | #3 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '181ae4fb-0ef7-401f-bae9-6ee06c1f8398'} -> waited 30 s | #4 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '30d9ee78-b9db-42a0-98ed-87b85330a7e0'} | #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '1fe6fc4e-76c6-491c-87fa-1fd1e04f6481'} -> waited 30 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '4c1ea962-478c-4835-9f8f-8f6170005991'} -> waited 30 s | #3 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'e0509cba-dad7-46d2-8c62-deaf20d4ddf8'} -> waited 30 s | #4 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '2243cee5-24c5-483e-b805-8292a2000066'} | #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '213da0e8-67ee-4e81-8aeb-3805b50d8f3a'} -> waited 30 s | #2 router 0.03 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '85704440-098b-4255-acad-b98309825098'} -> waited 30 s | #3 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'c89dddce-9eef-4c74-afc5-e23493937847'} -> waited 30 s | #4 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'abdd76e1-dd69-40db-bb32-ea0aaae0c810'}

Review split into parts (Groq's 8,000-token limit):
- part 1/3: findings + steps and notes: ERROR
- part 2/3: steps and notes: ERROR
- part 3/3: steps and notes: ERROR

### 6. Document Builder: OK

LLM prose passed the checks | notes: 11 in (4 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (56.77 s)

### 7. Report check: OK

0 problem(s), 0 warning(s)
