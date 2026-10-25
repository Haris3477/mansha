# Mansha run: REPORT (ELIGIBLE)

- **Message:** We are a bakery in Sharjah. We bake sweet biscuits from imported flour, sugar and butter and want to export them to India. The shipment is worth USD 27,000.
- **Total time:** 175.55 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 5.43 | groq/openai/gpt-oss-120b | product='sweet biscuits'; destination='India'; role=manufacturer; value=27000 USD; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-19053100; bill of materials: given; evidence 19624 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 123.77 | openrouter/dots-studio/dots-3-note-preview:free | line 19053100 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.39 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 42.03 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 13 in (10 mandatory, verbatim) -> 12 in the report |
| 7 | Prose QA (round 1) | OK | 0.92 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='sweet biscuits' | destination='India' | role=manufacturer | value=27000 USD | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (5.43 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-19053100 | bill of materials: given | evidence 19624 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:19053100 RULE_FOUND; TOOL:origin:19053100 MEETS; TOOL:duty:19053100 ESTIMATED; TOOL:coo_fee CURRENCY_NOT_AED

### 4. Researcher (round 1): OK

line 19053100 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (123.76 s)

Normalized by code:
- origin_result.basis: check names written in plain words
- caveats[6]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.75 s)
- served by cerebras/gpt-oss-120b (0.98 s)
- served by cerebras/gpt-oss-120b (0.64 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.75 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.98 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.64 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 13 in (10 mandatory, verbatim) -> 12 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (42.02 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.92 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
