# Mansha run: REPORT (NO_PREFERENCE)

- **Message:** We make plastic packing articles in Ajman, HS code 39239090, and want to ship AED 50,000 worth of them to India.
- **Total time:** 99.95 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 4.76 | groq/openai/gpt-oss-120b | product='plastic packing articles'; destination='India'; role=manufacturer; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-39239090; bill of materials: not given; evidence 18090 chars, 23 IDs |
| 4 | Researcher (round 1) | OK | 45.83 | openrouter/dots-studio/dots-3-note-preview:free | line 39239090 (high); origin NOT_APPLICABLE; verdict NO_PREFERENCE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | OK | 49.36 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 4 in (1 mandatory, verbatim) -> 4 in the report |

## Phase details

### 1. Intake: OK

product='plastic packing articles' | destination='India' | role=manufacturer | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (4.76 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-39239090 | bill of materials: not given | evidence 18090 chars, 23 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:duty:39239090 NO_PREFERENCE; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 39239090 (high) | origin NOT_APPLICABLE | verdict NO_PREFERENCE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (45.83 s)

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: OK

LLM prose passed the checks | notes: 4 in (1 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (49.35 s)
