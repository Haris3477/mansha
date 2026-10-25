# Mansha run: LLM_ERROR

- **Message:** We make plastic packing articles in Ajman, HS code 39239090, and want to ship AED 50,000 worth of them to India.
- **Total time:** 1.02 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.01 | groq/openai/gpt-oss-120b | product='plastic packing articles'; destination='India'; role=manufacturer; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-39239090; bill of materials: not given; evidence 18174 chars, 23 IDs |
| 4 | Researcher (round 1) | FAILED | 0.01 | - | LLM call failed |

## Phase details

### 1. Intake: OK

product='plastic packing articles' | destination='India' | role=manufacturer | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.01 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-39239090 | bill of materials: not given | evidence 18174 chars, 23 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:duty:39239090 NO_PREFERENCE; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

LLM call failed

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~6m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792855887111}, 'execution_id': '94062df8-0d9f-4549-94a2-c65a984756d2'} (router cooldown, no model tried) -> gave up: router busy for ~370s (> 90s cap)

Problems:
- [researcher] gave up: router busy for ~370s (longer than the 90s cap). Last problem: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~6m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792855887111}, 'execution_id': '94062df8-0d9f-4549-94a2-c65a984756d2'}
