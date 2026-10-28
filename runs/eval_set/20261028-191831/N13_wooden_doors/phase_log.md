# Mansha run: REPORT (REGULATORY_GAP_DETECTED)

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 84.57 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.04 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20674 chars, 31 IDs |
| 4 | Researcher (round 1) | FAILED | 44.1 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 2; warnings 0 |
| 5 | QA (round 1) | FAILED | 0.02 | - | QA call failed: output NOT reviewed by QA |
| 6 | Researcher (round 2) | OK | 14.74 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 0; warnings 0 |
| 7 | QA (round 2) | FAILED | 0.01 | - | QA call failed: output NOT reviewed by QA |
| 8 | Document Builder | OK | 24.65 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose NOT reviewed by QA; rounds: 1; notes: 2 in (2 mandatory, verbatim) -> 2 in the report |
| 9 | Prose QA (round 1) | FAILED | 0.01 | - | prose QA call failed: prose NOT reviewed by QA |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Warnings

- QA round 1: QA call failed: output NOT reviewed by QA
- QA round 2: QA call failed: output NOT reviewed by QA
- Document Builder: report prose NOT reviewed by QA (prose QA call failed: prose NOT reviewed by QA)

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.04 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20674 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 2 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (44.09 s)

Problems:
- caveats[0].note contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- gaps[0].text contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- source_id: square brackets removed around 8 evidence ID(s) (classification, tariff, origin_rule, origin_result, estimated_saving, caveats[0], caveats[1], gaps[0])

### 5. QA (round 1): FAILED

QA call failed: output NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~8m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201821135}, 'execution_id': 'ae32550c-d25e-4047-ba8e-32152301707c'} (router cooldown, no model tried) -> gave up: router busy for ~473s (> 90s cap)

### 6. Researcher (round 2): OK

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 0 | warnings 0

Corrections sent (one shared revision):
- caveats[0].note contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- gaps[0].text contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (14.73 s)

### 7. QA (round 2): FAILED

QA call failed: output NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~8m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201821135}, 'execution_id': 'ee796f4d-d200-433b-ae6d-c7906e433883'} (router cooldown, no model tried) -> gave up: router busy for ~458s (> 90s cap)

### 8. Document Builder: OK

LLM prose passed the code checks; prose NOT reviewed by QA | rounds: 1 | notes: 2 in (2 mandatory, verbatim) -> 2 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (24.64 s)

### 9. Prose QA (round 1): FAILED

prose QA call failed: prose NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~7m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201821135}, 'execution_id': 'b2131a2b-c83b-4ceb-ad99-6a7837ade881'} (router cooldown, no model tried) -> gave up: router busy for ~434s (> 90s cap)

### 10. Report check: OK

0 problem(s), 0 warning(s)
