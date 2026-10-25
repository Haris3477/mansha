# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 345.15 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.11 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 147.29 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | FALLBACK | 196.75 | - | code-only report (fallback); notes: 7 in (3 mandatory, verbatim) -> 7 in the report |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.11 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (58.52 s); attempts: #1 router 1.12 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (upstream_error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.6-flash key1: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '168a0114-143b-4d9a-b4b2-9c41795e8efd'} -> waited 30 s | #2 router 1.65 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (upstream_error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.5-flash key1: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '2c66c13c-8124-4d62-a452-61aa7349021e'} -> waited 30 s | #3 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~25s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792160617135}, 'execution_id': '81c7386f-d236-401b-b158-e3f9fe73b4ff'} (router cooldown, no model tried) -> waited 26.0 s | #4 openrouter/dots-studio/dots-3-note-preview:free 58.52 s OK

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: FALLBACK

code-only report (fallback) | notes: 7 in (3 mandatory, verbatim) -> 7 in the report

LLM calls:
- call FAILED; attempts: #1 router 61.29 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (timeout ×1, upstream_error ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: openrouter/dots-studio/dots-3-note-preview:free key1: timeout; google/gemini-3.6-flash key2: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '92f524f0-5422-47c3-bce9-58ef08e8c95b'} -> waited 30 s | #2 router 1.22 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (upstream_error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.5-flash key1: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '54042371-608c-4ca6-9bbc-c169175323fa'} -> waited 30 s | #3 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~27s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792160826681}, 'execution_id': '47d9ed82-96c8-443e-b78a-2f3bfdc445af'} (router cooldown, no model tried) -> waited 28.5 s | #4 router 15.69 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (empty_completion ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: openrouter/dots-studio/dots-3-note-preview:free key1: empty_completion. Last error: empty completion from Dots3 Note Preview (free)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '7c63f233-2d9c-4b5c-978b-0728d63ee671'} -> waited 30 s | #5 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~60s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792160933376}, 'execution_id': '8f6dd1a5-1007-4c18-9ca3-2d728ab61907'} (router cooldown, no model tried) -> gave up: call budget: 197s used of 240s

Problems:
- LLM call failed: [document_builder] gave up after 197s (3 model attempt(s)): the call budget is 240s. Last problem: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~60s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792160933376}, 'execution_id': '8f6dd1a5-1007-4c18-9ca3-2d728ab61907'}
