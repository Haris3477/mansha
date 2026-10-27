# Mansha run: REPORT (ELIGIBLE)

- **Message:** Our factory is in a free zone in the UAE. We make wooden bedroom furniture from imported hardwood and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 293.06 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.11 | groq/openai/gpt-oss-120b | product='hardwood bedroom furniture'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-94036000; bill of materials: given; evidence 19694 chars, 26 IDs |
| 4 | Researcher (round 1) | OK | 147.78 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 3.56 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | OK | 44.78 | openrouter/dots-studio/dots-3-note-preview:free | line 94036000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 44.72 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 8 | Document Builder | OK | 50.08 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 16 in (9 mandatory, verbatim) -> 11 in the report; summary cautions (code): FREE_ZONE |
| 9 | Prose QA (round 1) | OK | 1.02 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='hardwood bedroom furniture' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.11 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-94036000 | bill of materials: given | evidence 19694 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:94036000 RULE_FOUND; TOOL:origin:94036000 MEETS; TOOL:duty:94036000 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (147.77 s)

Normalized by code:
- caveats[2]: note written from the KB, qualifier kept (TOOL:origin:94036000)
- follow_up_questions[0]: HS-code confirmation dropped, the tariff lookup found no conflict: "Please confirm the HS code for 'hardwood bedroom furniture' is 94036000 (Other wooden furniture)."
- caveats[12]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.43 s)
- served by cerebras/gpt-oss-120b (1.3 s)
- served by cerebras/gpt-oss-120b (0.81 s)

Problems:
- caveats[7].note: The note adds an inference ('which may affect the value addition calculation') that is not present in the cited record. Fix: 'Direct labour cost' and 'direct overhead cost' are not defined in the agreement. Cite P-AGR-3.2.2-VA in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.43 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.3 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.81 s)

### 6. Researcher (round 2): OK

line 94036000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: caveats[7].note: The note adds an inference ('which may affect the value addition calculation') that is not present in the cited record. Fix: 'Direct labour cost' and 'direct overhead cost' are not defined in the agreement. Cite P-AGR-3.2.2-VA in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (44.77 s)

Normalized by code:
- caveats[12]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.5 s)
- served by cerebras/gpt-oss-120b (1.32 s); attempts: #1 (waited 11.2 s for the per-minute limit) router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '5026c2a4-15fa-4da8-8921-b9ee84ec0158'} -> waited 30 s | #2 cerebras/gpt-oss-120b 1.32 s OK
- served by cerebras/gpt-oss-120b (0.71 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.5 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.32 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.71 s)

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 16 in (9 mandatory, verbatim) -> 11 in the report | summary cautions (code): FREE_ZONE

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (50.07 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by cerebras/gpt-oss-120b (1.02 s)

### 10. Report check: OK

0 problem(s), 0 warning(s)
