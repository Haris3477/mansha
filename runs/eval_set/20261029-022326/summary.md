# Evaluation set run 20261029-022326

**0/2 runs pass every code check** (expected failures not counted); verdicts correct 2/2; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 0; pacing waits 23.6 s; median report time 86.2 s.

| Case | Result | Status | Verdict | Seconds | long | arabic | judge | Slips |
|---|---|---|---|---|---|---|---|---|
| N15_arabic_windows_nodata_r1 | FAIL | REPORT | NEEDS_MORE_DATA | 115.3 | 1 | 1 | 4 | - |
| N15_arabic_windows_nodata_r2 | FAIL | REPORT | NEEDS_MORE_DATA | 57.0 | 1 | 1 | 3 | - |

## Failed code checks
- **N15 N15_arabic_windows_nodata_r1**
  - language: 105 English word(s) in an Arabic report: ['tariff', 'effective', 'The', 'in', 'the', 'rule', 'is', 'interpreted', 'as', 'meaning']
- **N15 N15_arabic_windows_nodata_r2**
  - language: 58 English word(s) in an Arabic report: ['The', 'in', 'the', 'rule', 'is', 'read', 'as', 'agreement', 'does', 'not']

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:arabic | 2 | 4034 | 1265 |
| auto:judge | 7 | 26212 | 9088 |
| auto:long | 2 | 16573 | 11781 |
| auto:qa | 2 | 1424 | 640 |
