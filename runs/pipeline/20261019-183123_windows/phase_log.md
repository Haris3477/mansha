# Mansha run: CHECKS_FAILED

- **Message:** We run a factory in Sharjah. We cut and assemble aluminium window frames from imported aluminium profiles and want to export them to India. The shipment is worth AED 100,000.
- **Total time:** 440.21 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 2.14 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.01 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: given; evidence 24172 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 92.77 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 2 |
| 5 | QA (round 1) | REJECTED | 131.87 | groq/openai/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 2 (2 real); 3 parts |
| 6 | Researcher (round 2) | OK | 51.99 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin QUALIFIES; verdict ELIGIBLE; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 161.43 | groq/openai/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (2.09 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: given | evidence 24172 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 MEETS; TOOL:duty:76101000 ESTIMATED; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 MEETS; TOOL:duty:76041010 ESTIMATED; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 MEETS; TOOL:duty:76151030 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 2

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (92.77 s)

Code warnings (for QA):
- procedure[1]: number(s) ['45'] not found in P-AGR-3.2-ORIGIN
- caveats[0]: number(s) ['45'] not found in TOOL:rule_lookup:76101000

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 2 (2 real) | 3 parts

LLM calls:
- served by groq/openai/gpt-oss-120b (3.74 s)
- served by groq/openai/gpt-oss-120b (4.54 s); attempts: #1 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'd1c78001-b4ae-42d2-95c2-80c8469d0248'} -> waited 30 s | #2 router 0.02 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '2d655341-be2e-4df8-8249-afe21e03de19'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 4.54 s OK
- served by groq/openai/gpt-oss-120b (3.48 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '6c4bfb35-abfe-43ad-aa99-c6d0c9dcd7fb'} -> waited 30 s | #2 router 0.03 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'fc00ebbe-66bd-43dc-95d9-1e243b49378e'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 3.48 s OK

Problems:
- procedure[1].step: Mentions specific rule details (CTSH + VA 45%) not found in the cited record. Fix: Ensure the product meets the origin criteria: it must either be wholly obtained or meet the applicable product-specific rule, and final manufacture must have occurred in the UAE. (see P-AGR-3.2-ORIGIN)
- caveats[0].note: Includes the percentage '45%' which is not found in the cited TOOL:rule_lookup record. Fix: The '+' in the rule 'CTSH + VA' is interpreted by Mansha as 'and', meaning both tests must pass. The agreement does not define '+'. (see TOOL:rule_lookup:76101000)
- caveats[13].note: The note mentions the website "doit.gov.ae", which is not supported by the cited record. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae. (see P-UAE-ISSUER)

Review split into parts (Groq's 8,000-token limit):
- part 1/3: findings + steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (3.74 s); code warnings W1
- part 2/3: steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (4.54 s); code warnings W2
- part 3/3: steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (3.48 s)

Code warnings judged by QA:
- W1 REAL: procedure[1]: number(s) ['45'] not found in P-AGR-3.2-ORIGIN -> Number 45 not present in P-AGR-3.2-ORIGIN
- W2 REAL: caveats[0]: number(s) ['45'] not found in TOOL:rule_lookup:76101000 -> The note cites the number 45, which is not present in the cited rule_lookup record.

### 6. Researcher (round 2): OK

line 76101000 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 0 | warnings 0

Corrections sent (one shared revision):
- QA: procedure[1].step: Mentions specific rule details (CTSH + VA 45%) not found in the cited record. Fix: Ensure the product meets the origin criteria: it must either be wholly obtained or meet the applicable product-specific rule, and final manufacture must have occurred in the UAE. (see P-AGR-3.2-ORIGIN)
- QA: caveats[0].note: Includes the percentage '45%' which is not found in the cited TOOL:rule_lookup record. Fix: The '+' in the rule 'CTSH + VA' is interpreted by Mansha as 'and', meaning both tests must pass. The agreement does not define '+'. (see TOOL:rule_lookup:76101000)
- QA: caveats[13].note: The note mentions the website "doit.gov.ae", which is not supported by the cited record. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae. (see P-UAE-ISSUER)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (51.99 s)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by groq/openai/gpt-oss-120b (3.67 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '048a9746-c213-4a0e-bdeb-048f27acb6e0'} -> waited 30 s | #2 groq/openai/gpt-oss-120b 3.67 s OK
- served by groq/openai/gpt-oss-120b (3.45 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '4f2ea08f-5cee-4c64-9571-f79b648c9b90'} -> waited 30 s | #2 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '11400c8c-836c-4f2f-b68b-d516b0bbfb1e'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 3.45 s OK
- served by groq/openai/gpt-oss-120b (4.18 s); attempts: #1 router 0.01 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': 'c0674135-0db0-442f-84fe-10cfbfc2541f'} -> waited 30 s | #2 router 0.04 s FAILED: HTTP 429: Error code: 429 - {'error': {'message': 'All models exhausted: 1 route checked (1 rate-limited or on cooldown). Add more API keys or wait for rate limits to reset.', 'type': 'rate_limit_error', 'code': 'rate_limit_exceeded'}, 'execution_id': '375ff449-44bd-47dc-b77f-376541ccbcaa'} -> waited 30 s | #3 groq/openai/gpt-oss-120b 4.18 s OK

Problems:
- caveats[13].note: The note cites the wrong website domain for the India-specific page. Fix: No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically: its service page covers preferential certificates in general, and the India-specific page is still on moet.gov.ae. (see P-UAE-ISSUER)

Review split into parts (Groq's 8,000-token limit):
- part 1/3: findings + steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (3.67 s)
- part 2/3: steps and notes: APPROVED, served by groq/openai/gpt-oss-120b (3.45 s)
- part 3/3: steps and notes: REJECTED, served by groq/openai/gpt-oss-120b (4.18 s)
