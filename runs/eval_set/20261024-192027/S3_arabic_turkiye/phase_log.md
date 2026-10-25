# Mansha run: NOT_COVERED

- **Message:** نصنع أكياس البولي إيثيلين في عجمان ونريد تصديرها إلى تركيا.
- **Total time:** 1.13 s | **language:** ar

| # | Phase | Status | Time (s) | Model | Result |
|---|---|---|---|---|---|
| 1 | Intake | OK | 1.13 | groq/openai/gpt-oss-120b | product='polyethylene bags'; destination='Türkiye'; role=manufacturer; value=None; language=ar |
| 2 | Coverage check | STOP | 0.0 | - | destination 'Türkiye' not covered (covered: India) |

## Phase details

### 1. Intake: OK

product='polyethylene bags' | destination='Türkiye' | role=manufacturer | value=None | language=ar

LLM calls:
- served by groq/openai/gpt-oss-120b (1.12 s)

Normalized by code:
- destination_country: 'Turkey' -> 'Türkiye' (canonical name; unknown names kept)

### 2. Coverage check: STOP

destination 'Türkiye' not covered (covered: India)
