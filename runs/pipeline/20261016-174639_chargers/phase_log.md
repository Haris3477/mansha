# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 165.59 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.15 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 112.02 | openrouter/dots-studio/dots-3-note-preview:free | line TL-IN-85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | OK | 51.42 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 9 in (4 mandatory, verbatim) -> 6 in the report |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.15 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line TL-IN-85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (57.65 s); attempts: #1 router 0.78 s FAILED: HTTP 502: Error code: 502 - {'error': {'message': 'All 1 routed attempt(s) failed with upstream provider errors (upstream_error ×1). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt trail: google/gemini-3.5-flash key1: upstream_error. Last error: Google API error 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'type': 'provider_error', 'code': 'upstream_failed'}, 'execution_id': '9d7f27e3-96f4-4c16-a725-77c705e590c2'} -> waited 30 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~23s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792158454561}, 'execution_id': '875ef443-9f28-4efb-9a1c-5470fd61257a'} (router cooldown, no model tried) -> waited 23.6 s | #3 openrouter/dots-studio/dots-3-note-preview:free 57.65 s OK

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: OK

LLM prose passed the checks | notes: 9 in (4 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (51.42 s)
