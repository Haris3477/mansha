# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We melt imported aluminium ingots, cast them and roll them into aluminium wire rods in Abu Dhabi, for export to India. The shipment is worth AED 100,000.
- **Total time:** 145.4 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.21 | groq/openai/gpt-oss-120b | product='aluminium wire rods'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76041010, TL-IN-76101000, TL-IN-76151030; bill of materials: given; evidence 24168 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 57.68 | openrouter/dots-studio/dots-3-note-preview:free | line 76041010 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 0.74 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 84.65 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 2 in (2 mandatory, verbatim) -> 2 in the report |
| 7 | Prose QA (round 1) | OK | 1.12 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium wire rods' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.21 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76041010, TL-IN-76101000, TL-IN-76151030 | bill of materials: given | evidence 24168 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 FAILS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 FAILS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 FAILS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76041010 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (57.67 s)

Normalized by code:
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Please confirm that the HS code 76041010 (aluminium wire rods) is correct for this shipment.'
- follow_up_questions: dropped for verdict NOT_ELIGIBLE (the result does not depend on more information from the user): 'The value addition is 30.0% on a build-down basis but the rule requires 45%. Can you provide a build-up calculation (originating materials plus direct labour plus direct overhead) or additional data on the origin of the aluminium ingots?'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76041010): "Duty estimates are on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76041010): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, SWS and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:76041010): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-UAE-ISSUER): 'No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-IN-IMPORTER): "That electronic certificates are accepted and uploaded to India's e-Sanchit system comes from CBIC Instruction 28/2022, which Mansha has read only through secondary reports (LiveLaw, taxmann), not the official text."

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.73 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 2 in (2 mandatory, verbatim) -> 2 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (84.65 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.12 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
