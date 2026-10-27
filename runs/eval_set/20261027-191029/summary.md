# Evaluation set run 20261027-191029

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 1; pacing waits 26.5 s; median report time 192.8 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| C1_windows | PASS | REPORT | ELIGIBLE | 129.7 | 2 | 3 | - |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 168.2 | 2 | 3 | - |
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 254.5 | 3 | 8 | G12 ×2 |
| N1_biscuits_usd | PASS | REPORT | ELIGIBLE | 217.5 | 3 | 5 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem G12: 1 run(s)
  - N5_paint_indian_resin [G12]: 'Agriculture Infrastructure' | 'AIDC'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 19 | 75207 | 24418 |
| auto:long | 10 | 56851 | 63641 |
| auto:qa | 4 | 2793 | 1224 |
