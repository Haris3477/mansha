# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 133.83 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.35 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 46.06 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.3 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 78.58 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 4 in (2 mandatory, verbatim) -> 4 in the report |
| 7 | Prose QA (round 1) | OK | 3.53 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.3 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (46.06 s)

Normalized by code:
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): "The duty estimate is on the shipment value given; India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Amounts are shown in the shipment's own currency and are not converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge and any anti-dumping or safeguard duty still apply.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (TOOL:duty:85044030): 'The CEPA rate applies only if the product qualifies under the rules of origin and a valid certificate of origin is presented at import.'
- caveats: dropped a note about claiming the CEPA rate for verdict NOT_ELIGIBLE (P-MOET-FACTORY-REG): 'Factory Registration (a prerequisite for the certificate of origin) requires the factory to be outside a free zone; a producer in a free zone is likely not eligible. Confirm with the Ministry of Economy and Tourism.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by groq/openai/gpt-oss-120b (3.3 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 4 in (2 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (78.58 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by groq/openai/gpt-oss-120b (3.53 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
