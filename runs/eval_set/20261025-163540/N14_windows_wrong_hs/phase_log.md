# Mansha run: CHECKS_FAILED

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames, HS code 39239090, and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 78.3 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 11.23 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-39239090; bill of materials: given; evidence 18305 chars, 23 IDs |
| 4 | Researcher (round 1) | FAILED | 34.0 | openrouter/dots-studio/dots-3-note-preview:free | line 39239090 (low); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 2; warnings 1 |
| 5 | QA (round 1) | REJECTED | 1.35 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 1 (0 real) |
| 6 | Researcher (round 2) | FAILED | 31.71 | openrouter/dots-studio/dots-3-note-preview:free | line None (None); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 2; warnings 1 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (11.23 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-39239090 | bill of materials: given | evidence 18305 chars, 23 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:duty:39239090 NO_PREFERENCE; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 39239090 (low) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 2 | warnings 1

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (34.0 s)

Problems:
- caveats[0].note contains 'TL-IN-76101000,': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- gaps[0].text contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Code warnings (for QA):
- caveats[0]: number(s) ['3923'] not found in TOOL:tariff_lookup

Normalized by code:
- follow_up_questions: dropped for verdict NO_PREFERENCE (the result does not depend on more information from the user): 'The HS code 39239090 corresponds to plastic articles for packing, not aluminium window frames. Please confirm whether the product description or the HS code is correct.'
- caveats: dropped a note about claiming the CEPA rate for verdict NO_PREFERENCE (TOOL:duty:39239090): 'India charges duty on the assessable (CIF) value at import, so actual duty amounts will differ from the estimate based on the shipment value given.'
- caveats: dropped a note about claiming the CEPA rate for verdict NO_PREFERENCE (P-IN-DUTY-SCOPE): 'The CEPA rate reduces Basic Customs Duty (and the Agriculture Infrastructure and Development Cess only for lines in Table II). IGST, GST compensation cess, the Social Welfare Surcharge, and any anti-dumping, countervailing or safeguard duties still apply.'

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 1 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (1.35 s)

Problems:
- classification: The classification lists tariff line 39239090, which does not match the product description of aluminium window frames. Fix: No suitable tariff line identified for aluminium window frames; classification fields should be null or omitted. Keep this field's source_id as it is.

Code warnings judged by QA:
- W1 NOISE: caveats[0]: number(s) ['3923'] not found in TOOL:tariff_lookup -> Number 3923 is present in the tariff line description.

### 6. Researcher (round 2): FAILED

line None (None) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 2 | warnings 1

Corrections sent (one shared revision):
- caveats[0].note contains 'TL-IN-76101000,': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- gaps[0].text contains 'TL-IN-76101000': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- QA: classification: The classification lists tariff line 39239090, which does not match the product description of aluminium window frames. Fix: No suitable tariff line identified for aluminium window frames; classification fields should be null or omitted. Keep this field's source_id as it is.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (31.7 s)

Problems:
- classification.confidence must be one of high, medium, low (got None): judge it from how well the description matches
- classification.tariff_line None does not match its source TL-IN-39239090 (line 39239090)

Code warnings (for QA):
- caveats[0]: number(s) ['3923'] not found in TOOL:tariff_lookup

### 7. QA (round 2): SKIPPED

not run: code checks still fail
