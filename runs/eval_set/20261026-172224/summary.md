# Evaluation set run 20261026-172224

**2/5 runs pass every code check** (expected failures not counted); verdicts correct 4/5; CHECKS_FAILED 0; LLM_ERROR 1; QA rejections 0, overruled 0; router refusals 1; pacing waits 55.0 s; median report time 240.5 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N2_furniture_freezone | FAIL | REPORT | ELIGIBLE | 268.2 | 2 | 4 | 96 ×1 |
| N3_steel_structures | FAIL | REPORT | ELIGIBLE | 341.9 | 3 | 8 | - |
| N7_wire_rods | PASS | REPORT | NOT_ELIGIBLE | 152.3 | 2 | 2 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 212.9 | 3 | 5 | - |
| C1_windows | FAIL | LLM_ERROR | - | 211.1 | 1 | 0 | - |

## Failed code checks
- **N2**
  - anchors: must say the free-zone caution in the summary
- **N3**
  - QA: QA (round 1) FAILED; QA (round 1): NOT reviewed
- **C1**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected ELIGIBLE

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 96: 1 run(s)
  - N2_furniture_freezone [96]: 'you should use box 9'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 19 | 69066 | 26379 |
| auto:long | 11 | 44068 | 62651 |
| auto:qa | 5 | 3483 | 1589 |
