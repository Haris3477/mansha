# Mansha run: REPORT (ELIGIBLE)

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 95.51 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 5.0 | google/gemini-3.7-flash | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.02 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 17.67 | google/gemini-3.7-flash | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 5 | QA (round 1) | FAILED | 0.21 | - | QA call failed: output NOT reviewed by QA |
| 6 | Document Builder | OK | 72.61 | openrouter/dots-studio/dots-3-note-preview:free | LLM prose passed the checks; notes: 6 in (5 mandatory, verbatim) -> 6 in the report |
| 7 | Report check | OK | 0.0 | - | 0 problem(s), 0 warning(s) |

## Warnings

- QA round 1: QA call failed: output NOT reviewed by QA

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by google/gemini-3.7-flash (4.95 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

LLM calls:
- served by google/gemini-3.7-flash (17.67 s)

### 5. QA (round 1): FAILED

QA call failed: output NOT reviewed by QA

LLM calls:
- call FAILED; attempts: #1 router 0.14 s FAILED: HTTP 413: Error code: 413 - {'error': {'message': "The request is too large for every routed candidate: all 1 attempt(s) were rejected as over the model's context/size limit. Retrying will not help — reduce the prompt/history size or enable a larger-context model. Attempt trail: groq/openai/gpt-oss-120b key1: context_too_large. Last error: Groq API error 413: Request too large for model `openai/gpt-oss-120b` in organization `org_01m4s0bhgbehx9yez7cepjne88` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Requested 8779, please reduce your message size and t...", 'type': 'invalid_request_error', 'code': 'context_length_exceeded'}, 'execution_id': '8df9696b-8511-41f6-b6f0-22b8c063853e'} | #2 router 0.07 s FAILED: HTTP 413: Error code: 413 - {'error': {'message': "The request is too large for every routed candidate: all 1 attempt(s) were rejected as over the model's context/size limit. Retrying will not help — reduce the prompt/history size or enable a larger-context model. Attempt trail: groq/openai/gpt-oss-120b key1: context_too_large. Last error: Groq API error 413: Request too large for model `openai/gpt-oss-120b` in organization `org_01m4s0bhgbehx9yez7cepjne88` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Requested 8779, please reduce your message size and t...", 'type': 'invalid_request_error', 'code': 'context_length_exceeded'}, 'execution_id': '43b71e76-604c-4ac9-910f-de5f37b1e761'}

### 6. Document Builder: OK

LLM prose passed the checks | notes: 6 in (5 mandatory, verbatim) -> 6 in the report

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (72.61 s)

### 7. Report check: OK

0 problem(s), 0 warning(s)
