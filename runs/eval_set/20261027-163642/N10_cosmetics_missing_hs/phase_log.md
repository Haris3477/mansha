# Mansha run: CHECKS_FAILED

- **Message:** We make cosmetic skin creams in Dubai and want to export them to India. The shipment is worth AED 60,000. Our bill of materials is attached.
- **Total time:** 151.19 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.4 | groq/openai/gpt-oss-120b | product='cosmetic skin creams'; destination='India'; role=manufacturer; value=60000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-33049990; bill of materials: given; evidence 18964 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 85.69 | openrouter/dots-studio/dots-3-note-preview:free | line 33049990 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.22 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | OK | 25.64 | openrouter/dots-studio/dots-3-note-preview:free | line 33049990 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 35.25 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |

## Phase details

### 1. Intake: OK

product='cosmetic skin creams' | destination='India' | role=manufacturer | value=60000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.36 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-33049990 | bill of materials: given | evidence 18964 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:33049990 RULE_FOUND; TOOL:origin:33049990 INSUFFICIENT_DATA; TOOL:duty:33049990 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 33049990 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (85.68 s)

Normalized by code:
- caveats[11]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions[1]: HS-code confirmation dropped, the tariff lookup found no conflict: "No HS code was provided for the product; please confirm that HS code 33049990 ('Other beauty or make-up preparations') is correct for these cosmetic skin creams."
- caveats[5]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.25 s)
- served by cerebras/gpt-oss-120b (0.99 s)
- served by cerebras/gpt-oss-120b (0.97 s)

Problems:
- origin_result.basis: Includes unsupported inference about tariff‑shift and value‑addition tests not mentioned in the cited record. Fix: The origin tool returned INSUFFICIENT_DATA and missing the 6‑digit HS code for the non‑originating input 'Emollients' (BOM row 2). Keep this field's source_id as it is.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.25 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.99 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.97 s)

### 6. Researcher (round 2): OK

line 33049990 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: origin_result.basis: Includes unsupported inference about tariff‑shift and value‑addition tests not mentioned in the cited record. Fix: The origin tool returned INSUFFICIENT_DATA and missing the 6‑digit HS code for the non‑originating input 'Emollients' (BOM row 2). Keep this field's source_id as it is.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (25.62 s)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.9 s)
- served by cerebras/gpt-oss-120b (2.34 s); attempts: #1 (waited 30.2 s for the per-minute limit) cerebras/gpt-oss-120b 2.34 s OK
- served by cerebras/gpt-oss-120b (0.75 s)

Problems:
- procedure[7].step: The statement drops the required qualifier; the record says the importer must hold origin information, not that it already holds it. Fix: The Indian importer: claims the CEPA rate when filing the bill of entry and must hold origin information under CAROTAR 2020, including which origin criterion is claimed. The importer keeps supporting documents for at least 5 years from filing and must answer a customs request within 10 working days. The certificate does not remove the importer's duty of reasonable care, so the UAE exporter may be asked for production and cost details. Cite P-IN-IMPORTER in source_id, not in the text.
- procedure[8].step: The statement drops the required qualifier; the record says the exporter must keep origin records, not that it simply keeps them. Fix: The exporter: must keep origin records, including the cost breakdown, for no less than five (5) years, starting from the end of the year of the date of its issue. Refusing a verification visit is grounds for denying preferential benefits. Cite P-AGR-RECORDS-VERIFICATION in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.9 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (2.34 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.75 s)
