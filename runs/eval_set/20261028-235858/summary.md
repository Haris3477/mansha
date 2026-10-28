# Evaluation set run 20261028-235858

**0/2 runs pass every code check** (expected failures not counted); verdicts correct 2/2; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 1; router refusals 0; pacing waits 0.0 s; median report time 377.0 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N15_arabic_windows_nodata_r1 | FAIL | REPORT | NEEDS_MORE_DATA | 485.4 | 4 | 4 | G12 ×1 |
| N15_arabic_windows_nodata_r2 | FAIL | REPORT | NEEDS_MORE_DATA | 268.6 | 4 | 5 | - |

## Failed code checks
- **N15 N15_arabic_windows_nodata_r1**
  - language: expected Arabic, found 2171 Arabic and 3388 Latin letters
- **N15 N15_arabic_windows_nodata_r2**
  - language: 89 English word(s) in an Arabic report: ['India', 'charges', 'duty', 'on', 'the', 'assessable', 'value', 'at', 'import', 'so']

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem G12: 1 run(s)
  - N15_arabic_windows_nodata_r1 [G12]: 'Agriculture Infrastructure'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 9 | 32335 | 11305 |
| auto:long | 8 | 33450 | 71526 |
| auto:qa | 2 | 1424 | 673 |
