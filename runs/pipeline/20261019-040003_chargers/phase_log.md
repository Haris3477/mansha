# Mansha run: REPORT (NOT_ELIGIBLE)

- **Message:** We are a trading company in Dubai. We buy battery chargers from China, repack and relabel them, and re-export them to India. The shipment is worth AED 50,000.
- **Total time:** 361.15 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 3.68 | groq/openai/gpt-oss-120b | product='battery chargers'; destination='India'; role=trader; value=50000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-85044030; bill of materials: given; evidence 20225 chars, 26 IDs |
| 4 | Researcher (round 1) | FAILED | 117.64 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 22; warnings 0 |
| 5 | QA (round 1) | REJECTED | 73.34 | groq/openai/gpt-oss-120b | REJECTED; factuality 0, completeness 0, formatting_safety 1; code warnings judged: 0 (0 real) |
| 6 | Researcher (round 2) | OK | 58.15 | openrouter/dots-studio/dots-3-note-preview:free | line 85044030 (high); origin DOES_NOT_QUALIFY; verdict NOT_ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | OK | 32.56 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real) |
| 8 | Document Builder | OK | 73.1 | google/gemini-3.7-flash | LLM prose passed the code checks; prose QA approved; rounds: 1; notes: 4 in (2 mandatory, verbatim) -> 4 in the report |
| 9 | Prose QA (round 1) | OK | 2.67 | groq/openai/gpt-oss-120b | APPROVED; factuality 1, completeness 1 |
| 10 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Phase details

### 1. Intake: OK

product='battery chargers' | destination='India' | role=trader | value=50000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (3.64 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-85044030 | bill of materials: given | evidence 20225 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:85044030 RULE_FOUND; TOOL:origin:85044030 FAILS; TOOL:duty:85044030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 22 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (117.63 s)

Problems:
- classification.source_id '[TL-IN-85044030]' is not an ID in the evidence
- tariff.source_id '[TL-IN-85044030]' is not an ID in the evidence
- origin_rule.source_id '[PSR-IN-R126]' is not an ID in the evidence
- origin_result.source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- estimated_saving.source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[0].source_id '[TL-IN-85044030]' is not an ID in the evidence
- caveats[1].source_id '[TL-IN-85044030]' is not an ID in the evidence
- caveats[2].source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- caveats[3].source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- caveats[4].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[5].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[6].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[7].source_id '[P-UAE-ISSUER]' is not an ID in the evidence
- caveats[8].source_id '[P-IN-IMPORTER]' is not an ID in the evidence
- caveats[9].source_id '[P-MOET-FACTORY-REG]' is not an ID in the evidence
- caveats[10].source_id '[P-AGR-3.2.2-VA]' is not an ID in the evidence
- caveats[11].source_id '[P-AGR-3.2.2-VA]' is not an ID in the evidence
- caveats[12].source_id '[P-AGR-3.4-DEMINIMIS]' is not an ID in the evidence
- caveats[13].source_id '[P-AGR-3.1-NOM]' is not an ID in the evidence
- caveats[14].source_id '[P-AGR-3.7-CUMULATION]' is not an ID in the evidence
- origin_result.source_id must be TOOL:origin:85044030 (the chosen line's result)
- origin_rule.source_id must be the rule record PSR-IN-R126 (TOOL:rule_lookup:85044030 names it, and the rule text is there)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 0, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by groq/openai/gpt-oss-120b (6.16 s); attempts: #1 groq/openai/gpt-oss-120b 7.1 s FAILED: truncated (finish_reason=length) | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '2c212a01-ea07-42e6-8919-07f5dcbf39bc'} -> waited 30 s | #3 router 0.04 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'bd6b85d5-3069-4177-882e-614c7d7c116d'} -> waited 30 s | #4 groq/openai/gpt-oss-120b 6.16 s OK

Problems:
- caveats[7].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[8].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[9].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[10].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[11].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[12].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[13].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- caveats[14].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- follow_up_questions[2]: The question asks for a bill of materials that the exporter has already provided. Fix: Remove this question or ask for additional information not already supplied.

### 6. Researcher (round 2): OK

line 85044030 (high) | origin DOES_NOT_QUALIFY | verdict NOT_ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- classification.source_id '[TL-IN-85044030]' is not an ID in the evidence
- tariff.source_id '[TL-IN-85044030]' is not an ID in the evidence
- origin_rule.source_id '[PSR-IN-R126]' is not an ID in the evidence
- origin_result.source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- estimated_saving.source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[0].source_id '[TL-IN-85044030]' is not an ID in the evidence
- caveats[1].source_id '[TL-IN-85044030]' is not an ID in the evidence
- caveats[2].source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- caveats[3].source_id '[TOOL:origin:85044030]' is not an ID in the evidence
- caveats[4].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[5].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[6].source_id '[TOOL:duty:85044030]' is not an ID in the evidence
- caveats[7].source_id '[P-UAE-ISSUER]' is not an ID in the evidence
- caveats[8].source_id '[P-IN-IMPORTER]' is not an ID in the evidence
- caveats[9].source_id '[P-MOET-FACTORY-REG]' is not an ID in the evidence
- caveats[10].source_id '[P-AGR-3.2.2-VA]' is not an ID in the evidence
- caveats[11].source_id '[P-AGR-3.2.2-VA]' is not an ID in the evidence
- caveats[12].source_id '[P-AGR-3.4-DEMINIMIS]' is not an ID in the evidence
- caveats[13].source_id '[P-AGR-3.1-NOM]' is not an ID in the evidence
- caveats[14].source_id '[P-AGR-3.7-CUMULATION]' is not an ID in the evidence
- origin_result.source_id must be TOOL:origin:85044030 (the chosen line's result)
- origin_rule.source_id must be the rule record PSR-IN-R126 (TOOL:rule_lookup:85044030 names it, and the rule text is there)
- QA: caveats[7].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[8].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[9].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[10].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[11].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[12].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[13].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: caveats[14].note: The note is not supported by any cited record in the evidence. Fix: Remove this note.
- QA: follow_up_questions[2]: The question asks for a bill of materials that the exporter has already provided. Fix: Remove this question or ask for additional information not already supplied.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (58.14 s)

### 7. QA (round 2): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real)

LLM calls:
- served by groq/openai/gpt-oss-120b (2.53 s); attempts: #1 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '0ffd041b-17aa-42ad-ac7d-bdb0e0b9e813'} -> waited 30 s | #2 groq/openai/gpt-oss-120b 2.53 s OK

### 8. Document Builder: OK

LLM prose passed the code checks; prose QA approved | rounds: 1 | notes: 4 in (2 mandatory, verbatim) -> 4 in the report

LLM calls:
- served by google/gemini-3.7-flash (13.01 s)

### 9. Prose QA (round 1): OK

APPROVED | factuality 1, completeness 1

LLM calls:
- served by groq/openai/gpt-oss-120b (2.67 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '365bba72-296d-4bcf-b270-db082d6eab92'} -> waited 30 s | #2 router 0.05 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'e34cd29c-f4c7-4fe9-8b51-b8829af97e5a'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 2.67 s OK

### 10. Report check: OK

0 problem(s), 0 warning(s)
