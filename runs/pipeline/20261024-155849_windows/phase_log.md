# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 297.11 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.1 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 101.37 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.01 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | OK | 31.96 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 2.3 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 8 | Document Builder | OK | 96.25 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 13 in (11 mandatory, verbatim) -> 13 in the report |
| 9 | Prose QA (round 1) | OK | 1.12 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.04 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (101.36 s)

Normalized by code:
- origin_result.basis: check names written in plain words

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.09 s)
- served by cerebras/gpt-oss-120b (1.89 s)

Problems:
- caveats[7].note: Qualifier "Inference" was omitted, turning an inference into a definitive statement. Fix: Inference: SWS is charged on the reduced BCD (no CEPA-specific text found). Cite P-IN-DUTY-SCOPE in source_id, not in the text.
- caveats[8].note: Qualifier "Inference" was omitted, turning an inference into a definitive statement. Fix: Inference: Anti-dumping and safeguard duties still apply (no exemption found). Cite P-IN-DUTY-SCOPE in source_id, not in the text.
- caveats[9].note: Incorrect source name "CBIT" and added detail not present in the record. Fix: Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system, but this is unconfirmed and seen only in secondary sources. Cite P-IN-IMPORTER in source_id, not in the text.

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.09 s)
- part 2/2: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.89 s)

### 6. Researcher (round 2): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: caveats[7].note: Qualifier "Inference" was omitted, turning an inference into a definitive statement. Fix: Inference: SWS is charged on the reduced BCD (no CEPA-specific text found). Cite P-IN-DUTY-SCOPE in source_id, not in the text.
- QA: caveats[8].note: Qualifier "Inference" was omitted, turning an inference into a definitive statement. Fix: Inference: Anti-dumping and safeguard duties still apply (no exemption found). Cite P-IN-DUTY-SCOPE in source_id, not in the text.
- QA: caveats[9].note: Incorrect source name "CBIT" and added detail not present in the record. Fix: Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system, but this is unconfirmed and seen only in secondary sources. Cite P-IN-IMPORTER in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (31.95 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.05 s)
- served by cerebras/gpt-oss-120b (1.23 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.05 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.23 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 13 in (11 mandatory, verbatim) -> 13 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (96.25 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.12 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
