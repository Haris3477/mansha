# Evaluation set run 20261026-161756

**4/5 runs pass every code check** (expected failures not counted); verdicts correct 4/5; CHECKS_FAILED 1; LLM_ERROR 0; QA rejections 2, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 134.8 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 197.4 | 2 | 4 | - |
| C1_windows | FAIL | CHECKS_FAILED | - | 175.8 | 2 | 3 | - |
| C2_chargers | PASS | REPORT | NOT_ELIGIBLE | 161.2 | 2 | 2 | - |
| C3_windows_nodata | PASS | REPORT | NEEDS_MORE_DATA | 108.4 | 3 | 5 | 95 ×1 |
| C4_plastic | PASS | REPORT | NO_PREFERENCE | 90.9 | 2 | 2 | - |

## Failed code checks
- **C1**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected ELIGIBLE

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 95: 1 run(s)
  - C3_windows_nodata [95]: 'checklist below'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 16 | 58630 | 18763 |
| auto:long | 11 | 66827 | 55935 |
| auto:qa | 5 | 3469 | 1381 |
