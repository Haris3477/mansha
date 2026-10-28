# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 173.61 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.44 | groq/openai/gpt-oss-120b | product='hardwood bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19431 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 83.58 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 5.22 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 80.98 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 16 in (11 mandatory, verbatim) -> 13 in the report; summary cautions (code): FREE_ZONE |
| 7 | Prose QA (round 1) | OK | 2.38 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='hardwood bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.44 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19431 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (83.57 s)

Normalized by code:
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm the HS code for hardwood bedroom furniture is 94036000.'
- follow_up_questions[0]: free-zone question dropped, the user already said the factory is in a free zone: 'Is the manufacturing facility located in a free zone? This affects eligibility for factory registration required for the certificate of origin.'
- procedure: 8 step(s) written by code from the knowledge base
- caveats[6]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.48 s)
- served by cerebras/gpt-oss-120b (2.91 s)
- served by cerebras/gpt-oss-120b (0.81 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.48 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (2.91 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.81 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 16 in (11 mandatory, verbatim) -> 13 in the report | summary cautions (code): FREE_ZONE

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (80.97 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (2.38 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
