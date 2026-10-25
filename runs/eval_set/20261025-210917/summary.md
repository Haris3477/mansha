# Evaluation set run 20261025-210917

**2/3 runs pass every code check** (expected failures not counted); verdicts correct 3/3; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 208.2 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N2_furniture_freezone | FAIL | REPORT | ELIGIBLE | 223.5 | 2 | 4 | - |
| N3_steel_structures | PASS | REPORT | ELIGIBLE | 208.2 | 3 | 5 | 96 ×1 |
| N7_wire_rods | PASS | REPORT | NOT_ELIGIBLE | 115.5 | 2 | 2 | - |

## Failed code checks
- **N2**
  - anchors: must say the free-zone caution in the summary

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 96: 1 run(s)
  - N3_steel_structures [96]: 'use box 9'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 11 | 37909 | 13212 |
| auto:long | 7 | 32108 | 33715 |
| auto:qa | 3 | 2090 | 927 |
