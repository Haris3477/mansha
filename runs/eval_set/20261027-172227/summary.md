# Evaluation set run 20261027-172227

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 1; pacing waits 0.0 s; median report time 225.0 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 271.2 | 3 | 5 | 72 ×1, 96 ×1 |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 387.6 | 6 | 4 | 96 ×1 |
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 178.7 | 3 | 5 | 72 ×1, G12 ×1 |
| C1_windows | PASS | REPORT | ELIGIBLE | 171.7 | 2 | 3 | 72 ×1 |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 3 run(s)
- problem 96: 2 run(s)
- problem G12: 1 run(s)
  - N10_cosmetics_missing_hs [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'
  - N10_cosmetics_missing_hs [96]: 'you should use box 9'
  - N2_furniture_freezone [96]: 'box 9 to be completed'
  - N5_paint_indian_resin [72]: "Ministry of Foreign Trade operates the e-service 'Certificate of Origin for India"
  - N5_paint_indian_resin [G12]: 'Agriculture Infrastructure'
  - C1_windows [72]: 'Certificate of Origin for India through the Ministry of Foreign Trade'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 17 | 69224 | 24024 |
| auto:long | 14 | 50878 | 68105 |
| auto:qa | 4 | 2788 | 1255 |
