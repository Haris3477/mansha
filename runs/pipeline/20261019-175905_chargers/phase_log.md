# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 203.19 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 5.46 | google/gemini-3.7-flash | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 130.31 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.01 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 60.95 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 7 in (2 mandatory, verbatim) -> 6 in the report |
| 7 | Prose QA (round 1) | OK | 3.46 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by google/gemini-3.7-flash (5.43 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (130.3 s)

Normalized by code:
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, SWS and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'The CEPA rate reduces Basic Customs Duty (BCD), and the Agriculture Infrastructure and Development Cess only for lines in Table II. IGST, GST compensation cess and the Social Welfare Surcharge still apply, as do any anti-dumping, countervailing or safeguard duties. Because the IGST base includes BCD, a lower BCD also lowers the IGST amount.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'SWS is charged on the reduced BCD (no CEPA-specific text found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-DUTY-SCOPE): 'anti-dumping and safeguard duties still apply (no exemption found).'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-UAE-ISSUER): 'No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-FACTORY-REG): 'Inference: a producer in a free zone is likely not eligible for Factory Registration, because it requires a factory outside a free zone, and registration is needed before applying for the certificate of origin for India. Confirm with the Ministry of Economy and Tourism.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-IMPORTER): "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-AGR-COO-RULES): "The agreement says box 8, but India's origin rules and certificate form say box 9; India's form governs entry into India."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-AGR-RECORDS-VERIFICATION): "UAE law sets a shorter 3-year minimum; the CEPA's 5 years governs CEPA claims."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-COO-INDIA): 'Fee bands are in AED and apply to the invoice value in AED; no currency conversion is done by Mansha.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:coo_fee): 'Fee bands are those of the certificate service (UAE e-service: Certificate of Origin for India; Ministry service pages; Cabinet Resolution 208/2025 fee schedule), charged on the invoice value in AED.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:coo_fee): "Assumes the certificate's invoice value equals the shipment value given."

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by groq/openai/gpt-oss-120b (3.01 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 7 in (2 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (60.93 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by groq/openai/gpt-oss-120b (3.46 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
