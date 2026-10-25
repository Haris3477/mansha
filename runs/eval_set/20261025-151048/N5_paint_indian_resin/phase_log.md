# Mansha run: REPORT (ELIGIBLE)

- **Message:** We make acrylic paint in Ajman from resin bought in India and imported pigments, and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 202.7 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.37 | groq/openai/gpt-oss-120b | product='acrylic paint (resin)'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-32091010; bill of materials: given; evidence 19621 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 92.05 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 1 |
| 5 | QA (round 1) | OK | 2.02 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 1 (0 real); 2 parts |
| 6 | Document Builder | OK | 46.48 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 14 in (11 mandatory, verbatim) -> 13 in the report |
| 7 | Prose QA (round 1) | OK | 0.77 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='acrylic paint (resin)' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.37 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-32091010 | bill of materials: given | evidence 19621 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:32091010 RULE_FOUND; TOOL:origin:32091010 MEETS; TOOL:duty:32091010 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 1

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (92.04 s)

Code warnings (for QA):
- caveats[0]: number(s) ['40'] not found in TOOL:rule_lookup:32091010

Normalized by code:
- caveats[10]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- caveats[7]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 1 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.08 s)
- served by cerebras/gpt-oss-120b (0.92 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.08 s); code warnings W1
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.92 s)

Code warnings judged by QA:
- W1 NOISE: caveats[0]: number(s) ['40'] not found in TOOL:rule_lookup:32091010 -> Number 40 is present in the rule string of TOOL:rule_lookup

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 14 in (11 mandatory, verbatim) -> 13 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (46.48 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.77 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
