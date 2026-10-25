# Mansha run: REPORT (NO_PREFERENCE)

- **Message:** We make plastic packing articles in Ajman, HS code 39239090, and want to ship AED 50,000 worth of them to India.
- **Total time:** 74.3 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.18 | groq/openai/gpt-oss-120b | product='plastic packing articles'; destination='India'; role=manufacturer; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-39239090; bill of materials: not given; evidence 18174 chars, 23 IDs |
| 4 | Researcher (round 1) | OK | 36.28 | openrouter/dots-studio/dots-3-note-preview:free | line 39239090 (high); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 0.59 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Document Builder | OK | 35.44 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 1 in (0 mandatory, verbatim) -> 1 in the report |
| 7 | Prose QA (round 1) | OK | 0.82 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 8 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='plastic packing articles' | destination='India' | role=manufacturer | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.18 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-39239090 | bill of materials: not given | evidence 18174 chars, 23 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:duty:39239090 NO_PREFERENCE; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 39239090 (high) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (36.26 s)

Normalized by code:
- caveats: dropped a note about claiming the CEPA rate for verdict NO_PREFERENCE (TOOL:duty:39239090): "This line is excluded from India's CEPA concessions: no preferential rate, the normal (MFN) duty applies whatever the origin."
- caveats: dropped a note about claiming the CEPA rate for verdict NO_PREFERENCE (TOOL:duty:39239090): "Estimate on the shipment value given. India charges duty on the assessable (CIF) value at import, so actual amounts will differ. Shown in the shipment's own currency; never converted."
- caveats: dropped a note about claiming the CEPA rate for verdict NO_PREFERENCE (P-IN-DUTY-SCOPE): 'The CEPA rate reduces Basic Customs Duty (BCD), and the Agriculture Infrastructure and Development Cess only for lines in Table II. IGST, GST compensation cess and the Social Welfare Surcharge still apply, as do any anti-dumping, countervailing or safeguard duties.'

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by cerebras/gpt-oss-120b (0.58 s)

### 6. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 1 in (0 mandatory, verbatim) -> 1 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (35.44 s)

### 7. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (0.82 s)

### 8. Report check: OK

0 problem(s), 0 warning(s)
