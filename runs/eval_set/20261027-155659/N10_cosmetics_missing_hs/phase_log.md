# Mansha run: CHECKS_FAILED

- **Message:** We make cosmetic skin creams in Dubai and want to export them to India. The shipment is worth AED 60,000. Our bill of materials is attached.
- **Total time:** 176.74 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.21 | groq/openai/gpt-oss-120b | product='cosmetic skin creams'; destination='India'; role=manufacturer; value=60000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-33049990; bill of materials: given; evidence 18964 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 75.61 | openrouter/dots-studio/dots-3-note-preview:free | line 33049990 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 2 |
| 5 | QA (round 1) | REJECTED | 4.25 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 2 (2 real); 3 parts |
| 6 | Researcher (round 2) | FAILED | 95.67 | openrouter/dots-studio/dots-3-note-preview:free | line 33049990 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 1; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='cosmetic skin creams' | destination='India' | role=manufacturer | value=60000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.21 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-33049990 | bill of materials: given | evidence 18964 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:33049990 RULE_FOUND; TOOL:origin:33049990 INSUFFICIENT_DATA; TOOL:duty:33049990 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 33049990 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 2

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (75.59 s)

Code warnings (for QA):
- caveats[0]: number(s) ['40'] not found in TOOL:rule_lookup:33049990
- procedure[3]: names 'Ministry of Foreign Trade', which P-AGR-COO-RULES does not; cite the record that states it, or split the step

Normalized by code:
- caveats[8]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- caveats[9]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 2 (2 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.88 s)
- served by cerebras/gpt-oss-120b (1.55 s)
- served by cerebras/gpt-oss-120b (0.8 s)

Problems:
- origin_result.basis: Includes 'possibly other non-originating inputs' not mentioned in the cited record Fix: Missing 6-digit HS code for Emollients (BOM row 2); no checks run. Keep this field's source_id as it is.
- follow_up_questions[0]: Asks for HS codes for other non-originating inputs not required by the cited record Fix: Provide the 6-digit HS code for Emollients (BOM row 2) as required by the origin rule. Cite TOOL:origin:33049990 in source_id, not in the text.
- procedure[3].step: Adds '(the Ministry of Foreign Trade)' which is not in the cited record Fix: The certificate must be issued before, at, or within 5 working days of export. It is valid for 12 months from issue and covers one import. It must bear the authorised signature and official seal of the competent authority. Cite P-AGR-COO-RULES in source_id, not in the text.
- caveats[0].note: The note includes the specific rule 'CTSH + VA 40%' which is not present in the cited record. Fix: The '+' in the rule is interpreted as 'and' (both tests must pass); the agreement does not define '+'. Cite TOOL:rule_lookup:33049990 in source_id, not in the text.
- caveats[13].note: The note adds an unsupported claim about Mansha not performing currency conversion. Fix: Certificate fee bands are in AED and apply to the invoice value in AED. Cite TOOL:coo_fee in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.88 s); code warnings W2
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.55 s); code warnings W1
- part 3/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (0.8 s)

Code warnings judged by QA:
- W2 REAL: procedure[3]: names 'Ministry of Foreign Trade', which P-AGR-COO-RULES does not; cite the record that states it, or split the step -> Procedure step cites 'Ministry of Foreign Trade' which is not in the source record
- W1 REAL: caveats[0]: number(s) ['40'] not found in TOOL:rule_lookup:33049990 -> The cited rule_lookup record does not contain the number '40', so the note references unsupported information.

### 6. Researcher (round 2): FAILED

line 33049990 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 1 | warnings 0

Corrections sent (one shared revision):
- QA: origin_result.basis: Includes 'possibly other non-originating inputs' not mentioned in the cited record Fix: Missing 6-digit HS code for Emollients (BOM row 2); no checks run. Keep this field's source_id as it is.
- QA: follow_up_questions[0]: Asks for HS codes for other non-originating inputs not required by the cited record Fix: Provide the 6-digit HS code for Emollients (BOM row 2) as required by the origin rule. Cite TOOL:origin:33049990 in source_id, not in the text.
- QA: procedure[3].step: Adds '(the Ministry of Foreign Trade)' which is not in the cited record Fix: The certificate must be issued before, at, or within 5 working days of export. It is valid for 12 months from issue and covers one import. It must bear the authorised signature and official seal of the competent authority. Cite P-AGR-COO-RULES in source_id, not in the text.
- QA: caveats[0].note: The note includes the specific rule 'CTSH + VA 40%' which is not present in the cited record. Fix: The '+' in the rule is interpreted as 'and' (both tests must pass); the agreement does not define '+'. Cite TOOL:rule_lookup:33049990 in source_id, not in the text.
- QA: caveats[13].note: The note adds an unsupported claim about Mansha not performing currency conversion. Fix: Certificate fee bands are in AED and apply to the invoice value in AED. Cite TOOL:coo_fee in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (95.66 s)

Problems:
- follow_up_questions[0] contains "TOOL:origin:33049990'}": this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

### 7. QA (round 2): SKIPPED

not run: code checks still fail
