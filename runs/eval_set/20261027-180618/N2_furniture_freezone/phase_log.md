# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 204.06 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.3 | groq/openai/gpt-oss-120b | product='hardwood bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19601 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 176.64 | google/gemini-3.6-flash | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 2.45 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Document Builder | OK | 21.0 | google/gemini-3.6-flash | LLM prose passed the code checks; prose QA approved; rounds: 2; notes: 7 in (6 mandatory, verbatim) -> 7 in the report; summary cautions (code): FREE_ZONE |
| 7 | Prose QA (round 1) | REJECTED | 1.63 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1 |
| 8 | Prose QA (round 2) | OK | 1.02 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 9 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='hardwood bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.3 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19601 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by google/gemini-3.6-flash (176.64 s)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.72 s)
- served by cerebras/gpt-oss-120b (0.72 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.72 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.72 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 2 | notes: 7 in (6 mandatory, verbatim) -> 7 in the report | summary cautions (code): FREE_ZONE

Corrections sent (one shared revision):
- QA: summary: Contains the sentence 'Please follow the checklist below to claim this preferential rate.' which is advice not present in FACTS or notes. Fix: Your hardwood bedroom furniture qualifies for the reduced duty rate under the India-UAE CEPA because it meets the required rule of origin. This gives an estimated duty saving of 7500.00 AED on your shipment to India. (see FACTS)

LLM calls:
- served by google/gemini-3.6-flash (13.23 s)
- served by google/gemini-3.6-flash (7.76 s)

### 7. Prose QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.63 s)

Problems:
- summary: Contains the sentence 'Please follow the checklist below to claim this preferential rate.' which is advice not present in FACTS or notes. Fix: Your hardwood bedroom furniture qualifies for the reduced duty rate under the India-UAE CEPA because it meets the required rule of origin. This gives an estimated duty saving of 7500.00 AED on your shipment to India. (see FACTS)

### 8. Prose QA (round 2): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.02 s)

### 9. Report check: OK

0 problem(s), 0 warning(s)
