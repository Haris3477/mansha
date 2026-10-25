# Mansha run: CHECKS_FAILED

- **Message:** We make aluminium window frames in Sharjah from imported aluminium profiles and want to export them to India.
- **Total time:** 207.56 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 61.02 | groq/openai/gpt-oss-120b | product='aluminium window frames'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | OK | 0.0 | - | candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030; bill of materials: not given; evidence 22267 chars, 34 IDs |
| 4 | Researcher (round 1) | FAILED | 73.53 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 2; warnings 0 |
| 5 | QA (round 1) | REJECTED | 4.66 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |
| 6 | Researcher (round 2) | OK | 65.49 | openrouter/dots-studio/dots-3-note-preview:free | line 76101000 (high); origin NEEDS_MORE_DATA; verdict NEEDS_MORE_DATA; problems 0; warnings 0 |
| 7 | QA (round 2) | REJECTED | 2.86 | cerebras/gpt-oss-120b | REJECTED; factuality 0, completeness 1, formatting_safety 1; code warnings judged: 0 (0 real); 2 parts |

## Phase details

### 1. Intake: OK

product='aluminium window frames' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (61.02 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: OK

candidates: TL-IN-76101000, TL-IN-76041010, TL-IN-76151030 | bill of materials: not given | evidence 22267 chars, 34 IDs

Tool results: TOOL:tariff_lookup CANDIDATES; TOOL:rule_lookup:76101000 RULE_FOUND; TOOL:origin:76101000 INSUFFICIENT_DATA; TOOL:duty:76101000 NEEDS_VALUE; TOOL:rule_lookup:76041010 RULE_FOUND; TOOL:origin:76041010 INSUFFICIENT_DATA; TOOL:duty:76041010 NEEDS_VALUE; TOOL:rule_lookup:76151030 RULE_FOUND; TOOL:origin:76151030 INSUFFICIENT_DATA; TOOL:duty:76151030 NEEDS_VALUE; TOOL:coo_fee NEEDS_VALUE

### 4. Researcher (round 1): FAILED

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 2 | warnings 0

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (73.52 s)

Problems:
- caveats[2].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- caveats[3].source_id 'P-AGR-3.2-VA' is not an ID in the evidence

Normalized by code:
- caveats[7]: note written from the KB (P-UAE-ISSUER)

### 5. QA (round 1): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.16 s)
- served by cerebras/gpt-oss-120b (1.69 s); attempts: #1 cerebras/gpt-oss-120b 1.79 s FAILED: truncated (finish_reason=length) | #2 cerebras/gpt-oss-120b 1.69 s OK

Problems:
- caveats[0].note: The note claims CEPA reduces only Basic Customs Duty, omitting the reduction of Agriculture Infrastructure and Development Cess and incorrectly using "only". Fix: The CEPA rate reduces Basic Customs Duty and, for lines in Table II, also the Agriculture Infrastructure and Development Cess; IGST, GST compensation cess, Social Welfare Surcharge, and any anti‑dumping or safeguard duty still apply. (see P-IN-DUTY-SCOPE)
- caveats[1].note: The note adds that duty saving depends on shipment value, which is not stated in the cited record. Fix: CEPA rates reduce Basic Customs Duty only; no shipment value was provided, so only the rate difference is shown. (see TOOL:duty:76101000)
- caveats[3].note: The claim about undefined "Direct labour cost" and "direct overhead cost" is not supported by any cited record. Fix: Remove this note or replace it with information that is supported by the available evidence.

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.16 s)
- part 2/2: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.69 s)

### 6. Researcher (round 2): OK

line 76101000 (high) | origin NEEDS_MORE_DATA | verdict NEEDS_MORE_DATA | problems 0 | warnings 0

Corrections sent (one shared revision):
- caveats[2].note contains 'PSR-IN-R118': this text is shown to the exporter, so write it in plain words without evidence IDs or internal words (cite only in source_id)
- caveats[3].source_id 'P-AGR-3.2-VA' is not an ID in the evidence
- QA: caveats[0].note: The note claims CEPA reduces only Basic Customs Duty, omitting the reduction of Agriculture Infrastructure and Development Cess and incorrectly using "only". Fix: The CEPA rate reduces Basic Customs Duty and, for lines in Table II, also the Agriculture Infrastructure and Development Cess; IGST, GST compensation cess, Social Welfare Surcharge, and any anti‑dumping or safeguard duty still apply. (see P-IN-DUTY-SCOPE)
- QA: caveats[1].note: The note adds that duty saving depends on shipment value, which is not stated in the cited record. Fix: CEPA rates reduce Basic Customs Duty only; no shipment value was provided, so only the rate difference is shown. (see TOOL:duty:76101000)
- QA: caveats[3].note: The claim about undefined "Direct labour cost" and "direct overhead cost" is not supported by any cited record. Fix: Remove this note or replace it with information that is supported by the available evidence.

LLM calls:
- served by openrouter/dots-studio/dots-3-note-preview:free (65.48 s)

Normalized by code:
- caveats[6]: note written from the KB (P-UAE-ISSUER)

### 7. QA (round 2): REJECTED

REJECTED | factuality 0, completeness 1, formatting_safety 1 | code warnings judged: 0 (0 real) | 2 parts

LLM calls:
- served by cerebras/gpt-oss-120b (1.1 s)
- served by cerebras/gpt-oss-120b (1.75 s)

Problems:
- caveats[0].note: The note omits the 'countervailing' duty qualifier present in the source record. Fix: The CEPA rate reduces Basic Customs Duty and, for lines in Table II, also the Agriculture Infrastructure and Development Cess; IGST, GST compensation cess, Social Welfare Surcharge, and any anti‑dumping, countervailing or safeguard duties still apply. (see P-IN-DUTY-SCOPE)

Review split into parts (Groq's 8,000-token limit):
- part 1/2: findings + steps and notes: APPROVED, served by cerebras/gpt-oss-120b (1.1 s)
- part 2/2: steps and notes: REJECTED, served by cerebras/gpt-oss-120b (1.75 s)
