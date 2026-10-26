# Reading sheet: evaluation set run 20261026-175604 (repeats sitting 5: pass 3 C1–C4)

Read by Claude (Mac chat), 26 Oct 2026 ~18:15 Dubai: every report, phase_log.md, QA problems, router requests table. Pipeline code = 2d8751f; grader 1da8e77.

**R1 was NOT in effect for this sitting.** Router check at 18:08 and 18:10 (read-only): `long` = Gemini 3.7, Dots3, Gemini 3.6, Gemini 3.5; `qa` = Gemini 3.7, Groq. So this sitting ran under the same router conditions as sittings 1–4 (counts as a normal repeat, not as "since R1").
Router before: Dots3 37/50 → 13 left → k = 4. Groq 16,845 / 400,000 tokens (24 h). No cooldowns.
Serving: Researcher + Builder Dots3 in every call (10 `long`); judge cerebras; Intake groq ×4. Intake Gemini 3.7 timeout first: C1, C2, C3 yes (61 s each); C4 no (1 s). Failovers: Gemini 3.6 returned 503 twice (14:06:33 after 38 s, 14:08:17) and Dots3 served both calls.
LLM_ERROR 0, QA ERROR 0, verdicts = baseline. G17 streak since sitting 4's C1: 4.

## C1_windows: REPORT / ELIGIBLE — PASS
- Qualifies, saving 10000.00 AED, steps. Summary points to the checklist correctly.
- [x] **slip 96 confirmed:** "use box 9 for remarks as required by India's certificate form, because India's form governs entry into India".
- Stale e-certificate note again.

## C2_chargers: REPORT / NOT_ELIGIBLE — PASS
- Summary names all four failed checks.
- [x] **slip 86 confirmed (full form):** "The India-UAE CEPA provides a normal (MFN) rate of 20%".
- Prose QA round 1 caught a slip-95 summary ("exporter should follow the checklist below" in a report with no checklist) and fixed it: prose QA working on 95.

## C3_windows_nodata: REPORT / NEEDS_MORE_DATA — PASS
- Asks BOM, declaration, shipment value.
- [x] **slip 95 confirmed:** "as listed in the checklist below" (they are in "What's still needed").
- QA round 1 rejected a caveat with a 45% figure not in its record (code warning judged real); round 2 fixed. QA round 2 took 36.5 s (pacing wait).
- E-certificate note reworded ("comes from secondary sources, not the official text of the agreement") and passed.

## C4_plastic: REPORT / NO_PREFERENCE — PASS
- Excluded, MFN applies, no steps, no checklist reference. Clean.

## Findings
1. 4/4 pass, verdicts = baseline. Slips: 96 (C1), 86 full (C2), 95 (C3); prose QA fixed another 95 in C2.
2. Intake timeouts 3 of 4 (R1 not applied).
3. Gemini 3.6 also returned 503s (2 calls) — relevant to R1: after removing 3.7, 3.6 is the next hop after Dots3.
