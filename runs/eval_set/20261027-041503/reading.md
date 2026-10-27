# Reading sheet: evaluation set run 20261027-041503 (fix round 1 + 1b + guard; code under test da3ecee, branch claude/fix-round-candidates-design-rz44re at c271cfb)

Read by Claude (Mac chat), 27 Oct ~04:35 Dubai: all 4 report.md, phase_log.md, researcher JSON (steps), the router's `requests` + `request_attempts`. Offline suite 19/19 on the Mac (26 Oct evening; no code change since).

**Router before (04:10):** R1 in effect (`long` = Dots3, Gemini 3.6, Gemini 3.5; `qa` = Groq; `judge` = Cerebras); Dots3 cooldown from 26 Oct expired, no cooldowns; Dots3 **0 attempts since 00:00 UTC** (router 24 h successes: 47); Groq 21,876 tokens; no upstream errors in the last hour.
**Router after (~04:30):** Dots3 2 attempts today (both ok); Gemini 3.6 8 requests in 24 h (RPD 20); Groq 25,862 tokens; no cooldowns.
**Guard cross-check:** request_attempts at the start = 0 Dots3 attempts since 00:00 UTC → the guard line should have read 0/50 (router 24 h: 47). Guard printout (terminal): `long need 12-20, left 41 OK (… dots-3 47/50 (OpenRouter UTC day: 0 attempts; router 24 h: 47))` — the day count matches request_attempts (0). Used = max(router 24 h, UTC-day attempts) by design (eval_set.py ~79), so Dots3 counted as 3 left: correct, because the router also enforces its own sliding window.

