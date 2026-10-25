# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 286.55 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 3.21 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 232.85 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | SKIPPED | 0.0 | - | QA Evaluator not built yet (Step 7): output NOT reviewed by QA |
| 6 | Document Builder | OK | 50.48 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 11 in (6 mandatory, verbatim) -> 6 in the report |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (3.18 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (135.27 s); attempts: #1 openrouter/dots-studio/dots-3-note-preview:free 97.57 s FAILED: truncated (finish_reason=length) | #2 openrouter/dots-studio/dots-3-note-preview:free 135.27 s OK

### 5. QA (round 1): SKIPPED

QA Evaluator not built yet (Step 7): output NOT reviewed by QA

### 6. Document Builder: OK

LLM prose passed the checks | notes: 11 in (6 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (50.47 s)
