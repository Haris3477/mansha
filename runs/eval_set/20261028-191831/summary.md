# Evaluation set run 20261028-191831

**0/3 runs pass every code check** (expected failures not counted); verdicts correct 3/3; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0, overruled 0; router refusals 11; pacing waits 0.0 s; median report time 174.1 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N4_windows_exw | FAIL | REPORT | ELIGIBLE | 418.0 | 3 | 5 | - |
| N9_smartphones_kits | FAIL | REPORT | NOT_ELIGIBLE | 174.1 | 2 | 3 | - |
| N13_wooden_doors | FAIL | REPORT | REGULATORY_GAP_DETECTED | 84.6 | 3 | 3 | - |

## Failed code checks
- **N4**
  - QA: QA (round 1) FAILED; QA (round 1): NOT reviewed
  - prose QA: Prose QA (round 1) FAILED; Prose QA (round 1): NOT reviewed
- **N9**
  - QA: QA (round 1) FAILED; QA (round 1): NOT reviewed
  - prose QA: Prose QA (round 1) FAILED; Prose QA (round 1): NOT reviewed
- **N13**
  - QA: QA (round 1) FAILED; QA (round 1): NOT reviewed; QA (round 2) FAILED; QA (round 2): NOT reviewed
  - prose QA: Prose QA (round 1) FAILED; Prose QA (round 1): NOT reviewed

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 11 | 0 | 0 |
| auto:long | 8 | 44336 | 59688 |
| auto:qa | 3 | 2082 | 954 |
