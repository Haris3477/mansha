# Evaluation set run 20261025-163540

**0/2 runs pass every code check** (expected failures not counted); verdicts correct 0/2; CHECKS_FAILED 2; LLM_ERROR 0; QA rejections 2, overruled 1; router refusals 1; pacing waits 54.0 s; median report time 203.9 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N13_wooden_doors | FAIL | REPORT | NEEDS_MORE_DATA | 203.9 | 2 | 4 | 72 ×1 |
| N14_windows_wrong_hs | XFAIL | CHECKS_FAILED | - | 78.3 | 2 | 1 | - |
| N15_arabic_windows_nodata | FAIL | CHECKS_FAILED | - | 234.2 | 2 | 9 | - |

## Failed code checks
- **N13**
  - verdict: NEEDS_MORE_DATA, expected REGULATORY_GAP_DETECTED
  - anchors: a claim checklist in a report whose verdict allows no claim
- **N14**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected ELIGIBLE
- **N15**
  - status: CHECKS_FAILED, expected REPORT
  - verdict: None, expected NEEDS_MORE_DATA

## Expected failures
- N14: still fails

## Slips (global anchors: known open problems, counted, confirmed by reading)
- problem 72: 1 run(s)
  - N13_wooden_doors [72]: "Ministry of Foreign Trade's 'Certificate of Origin for India"

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 14 | 54122 | 18986 |
| auto:long | 6 | 43541 | 35768 |
| auto:qa | 3 | 2091 | 911 |
