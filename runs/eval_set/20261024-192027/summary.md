# Evaluation set run 20261024-192027

**5/7 runs pass every code check** (expected failures not counted); verdicts correct 2/4; CHECKS_FAILED 0; LLM_ERROR 2; QA rejections 2, overruled 0; router refusals 2; pacing waits 0.0 s; median report time 144.6 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| C1_windows | PASS | REPORT | ELIGIBLE | 183.0 | 3 | 5 | 72 ×1 |
| C2_chargers | PASS | REPORT | NOT_ELIGIBLE | 106.2 | 3 | 3 | - |
| C3_windows_nodata | FAIL | LLM_ERROR | - | 1.2 | 1 | 0 | - |
| C4_plastic | FAIL | LLM_ERROR | - | 1.0 | 1 | 0 | - |
| S1_vague | PASS | NEEDS_INPUT | - | 0.8 | 0 | 0 | - |
| S2_dates | PASS | NOT_COVERED | - | 1.6 | 0 | 0 | - |
| S3_arabic_turkiye | PASS | NOT_COVERED | - | 1.1 | 0 | 0 | - |

## Failed code checks
- **C3**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected NEEDS_MORE_DATA
- **C4**
  - status: LLM_ERROR, expected REPORT
  - verdict: None, expected NO_PREFERENCE

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 1 run(s)
  - C1_windows [72]: 'Ministry of Foreign Trade provides the Certificate of Origin for India'

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 8 | 28999 | 9746 |
| auto:long | 8 | 39838 | 21388 |
| auto:qa | 7 | 4812 | 2054 |
