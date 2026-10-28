# Mansha run: REPORT (REGULATORY_GAP_DETECTED)

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 108.62 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.16 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20945 chars, 31 IDs |
| 4 | Researcher (round 1) | FAILED | 44.33 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 2; warnings 0 |
| 5 | QA (round 1) | OK | 1.0 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Researcher (round 2) | OK | 20.51 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 0.73 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 8 | Document Builder | OK | 40.17 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 1 in (1 mandatory, verbatim) -> 1 in the report |
| 9 | Prose QA (round 1) | OK | 0.71 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.16 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20945 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 2 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (44.32 s)

Problems:
- origin_rule.source_id None is not an ID in the evidence
- estimated_saving.source_id None is not an ID in the evidence

Normalized by code:
- source_id: square brackets removed around 5 evidence ID(s) (classification, tariff, origin_result, caveats[0], gaps[0])
- follow_up_questions: emptied for a gap (2 item(s); no line, so nothing to claim or supply)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (1.0 s)

### 6. Researcher (round 2): OK

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 0 | warnings 0

Corrections sent (one shared revision):
- origin_rule.source_id None is not an ID in the evidence
- estimated_saving.source_id None is not an ID in the evidence

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (20.5 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.73 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 1 in (1 mandatory, verbatim) -> 1 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (40.16 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.71 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
