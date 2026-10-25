# Mansha run: CHECKS_FAILED

- **Message:** نصنع إطارات نوافذ من الألمنيوم في الشارقة من مقاطع ألمنيوم مستوردة ونريد تصديرها إلى الهند. قيمة الشحنة ١٠٠٬٠٠٠ درهم.
- **Total time:** 234.25 s | **language:** ar

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.18 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=ar |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22912 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 110.37 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 1; warnings 0 |
| 5 | QA (round 1) | OVERRULED | 4.78 | cerebras/gpt-oss-120b | OVERRULED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 correction(s) overruled by the KB, after a re-judge; 3 parts |
| 6 | Researcher (round 2) | OK | 29.08 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 88.84 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 correction(s) overruled by the KB, after a re-judge; 3 parts |

## Warnings

- QA round 1: rejection overruled by the KB (every correction dropped a qualifier its record's note carries, or rejected the record's own note: caveats[7].note, caveats[7].note)

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=ar

LLM calls:
- served by groq/openai/gpt-oss-120b (1.18 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22912 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (110.36 s)

Problems:
- origin_result.basis contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- caveats[14]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions[2]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm the HS code for aluminium window frames (likely 76101000) to ensure correct classification.'

### 5. QA (round 1): OVERRULED

OVERRULED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 correction(s) overruled by the KB, after a re-judge | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (0.84 s)
- served by cerebras/gpt-oss-120b (1.86 s)
- served by cerebras/gpt-oss-120b (1.41 s)
- served by cerebras/gpt-oss-120b (0.65 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.84 s)
- part 2/3: steps and notes: OVERRULED, served by cerebras/gpt-oss-120b (3.27 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.65 s)

QA corrections overruled by the KB (not sent to the Researcher):
- caveats[7].note: fix "Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text." rejects text that is P-IN-IMPORTER's own KB note "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."
- caveats[7].note: fix "Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text." rejects text that is P-IN-IMPORTER's own KB note "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."

### 6. Researcher (round 2): OK

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

Corrections sent (one shared revision):
- origin_result.basis contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (29.06 s)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 correction(s) overruled by the KB, after a re-judge | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.32 s); attempts: #1 (waited 27.1 s for the per-minute limit) cerebras/gpt-oss-120b 1.32 s OK
- served by cerebras/gpt-oss-120b (1.25 s); attempts: #1 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '3929e84d-1bd4-4bc4-b94e-ccdaddc0c375'} -> waited 30 s | #2 cerebras/gpt-oss-120b 1.25 s OK
- served by cerebras/gpt-oss-120b (1.47 s)
- served by cerebras/gpt-oss-120b (0.68 s); attempts: #1 (waited 26.9 s for the per-minute limit) cerebras/gpt-oss-120b 0.68 s OK

Problems:
- origin_result.basis: Adds an unsupported definition of CTSH as "change in tariff heading" without qualifier. Fix: The product-specific rule requires CTSH and at least 45% value addition. No checks have been performed because the necessary data is missing: a bill of materials (each input's description, 6-digit HS code, origin country, value and currency) and a declaration stating the product price, whether it is FOB or Ex-Works, that the final manufacture occurred in the UAE, and the operations done in the UAE. Keep this field's source_id as it is.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.32 s)
- part 2/3: steps and notes: OVERRULED, served by cerebras/gpt-oss-120b (2.72 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.68 s)

QA corrections overruled by the KB (not sent to the Researcher):
- caveats[7].note: fix "Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system (unconfirmed: seen only in secondary sources)." rejects text that is P-IN-IMPORTER's own KB note "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."
- caveats[7].note: fix "Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system (unconfirmed: seen only in secondary sources)." rejects text that is P-IN-IMPORTER's own KB note "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."
