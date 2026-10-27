# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 280.83 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.21 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24079 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 116.72 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.71 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | OK | 44.08 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 46.56 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 8 | Document Builder | OK | 64.99 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 2; notes: 17 in (11 mandatory, verbatim) -> 13 in the report |
| 9 | Prose QA (round 1) | REJECTED | 2.21 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1 |
| 10 | Prose QA (round 2) | OK | 1.34 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 11 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.21 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24079 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (116.7 s)

Problems:
- caveats[3].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- caveats[8]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: 'Confirm the HS code for aluminium window frames (the best match is 76101000).'

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.38 s)
- served by cerebras/gpt-oss-120b (1.35 s)
- served by cerebras/gpt-oss-120b (0.96 s)

Problems:
- caveats[4].note: The note claims that CTSH and VA checks are based on the exporter's own declaration, which is not supported by the cited record. Fix: The origin checks (final manufacture and minimal operations) are based on the exporter's own declaration. Cite TOOL:origin:76101000 in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.38 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.35 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.96 s)

### 6. Researcher (round 2): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- caveats[3].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- QA: caveats[4].note: The note claims that CTSH and VA checks are based on the exporter's own declaration, which is not supported by the cited record. Fix: The origin checks (final manufacture and minimal operations) are based on the exporter's own declaration. Cite TOOL:origin:76101000 in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (44.07 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.37 s)
- served by cerebras/gpt-oss-120b (1.49 s); attempts: #1 (waited 11.8 s for the per-minute limit) router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '61e2fd40-5c29-4916-9207-d3013107d25e'} -> waited 30 s | #2 cerebras/gpt-oss-120b 1.49 s OK
- served by cerebras/gpt-oss-120b (1.81 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.37 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.49 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.81 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 2 | notes: 17 in (11 mandatory, verbatim) -> 13 in the report

Corrections sent (one shared revision):
- QA: summary: Includes the sentence "See the checklist below for the steps to claim the preference." which is not present in FACTS or any note. Fix: The aluminium window frames meet the rule of origin, so the CEPA rate can be claimed. This results in an estimated saving of 10000.00 AED. (see FACTS)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (51.53 s)
- served by openrouter/dots-studio/dots-3-note-preview:free (13.45 s)

### 9. Prose QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (2.21 s)

Problems:
- summary: Includes the sentence "See the checklist below for the steps to claim the preference." which is not present in FACTS or any note. Fix: The aluminium window frames meet the rule of origin, so the CEPA rate can be claimed. This results in an estimated saving of 10000.00 AED. (see FACTS)

### 10. Prose QA (round 2): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.34 s)

### 11. Report check: OK

0 problem(s), 0 warning(s)
