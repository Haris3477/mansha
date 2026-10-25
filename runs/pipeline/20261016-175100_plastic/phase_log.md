# Mansha run: REPORT (NO_PREFERENCE)

- **Message:** We make plastic packing articles in Ajman, HS code 39239090, and want to ship AED 50,000 worth of them to India.
- **Total time:** 140.1 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.0 | groq/openai/gpt-oss-120b | product='plastic packing articles'; destination='India'; role=manufacturer; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-39239090; bill of materials: not given; evidence 18174 chars, 23 IDs |
| 4 | Researcher (round 1) | FAILED | 79.46 | openrouter/dots-studio/dots-3-note-preview:free | line 39239090 (3923 90 90) (high); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 1; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Researcher (round 2) | OK | 12.52 | openrouter/dots-studio/dots-3-note-preview:free | line 39239090 (high); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 0; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 8 | Document Builder | OK | 47.12 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 3 in (1 mandatory, verbatim) -> 3 in the report |

## Phase details

### 1. Intake: OK

product='plastic packing articles' | destination='India' | role=manufacturer | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (0.99 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-39239090 | bill of materials: not given | evidence 18174 chars, 23 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:duty:39239090 NO_PREFERENCE; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 39239090 (3923 90 90) (high) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (23.46 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 4 routes checked (4 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~55s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792158716080}, 'execution_id': '6c7198bc-a575-40ab-a515-4e87434bc37d'} (router cooldown, no model tried) -> waited 56.0 s | #2 openrouter/dots-studio/dots-3-note-preview:free 23.46 s OK

Problems:
- classification.tariff_line '39239090 (3923 90 90)' does not match its source TL-IN-39239090 (line 39239090)

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Researcher (round 2): OK

line 39239090 (high) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 0 | warnings 0

Corrections sent (one shared revision):
- classification.tariff_line '39239090 (3923 90 90)' does not match its source TL-IN-39239090 (line 39239090)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (12.51 s)

### 7. QA (round 2): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 8. Document Builder: OK

LLM prose passed the checks | notes: 3 in (1 mandatory, verbatim) -> 3 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (47.12 s)
