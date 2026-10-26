# Mansha run: REPORT (ELIGIBLE)

- **Message:** We fabricate steel building structures in Abu Dhabi from imported steel H-sections and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 101.43 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.18 | groq/openai/gpt-oss-120b | product='steel building structures'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-73089090; bill of materials: given; evidence 19653 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 52.87 | openrouter/dots-studio/dots-3-note-preview:free | line 73089090 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 2.14 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Document Builder | OK | 44.22 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 11 in (10 mandatory, verbatim) -> 11 in the report |
| 7 | Prose QA (round 1) | OK | 1.02 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='steel building structures' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.18 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-73089090 | bill of materials: given | evidence 19653 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:73089090 RULE_FOUND; TOOL:origin:73089090 MEETS; TOOL:duty:73089090 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 73089090 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (52.85 s)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.29 s)
- served by cerebras/gpt-oss-120b (0.84 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.29 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.84 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 11 in (10 mandatory, verbatim) -> 11 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (44.21 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.02 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
