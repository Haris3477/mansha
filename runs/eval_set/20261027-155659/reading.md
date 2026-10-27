# Reading sheet: evaluation set run 20261027-155659 (Dots3 confirmation sitting for fix round 1; code under test 907d5f1, branch claude/fix-round-candidates-design-rz44re)

Read by Claude (Mac chat), 27 Oct ~16:15–16:40 Dubai: all 3 report.md + N10 notice.md, every phase_log.md, researcher_1/2.json (N10, C1, N2), N5/N10/C1 evidence.txt (duty-scope, rule, fee records), C1 qa_1.json, the router's `requests` + `request_attempts` (ids 1148–1183). Offline suite 19/19 at 907d5f1 (runbook list, `test_intake --offline`), 27 Oct 15:55.

**A′ live:** OpenRouter credit bought 27 Oct 15:43 Dubai ($5.22; lifetime $10.22 with June's $5.00, over the 1000/day line); Dots3 (OpenRouter) RPD = 1000 in the router (`models.rpd_limit` and `model_overrides`, 15:47). The 1000/day unlock itself was NOT exercised (12 OpenRouter attempts in the UTC day, under 50).
**Router before (15:49):** R1 in effect (`long` = Dots3, Gemini 3.6, Gemini 3.5; `qa` = Groq; `judge` = Cerebras); no cooldowns; Dots3 router 24 h 49/1000, OpenRouter UTC day 2 attempts; Gemini 3.6 8/20; Groq 26 req / 25,862 tokens; Cerebras 90 req.
**Guard printout:** `long need 12-20, left 983 OK (gemini-3.5 0/20, gemini-3.6 8/20, dots-3 49/1000 (OpenRouter UTC day: 2 attempts; router 24 h: 49))`; `qa need 4-8, left 974 OK (groq 26/1000)`; `judge need 16-56, left 2310 OK (cerebras 90/2400)`. Guard reads the new RPD correctly.
**Router after (~16:20):** Dots3 59/1000 (24 h), UTC day 12 attempts, all ok; Gemini 3.6 8/20 (unused); Groq 30 req / 29,898 tokens; Cerebras 112 req; no cooldowns.

**Result:** 3/4 pass every code check; verdicts 3/4; CHECKS_FAILED 1 (N10); LLM_ERROR 0; QA rejections 3 (all three judged right on reading), overruled 0; router refusals 2 (Cerebras RPM, see below); median 238.2 s.

## Serving models — this IS the Dots3 check
| Case | Seconds | Intake | Researcher r1 | Researcher r2 | Builder |
|---|---|---|---|---|---|
| N5 | 160.3 | Groq 1.25 | Dots3 99.6 | – | Dots3 55.4 |
| N10 | 176.7 | Groq 1.21 | Dots3 75.6 | Dots3 95.7 | – (CHECKS_FAILED) |
| C1 | 238.2 | Groq 1.09 | Dots3 87.8 | Dots3 52.1 | Dots3 52.9 |
| N2 | 293.1 | Groq 1.11 | Dots3 **147.8** | Dots3 44.8 | Dots3 50.1 |
- **Dots3 served 10 of 10 `long` calls, all at ordinal 0, no failover, no Gemini.** Every judge call on Cerebras, every Intake on Groq.
- N2's Researcher r1 took 147.8 s against `PROVIDER_TIMEOUT_OPENROUTER=150000`: 2.2 s from a timeout (the 24–26 Oct "150 s timeout → Gemini rescue" pattern). Watch.
- Router refusals 2: QA round 2 in C1 and N2 each got one router 429 for Cerebras (RPM 5, "1 route … rate-limited") right after the client's own pacing wait (1.5 s / 11.2 s); the client waited 30 s and the retry passed. Client pacing (4/60 s) and the router's RPM window don't line up exactly; cost ~30 s per case, no failure.

## N5_paint_indian_resin: REPORT / ELIGIBLE — PASS
- [x] Indian inputs count as originating only with proof — PASS (summary caution + note 2)
- [x] anchor 97 INDIAN_INPUTS — PASS. Summary ends: "Caution: this result counts your inputs from India as originating, which holds only with proof of their originating status; without that proof they count as non-originating inputs. Keep that proof before relying on this result." (907d5f1 wording, first live)
- [x] no "Indian inputs count automatically" — PASS
- [x] "What's still needed": none (7.9 dropped an HS-code confirmation correctly: tariff lookup found no conflict) — PASS
- [x] no claim stronger/weaker than its source — PASS
- [ ] steps say what their sources say — slip 72 milder: steps 2 and 4–7 carry "Authority: The Ministry of Foreign Trade" for the MoET India e-service steps (actor from the KB record; not caught by the anchor because the step text isn't actor-first). Expected until the KB batch.
- **Reading question (does the caution now say clearly what to do?): YES.** Condition, consequence ("count as non-originating inputs") and action ("Keep that proof before relying on this result") are all there, in KB-consistent words. Remaining gap (small, not this fix's job): it doesn't say whether the result would change without the proof (here it would: ~35% non-originating → VA 65% depends on the resin), and the rule section still never says the resin was counted as originating.
- Finding 3 (merged "Inference:" notes of P-IN-DUTY-SCOPE): NOT exercised in any case: no Researcher output (N5, C1 r1/r2, N2 r1/r2) wrote the two "Inference:" notes of P-IN-DUTY-SCOPE (N5 and C1 used one plain duty-scope note). No check-10 problem.
- Dots3 output is full again: 12 notes, 11 steps (Gemini 3.6 on 041503: 5 notes).

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — FAIL (CHECKS_FAILED) — NEW PROBLEM (code)
- [ ] asks only for the 6-digit HS code of BOM row 2 — FAIL in round 1, fixed in round 2, but the run ended CHECKS_FAILED so the user saw only the notice.
- [x] no whole bill of materials — PASS (both rounds)
- **What happened:**
  1. Round 1 (Dots3): follow-up "Provide the 6-digit HS code for Emollients (BOM row 2) **and for any other non-originating inputs**" and basis "…and possibly other non-originating inputs". The G9 prompt rule was not fully obeyed by Dots3 (Gemini obeyed it on 041503; first Dots3 N10 since 1b).
  2. QA (Cerebras) rejected with 5 corrections, all real on reading: the two "other inputs" additions; step 3's "(the Ministry of Foreign Trade)" not in P-AGR-COO-RULES (W2, slip-72 kind, caught here); caveat 0's "CTSH + VA 40%" not in TOOL:rule_lookup (it is in TOOL:origin / PSR-IN-R046: correct per citation, pedantic); caveat 13's "no currency conversion is done by Mansha" not in TOOL:coo_fee (true).
  3. Round 2 (Dots3) fixed all 5 content points, but turned `follow_up_questions[0]` from a string into an object `{"step": "Provide the 6-digit HS code for Emollients (BOM row 2) as required by the origin rule.", "source_id": "TOOL:origin:33049990"}`. The check stringified it and found "TOOL:origin:33049990'}" in exporter text → problem → QA round 2 skipped → CHECKS_FAILED.
- **Cause (code, not the model):** `mansha/qa.py` `correction_text()` (7.6g, c1151c7) appends "Cite <source_id> in source_id, not in the text." to every correction with a source_id, including corrections on `follow_up_questions[i]`, a plain-string field with no source_id in the schema (`prompts/researcher.md` line 78). Dots3 followed the instruction literally by adding a source_id. First time a QA correction on a follow-up carried a source_id in a live run. **Candidate fix (for the cloud):** no "Cite … in source_id" suffix for fields without a source_id (follow_up_questions), and/or normalize an object follow-up back to its text in code. Also: G9 rule on Dots3 needs another look (round-1 broadening).
- Positive: 7.9 did not drop the input question (finding from 213601 stays fixed); no forced revision from check 7.

## C1_windows: REPORT / ELIGIBLE — PASS (regression)
- [x] qualifies: VA 49% against 45% — PASS
- [x] saving AED 10,000 (table "10000.00 AED") — PASS
- [x] steps to claim — PASS (6 steps incl. retrospective box 9, verification)
- [x] not "all customs duty removed" — PASS
- [x] no "Caution:" sentence, no step marker — PASS
- [x] "What's still needed": none — PASS
- [ ] no claim stronger/weaker — FAIL (G12 confirmed): note "The 0% CEPA rate applies only to Basic Customs Duty and the Agriculture Infrastructure and Development Cess." The KB (P-IN-DUTY-SCOPE) says AIDC is reduced **only for lines in Table II**; the Researcher's round-2 note kept "for lines in Table II" (after QA's correct AIDC correction), the **Builder dropped it**, prose QA approved. Whether 76101000 is a Table II line is not in the evidence, so the report claims an AIDC cut it can't support.
- [ ] steps say what their sources say — slip 72 confirmed ("The Ministry of Foreign Trade offers the Certificate of Origin for India e-service").
- [x] slip 86 confirmed: "The India-UAE CEPA sets a normal (MFN) rate of 10%" (the MFN rate isn't set by the CEPA).
- QA r1 rejected 2 notes: AIDC omission (right, per KB) and "CTSH + VA 45%" in a TOOL:rule_lookup note (W1; same pedantic citation point as N10). Round 2 approved.
- **P1 exercised live for the first time: PASS.** QA r1 part 2: attempt #1 `finish_reason=length` at max_tokens 3000 (2.13 s) → retry at **max_tokens 6000**, OK (2.4 s) (qa_1.json).

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS (97 FREE_ZONE, 3rd live PASS)
- [x] duty reduced 20% → 12.5%, not removed — PASS (table shows "20% (effective 20%)": odd but true)
- [x] likely not eligible for factory registration; confirm with MoET — PASS
- [x] anchor 97 FREE_ZONE — PASS: summary ends "Caution: your factory is in a free zone, so it is likely not eligible for the factory registration needed before applying for the certificate of origin; confirm with the Ministry of Economy and Tourism before relying on this result."; step 1 bold marker "Your factory is in a free zone: see the caution in the summary."
- [x] no duty-free / eliminates / no duty / "cannot claim" — PASS
- [ ] "What's still needed" only user items that could change the result — **FAIL**: "Is the factory located in a free zone? If so, it may not be eligible…", although the message's first sentence says so and the summary caution says it too. Same as sitting 4 (20261026-172224, problem 97 register / G9 row). Researcher r1 and r2 both wrote it; QA approved it twice; the Builder kept it. Now 2 of the last 4 Dots3 N2 runs.
- [ ] no claim stronger/weaker — mostly PASS; slip 96 confirmed ("Since India's form governs entry into India, you should use box 9 on your submission"; drops "for the retrospective mark").
- [ ] steps say what their sources say — slip 72 confirmed ("The Ministry of Foreign Trade provides the 'Certificate of Origin for India' e-service").
- Also: the free-zone point appears 4 times (summary caution, step marker, two notes: the tool note and a reworded KB inference note "you may not be eligible … verify your facility's location status") — repetitive; with the follow-up it reads as if Mansha didn't hear the user.
- QA r1 rejected caveat 7 (added "which may affect the value addition calculation" to the undefined-terms note): right. Round 2 approved.

## P1
Exercised once (C1 QA r1 part 2): length → retry with max_tokens 6000 → OK. PASS.

## Findings
1. **This is the Dots3 check:** Dots3 served 10/10 `long` calls first-try with A′ live (RPD 1000). The 041503 Gemini routing came from the router's own 47/50 count, as suspected.
2. **Fix round 1 on Dots3:** 97 FREE_ZONE PASS (N2), 97 INDIAN_INPUTS PASS with the new consequence + action (N5; reading question YES), C1 regression clean, P1 PASS (first live). **G9 on Dots3: round 1 broadened the question ("and any other inputs"); QA caught it.**
3. **NEW (code): N10 CHECKS_FAILED** because `correction_text()` tells the Researcher to "Cite … in source_id" for a `follow_up_questions` correction; Dots3 turned the question into an object with a source_id and the exporter-text check failed. Fix in the cloud (no suffix for fields without a source_id; maybe normalize object follow-ups in code). This blocks "done" for fix round 1 unless judged a separate pre-existing bug.
4. Known, repeated: N2 asks whether the factory is in a free zone although the user said so (2nd time; problem 97 register / G9); G12 AIDC without "Table II" in C1 (Builder drop); slips 72 (all 4 runs, incl. N5 authority lines), 86 (C1), 96 (N2).
5. Watch: N2 Researcher 147.8 s vs the 150 s OpenRouter timeout; Cerebras RPM 429 from the router twice in QA round 2 despite client pacing (+30 s each, recovered).
6. QA pedantry: "CTSH + VA nn%" in a TOOL:rule_lookup note flagged (number not in that record; it's in TOOL:origin) in 2 cases — correct by the citation rule, costs a revision round.
7. **G17 under R1: 16 counted runs, 1 LLM_ERROR (215953); streak 8.**
