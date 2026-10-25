# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 130.58 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.57 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 57.69 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.16 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 64.64 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 4 in (3 mandatory, verbatim) -> 4 in the report |
| 7 | Prose QA (round 1) | OK | 2.52 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.53 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (57.68 s)

Normalized by code:
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'Confirm whether the final manufacture of these battery chargers took place in the UAE, as the origin check reports it did not.'
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'Provide a bill of materials showing the origin, HS code and value of each input used in the battery chargers, so the CTH and value-added tests can be recalculated.'
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'Verify whether the operations performed (repacking and relabeling) are the only operations, or whether additional manufacturing steps were taken.'
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'Confirm the HS code for these battery chargers, as none was provided with the query.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'India charges duty on the assessable (CIF) value at import, so actual amounts will differ from the estimate.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, SWS and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-UAE-ISSUER): 'No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically; the India-specific service page is still on moet.gov.ae.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-IMPORTER): "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from a secondary source (CBIC Instruction 28/2022 read through LiveLaw and taxmann), not the official text."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-FACTORY-REG): 'A producer in a free zone is likely not eligible for Factory Registration, which is required before applying for a certificate of origin for India.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by groq/openai/gpt-oss-120b (3.16 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 4 in (3 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (64.64 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by groq/openai/gpt-oss-120b (2.52 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
