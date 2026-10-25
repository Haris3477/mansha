# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 245.65 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.07 | groq/openai/gpt-oss-120b | product='hardwood bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19694 chars, 26 IDs |
| 4 | Researcher (round 1) | FAILED | 60.23 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 5 | QA (round 1) | OK | 2.14 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | OK | 53.74 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 2.36 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 8 | Document Builder | OK | 64.19 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 15 in (10 mandatory, verbatim) -> 12 in the report |
| 9 | Prose QA (round 1) | OK | 1.92 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='hardwood bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.07 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19694 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (60.22 s)

Problems:
- caveats[0].note contains 'PSR-IN-R136': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- caveats[12]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)
- caveats[13]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.05 s)
- served by cerebras/gpt-oss-120b (1.07 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.05 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.07 s)

### 6. Researcher (round 2): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- caveats[0].note contains 'PSR-IN-R136': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (53.73 s)

Normalized by code:
- caveats[9]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.09 s)
- served by cerebras/gpt-oss-120b (1.25 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.09 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.25 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 15 in (10 mandatory, verbatim) -> 12 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (64.18 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.92 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
