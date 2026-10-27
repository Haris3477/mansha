# Reading sheet: evaluation set run 20261027-172227 (fix round 1d live check; code under test 911109b, branch claude/fix-round-1-handoff-vluyq2)

Read by Claude (Mac chat), 27 Oct ~17:42–18:00 Dubai: all 4 report.md, every phase_log.md, researcher_1/2.json (N10, C1), the router's `requests` + `request_attempts` (ids 1222–1255). Offline suite 19/19 at 911109b (runbook list, `test_intake --offline`; new 1d checks pass in test_qa incl. the N10 16:36 replay, test_pipeline; 'eliminat' checks in test_eval_set), 27 Oct 17:21.

**Re-grade of 163642** (`python -m scripts.eval_set --grade runs/eval_set/20261027-163642`): **3/4 PASS** (C1, N2, N5 PASS; N10 CHECKS_FAILED, old code). N2's 'eliminat' false alarm gone. `--grade` printed only; 163642's summary.md/reading.md unchanged.

**Router before (17:22):** R1 in effect; no cooldowns (Cerebras included); Dots3 RPD 1000, router 24 h 58, OpenRouter UTC day 22 attempts; Gemini 3.6 8/20; Groq 29 req / 29,057 tokens; Cerebras 120 req.
**Guard printout:** `long need 12-20, left 974 OK (gemini-3.5 0/20, gemini-3.6 8/20, dots-3 58/1000 (OpenRouter UTC day: 22 attempts; router 24 h: 58))`; `qa need 4-8, left 971 OK (groq 29/1000)`; `judge need 16-56, left 2280 OK (cerebras 120/2400)`.
**Router after (~17:42):** OpenRouter UTC day 34 attempts (32 ok, 2 error); router 24 h counts are lower than before because 26/27 Oct entries aged out of the sliding window (Dots3 58, Groq 28 / 28,028 tokens, Cerebras 119, Gemini 3.6 8); no cooldowns. This run: 12 Dots3 successes, 4 Groq, 17 Cerebras requests (all ok).

**Network drop during N2's Builder (~17:29–17:33 Dubai):** OpenRouter returned HTTP 200 with a non-JSON body after 94.7 s (router → 502), then `fetch failed (ENOTFOUND openrouter.ai)` and `ENOTFOUND generativelanguage.googleapis.com` (DNS gone = the Mac's connection dropped; the Gemini attempts were failovers, not served). The client's busy waits held on; Dots3 served the Builder at 17:33 (59.7 s). Builder phase 275.6 s. No user-visible effect.

**Result:** **4/4 pass every code check**; verdicts 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA (Researcher) rejections 1 (N10 r1), overruled 0; prose QA rejections 1 (N5 r1); median ~225 s.

