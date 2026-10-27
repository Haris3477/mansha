# Evaluation set run 20261027-041404

**0/4 runs pass every code check** (expected failures not counted); verdicts correct 0/4; CHECKS_FAILED 0; LLM_ERROR 4; QA rejections 0, overruled 0; router refusals 0; pacing waits 0.0 s; median report time None s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | FAIL | LLM_ERROR | - | 0.1 | 0 | 0 | - |
| N10_cosmetics_missing_hs | FAIL | LLM_ERROR | - | 0.0 | 0 | 0 | - |
| C1_windows | FAIL | LLM_ERROR | - | 0.0 | 0 | 0 | - |
| N2_furniture_freezone | FAIL | LLM_ERROR | - | 0.0 | 0 | 0 | - |

## Failed code checks
- **N5**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected ELIGIBLE
  - intake: no Intake output
  - anchors: must say the Indian-origin proof condition in the summary
- **N10**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected NEEDS_MORE_DATA
  - intake: no Intake output
- **C1**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected ELIGIBLE
  - intake: no Intake output
- **N2**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected ELIGIBLE
  - intake: no Intake output
  - anchors: must say the free-zone caution in the summary

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:qa | 8 | 0 | 0 |
