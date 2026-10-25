# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 537.49 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 213.1 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 19579 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 50.78 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | FALLBACK | 273.61 | - | code-only report (fallback); notes: 8 in (4 mandatory, verbatim) -> 8 in the report |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.25 s); attempts: #1 router 180.84 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (upstream_error ×1, timeout ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.7-flash key1: upstream_error; nvidia/nvidia/nemotron-3-ultra-550b-a55b key2: timeout. Last error: The operation was aborted (nvidia, chat, 180s)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '4ec9cb0b-5c27-411a-958d-1673dac1f6ed'} -> waited 30 s | #2 groq/openai/gpt-oss-120b 2.25 s OK

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 19579 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (50.78 s)

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: FALLBACK

code-only report (fallback) | notes: 8 in (4 mandatory, verbatim) -> 8 in the report

LLM calls:
- call FAILED; attempts: #1 router 61.44 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (timeout ×1, upstream_error ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: openrouter/dots-studio/dots-3-note-preview:free key1: timeout; google/gemini-3.7-flash key2: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '0aabb0f9-9331-4592-865e-eed7c9aa7779'} -> waited 30 s | #2 router 182.16 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (upstream_error ×1, timeout ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.6-flash key1: upstream_error; nvidia/nvidia/nemotron-3-ultra-550b-a55b key2: timeout. Last error: The operation was aborted (nvidia, chat, 180s)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '5c5732f1-d4dd-460f-a8c7-191b28e7cdcf'}

Problems:
- LLM call failed: [document_builder] failed after 2 model attempt(s) and 0 cooldown wait(s). Last problem: HTTP 502: Error code: 502 - {'error': {'message': 'All 2 routed attempt(s) failed with upstream provider errors (upstream_error ×1, timeout ×1) (stopped early: retry time budget 45s exceeded — one failover hop is always allowed, and past that the budget stops starting further retries and cancels an attempt still waiting on its first byte; raise FALLBACK_TIME_BUDGET_MS or the fallback_time_budget_ms setting to allow a longer failover chain). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.6-flash key1: upstream_error; nvidia/nvidia/nemotron-3-ultra-550b-a55b key2: timeout. Last error: The operation was aborted (nvidia, chat, 180s)', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '5c5732f1-d4dd-460f-a8c7-191b28e7cdcf'}
