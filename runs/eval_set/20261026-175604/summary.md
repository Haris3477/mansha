# Evaluation set run 20261026-175604

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 0; pacing waits 33.6 s; median report time 178.7 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| C1_windows | PASS | REPORT | ELIGIBLE | 179.0 | 2 | 4 | 96 ×1 |
| C2_chargers | PASS | REPORT | NOT_ELIGIBLE | 178.4 | 3 | 3 | 86 ×1 |
| C3_windows_nodata | PASS | REPORT | NEEDS_MORE_DATA | 323.1 | 3 | 7 | 95 ×1 |
| C4_plastic | PASS | REPORT | NO_PREFERENCE | 88.8 | 2 | 2 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 86: 1 run(s)
- problem 95: 1 run(s)
- problem 96: 1 run(s)
  - C1_windows [96]: 'use box 9'
  - C2_chargers [86]: 'CEPA provides a normal'
  - C3_windows_nodata [95]: 'checklist below'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 16 | 55129 | 16242 |
| auto:long | 10 | 51489 | 43125 |
| auto:qa | 4 | 2775 | 1039 |
