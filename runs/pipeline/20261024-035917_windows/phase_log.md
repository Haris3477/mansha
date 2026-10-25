# Mansha run: CHECKS_FAILED

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 206.88 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 43.49 | google/gemini-3.7-flash | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 138.76 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 2.41 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | OK | 19.96 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (None); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 2.25 | cerebras/gpt-oss-120b | REJECTED; factuality 1, completeness 1, formatting_safety 0; code warnings judged: 0 (0 real); 2 parts |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by google/gemini-3.7-flash (43.46 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (138.76 s)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.36 s)
- served by cerebras/gpt-oss-120b (1.03 s)

Problems:
- classification.confidence: Confidence level is not supported by any cited evidence. Fix: Remove the confidence field or set it to null.

Review split into parts (size limit):
- part 1/2: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.36 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.03 s)

### 6. Researcher (round 2): OK

line 76101000 (None) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: classification.confidence: Confidence level is not supported by any cited evidence. Fix: Remove the confidence field or set it to null.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (19.96 s)

Normalized by code:
- caveats[0]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): REJECTED

REJECTED | factuality 1, completeness 1, formatting_safety 0 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.21 s)
- served by cerebras/gpt-oss-120b (1.03 s)

Problems:
- origin_result.basis: Contains internal field names (e.g., 'final_manufacture_in_uae') which should not be shown to the exporter. Fix: The final manufacture took place in the UAE; the manufacturing goes beyond the minimal operations of Art. 3.5.1; all three non‑originating inputs are classified outside subheading 761010; the value‑addition build‑down is 49.0% against the 45% threshold on an FOB basis. Cite TOOL:origin:76101000 in source_id, not in the text.

Review split into parts (size limit):
- part 1/2: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.21 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.03 s)
