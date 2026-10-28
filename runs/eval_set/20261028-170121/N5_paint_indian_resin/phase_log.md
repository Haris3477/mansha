# Mansha run: REPORT (ELIGIBLE)

- **Message:** We make acrylic paint in Ajman from resin bought in India and imported pigments, and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 169.31 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.28 | groq/openai/gpt-oss-120b | product='acrylic paint'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-32091010; bill of materials: given; evidence 19350 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 107.42 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 4.01 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 55.29 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 16 in (12 mandatory, verbatim) -> 14 in the report; summary cautions (code): INDIAN_INPUTS |
| 7 | Prose QA (round 1) | OK | 1.31 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='acrylic paint' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.24 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-32091010 | bill of materials: given | evidence 19350 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:32091010 RULE_FOUND; TOOL:origin:32091010 MEETS; TOOL:duty:32091010 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (107.41 s)

Normalized by code:
- caveats[13]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.69 s)
- served by cerebras/gpt-oss-120b (1.07 s)
- served by cerebras/gpt-oss-120b (1.23 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.69 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.07 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.23 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 16 in (12 mandatory, verbatim) -> 14 in the report | summary cautions (code): INDIAN_INPUTS

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (55.28 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.31 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
