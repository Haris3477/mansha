# Reading sheet: evaluation set run 20261025-210917 (repeats, pass 1, sitting 2: N2, N3, N7)

Read by Claude (Mac chat), 25 Oct 2026 ~21:35 Dubai: every report.md and phase_log.md; router requests table for Intake. Pipeline code = 2d8751f (main 04f8932, docs-only since).

Serving: Intake groq ×3, each after a Gemini 3.7 60 s timeout (requests table 21:10:17, 21:14:01, 21:17:29 Dubai) → Intake 61 s in every run. Researcher: Dots3 (N2, N3), Gemini 3.6 (N7, 16 s). Builder: Dots3 ×3. Judge: cerebras. LLM_ERROR 0, QA ERROR 0, verdicts = baseline. G17 streak (repeats): 7.
Router after the sitting: Dots3 46/50 (24 h), no cooldowns, Google successes since 11:00: 5.

## N2_furniture_freezone: REPORT / ELIGIBLE — FAIL (anchor: free-zone caution in the summary)
- Same failure as baseline N2 (problem 97): summary says "meets the rule of origin, so the CEPA rate can be claimed" and saves 7500 AED; the free-zone caution appears only as a note ("Factory declared in a free zone: likely not eligible for the ministry's factory registration; confirm with the ministry").
- Worse in reading: checklist step 1 tells the user to register the factory, "which requires the factory to be located outside a free zone" — the user's factory is in a free zone, so the first step is one the user cannot do, while the result says Eligible. This is the core of problem 97.
- Numbers OK: BCD 20% → 12.5%, saving 7500.00 AED, VA 52.0% ≥ 40%, fee AED 50 (100,000 band).
- Stale e-certificate note again ("reportedly … secondary sources").
- No slip anchors fired.

## N3_steel_structures: REPORT / ELIGIBLE — PASS
- [x] qualifies (CTSH + VA 45.0% ≥ 40%), saving 10000.00 AED (effective 10% → 0%), steps — PASS
- [x] **slip 96 confirmed:** "India's origin rules and certificate form specify box 9, not box 8, so the certificate must use box 9."
- Prose QA round 1 rejected a note that added a record-retention fact; its fix ("The CEPA's 5-year period governs CEPA claims, which is longer than the UAE's 3-year minimum") matches the source; round 2 approved.
- G12: free-zone note for a user who did not mention a free zone. Stale e-certificate note. 1 HS-code follow-up dropped by 7.9 (correct).

## N7_wire_rods: REPORT / NOT_ELIGIBLE — PASS
- [x] VA 30.0% < 45% named as the failed check; CTSH passed; no steps; no saving — PASS
- [ ] **slip 95 (reading only, no anchor):** summary says "Please review the checklist and details below" but a NOT_ELIGIBLE report has no checklist.
- Milder slip-86 form ("Under the India-UAE CEPA, the normal (MFN) rate … is 7.5%").
- Researcher on Gemini 3.6: 16 s (vs 68–107 s on Dots3).

## Findings
1. Problem 97 repeats in N2 (2 of 2 runs now) — reading adds the checklist contradiction (step 1 requires a non-free-zone factory).
2. Intake: the router tries Gemini 3.7 first and it times out at 60 s, in 4 of 7 repeat runs (C2, N2, N3, N7; C1 and C4 got fast 503s, C3 not checked) → ~60 s of every run (G16). Router-order fix candidate (Groq first in `qa`), not a pipeline change.
3. Slip 96 in 2 of 7 repeat runs (C3, N3); slip 95 once (N7).
