# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We assemble smartphones in Dubai from imported kits, HS code 8517 12 11, and want to export them to India. The shipment is worth AED 90,000.
- **Total time:** 174.06 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.17 | groq/openai/gpt-oss-120b | product='smartphones'; destination='India'; role=manufacturer; value=90000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85171300; bill of materials: given; evidence 19949 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 78.07 | openrouter/dots-studio/dots-3-note-preview:free | line 85171300 (medium); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | FAILED | 12.13 | - | QA call failed: output NOT reviewed by QA |
| 6 | Document Builder | OK | 82.66 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose NOT reviewed by QA; rounds: 1; notes: 7 in (5 mandatory, verbatim) -> 7 in the report |
| 7 | Prose QA (round 1) | FAILED | 0.03 | - | prose QA call failed: prose NOT reviewed by QA |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Warnings

- QA round 1: QA call failed: output NOT reviewed by QA
- Document Builder: report prose NOT reviewed by QA (prose QA call failed: prose NOT reviewed by QA)

## Phase details

### 1. Intake: OK

product='smartphones' | destination='India' | role=manufacturer | value=90000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.17 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85171300 | bill of materials: given | evidence 19949 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85171300 RULE_FOUND; TOOL:origin:85171300 FAILS; TOOL:duty:85171300 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85171300 (medium) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (78.05 s)

Normalized by code:
- caveats[13]: note written from the KB (P-UAE-ISSUER)
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'The HS code you provided (85171211) is an older HS 2017 code; the current tariff line is 85171300. Please confirm that you want to use the current line.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge (SWS) and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'The Social Welfare Surcharge (SWS) is likely charged on the reduced BCD (no CEPA-specific text on it was found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'Anti-dumping and safeguard duties likely still apply (no CEPA exemption from them was found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-IMPORTER): "The certificate does not remove the importer's duty of reasonable care, so the UAE exporter may be asked for production and cost details."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-UAE-ISSUER): 'No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-COO-INDIA): 'Fee bands are in AED and apply to the invoice value in AED; no currency conversion is done by Mansha.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-FACTORY-REG): 'A producer in a free zone is likely not eligible for Factory Registration, because it requires a factory outside a free zone, and registration is needed before applying for the certificate of origin for India. Confirm with the Ministry of Economy and Tourism.'

### 5. QA (round 1): FAILED

QA call failed: output NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.03 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~11s.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201219751}, 'execution_id': 'd85e411d-1805-48ef-826a-0a1fe9f67050'} (router cooldown, no model tried) -> waited 11.7 s | #2 router 0.38 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models rate-limited after 1 attempt. Soonest cooldown reset ~10m. Attempt trail: cerebras/gpt-oss-120b key1: rate_limited. Last error: Cerebras API error 429: Too Many Requests', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201821135}, 'execution_id': '5188a20e-a4c2-49e7-8364-3b1fd9838886'} (router cooldown, no model tried) -> gave up: router busy for ~601s (> 90s cap)

### 6. Document Builder: OK

LLM prose passed the code checks; prose NOT reviewed by QA | rounds: 1 | notes: 7 in (5 mandatory, verbatim) -> 7 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (82.65 s)

### 7. Prose QA (round 1): FAILED

prose QA call failed: prose NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.03 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~9m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1793201821135}, 'execution_id': 'c0409807-bf06-4676-85da-91c3e1c650a4'} (router cooldown, no model tried) -> gave up: router busy for ~518s (> 90s cap)

### 8. Report check: OK

0 problem(s), 0 warning(s)
