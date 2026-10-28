# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We assemble smartphones in Dubai from imported kits, HS code 8517 12 11, and want to export them to India. The shipment is worth AED 90,000.
- **Total time:** 321.05 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.27 | groq/openai/gpt-oss-120b | product='smartphones'; destination='India'; role=manufacturer; value=90000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85171300; bill of materials: given; evidence 19949 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 236.6 | openrouter/dots-studio/dots-3-note-preview:free | line 85171300 (medium); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 1.61 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 79.19 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 2; notes: 8 in (5 mandatory, verbatim) -> 7 in the report |
| 7 | Prose QA (round 1) | REJECTED | 1.32 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1 |
| 8 | Prose QA (round 2) | OK | 1.07 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 9 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='smartphones' | destination='India' | role=manufacturer | value=90000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.26 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85171300 | bill of materials: given | evidence 19949 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85171300 RULE_FOUND; TOOL:origin:85171300 FAILS; TOOL:duty:85171300 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85171300 (medium) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (71.66 s); attempts: #1 openrouter/dots-studio/dots-3-note-preview:free 164.92 s FAILED: truncated (finish_reason=length) | #2 openrouter/dots-studio/dots-3-note-preview:free 71.66 s OK

Normalized by code:
- origin_result.basis: check names written in plain words
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "The code 85171211 given is India's older HS 2017 code; the current tariff line is 85171300."
- caveats: note written from TOOL:tariff_lookup: "The code 85171211 you gave is India's older HS 2017 code for this product; India's current tariff line is 85171300."
- caveats[4]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): "Please confirm the HS code for smartphones: the code you gave (85171211) is India's older HS 2017 code; the current tariff line is 85171300. Is that correct?"
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge (SWS) and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85171300): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'The Social Welfare Surcharge (SWS) is likely charged on the reduced BCD (no CEPA-specific text on it was found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'Anti-dumping and safeguard duties likely still apply (no CEPA exemption from them was found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-UAE-ISSUER): 'No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-COO-INDIA): 'Fee bands are in AED and apply to the invoice value in AED; no currency conversion is done by Mansha.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:coo_fee): 'Fee bands are those of the certificate service (UAE e-service: Certificate of Origin for India; Ministry service pages; Cabinet Resolution 208/2025 fee schedule), charged on the invoice value in AED.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:coo_fee): "Assumes the certificate's invoice value equals the shipment value given."

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (1.6 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 2 | notes: 8 in (5 mandatory, verbatim) -> 7 in the report

Corrections sent (one shared revision):
- QA: notes[0].text: The note adds "which may affect how you declare the shipment," which is not present in N1. Fix: India's CEPA tariff schedule (Annex 2A) lists this product under its older HS 2017 code 8517 12 11. (see N1)
- QA: notes[1].text: The note adds the examples "such as simple assembly or packaging," which are not in N2. Fix: A product that only undergoes minimal operations (Art. 3.5.1 a-q) does not originate, even if it meets its product-specific rule. (see N2)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (50.71 s)
- served by openrouter/dots-studio/dots-3-note-preview:free (28.47 s)

### 7. Prose QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.32 s)

Problems:
- notes[0].text: The note adds "which may affect how you declare the shipment," which is not present in N1. Fix: India's CEPA tariff schedule (Annex 2A) lists this product under its older HS 2017 code 8517 12 11. (see N1)
- notes[1].text: The note adds the examples "such as simple assembly or packaging," which are not in N2. Fix: A product that only undergoes minimal operations (Art. 3.5.1 a-q) does not originate, even if it meets its product-specific rule. (see N2)

### 8. Prose QA (round 2): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.07 s)

### 9. Report check: OK

0 problem(s), 0 warning(s)
