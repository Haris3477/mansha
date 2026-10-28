# Mansha run: REPORT (ELIGIBLE)

- **Message:** We make aluminium windows in Sharjah from imported profiles, UAE HS code 7610 10 90, and want to export them to India. Our ex-works price for the shipment is AED 100,000.
- **Total time:** 418.02 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.99 | groq/openai/gpt-oss-120b | product='aluminium windows'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000; bill of materials: given; evidence 19525 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 323.74 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (medium); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 1 |
| 5 | QA (round 1) | FAILED | 0.71 | - | QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts) |
| 6 | Document Builder | OK | 52.88 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose NOT reviewed by QA; rounds: 1; notes: 15 in (10 mandatory, verbatim) -> 12 in the report |
| 7 | Prose QA (round 1) | FAILED | 38.69 | - | prose QA call failed: prose NOT reviewed by QA |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Warnings

- QA round 1: QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts)
- Researcher round 1: 1 code warning(s) not reviewed by QA
- Document Builder: report prose NOT reviewed by QA (prose QA call failed: prose NOT reviewed by QA)

## Phase details

### 1. Intake: OK

product='aluminium windows' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.95 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000 | bill of materials: given | evidence 19525 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (medium) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 1

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (158.41 s); attempts: #1 openrouter/dots-studio/dots-3-note-preview:free 165.31 s FAILED: truncated (finish_reason=length) | #2 openrouter/dots-studio/dots-3-note-preview:free 158.41 s OK

Code warnings (for QA):
- caveats[0]: number(s) ['45'] not found in TOOL:rule_lookup:76101000

Normalized by code:
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "The 8-digit HS code 76101090 given is not a line in India's tariff; the match was made on the first 6 digits (761010). 8-digit codes are national and differ between the UAE and India."
- caveats: note written from TOOL:tariff_lookup: "The 8-digit code 76101090 you gave is not a line in India's tariff; Mansha matched it on its first 6 digits (761010). 8-digit codes are national and differ between the UAE and India."
- caveats[9]: note written from the KB (P-UAE-ISSUER)
- follow_up_questions: dropped for verdict ELIGIBLE (the result does not depend on more information from the user): 'Is your factory located inside a free zone? Factory registration requires the factory to be outside a free zone.'

### 5. QA (round 1): FAILED

QA part 1/3, part 2/3, part 3/3 failed: output NOT reviewed by QA in full (3 parts)

LLM calls:
- call FAILED; attempts: #1 router 0.69 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models rate-limited after 1 attempt. Soonest cooldown reset ~2m. Attempt trail: cerebras/gpt-oss-120b key1: rate_limited. Last error: Cerebras API error 429: Too Many Requests', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201128168}, 'execution_id': '9a5146c8-85f7-43c5-b9cf-d9aa61d66e71'} (router cooldown, no model tried) -> gave up: router busy for ~91s (> 90s cap) | #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~2m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201128168}, 'execution_id': 'cb4b7c17-4ca3-499d-9ea2-a6e717d92e70'} (router cooldown, no model tried) -> gave up: router busy for ~91s (> 90s cap) | #1 router 0.0 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~2m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201128168}, 'execution_id': 'b54a0d1d-50bf-4050-94ba-bbfd29fc71b1'} (router cooldown, no model tried) -> gave up: router busy for ~91s (> 90s cap)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: ERROR
- part 2/3: steps and notes: ERROR; code warnings W1
- part 3/3: steps and notes: ERROR

### 6. Document Builder: OK

LLM prose passed the code checks; prose NOT reviewed by QA | rounds: 1 | notes: 15 in (10 mandatory, verbatim) -> 12 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (52.89 s)

### 7. Prose QA (round 1): FAILED

prose QA call failed: prose NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~37s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201128168}, 'execution_id': 'ab3066c9-9cad-426e-b2be-990b87b94a13'} (router cooldown, no model tried) -> waited 38.1 s | #2 router 0.58 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models rate-limited after 1 attempt. Soonest cooldown reset ~2m. Attempt trail: cerebras/gpt-oss-120b key1: rate_limited. Last error: Cerebras API error 429: Too Many Requests', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201219751}, 'execution_id': '0a249792-1483-4869-a8dc-1f7f9fe18e9c'} (router cooldown, no model tried) -> gave up: router busy for ~91s (> 90s cap)

### 8. Report check: OK

0 problem(s), 0 warning(s)
