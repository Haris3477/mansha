# Evaluation set run 20261025-162526

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 106.9 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N8_cookware_handles | PASS | REPORT | NOT_ELIGIBLE | 93.8 | 2 | 2 | - |
| N9_smartphones_kits | PASS | REPORT | NOT_ELIGIBLE | 120.1 | 2 | 2 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 138.7 | 3 | 5 | - |
| N11_perfume | PASS | REPORT | NO_PREFERENCE | 77.9 | 2 | 2 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 11 | 39401 | 12816 |
| auto:long | 9 | 46374 | 41160 |
| auto:qa | 4 | 2776 | 1312 |
