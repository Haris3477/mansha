# Mansha run: REPORT (REGULATORY_GAP_DETECTED)

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 115.83 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.07 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20945 chars, 31 IDs |
| 4 | Researcher (round 1) | OK | 72.16 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 1.54 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Researcher (round 2) | OK | 11.32 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 0.89 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 8 | Document Builder | OK | 28.13 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 2 in (2 mandatory, verbatim) -> 2 in the report |
| 9 | Prose QA (round 1) | OK | 0.72 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.04 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20945 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): OK

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (72.15 s)

Normalized by code:
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "No tariff line in the sources matches the whole description 'wooden doors'; the closest lines are 'Doors, windows and their frames and thresholds for doors (aluminium)' and 'Other wooden furniture'."
- caveats: note written from TOOL:tariff_lookup: "No tariff line in Mansha's sources matches the whole description 'wooden doors': the closest lines are 'Doors, windows and their frames and thresholds for doors (aluminium)' and 'Other wooden furniture'."
- follow_up_questions: emptied for a gap (2 item(s); no line, so nothing to claim or supply)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (1.53 s)

Problems:
- gaps[0].text: Contains an unsupported inference that the product may fall under a different HS code, which is not stated in the cited record. Fix: No tariff line in the evidence matches the product description 'wooden doors'. The candidate lines are for aluminium doors and other wooden furniture, neither of which describes wooden doors. Therefore, the classification is a regulatory gap. Cite TOOL:tariff_lookup in source_id, not in the text.

### 6. Researcher (round 2): OK

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: gaps[0].text: Contains an unsupported inference that the product may fall under a different HS code, which is not stated in the cited record. Fix: No tariff line in the evidence matches the product description 'wooden doors'. The candidate lines are for aluminium doors and other wooden furniture, neither of which describes wooden doors. Therefore, the classification is a regulatory gap. Cite TOOL:tariff_lookup in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (11.32 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.88 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 2 in (2 mandatory, verbatim) -> 2 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (28.13 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.72 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
