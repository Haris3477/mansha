# Mansha run: REPORT (ELIGIBLE)

- **Message:** We make aluminium windows in Sharjah from imported profiles, UAE HS code 7610 10 90, and want to export them to India. Our ex-works price for the shipment is AED 100,000.
- **Total time:** 116.72 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.48 | groq/openai/gpt-oss-120b | product='aluminium windows'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000; bill of materials: given; evidence 19525 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 58.06 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (medium); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | OK | 3.84 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Document Builder | FALLBACK | 49.21 | openrouter/dots-studio/dots-3-note-preview:free | code-only report (fallback): prose QA still failing after round 2; rounds: 2; notes: 12 in (11 mandatory, verbatim) -> 12 in the report |
| 7 | Prose QA (round 1) | REJECTED | 1.54 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1 |
| 8 | Prose QA (round 2) | REJECTED | 2.58 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1 |
| 9 | Report check | FLAGGED | 0.0 | - | 1 problem(s), 0 warning(s); report shown anyway (flag only) |

## Warnings

- Report check: 1 problem(s) in the report shown to the user (flag only): read report.md

## Phase details

### 1. Intake: OK

product='aluminium windows' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.44 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000 | bill of materials: given | evidence 19525 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (medium) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (58.05 s)

Normalized by code:
- origin_result.basis: check names written in plain words
- caveats[0]: restated note of TOOL:tariff_lookup dropped: "The 8-digit HS code 76101090 you gave is not a line in India's tariff; Mansha matched it on its first 6 digits (761010). 8-digit codes are national and differ between the UAE and India."
- caveats: note written from TOOL:tariff_lookup: "The 8-digit code 76101090 you gave is not a line in India's tariff; Mansha matched it on its first 6 digits (761010). 8-digit codes are national and differ between the UAE and India."
- procedure: 8 step(s) written by code from the knowledge base

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.92 s)
- served by cerebras/gpt-oss-120b (1.9 s)

Review split into parts (size limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.92 s)
- part 2/2: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.9 s)

### 6. Document Builder: FALLBACK

code-only report (fallback): prose QA still failing after round 2 | rounds: 2 | notes: 12 in (11 mandatory, verbatim) -> 12 in the report

Corrections sent (one shared revision):
- QA: origin: The origin text says "which is above the 40% threshold", which is not stated in FACTS or the notes. Fix: The rule of origin requires a change in tariff subheading (CTSH) and value addition (VA) of at least 45%. The product meets this rule because the final manufacture check passed, the minimal operations check passed, the CTSH check passed, and the VA check passed with 43.0% value addition on an EXW basis, satisfying the required threshold. (see FACTS)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (27.0 s)
- served by openrouter/dots-studio/dots-3-note-preview:free (22.21 s)

Problems:
- QA: origin: It states that the rule of origin requires a value addition of at least 45% and that a 43.0% value addition satisfies the required threshold, which contradicts the FACTS (VA threshold is 40%). Fix: The rule of origin requires CTSH and a value addition that together meet the 45% requirement; the product meets this because CTSH passed and the VA check passed with 43.0% value addition, which exceeds the VA threshold of 40% on an EXW basis. (see FACTS)

### 7. Prose QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.54 s)

Problems:
- origin: The origin text says "which is above the 40% threshold", which is not stated in FACTS or the notes. Fix: The rule of origin requires a change in tariff subheading (CTSH) and value addition (VA) of at least 45%. The product meets this rule because the final manufacture check passed, the minimal operations check passed, the CTSH check passed, and the VA check passed with 43.0% value addition on an EXW basis, satisfying the required threshold. (see FACTS)

### 8. Prose QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (2.58 s)

Problems:
- origin: It states that the rule of origin requires a value addition of at least 45% and that a 43.0% value addition satisfies the required threshold, which contradicts the FACTS (VA threshold is 40%). Fix: The rule of origin requires CTSH and a value addition that together meet the 45% requirement; the product meets this because CTSH passed and the VA check passed with 43.0% value addition, which exceeds the VA threshold of 40% on an EXW basis. (see FACTS)

### 9. Report check: FLAGGED

1 problem(s), 0 warning(s) | report shown anyway (flag only)

Problems:
- status code 'PASS' in the report: …ule of origin. final manufacture check: PASS; minimal operations check: PASS; CTSH:…
