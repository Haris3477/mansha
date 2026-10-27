# Evaluation set run 20261027-180618

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 2, overruled 0; router refusals 1; pacing waits 69.3 s; median report time 244.6 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 253.0 | 3 | 7 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 236.1 | 3 | 7 | - |
| C1_windows | PASS | REPORT | ELIGIBLE | 280.8 | 4 | 9 | - |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 204.1 | 3 | 4 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 27 | 100520 | 31855 |
| auto:long | 13 | 73380 | 57097 |
| auto:qa | 4 | 2788 | 1230 |
