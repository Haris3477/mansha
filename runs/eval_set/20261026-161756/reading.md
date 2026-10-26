# Reading sheet: evaluation set run 20261026-161756 (repeats sitting 3: pass 1 N10; pass 2 C1–C4)

Read by Claude (Mac chat), 26 Oct 2026 ~16:45 Dubai: every report/notice, phase_log.md, QA problems, router requests table. Pipeline code = 2d8751f.

Router before: Dots3 31/50 → 19 left → k = 5; no cooldowns; no router calls earlier today. After: Dots3 33/50 (24 h window), no cooldowns.
Serving: Researcher + Builder Dots3 in every call (11 `long`); judge cerebras; Intake groq ×5. Intake Gemini 3.7 first: N10 fast 503 (2.3 s), **C1 timeout 60 s, C2 timeout 60 s**, C3 and C4 not tried (Groq ~1 s).
LLM_ERROR 0, QA ERROR 0 → G17 streak 12. **STOP CONDITION TRIPPED: C1 verdict differs from the baseline (CHECKS_FAILED vs REPORT/ELIGIBLE).**

## C1_windows: CHECKS_FAILED — FAIL (stop condition)
Chain of events:
1. Researcher round 1 (Dots3): code problem, rule ID PSR-IN-R118 in caveats[3] (same as sitting 1's C1, which round 2 fixed).
2. QA round 1 (parts 2/3, 3/3) REJECTED two notes: (a) caveats[7], the e-certificate note: "adds qualifiers 'reportedly' and 'but this is unconfirmed' which are not present in the cited record" — **wrong: the KB record carries that qualifier** (the code check in round 2 says so); QA's fix removed it. (b) caveats[14] box 8/9 note: "unsupported qualifier about retrospective remark"; fix text OK.
3. Researcher round 2 followed QA's fix → caveats[7] now states as plain fact what its record qualifies with "reportedly" → the 7.6e qualifier code check fails → one revision used → CHECKS_FAILED.
4. User sees the safe notice ("Mansha couldn't verify this result…"). Safe, but a correct eligible case got no report.
Diagnosis: a QA correction that removes a KB qualifier collides with the code's keep-the-qualifier rule (7.6e), and the shared single revision can't recover. The 7.6i shield only protects notes code wrote verbatim (caveats 5, 10, 11 here), not this model-written note. Related: problem 99 (N15 safe CHECKS_FAILED from a QA/code conflict) and the stale e-certificate KB note (fact base: CBIC Instruction 28/2022 is PRIMARY since 17 Oct) — QA's instinct matches the fact base; the KB is out of date.

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS
- [x] names the missing 6-digit HS code for the emollients (row 2), saving 12000.00 AED only-if — PASS
- "What's still needed" asks for a whole bill of materials (with the row-2 gap in brackets): wider than needed, not wrong.
- E-certificate note reworded without "reportedly" ("which Mansha has read only through secondary reports") and passed the code check.
- Researcher 111.8 s, Builder 78.4 s on Dots3 (G16).

## C2_chargers: REPORT / NOT_ELIGIBLE — PASS
- [x] summary names final manufacture, minimal operations, tariff shift and VA — PASS (better than sitting 1)
- No slip 86 this time.

## C3_windows_nodata: REPORT / NEEDS_MORE_DATA — PASS
- [x] asks shipment value, BOM, declaration — PASS; no duplicate; no how-saving
- [x] **slip 95 confirmed:** summary "Please provide the required details as listed in the checklist below" (they are in "What's still needed").
- New 4th "What's still needed" item: "Confirm whether the factory is located outside a free zone and is registered" — user data that affects the claim; acceptable.
- QA round 1 rejected the e-certificate note in the **opposite** direction to C1 (wanted "reportedly … unconfirmed" kept) → round 2 approved. Same stale note, two QA verdicts.

## C4_plastic: REPORT / NO_PREFERENCE — PASS
- [x] excluded, MFN 15% applies, no steps — PASS
- [ ] **slip 95 by reading, missed by the anchor:** summary "Please refer to the claim checklist below for further steps" — a NO_PREFERENCE report has no checklist. Grader gap: anchor 95 did not fire on "claim checklist below".
- "the CEPA rate … is excluded" wording (N11 slip, 25 Oct).

## Findings
1. **C1 CHECKS_FAILED (stop condition):** QA removes a KB qualifier → 7.6e fails → no revision left. New problem candidate; links to 99 and to the stale e-certificate KB note. The e-certificate note is now churning QA in 2 of 5 runs (C1, C3).
2. Slip 95 ×2 (C3 anchored, C4 by reading: anchor gap).
3. Intake Gemini 3.7 timeouts: 2 of 5 (C1, C2).
