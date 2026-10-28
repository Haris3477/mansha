# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 153.5 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.43 | groq/openai/gpt-oss-120b | product='hardwood bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19431 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 60.1 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.09 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 83.26 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 13 in (10 mandatory, verbatim) -> 12 in the report; summary cautions (code): FREE_ZONE |
| 7 | Prose QA (round 1) | OK | 5.62 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='hardwood bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.38 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19431 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (60.09 s)

Normalized by code:
- origin_result.basis: check names written in plain words
- caveats[8]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- procedure: 8 step(s) written by code from the knowledge base
- caveats[9]: restated P-AGR-RECORDS-VERIFICATION step cut to its KB note
- caveats[11]: restated P-MOET-COO-INDIA step cut to its KB note
- caveats[12]: dropped, it restates the checklist step from P-AGR-3.17-APPLICATION: 'The issuing authority may apply risk management, including asking for detailed c'
- caveats[10]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.51 s)
- served by cerebras/gpt-oss-120b (0.95 s)
- served by cerebras/gpt-oss-120b (0.62 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.51 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.95 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.62 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 13 in (10 mandatory, verbatim) -> 12 in the report | summary cautions (code): FREE_ZONE

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (83.25 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (5.62 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