**Result:** 4/4 pass every code check; verdicts 4/4; CHECKS_FAILED 0; LLM_ERROR 0; QA rejections 0; router refusals 0; median 92.5 s. One recovered provider failure (Gemini 3.6 503 in N10's Builder → Dots3).

## Serving models — NOT the baseline mix
| Case | Seconds | Intake | Researcher | Builder |
|---|---|---|---|---|
| N5 | 29.4 | Groq 0.99 | **Gemini 3.6** 17.0 | **Gemini 3.6** 8.6 |
| N10 | 129.7 | Groq 1.22 | **Gemini 3.6** 31.9 | Gemini 3.6 503 (9.0 s) → Dots3 69.4 |
| C1 | 166.1 | Groq 0.64 | Dots3 147.2 | **Gemini 3.6** 15.5 |
| N2 | 55.2 | Groq 1.19 | **Gemini 3.6** 29.7 | **Gemini 3.6** 10.8 |
- The router put **Gemini 3.6 first in 7 of 8 `long` calls** while Dots3 had 50 left (all ordinal 0, no Dots3 attempt). Router setting `routing_strategy = smartest`; Dots3 is rank 35 vs 3.6 rank 39. Likely cause (not verified): the router enforces its OWN sliding-24 h RPD, which still counted 47/50 for Dots3 (only 3 left in its view, freeing from ~16:19), so it routed to models with more headroom; a leftover 429/failure penalty from 26 Oct (router.ts PENALTY_PER_429 / PENALTY_PER_FAIL) may add to it. Effect: 3 of 4 Researcher outputs are Gemini 3.6, so this sitting is **not comparable to the Dots3 baseline**, and Gemini 3.6's 20/day is being spent instead of Dots3's.
- Gemini 3.6 Researcher outputs are much thinner: N5 5 notes (sitting-6 Dots3 N2: 14–15), N2 6 notes. No retrospective, direct-shipment or (N5) e-certificate items. All anchors still pass and QA approved; worth knowing for completeness (G-register).

## N5_paint_indian_resin: REPORT / ELIGIBLE — PASS (97 INDIAN_INPUTS first live test: PASS)
- [x] Indian inputs need proof of origin — PASS (summary caution)
- [x] anchor 97 — PASS. Summary ends: "Caution: this result counts your inputs from India as originating, which holds only with proof of their originating status." Phase log: "summary cautions (code): INDIAN_INPUTS".
- [x] no "Indian inputs count automatically" — PASS
- **Reading question (clear in context?):** clear about the *condition*, weak on *consequence and action*. A reader learns that the result depends on proof, but not what happens without it (does the paint still qualify?) or what to do (get origin proof from the Indian resin supplier). Compare N2's caution, which ends with an action ("confirm with MoET before relying on this result"). It also sits after "refer to the checklist below", as in N2. The rule section never says the resin was counted as originating, so the caution has no anchor elsewhere in the report. Suggest: an action/consequence clause, only from KB wording (don't invent the proof document).
- Finding 3 (merged inference notes) NOT exercised: the Gemini Researcher didn't write the SWS/anti-dumping inference notes at all (the duty-scope note covers them as plain "still apply"; "SWS on reduced BCD" is absent). No check-10 problem.
- G14 / formatting: every step is actor-first and starts lower-case ("the Ministry of Economy and Tourism requires factory registration outside a free zone…": garbled, it's the factory that must be outside). Slip 72: "the Ministry of Foreign Trade provides the Certificate of Origin for India e-service…". "All 2 non-originating inputs" (awkward). 86 milder form.

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS (G9 + finding 2)
- [x] "What's still needed": only "Please provide the 6-digit HS code for the non-originating input in BOM row 2 (Emollients)." — PASS
- [x] no "HS-code confirmation dropped" line; **no revision** (1 Researcher round). The question contains "input", though, so the 6bbea54 exemption for a question *without* an input word was not exercised.
- [x] saving 12000.00 AED only-if; no whole BOM — PASS
- Slip 72 ("The Ministry of Foreign Trade provides the Certificate of Origin for India e-service…"); e-cert step keeps "reportedly … (unconfirmed)". Free-zone note no longer shown (G12 better here).

## C1_windows: REPORT / ELIGIBLE — PASS (regression check)
- [x] ELIGIBLE, no "Caution:" sentence, no free-zone step marker — PASS
- Dots3 Researcher: full report (11 notes, the two "Inference:" notes as separate lines, e-cert qualifier kept). Slip 72 + 94 (step 2 "The Ministry of Foreign Trade issues the certificate: log in…"). This is the KB record's own `actor` (P-MOET-COO-INDIA actor = Ministry of Foreign Trade), so 72 now fires whenever that step is actor-first.

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS (97 FREE_ZONE, 2nd live PASS)
- [x] caution at the end of the summary; step 1 bold line "Your factory is in a free zone: see the caution in the summary."; phase log FREE_ZONE — PASS
- [x] duty reduced 20% → 12.5% (table + duty paragraph), not "removed" — PASS
- Gemini 3.6 Researcher: e-cert qualifier only "reportedly" inside the importer step (not 101: qualifier kept). Slip 72. Missing the retrospective and direct-shipment steps (thinner).

## P1
Not exercised (no judge finish_reason=length; all judge calls 3000).

## Findings
1. **All 3 fixes pass live:** 97 FREE_ZONE (N2, 2/2), 97 INDIAN_INPUTS (N5, 1/1), G9 narrow question (N10, no revision); C1 regression clean.
2. **But 6 of 8 Researcher/Builder calls ran on Gemini 3.6**, not Dots3: the router ordered Gemini 3.6 first (probably a leftover Dots3 penalty from 26 Oct). Not comparable to the Dots3 baseline; finding 3 and the 7.9 no-"input" path were not exercised. Repeat on Dots3 before calling fix round 1 done.
3. N5 caution reads clearly as a condition but gives no consequence/action (reading question).
4. Slip 72 in 4/4: actor-first steps reuse the KB actor "Ministry of Foreign Trade" for MoET's India e-service (G14 + 72); Gemini writes actor-first lower-case steps.
5. G17 under R1: 12 runs, 1 LLM_ERROR (215953); streak since then 4.
