# Evaluation set run 20261026-213601

**2/3 runs pass every code check** (expected failures not counted); verdicts correct 2/3; CHECKS_FAILED 1; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 293.4 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 156.0 | 3 | 5 | - |
| N5_paint_indian_resin | FAIL | CHECKS_FAILED | - | 172.9 | 2 | 3 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 430.8 | 5 | 5 | - |

## Failed code checks
- **N5**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected ELIGIBLE
  - anchors: must say the Indian-origin proof condition in the summary

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 13 | 51250 | 15356 |
| auto:long | 10 | 53077 | 40012 |
| auto:qa | 3 | 2089 | 959 |
