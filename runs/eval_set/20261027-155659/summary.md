# Evaluation set run 20261027-155659

**3/4 runs pass every code check** (expected failures not counted); verdicts correct 3/4; CHECKS_FAILED 1; LLM_ERROR 0; QA rejections 3, overruled 0; router refusals 2; pacing waits 12.7 s; median report time 238.2 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 160.3 | 2 | 4 | - |
| N10_cosmetics_missing_hs | FAIL | CHECKS_FAILED | - | 176.7 | 2 | 3 | - |
| C1_windows | PASS | REPORT | ELIGIBLE | 238.2 | 3 | 9 | 72 ×1, 86 ×1, G12 ×1 |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 293.1 | 3 | 8 | 72 ×1, 96 ×1 |

## Failed code checks
- **N10**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected NEEDS_MORE_DATA

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 2 run(s)
- problem 86: 1 run(s)
- problem 96: 1 run(s)
- problem G12: 1 run(s)
  - C1_windows [72]: 'Ministry of Foreign Trade offers the Certificate of Origin for India'
  - C1_windows [86]: 'CEPA sets a normal'
  - C1_windows [G12]: 'Agriculture Infrastructure'
  - N2_furniture_freezone [72]: "Ministry of Foreign Trade provides the 'Certificate of Origin for India"
  - N2_furniture_freezone [96]: 'you should use box 9'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 24 | 87139 | 33041 |
| auto:long | 10 | 66969 | 71257 |
| auto:qa | 4 | 2788 | 1248 |
