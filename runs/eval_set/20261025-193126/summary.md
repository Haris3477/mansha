# Evaluation set run 20261025-193126

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 1; pacing waits 14.9 s; median report time 171.8 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| C1_windows | PASS | REPORT | ELIGIBLE | 194.9 | 3 | 7 | - |
| C2_chargers | PASS | REPORT | NOT_ELIGIBLE | 177.6 | 2 | 2 | 86 ×1 |
| C3_windows_nodata | PASS | REPORT | NEEDS_MORE_DATA | 165.9 | 3 | 5 | 96 ×1 |
| C4_plastic | PASS | REPORT | NO_PREFERENCE | 74.3 | 2 | 2 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 86: 1 run(s)
- problem 96: 1 run(s)
  - C2_chargers [86]: 'CEPA provides a normal'
  - C3_windows_nodata [96]: 'box 9 should be used'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 16 | 54410 | 17794 |
| auto:long | 10 | 52446 | 46859 |
| auto:qa | 4 | 2775 | 1131 |
