# Evaluation set run 20261028-170121

**2/2 runs pass every code check** (expected failures not counted); verdicts correct 2/2; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 1; pacing waits 2.2 s; median report time 236.4 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 169.3 | 2 | 4 | 94 ×1 |
| C1_windows | PASS | REPORT | ELIGIBLE | 303.5 | 3 | 8 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 94: 1 run(s)
  - N5_paint_indian_resin [94]: "*Authority: Not in Mansha's sources"

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 12 | 43736 | 14563 |
| auto:long | 5 | 31383 | 39886 |
| auto:qa | 2 | 1395 | 573 |
