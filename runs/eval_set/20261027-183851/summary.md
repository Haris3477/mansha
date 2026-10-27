# Evaluation set run 20261027-183851

**4/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 0; pacing waits 0.0 s; median report time 252.4 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 272.5 | 3 | 5 | 96 ×1 |
| C1_windows | PASS | REPORT | ELIGIBLE | 195.4 | 3 | 4 | - |
| N1_biscuits_usd | PASS | REPORT | ELIGIBLE | 232.3 | 2 | 3 | - |
| N4_windows_exw | PASS | REPORT | ELIGIBLE | 275.4 | 3 | 4 | - |

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 96: 1 run(s)
  - N2_furniture_freezone [96]: 'use box 9'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 16 | 61742 | 21435 |
| auto:long | 11 | 44100 | 76135 |
| auto:qa | 4 | 2804 | 1220 |
