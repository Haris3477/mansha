# Evaluation set run 20261028-215427

**2/4 runs pass every code check** (expected failures not counted); verdicts correct 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 1, overruled 0; router refusals 6; pacing waits 26.7 s; median report time 166.7 s.

| Case | Result | Status | Verdict | Seconds | long | judge | Slips |
|---|---|---|---|---|---|---|---|
| N4_windows_exw | FAIL | REPORT | ELIGIBLE | 116.7 | 3 | 4 | - |
| N2_furniture_freezone | PASS | REPORT | ELIGIBLE | 173.6 | 2 | 4 | - |
| N10_cosmetics_missing_hs | PASS | REPORT | NEEDS_MORE_DATA | 159.8 | 2 | 4 | - |
| N15_arabic_windows_nodata | FAIL | REPORT | NEEDS_MORE_DATA | 428.1 | 4 | 13 | - |

## Failed code checks
- **N4**
  - report check: 1 problem(s): status code 'PASS' in the report: …ule of origin. final manufacture check: PASS; minimal operations check: PASS; CTSH:…
- **N15**
  - QA: QA (round 2) FAILED; QA (round 2): NOT reviewed
  - prose QA: Prose QA (round 1) FAILED; Prose QA (round 1): NOT reviewed

## Slips (global anchors: known open problems, counted, confirmed by reading)
- none

## Requests and tokens
| Chain | Requests | Prompt | Completion |
|---|---|---|---|
| auto:judge | 25 | 63126 | 22528 |
| auto:long | 11 | 49533 | 51416 |
| auto:qa | 4 | 2812 | 1277 |
