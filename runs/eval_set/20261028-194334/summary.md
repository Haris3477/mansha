# Evaluation set run 20261028-194334

**1/3 runs pass every code check** (expected failures not counted); verdicts correct 2/3; CHECKS_FAILED 1; LLM_ERROR 0; QA rejections 2, overruled 0; router refusals 2; pacing waits 6.5 s; median report time 318.0 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N4_windows_exw | FAIL | REPORT | ELIGIBLE | 314.9 | 3 | 8 | - |
| N9_smartphones_kits | PASS | REPORT | NOT_ELIGIBLE | 321.1 | 4 | 3 | - |
| N13_wooden_doors | FAIL | CHECKS_FAILED | - | 205.7 | 2 | 2 | - |

## Failed code checks
- **N4**
  - QA: QA (round 2) FAILED; QA (round 2): NOT reviewed
- **N13**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected REGULATORY_GAP_DETECTED

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 13 | 44877 | 16049 |
| auto:long | 9 | 56850 | 70551 |
| auto:qa | 3 | 2082 | 937 |
