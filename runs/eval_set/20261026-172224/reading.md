# Reading sheet: evaluation set run 20261026-172224 (repeats sitting 4: pass 2 N2, N3, N7, N10; pass 3 C1)

Read by Claude (Mac chat), 26 Oct 2026 ~17:55 Dubai: every report, phase_log.md, Researcher/QA JSON where needed, router requests table. Pipeline code = 2d8751f; grader at 1da8e77 (anchor 95 widened; diff: eval_grade.py + test_eval_set.py only).

Router before: Dots3 27/50 → 23 left → k = 5; no cooldowns. After: Dots3 37/50, no cooldowns.
**STOP CONDITIONS TRIPPED: C1 LLM_ERROR; N3 QA part not reviewed (QA ERROR kind). G17 streak: 12 entering, 13 after N2, broken by N3 (QA round 1 FAILED, part not reviewed) and again by C1 (LLM_ERROR). Streak now 0 (N7, N10 after N3 → 2 before C1; 0 after C1).**

Intake Gemini 3.7 timeout first: N2 yes, N3 yes, N7 yes, N10 no, C1 no (Groq ~1 s).

## C1_windows: LLM_ERROR — FAIL (stop)
- Researcher: router attempt 1 Dots3 timed out at 150 s (requests 13:41:11 UTC), failover to Gemini 3.7, aborted at 210 s (13:42:11). Router: "All 2 routed attempts failed (timeout ×2) … retry time budget 45s exceeded — one failover hop is always allowed". Client gave up at 210 s of its 240 s budget. Gemini 3.5/3.6 were never tried.
- Same Dots3 150 s timeout as 25 Oct (then rescued by Gemini 3.5); today the next hop was Gemini 3.7, which timed out on every call today (Intake ×6 + this one).
- G17 under A: the bar (10 in a row) was met at 12, then broken. Cause: provider (Dots3 slow + Gemini 3.7 down) and the router's 45 s failover budget.

## N3_steel_structures: REPORT / ELIGIBLE — FAIL (QA part 2/3 NOT reviewed)
- QA part 2/3: first call 429 ("all models exhausted", cerebras) right after a 55.0 s pacing wait; then two calls truncated (finish_reason=length) at the part budget → part ERROR → "output NOT reviewed by QA in full". The report shipped (Builder + prose QA OK). G11 bar ("no NOT reviewed") broken; problem 80 kind (pacing counts requests, not tokens) + part-budget truncation.
- Part 1/3 also had a QA correction removed by code validation (classification confidence is not a claim).
- Content: saving 10000 AED, CTSH + VA 45% OK; box 8/9 note neutral ("India's form determines the entry"): no 96.
- Prose QA round 1 rejected "Only originating materials from India can be counted" (added "only"); fix correct.

## N2_furniture_freezone: REPORT / ELIGIBLE — FAIL (anchor: free-zone caution in the summary)
- Problem 97 again (3 of 3 N2 runs), **worse form**: the Researcher dropped the tool's note "Factory declared in a free zone: likely not eligible for the ministry's factory registration" (in evidence, line 48) and instead wrote a "What's still needed" item asking "Is the manufacturing factory located in a free zone?" — the user's first sentence says it is. An ELIGIBLE report with a "What's still needed" section re-asking stated user data (problems 85/56, G9). QA approved all 3 parts.
- Checklist step 1 still requires a factory outside a free zone (contradiction as in sitting 2).
- **Slip 96 confirmed:** "you should use box 9".
- Stale e-certificate note again.

## N7_wire_rods: REPORT / NOT_ELIGIBLE — PASS
- VA failure named; no checklist; no slip 95 this time. Clean.

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS
- Names the missing Emollients HS code; adds a free-zone question to "What's still needed" (user did not say; acceptable).
- [ ] **slip 95 by reading, missed by the widened anchor:** summary "Please see the checklist for the required information" — the items are in "What's still needed" (anchor 95 catches "checklist … below", not "see the checklist for").
- Prose QA fix correct ("only" qualifier).

## Findings
1. G17: streak broken (C1 LLM_ERROR; N3 QA not reviewed). Root causes: Dots3 150 s timeout + Gemini 3.7 failing all day + the router's 45 s failover budget (only one hop); judge 429 after pacing + part-budget truncation.
2. Problem 97 in N2: now 3 of 3, and this time the user-declared free zone is asked back.
3. Slip 95 anchor still misses "see the checklist for" (N10).
4. Intake Gemini 3.7 timeouts: 3 of 5 today (N2, N3, N7); Gemini 3.7 had no successful call all day.
