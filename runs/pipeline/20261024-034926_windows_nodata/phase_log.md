# Mansha run: CHECKS_FAILED

- **Message:** We make aluminium window frames in Sharjah from imported aluminium profiles and want to export them to India.
- **Total time:** 149.96 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.04 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22267 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 62.61 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 1 |
| 5 | QA (round 1) | REJECTED | 2.96 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 1 (1 real); 3 parts |
| 6 | Researcher (round 2) | OK | 20.59 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 2.75 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.04 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22267 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 NEEDS_VALUE; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): OK

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 1

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (62.6 s)

Code warnings (for QA):
- caveats[0]: number(s) ['45'] not found in TOOL:rule_lookup:76101000

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 1 (1 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.1 s)
- served by cerebras/gpt-oss-120b (1.24 s)
- served by cerebras/gpt-oss-120b (0.6 s)

Problems:
- caveats[0].note: The note references a 'VA 45%' percentage that is not present in the cited rule_lookup record. Fix: The '+' in the rule 'CTSH + VA' is read as 'and' (both tests must pass); the agreement does not define '+', so this is Mansha's interpretation. Cite TOOL:rule_lookup:76101000 in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.1 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.24 s); code warnings W1
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.6 s)

Code warnings judged by QA:
- W1 REAL: caveats[0]: number(s) ['45'] not found in TOOL:rule_lookup:76101000 -> Number 45 is not found in the cited rule_lookup record

### 6. Researcher (round 2): OK

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: caveats[0].note: The note references a 'VA 45%' percentage that is not present in the cited rule_lookup record. Fix: The '+' in the rule 'CTSH + VA' is read as 'and' (both tests must pass); the agreement does not define '+', so this is Mansha's interpretation. Cite TOOL:rule_lookup:76101000 in source_id, not in the text.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (20.58 s)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (0.96 s)
- served by cerebras/gpt-oss-120b (1.76 s)
- call FAILED; attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset. Soonest reset ~9m.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded', 'retryAtMs': 1792800027000}, 'execution_id': '74701ea0-f279-417a-b0e1-cc82a945cfb9'} (router cooldown, no model tried) -> gave up: router busy for ~511s (> 90s cap)

Problems:
- caveats[7].note: The note adds unsupported detail about CBIC Instruction 28/2022 which is not in the cited record. Fix: Electronic certificates are reportedly accepted and uploaded to India's e‑Sanchit system, as noted from secondary sources. Cite P-IN-IMPORTER in source_id, not in the text.

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.96 s)
- part 2/3: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.76 s)
- part 3/3: steps and notes: ERROR
