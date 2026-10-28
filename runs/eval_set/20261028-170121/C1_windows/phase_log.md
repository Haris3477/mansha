# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 303.48 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.08 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 23971 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 149.04 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.43 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | OK | 54.01 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 35.66 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 8 | Document Builder | OK | 58.98 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 13 in (10 mandatory, verbatim) -> 12 in the report |
| 9 | Prose QA (round 1) | OK | 1.29 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.08 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 23971 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (149.02 s)

Normalized by code:
- caveats[6]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm the HS code for aluminium window frames (we used 76101000).'
- caveats[8]: note written from the KB (P-UAE-ISSUER)
- follow_up_questions: dropped for verdict ELIGIBLE (the result does not depend on more information from the user): 'Is the factory located outside a free zone? Factory Registration, a prerequisite for the Certificate of Origin, requires the factory to be outside a free zone.'

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.22 s)
- served by cerebras/gpt-oss-120b (1.23 s)
- served by cerebras/gpt-oss-120b (0.96 s)

Problems:
- caveats[10].note: Includes an unsupported claim that no currency conversion is done by Mansha. Fix: The certificate fee estimate assumes the certificate's invoice value equals the shipment value given (100000 AED). Fee bands are in AED and apply to the invoice value in AED. Cite TOOL:coo_fee in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.22 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.23 s)
- part 3/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (0.96 s)

### 6. Researcher (round 2): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: caveats[10].note: Includes an unsupported claim that no currency conversion is done by Mansha. Fix: The certificate fee estimate assumes the certificate's invoice value equals the shipment value given (100000 AED). Fee bands are in AED and apply to the invoice value in AED. Cite TOOL:coo_fee in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (54.0 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.4 s)
- served by cerebras/gpt-oss-120b (1.38 s); attempts: #1 (waited 2.2 s for the per-minute limit) router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'f23adad2-8739-4216-be09-0d611b058c6c'} -> waited 30 s | #2 cerebras/gpt-oss-120b 1.38 s OK
- served by cerebras/gpt-oss-120b (0.66 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.4 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.38 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.66 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 13 in (10 mandatory, verbatim) -> 12 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (58.97 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.29 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
