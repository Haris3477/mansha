# Mansha run: REPORT (REGULATORY_GAP_DETECTED)

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 88.15 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.14 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20945 chars, 31 IDs |
| 4 | Researcher (round 1) | OK | 32.91 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (low); origin REGULATORY_GAP_DETECTED; verdict REGULATORY_GAP_DETECTED; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 0.86 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 51.13 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 2; notes: 1 in (1 mandatory, verbatim) -> 1 in the report |
| 7 | Prose QA (round 1) | OK | 0.84 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Prose QA (round 2) | OK | 1.27 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 9 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.1 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20945 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): OK

line REGULATORY_GAP_DETECTED (low) | origin REGULATORY_GAP_DETECTED | verdict REGULATORY_GAP_DETECTED | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (32.91 s)

Normalized by code:
- source_id: square brackets removed around 8 evidence ID(s) (classification, tariff, origin_rule, origin_result, estimated_saving, caveats[0], caveats[1], gaps[0])
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "No candidate matches the whole description 'wooden doors': 'Doors, windows and their frames and thresholds for doors (aluminium)' matches only 'door', 'Other wooden furniture' matches only 'wooden'."
- caveats: note written from TOOL:tariff_lookup: "No tariff line in Mansha's sources matches the whole description 'wooden doors': the closest lines are 'Doors, windows and their frames and thresholds for doors (aluminium)' and 'Other wooden furniture'."
- caveats: dropped for a gap, no line was chosen (P-IN-DUTY-SCOPE): 'The CEPA rate reduces Basic Customs Duty (BCD) only; IGST, GST compensation cess, the Social Welfare Surcharge, and any anti-dumping or safeguard duty still apply.'
- tariff: written for a gap (was {'agreement': 'India-UAE CEPA', 'mfn_rate': 'REGULATORY_GAP_DETECTED', 'preferential_rate': 'REGULATORY_GAP_DETECTED', 'source_id': 'TOOL:tariff_lookup'})
- follow_up_questions: emptied for a gap (1 item(s); no line, so nothing to claim or supply)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.85 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 2 | notes: 1 in (1 mandatory, verbatim) -> 1 in the report

Corrections sent (one shared revision):
- `duty`: 'No duty' says all duty is removed, but the CEPA rate applies to Basic Customs Duty only; IGST and other import charges are still paid, so say the CEPA rate reduces (or removes) Basic Customs Duty, never all duty

Code check problems by round:
- round 1: `duty`: 'No duty' says all duty is removed, but the CEPA rate applies to Basic Customs Duty only; IGST and other import charges are still paid, so say the CEPA rate reduces (or removes) Basic Customs Duty, never all duty

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (30.18 s)
- served by openrouter/dots-studio/dots-3-note-preview:free (20.95 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.84 s)

### 8. Prose QA (round 2): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.27 s)

### 9. Report check: OK

0 problem(s), 0 warning(s)
