# Mansha run: REPORT (ELIGIBLE)

- **Message:** We make acrylic paint in Ajman from resin bought in India and imported pigments, and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 337.14 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.13 | groq/openai/gpt-oss-120b | product='acrylic paint'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-32091010; bill of materials: given; evidence 19613 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 92.69 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 1 |
| 5 | QA (round 1) | REJECTED | 2.97 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 1 (1 real); 3 parts |
| 6 | Researcher (round 2) | OK | 95.62 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 6.86 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 8 | Document Builder | OK | 136.96 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 17 in (11 mandatory, verbatim) -> 13 in the report; summary cautions (code): INDIAN_INPUTS |
| 9 | Prose QA (round 1) | OK | 0.9 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='acrylic paint' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.13 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-32091010 | bill of materials: given | evidence 19613 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:32091010 RULE_FOUND; TOOL:origin:32091010 MEETS; TOOL:duty:32091010 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 1

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (92.68 s)

Code warnings (for QA):
- procedure[6]: names 'Indian importer', which P-AGR-3.12-DIRECT does not; cite the record that states it, or split the step

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 1 (1 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.3 s)
- served by cerebras/gpt-oss-120b (0.9 s)
- served by cerebras/gpt-oss-120b (0.76 s)

Problems:
- procedure[6].step: The step includes the name 'Indian importer', which is not present in the cited record. Fix: The exporter sends the certificate; if a third party issues the invoice, the exporter must indicate 'third-party invoicing'. Cite P-AGR-3.12-DIRECT in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.3 s); code warnings W1
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.9 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.76 s)

Code warnings judged by QA:
- W1 REAL: procedure[6]: names 'Indian importer', which P-AGR-3.12-DIRECT does not; cite the record that states it, or split the step -> Procedure step mentions 'Indian importer' which is not found in the cited record.

### 6. Researcher (round 2): OK

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: procedure[6].step: The step includes the name 'Indian importer', which is not present in the cited record. Fix: The exporter sends the certificate; if a third party issues the invoice, the exporter must indicate 'third-party invoicing'. Cite P-AGR-3.12-DIRECT in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (95.6 s)

Normalized by code:
- caveats[11]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (3.63 s)
- served by cerebras/gpt-oss-120b (2.55 s)
- served by cerebras/gpt-oss-120b (0.67 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (3.63 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (2.55 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.67 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 17 in (11 mandatory, verbatim) -> 13 in the report | summary cautions (code): INDIAN_INPUTS

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (136.95 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.9 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
