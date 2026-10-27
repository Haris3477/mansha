# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 171.69 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.25 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 101.49 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 2.78 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Document Builder | OK | 63.93 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 14 in (10 mandatory, verbatim) -> 12 in the report |
| 7 | Prose QA (round 1) | OK | 1.23 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.25 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (101.49 s)

Normalized by code:
- caveats[12]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)
- caveats[13]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.39 s)
- served by cerebras/gpt-oss-120b (1.37 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.39 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.37 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 14 in (10 mandatory, verbatim) -> 12 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (63.92 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.23 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
