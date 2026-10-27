# Evaluation set run 20261027-041503

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 0; pacing waits 26.2 s; median report time 92.5 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N5_paint_indian_resin | PASS | REPORT | ELIGIBLE | 29.4 | 2 | 3 | 72 ×1 |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 129.7 | 2 | 3 | 72 ×1 |
| C1_windows | PASS | REPORT | ELIGIBLE | 166.1 | 2 | 3 | 72 ×1, 94 ×1 |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 55.2 | 2 | 3 | 72 ×1 |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 4 run(s)
- problem 94: 1 run(s)
  - N5_paint_indian_resin [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'
  - N10_cosmetics_missing_hs [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'
  - C1_windows [72]: 'Ministry of Foreign Trade issues the certificate: log in to the ministry e-services portal, choose t'
  - C1_windows [94]: '- [ ] The Ministry of Foreign Trade issues the certificate: '
  - N2_furniture_freezone [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 12 | 41266 | 12778 |
| auto:long | 8 | 39129 | 25318 |
| auto:qa | 4 | 2788 | 1198 |
