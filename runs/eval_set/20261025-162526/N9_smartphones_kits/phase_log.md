# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We assemble smartphones in Dubai from imported kits, HS code 8517 12 11, and want to export them to India. The shipment is worth AED 90,000.
- **Total time:** 120.1 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 3.36 | groq/openai/gpt-oss-120b | product='smartphones'; destination='India'; role=manufacturer; value=90000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85171300; bill of materials: given; evidence 20099 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 49.67 | openrouter/dots-studio/dots-3-note-preview:free | line 85171300 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 1.17 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 65.03 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 4 in (3 mandatory, verbatim) -> 4 in the report |
| 7 | Prose QA (round 1) | OK | 0.87 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='smartphones' | destination='India' | role=manufacturer | value=90000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (3.36 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85171300 | bill of materials: given | evidence 20099 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85171300 RULE_FOUND; TOOL:origin:85171300 FAILS; TOOL:duty:85171300 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85171300 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (49.66 s)

Normalized by code:
- caveats[6]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): "The duty estimate is based on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, SWS and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (1.16 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 4 in (3 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (65.03 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.87 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
