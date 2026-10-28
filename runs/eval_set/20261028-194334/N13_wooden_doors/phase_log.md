# Mansha run: CHECKS_FAILED

- **Message:** We make wooden doors in Ras Al Khaimah for India.
- **Total time:** 205.73 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.19 | groq/openai/gpt-oss-120b | product='wooden doors'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-94036000; bill of materials: not given; evidence 20945 chars, 31 IDs |
| 4 | Researcher (round 1) | FAILED | 151.36 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (low); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 1; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.19 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | FAILED | 49.98 | openrouter/dots-studio/dots-3-note-preview:free | line REGULATORY_GAP_DETECTED (REGULATORY_GAP_DETECTED); origin NEEDS_MORE_DATA; verdict REGULATORY_GAP_DETECTED; problems 3; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='wooden doors' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.19 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-94036000 | bill of materials: not given | evidence 20945 chars, 31 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 INSUFFICIENT_DATA; TOOL:duty:94036000 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

line 94036000 (low) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (151.35 s)

Problems:
- TOOL:tariff_lookup found no candidate that matches the whole product description (each matches different words), so none of them describes the product: set the classification values to REGULATORY_GAP_DETECTED and say in gaps that no tariff line in the evidence covers this product

Normalized by code:
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "No tariff line in the sources matches the whole description 'wooden doors'. The closest lines are 'Doors, windows and their frames and thresholds for doors (aluminium)' (76101000) which matches only 'door', and 'Other wooden furniture' (94036000) which matches only 'wooden'. The classification may be incorrect."
- caveats: note written from TOOL:tariff_lookup: "No tariff line in Mansha's sources matches the whole description 'wooden doors': the closest lines are 'Doors, windows and their frames and thresholds for doors (aluminium)' and 'Other wooden furniture'."
- caveats[6]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.67 s)
- served by cerebras/gpt-oss-120b (1.51 s)

Problems:
- caveats[5].note: The note includes an unsupported claim that value addition percentages are on an FOB basis, which is not present in the cited record. Fix: On an Ex-Works basis the threshold is 5 percentage points lower. Cite PSR-GEN-EXW in source_id, not in the text.

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.67 s)
- part 2/2: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.51 s)

### 6. Researcher (round 2): FAILED

line REGULATORY_GAP_DETECTED (REGULATORY_GAP_DETECTED) | origin NEEDS_MORE_DATA | verdict REGULATORY_GAP_DETECTED | problems 3 | warnings 0

Corrections sent (one shared revision):
- TOOL:tariff_lookup found no candidate that matches the whole product description (each matches different words), so none of them describes the product: set the classification values to REGULATORY_GAP_DETECTED and say in gaps that no tariff line in the evidence covers this product
- QA: caveats[5].note: The note includes an unsupported claim that value addition percentages are on an FOB basis, which is not present in the cited record. Fix: On an Ex-Works basis the threshold is 5 percentage points lower. Cite PSR-GEN-EXW in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (49.97 s)

Problems:
- origin_result.status is 'NEEDS_MORE_DATA' but must be 'REGULATORY_GAP_DETECTED' (no tariff line was chosen)
- estimated_saving.status is 'NEEDS_VALUE' but must be 'REGULATORY_GAP_DETECTED'
- procedure must be an empty list when the status is REGULATORY_GAP_DETECTED

Normalized by code:
- caveats[6]: note written from the KB (P-UAE-ISSUER)
- caveats: dropped a note on a line that was not chosen (TOOL:origin:94036000): "The '+' in the origin rule 'CTH + VA 40%' is read as 'and' (both tests must pass). The agreement does not define '+', so this is an interpretation."
- caveats: dropped a note on a line that was not chosen (TOOL:duty:94036000): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge (SWS) and any anti-dumping or safeguard duty still apply.'

### 7. QA (round 2): SKIPPED

not run: code checks still fail
