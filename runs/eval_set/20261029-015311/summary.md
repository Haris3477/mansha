# Evaluation set run 20261029-015311

**0/2 runs pass every code check** (expected failures not counted); verdicts correct 2/2; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 91.1 s.

| Case | Result | Status | Verdict | Seconds | long | arabic | judge | Slips |
|---|---|---|---|---|---|---|---|---|
| N15_arabic_windows_nodata_r1 | FAIL | REPORT | NEEDS_MORE_DATA | 59.6 | 1 | 1 | 3 | - |
| N15_arabic_windows_nodata_r2 | FAIL | REPORT | NEEDS_MORE_DATA | 122.5 | 1 | 2 | 3 | - |

## Failed code checks
- **N15 N15_arabic_windows_nodata_r1**
  - language: 110 English word(s) in an Arabic report: ['The', 'estimate', 'is', 'based', 'on', 'the', 'shipment', 'value', 'given', 'India']
- **N15 N15_arabic_windows_nodata_r2**
  - language: 61 English word(s) in an Arabic report: ['effective', 'Estimate', 'on', 'the', 'shipment', 'value', 'given', 'India', 'charges', 'duty']

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:arabic | 3 | 3929 | 1203 |
| auto:judge | 6 | 24139 | 8608 |
| auto:long | 2 | 16573 | 11213 |
| auto:qa | 2 | 1424 | 640 |
