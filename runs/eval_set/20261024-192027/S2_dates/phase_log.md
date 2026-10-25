# Mansha run: NOT_COVERED

- **Message:** We pack Medjool dates in Al Ain and want to export them to India.
- **Total time:** 1.58 s | **language:** en

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.58 | groq/openai/gpt-oss-120b | product='Medjool dates'; destination='India'; role=manufacturer; value=None; language=en |
| 2 | Coverage check | OK | 0.0 | - | India -> corridor 'india' |
| 3 | Tools + evidence | STOP | 0.0 | - | candidates: none; bill of materials: not given; evidence 17090 chars, 21 IDs |

## Phase details

### 1. Intake: OK

product='Medjool dates' | destination='India' | role=manufacturer | value=None | language=en

LLM calls:
- served by groq/openai/gpt-oss-120b (1.58 s)

### 2. Coverage check: OK

India -> corridor 'india'

### 3. Tools + evidence: STOP

candidates: none | bill of materials: not given | evidence 17090 chars, 21 IDs

Tool results: TOOL:tariff_lookup NOT_FOUND; TOOL:coo_fee NEEDS_VALUE
