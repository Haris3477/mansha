# Evaluation set run 20261025-151048

**2/3 runs pass every code check** (expected failures not counted); verdicts correct 3/3; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 0; pacing waits 27.3 s; median report time 202.7 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N4_windows_exw | PASS | REPORT | ELIGIBLE | 257.8 | 3 | 7 | 72 ×1 |
| N5_paint_indian_resin | FAIL | REPORT | ELIGIBLE | 202.7 | 2 | 3 | - |
| N7_wire_rods | PASS | REPORT | NOT_ELIGIBLE | 155.1 | 2 | 2 | 86 ×1 |

## Failed code checks
- **N5**
  - privacy: input amount 10000.00 (Paint additives) appears

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 1 run(s)
- problem 86: 1 run(s)
  - N4_windows_exw [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'
  - N7_wire_rods [86]: 'CEPA sets a normal'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 12 | 45970 | 13035 |
| auto:long | 7 | 38540 | 42575 |
| auto:qa | 3 | 2090 | 831 |
