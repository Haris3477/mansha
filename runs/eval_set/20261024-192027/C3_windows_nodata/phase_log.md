# Mansha run: LLM_ERROR

- **Message:** We make aluminium window frames in Sharjah from imported aluminium profiles and want to export them to India.
- **Total time:** 1.25 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.24 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22267 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 0.01 | - | LLM call failed |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.24 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22267 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 NEEDS_VALUE; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

LLM call failed

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~6m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792855887111}, 'execution_id': '0b6dffad-fc70-4cd1-a7e6-0053d5366686'} (router cooldown, no model tried) -> gave up: router busy for ~371s (> 90s cap)

Problems:
- [researcher] gave up: router busy for ~371s (longer than the 90s cap). Last problem: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~6m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792855887111}, 'execution_id': '0b6dffad-fc70-4cd1-a7e6-0053d5366686'}
