# Evaluation set run 20261026-215953

**0/1 runs pass every code check** (expected failures not counted); verdicts correct 0/1; CHECKS_FAILED 0; LLM_ERROR 1; QA rejections 0, overruled 0; router refusals 1; pacing waits 0.0 s; median report time None s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | FAIL | LLM_ERROR | - | 130.0 | 5 | 0 | - |

## Failed code checks
- **N5**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected ELIGIBLE
  - anchors: must say the Indian-origin proof condition in the summary

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:long | 5 | 0 | 0 |
| auto:qa | 1 | 696 | 293 |
