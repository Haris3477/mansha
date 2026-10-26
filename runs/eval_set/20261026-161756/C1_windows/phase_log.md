# Mansha run: CHECKS_FAILED

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 175.75 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.21 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 85.61 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.88 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | FAILED | 25.04 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.21 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (85.6 s)

Problems:
- caveats[3].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- caveats[10]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)
- caveats[11]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm that HS code 76101000 (doors, windows and their frames and thresholds for doors (aluminium)) is the correct classification for your aluminium window frames.'
- caveats[5]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.2 s)
- served by cerebras/gpt-oss-120b (1.55 s)
- served by cerebras/gpt-oss-120b (1.12 s)

Problems:
- caveats[7].note: The note adds qualifiers "reportedly" and "but this is unconfirmed" which are not present in the cited record. Fix: Electronic certificates are accepted and uploaded to India's e-Sanchit system, and this comes from CBIC Instruction 28/2022 read only through secondary reports. Cite P-IN-IMPORTER in source_id, not in the text.
- caveats[14].note: The note adds an unsupported qualifier about the retrospective issuance remark that is not present in the cited record. Fix: The agreement says box 8, but India's origin rules and certificate form say box 9; India's form governs entry into India. Cite P-AGR-COO-RULES in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.2 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.55 s)
- part 3/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.12 s)

### 6. Researcher (round 2): FAILED

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

Corrections sent (one shared revision):
- caveats[3].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- QA: caveats[7].note: The note adds qualifiers "reportedly" and "but this is unconfirmed" which are not present in the cited record. Fix: Electronic certificates are accepted and uploaded to India's e-Sanchit system, and this comes from CBIC Instruction 28/2022 read only through secondary reports. Cite P-IN-IMPORTER in source_id, not in the text.
- QA: caveats[14].note: The note adds an unsupported qualifier about the retrospective issuance remark that is not present in the cited record. Fix: The agreement says box 8, but India's origin rules and certificate form say box 9; India's form governs entry into India. Cite P-AGR-COO-RULES in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (25.03 s)

Problems:
- caveats[7].note states as a plain fact what its cited record qualifies with 'reportedly' ('Electronic certificates are reportedly accepted and uploaded to e-Sanchit (unconfirmed: seen only in secondary sources).'): keep that qualifier in the text

### 7. QA (round 2): SKIPPED

not run: code checks still fail
