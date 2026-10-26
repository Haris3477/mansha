# Mansha run: CHECKS_FAILED

- **Message:** We make acrylic paint in Ajman from resin bought in India and imported pigments, and want to export it to India. The shipment is worth AED 100,000.
- **Total time:** 172.9 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.17 | groq/openai/gpt-oss-120b | product='acrylic paint'; destination='India'; role=manufacturer; value=100000 AED; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-32091010; bill of materials: given; evidence 19613 chars, 26 IDs |
| 4 | Researcher (round 1) | FAILED | 127.47 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 5 | QA (round 1) | OK | 3.71 | cerebras/gpt-oss-120b | APPROVED; factuality 1, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 3 parts |
| 6 | Researcher (round 2) | FAILED | 40.55 | openrouter/dots-studio/dots-3-note-preview:free | line 32091010 (high); origin QUALIFIES; verdict ELIGIBLE; problems 1; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='acrylic paint' | destination='India' | role=manufacturer | value=100000 AED | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.17 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-32091010 | bill of materials: given | evidence 19613 chars, 26 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:32091010 RULE_FOUND; TOOL:origin:32091010 MEETS; TOOL:duty:32091010 ESTIMATED; TOOL:coo_fee ESTIMATED

### 4. Researcher (round 1): FAILED

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (127.46 s)

Problems:
- caveats[15].note states as a plain fact what its cited record qualifies with 'Inference' ('Inference: SWS is charged on the reduced BCD (no CEPA-specific text found).'): keep that qualifier in the text

Normalized by code:
- origin_result.basis: check names written in plain words
- caveats[8]: note written from the KB, qualifier kept (P-AGR-3.4-DEMINIMIS)
- caveats[12]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): OK

APPROVED | factuality 1, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 3 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.72 s)
- served by cerebras/gpt-oss-120b (1.09 s)
- served by cerebras/gpt-oss-120b (0.88 s)

Review split into parts (size limit):
- part 1/3: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.72 s)
- part 2/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.09 s)
- part 3/3: steps and notes: APPROVED, served by cerebras/gpt-oss-120b (0.88 s)

### 6. Researcher (round 2): FAILED

line 32091010 (high) | origin QUALIFIES | verdict ELIGIBLE | problems 1 | warnings 0

Corrections sent (one shared revision):
- caveats[15].note states as a plain fact what its cited record qualifies with 'Inference' ('Inference: SWS is charged on the reduced BCD (no CEPA-specific text found).'): keep that qualifier in the text

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (40.54 s)

Problems:
- caveats[15].note states as a plain fact what its cited record qualifies with 'Inference' ('Inference: anti-dumping and safeguard duties still apply (no exemption found).'): keep that qualifier in the text

### 7. QA (round 2): SKIPPED

not run: code checks still fail