## Serving models — valid 1d check
| Case | Seconds | Intake | Researcher r1 | Researcher r2 | Builder |
|---|---|---|---|---|---|
| N10 | 271.2 | Groq 1.03 | Dots3 141.0 | Dots3 42.4 | Dots3 80.2 |
| N2 | 387.6 | Groq 1.41 | Dots3 106.5 | – | Dots3 (after network failures) 275.6 phase / 59.7 call |
| N5 | 178.7 | Groq 2.24 | Dots3 109.8 | – | Dots3 59.2 |
| C1 | 171.7 | Groq 2.25 | Dots3 101.5 | – | Dots3 63.9 |
- Every Researcher and Builder served by Dots3 at ordinal 0 (N2's Builder: Dots3 after the failed attempts). No Gemini-served call. N10 Researcher r1 141.0 s (9 s under the 150 s timeout).

## QA statuses per round
| Case | QA r1 | QA r2 | Prose QA |
|---|---|---|---|
| N10 | REJECTED (1 correction, right) | APPROVED | APPROVED r1 |
| N2 | APPROVED | – | APPROVED r1 |
| N5 | APPROVED | – | REJECTED r1 → APPROVED r2 |
| C1 | APPROVED | – | APPROVED r1 |
- **1d NOT exercised: no SETTLED in any case** (only N10 had a round 2, and QA r2 approved). No settled corrections to judge.

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS
- [x] asks only for the 6-digit HS code of BOM row 2 — PASS: "Please provide the 6-digit HS code for the non-originating input 'Emollients' (BOM row 2)." (both rounds; G9 obeyed)
- [x] no whole bill of materials — PASS
- [x] summary: can't confirm yet, saving 12000.00 AED only if it qualifies — PASS
- QA r1's one correction: caveat 12 "…no currency conversion is done by Mansha" not in TOOL:coo_fee — right (same point as 155659). Round 2 fixed it; QA r2 approved.
- [ ] slip 72 confirmed ("The Ministry of Foreign Trade provides the Certificate of Origin for India e-service…"); slip 96 confirmed ("since India's form governs entry into India, you should use box 9").
- Free-zone KB note shown to a user who said nothing about free zones (G12 register: acceptable). "UAE law … 3 years … so you must keep records for 5 years": fine (the CEPA requirement).
- First N10 REPORT on Dots3 since fix round 1 (155659 and 163642 were CHECKS_FAILED).

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS
- [x] duty reduced, not removed — PASS (summary "reduces the Basic Customs Duty from the normal rate"; no "eliminat" anywhere)
- [x] likely not eligible for factory registration; confirm with MoET — PASS
- [x] anchor 97 FREE_ZONE — PASS (summary caution; step 1 bold marker)
- [x] "What's still needed": none — PASS. **1c free-zone drop fired live for the first time:** "follow_up_questions[0]: free-zone question dropped, the user already said the factory is in a free zone: 'Is the manufacturing facility located in a free zone?'"
- [ ] slip 96 confirmed: "India's origin rules and certificate form require box 9 to be completed".
- Free-zone point still appears 4× (caution, marker, tool note, and the raw KB note "Inference: a producer in a free zone is likely not eligible…" with its "Inference:" label shown to the user). Summary doesn't give the rates (12.5% vs 20%): they're in the duty table.

## N5_paint_indian_resin: REPORT / ELIGIBLE — PASS
- [x] anchor 97 INDIAN_INPUTS — PASS (same caution: condition + consequence + action)
- [x] no "Indian inputs count automatically" — PASS; "What's still needed": none
- Prose QA r1 rejected the summary's "Please follow the checklist below to claim the preference." (not in FACTS; problem 95 kind): fixed in r2.
- [ ] slip 72 confirmed ("The Ministry of Foreign Trade operates the e-service 'Certificate of Origin for India'"). 
- [ ] G12 confirmed, mild: note "The CEPA rate of 0% reduces the Basic Customs Duty (BCD) and the Agriculture Infrastructure and Development Cess only for lines in Table II…" on a Table I line: qualifier kept (not wrong), but AIDC is irrelevant here and reads as if it might apply.
- Raw "Inference: a producer in a free zone…" KB note shown to a user who isn't in a free zone.

## C1_windows: REPORT / ELIGIBLE — PASS
- [x] VA 49% vs 45%, saving 10000.00 AED, steps, no "duty removed", no "Caution:", no marker — PASS
- [ ] slip 72 confirmed ("Certificate of Origin for India through the Ministry of Foreign Trade").
- **Finding 3 exercised:** "caveats[12]/[13]: note written from the KB, qualifier kept (P-IN-DUTY-SCOPE)"; the report shows the two KB notes "Inference: SWS is charged on the reduced BCD (no CEPA-specific text found)." and "Inference: anti-dumping and safeguard duties still apply (no exemption found)." No check-10 problem. Side effect: the "Inference:" label and the abbreviation "SWS" reach the user verbatim (KB wording).
- No G12 this time.

## P1
Not exercised (no finish_reason=length).

## Findings
1. **4/4 code PASS, verdicts 4/4, 0 CHECKS_FAILED, 0 LLM_ERROR** on Dots3 (every Researcher and Builder at ordinal 0).
2. **1d not exercised** (no QA round-2 rejection anywhere; only N10 had a round 2, approved). Evidence for 1d is offline only (incl. the 16:36 replay).
3. **1c free-zone drop fired live correctly in N2.** 1c follow-up path (correction on a follow-up / object follow-up) still not exercised live.
4. Finding 3 (P-IN-DUTY-SCOPE inference notes restored, qualifier kept) exercised in C1, no check-10 problem.
5. Re-grade 163642: 3/4 (N2 false alarm fixed).
6. Network drop (DNS) during N2's Builder: recovered by the client's busy waits, +~200 s.
7. Known slips: 72 in 3 runs (N10, N5, C1), 96 in 2 (N10, N2), G12 mild (N5); raw "Inference:" labels and "SWS" reach exporters through verbatim KB notes (N2, N5, C1) — wording for the KB batch.
8. **G17 under R1: 24 counted runs, 1 LLM_ERROR (215953); streak 16.**
