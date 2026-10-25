# Mansha run: REPORT (NEEDS_MORE_DATA)

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 203.94 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.15 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20704 chars, 31 IDs |
| 4 | Researcher (round 1) | OK | 102.75 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (medium); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 2.87 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Document Builder | OK | 36.19 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 14 in (8 mandatory, verbatim) -> 10 in the report |
| 7 | Prose QA (round 1) | OK | 0.98 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.11 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20704 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): OK

line 94036000 (medium) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (102.74 s)

Normalized by code:
- caveats[6]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm the HS code for wooden doors; the best match found is 94036000 (Other wooden furniture).'
- caveats[7]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.18 s)
- served by cerebras/gpt-oss-120b (0.95 s)
- served by cerebras/gpt-oss-120b (0.72 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.18 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.95 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.72 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 14 in (8 mandatory, verbatim) -> 10 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (36.19 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.98 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
