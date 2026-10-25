# Mansha run: CHECKS_FAILED

- **Message:** We make aluminium window frames in Sharjah from imported aluminium profiles and want to export them to India.
- **Total time:** 151.34 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 0.8 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22267 chars, 34 IDs |
| 4 | Researcher (round 1) | OK | 65.96 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 5 | QA (round 1) | REJECTED | 6.32 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | FAILED | 78.26 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 2; warnings 0 |
| 7 | QA (round 2) | SKIPPED | 0.0 | - | not run: code checks still fail |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (0.8 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22267 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 NEEDS_VALUE; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): OK

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (65.95 s)

Normalized by code:
- caveats[4]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.74 s); attempts: #1 cerebras/gpt-oss-120b 1.93 s FAILED: truncated (finish_reason=length) | #2 cerebras/gpt-oss-120b 1.74 s OK
- served by cerebras/gpt-oss-120b (1.31 s); attempts: #1 cerebras/gpt-oss-120b 1.32 s FAILED: truncated (finish_reason=length) | #2 cerebras/gpt-oss-120b 1.31 s OK

Problems:
- gaps[0]: The claim about the agreement not defining 'direct labour cost' and 'direct overhead cost' is not supported by any cited record. Fix: The cited records do not provide information on whether the agreement defines 'direct labour cost' and 'direct overhead cost' for the build‑up value addition method.
- gaps[1]: The statement contradicts the cited record that identifies the Ministry of Foreign Trade as the issuing authority. Fix: The Ministry of Foreign Trade is identified as the issuing authority for the India CEPA Certificate of Origin in the cited records. (see P-MOET-COO-INDIA)
- gaps[3]: The claim contradicts the cited record which confirms that free‑zone factories cannot obtain registration. Fix: According to the cited record, factory registration requires the factory to be located outside a free zone, confirming that free‑zone factories cannot obtain registration. (see P-MOET-FACTORY-REG)
- caveats[3].note: The note adds that value addition percentages are on an FOB basis, which is not stated in the cited record. Fix: The value addition threshold is 5 percentage points lower when the Ex-Works price is used as the basis. (see PSR-GEN-EXW)

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.74 s)
- part 2/2: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.31 s)

### 6. Researcher (round 2): FAILED

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 2 | warnings 0

Corrections sent (one shared revision):
- QA: gaps[0]: The claim about the agreement not defining 'direct labour cost' and 'direct overhead cost' is not supported by any cited record. Fix: The cited records do not provide information on whether the agreement defines 'direct labour cost' and 'direct overhead cost' for the build‑up value addition method.
- QA: gaps[1]: The statement contradicts the cited record that identifies the Ministry of Foreign Trade as the issuing authority. Fix: The Ministry of Foreign Trade is identified as the issuing authority for the India CEPA Certificate of Origin in the cited records. (see P-MOET-COO-INDIA)
- QA: gaps[3]: The claim contradicts the cited record which confirms that free‑zone factories cannot obtain registration. Fix: According to the cited record, factory registration requires the factory to be located outside a free zone, confirming that free‑zone factories cannot obtain registration. (see P-MOET-FACTORY-REG)
- QA: caveats[3].note: The note adds that value addition percentages are on an FOB basis, which is not stated in the cited record. Fix: The value addition threshold is 5 percentage points lower when the Ex-Works price is used as the basis. (see PSR-GEN-EXW)

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (78.26 s)

Problems:
- gaps[1] contains 'P-MOET-COO-INDIA)': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- gaps[3] contains 'P-MOET-FACTORY-REG)': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)

Normalized by code:
- caveats[4]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): SKIPPED

not run: code checks still fail
