# Evaluation set run 20261027-163642

**2/4 runs pass every code check** (expected failures not counted); verdicts correct 3/4; CHECKS_FAILED 1; LLM_ERROR 0; QA rejections 4, overruled 0; router refusals 1; pacing waits 36.9 s; median report time 221.3 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N10_cosmetics_missing_hs | FAIL | CHECKS_FAILED | - | 151.2 | 2 | 6 | - |
| N2_furniture_freezone | FAIL | REPORT | ELIGIBLE | 221.3 | 3 | 8 | 72 ×1 |
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 337.1 | 3 | 7 | 72 ×1 |
| C1_windows | PASS | REPORT | ELIGIBLE | 155.7 | 2 | 4 | - |

## Failed code checks
- **N10**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected NEEDS_MORE_DATA
- **N2**
  - anchors: must not say duty removed wording: 'eliminate'

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 2 run(s)
  - N2_furniture_freezone [72]: 'Certificate of Origin for India through the Ministry of Foreign Trade'
  - N5_paint_indian_resin [72]: "Ministry of Foreign Trade provides the 'Certificate of Origin for India"

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 25 | 97542 | 30820 |
| auto:long | 10 | 65157 | 59013 |
| auto:qa | 4 | 2788 | 1221 |
