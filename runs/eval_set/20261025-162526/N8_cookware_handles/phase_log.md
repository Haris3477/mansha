# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We press aluminium cookware in Dubai from imported aluminium sheet and fit imported handles, for export to India. The shipment is worth AED 100,000.
- **Total time:** 93.75 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.64 | groq/openai/gpt-oss-120b | product='aluminium cookware'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76151030, TL-IN-76041010, TL-IN-76101000; bill of materials: given; evidence 24271 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 36.25 | openrouter/dots-studio/dots-3-note-preview:free | line 76151030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 0.79 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 53.15 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 5 in (4 mandatory, verbatim) -> 5 in the report |
| 7 | Prose QA (round 1) | OK | 0.92 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium cookware' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.6 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76151030, TL-IN-76041010, TL-IN-76101000 | bill of materials: given | evidence 24271 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 FAILS; TOOL:duty:76151030 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76151030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (36.23 s)

Normalized by code:
- caveats[5]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76151030): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76151030): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, SWS and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76151030): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.78 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 5 in (4 mandatory, verbatim) -> 5 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (53.14 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.92 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
