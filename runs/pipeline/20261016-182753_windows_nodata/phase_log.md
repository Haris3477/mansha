# Mansha run: LLM_ERROR

- **Message:** We make aluminium window frames in Sharjah from imported aluminium profiles and want to export them to India.
- **Total time:** 183.64 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.55 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22267 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 182.1 | - | LLM call failed |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.55 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22267 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 NEEDS_VALUE; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

LLM call failed

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~58s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792160933376}, 'execution_id': '4eca3db7-8762-4fe1-b8c2-7d35c423476a'} (router cooldown, no model tried) -> waited 59.4 s | #2 router 61.13 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (upstream_error ×1, timeout ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.7-flash key1: upstream_error; openrouter/dots-studio/dots-3-note-preview:free key2: timeout. Last error: This operation was aborted', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': 'b841063b-21a2-4a54-ba8a-33c2a9761b61'} -> waited 30 s | #3 router 1.51 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (upstream_error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.7-flash key1: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': 'aa269800-329e-455e-bf24-c09de7d6183d'} -> waited 30 s | #4 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~60s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792161117027}, 'execution_id': 'ce42c97e-fb5b-49bc-99a9-e31099a4a33d'} (router cooldown, no model tried) -> gave up: call budget: 182s used of 240s

Problems:
- [researcher] gave up after 182s (2 model attempt(s)): the call budget is 240s. Last problem: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~60s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792161117027}, 'execution_id': 'ce42c97e-fb5b-49bc-99a9-e31099a4a33d'}
