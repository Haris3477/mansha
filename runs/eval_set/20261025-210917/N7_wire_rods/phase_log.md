# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We melt imported aluminium ingots, cast them and roll them into aluminium wire rods in Abu Dhabi, for export to India. The shipment is worth AED 100,000.
- **Total time:** 115.54 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.18 | groq/openai/gpt-oss-120b | product='aluminium wire rods'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76041010, TL-IN-76101000, TL-IN-76151030; bill of materials: given; evidence 24168 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 16.33 | google/gemini-3.6-flash | line 76041010 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 0.91 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 36.27 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 2 in (2 mandatory, verbatim) -> 2 in the report |
| 7 | Prose QA (round 1) | OK | 0.85 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium wire rods' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.18 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76041010, TL-IN-76101000, TL-IN-76151030 | bill of materials: given | evidence 24168 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 FAILS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 FAILS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 FAILS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76041010 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by google/gemini-3.6-flash (16.32 s)

Normalized by code:
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76041010): 'India charges duty on the assessable (CIF) value at import, so actual duty amounts will differ.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76041010): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, Social Welfare Surcharge, and any anti-dumping or safeguard duty still apply.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.9 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 2 in (2 mandatory, verbatim) -> 2 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (36.26 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.85 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
