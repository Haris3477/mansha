# Evaluation set run 20261026-194504

**3/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 2, overruled 0; router refusals 1; pacing waits 14.7 s; median report time 161.2 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N2_furniture_freezone | FAIL | REPORT | ELIGIBLE | 177.1 | 3 | 5 | - |
| N3_steel_structures | PASS | REPORT | ELIGIBLE | 101.4 | 2 | 3 | - |
| N7_wire_rods | PASS | REPORT | NOT_ELIGIBLE | 145.4 | 2 | 2 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 191.3 | 3 | 6 | 72 ×1 |

## Failed code checks
- **N2**
  - anchors: must say the free-zone caution in the summary

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 1 run(s)
  - N10_cosmetics_missing_hs [72]: 'Ministry of Foreign Trade issues the preferential certificate through the Certificate of Origin for '

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 16 | 61434 | 22283 |
| auto:long | 10 | 56863 | 52317 |
| auto:qa | 4 | 2784 | 1319 |
