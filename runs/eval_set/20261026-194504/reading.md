# Reading sheet: evaluation set run 20261026-194504 (repeats sitting 6: pass 3 N2, N3, N7, N10; FIRST UNDER R1)

Read by Claude (Mac chat), 26 Oct 2026 ~20:00 Dubai: every report.md, phase_log.md, researcher/QA JSON where a correction or rejection happened, the router's `requests` + `request_attempts` tables. Pipeline code = 2d8751f (frozen); grader eb8098d; brief `docs/cloud/repeats_sitting6_brief.md` (8288a77).

**Router before (19:39–19:44, read-only):** R1 in effect: `long` = Dots3 (OpenRouter), Gemini 3.6, Gemini 3.5; `qa` = Groq GPT-OSS 120B; `judge` = Cerebras; no Gemini 3.7. Dots3 RPD 50 (no A′), 13 left at 19:44 → k = 4. Groq 17,759 / 400,000 tokens (24 h). No cooldowns.
**Router after (~19:58):** Dots3 4 left (9 used), Groq 20,856 tokens, no cooldowns.

**Result:** 3/4 pass every code check; verdicts = baseline 4/4; LLM_ERROR 0; QA ERROR 0; CHECKS_FAILED 0; parts NOT reviewed 0; QA rejections 2 (1 right, 1 wrong), overruled 0; router refusals 1 (recovered); median report time 161.2 s.
**Stop rules:** none tripped. N2 FAIL = anchor 97 (known result). No 101 repeat, no judge truncation.

## R1 measurements
| Case | Seconds | Intake s (model) | Researcher | Builder | `long` | `judge` | Failovers |
|---|---|---|---|---|---|---|---|
| N2 | 177.1 | 1.24 (Groq) | Dots3 80.9 + 24.4 | Dots3 63.3 | 3 | 5 | none |
| N3 | 101.4 | 1.18 (Groq) | Dots3 52.9 | Dots3 44.2 | 2 | 3 | none |
| N7 | 145.4 | 1.21 (Groq) | Dots3 57.7 | Dots3 84.7 | 2 | 2 | none |
| N10 | 191.3 | 1.22 (Groq) | Dots3 96.9 + 27.0 | **Gemini 3.6** 14.0 (phase 58.8 s incl. prose QA waits) | 3 | 6 | none |

- **Intake: ~1.2 s on Groq in 4 of 4** (before R1: ~61 s Gemini 3.7 timeout in 12 of 21 repeat runs). R1 removed the Intake timeouts as intended.
- **Failovers: 0.** Every `request_attempts` row this sitting is `ok` on the first model. N10's Builder went to Gemini 3.6 **directly** (attempt ordinal 0, 14.0 s, no Dots3 attempt, no error); the DB doesn't show why the router picked it over Dots3 (Dots3 had ~5 left at that moment). No Gemini 503s.
- **Median 161.2 s** (sitting 5: 178.7 s; G16 bar < 60 s not met: Dots3 calls 24–97 s each).
- **Router refusal (counted, not a fail, E3):** N10 prose QA: pacing waited 14.7 s, router answered 429 "1 route rate-limited or on cooldown" in 0.02 s, the retry 30 s later served (Cerebras 2.1 s). Not in the `requests` table (refused inside the router). Same kind as 24 Oct 16:46 and 25 Oct C1 (pacing counts requests, not tokens; G11).
- **G17 streak under R1: 4** (4 runs, 0 LLM_ERROR, 0 QA ERROR of any kind).

## N2_furniture_freezone: REPORT / ELIGIBLE — FAIL (anchor 97, known; 4 of 4 in repeats)
- [x] must say: duty reduced 20% → 12.5%, not removed — PASS
- [x] must say: likely not eligible for factory registration; confirm with MoET (problem 57) — PASS (notes 6 and 11)
- [ ] **must say: the summary says the free-zone factory may not be able to register (problem 97) — FAIL.** Summary: "meets the rule of origin … so the CEPA rate can be claimed … estimated saving of 7500.00 AED". The caution is only notes 6 and 11 of 14; checklist step 1 again lists "factory must be outside a free zone" without saying this factory is in one (as sitting 2).
- [x] must not say: duty-free / eliminates / no duty / "the free-zone factory cannot claim" — PASS
- [x] problem 56: no "What's still needed" (ELIGIBLE, 0 follow-ups, 0 gaps) — PASS. **Better than sitting 4:** the Researcher kept the tool note "Factory declared in a free zone…" and did not ask back whether the factory is in a free zone.
- [x] G35: PASS (slip 86 milder form only: "Under the India-UAE CEPA, the normal (MFN) rate … is 20%").
- [x] G8 / 72: PASS. Retrospective step says "marked 'ISSUED RETROSPECTIVELY' in box 9" without "of India's certificate form" (the KB summary has it); the box-8/box-9 note is not in this report. Minor, not 96.
- QA round 1 rejected caveat 14 (`TOOL:coo_fee`): "no currency conversion is done by Mansha" is not in the fee tool's record — **right rejection** (the wording comes from the duty tool's note). Round 2 dropped the clause; the Builder then dropped that optional note (15 → 14).

## N3_steel_structures: REPORT / ELIGIBLE — PASS
- [x] both rates (tariff 15%, effective 10%) — PASS; [x] saving measured from 10% (10000.00 AED) — PASS; [x] no 15% saving — PASS
- [x] problem 56: no "What's still needed" — PASS
- [x] G35: PASS with two minor slips: 86 milder form ("Under the India-UAE CEPA, the normal (MFN) rate is 15% (with an effective rate of 10%)"); duty paragraph says IGST "**may** still be payable" where the record says "still apply" (weaker; the mandatory note right below says "still apply").
- [x] G8 / 72: PASS. Step times (3 working days, 1 working day) and the calendar-year record clock all match their records.
- G12: free-zone note in an Abu Dhabi report with no free-zone mention (known). QA 2 parts approved round 1, no truncation (sitting 4's N3 truncation did not recur).

## N7_wire_rods: REPORT / NOT_ELIGIBLE — PASS
- [x] names only the VA failure (30.0% vs 45%); CTSH stated as met — PASS
- [x] no claim steps, no saving, no "subheading change failed" — PASS
- [x] problem 56: no "What's still needed" (7.9 dropped an HS question; 7.6c dropped a build-up follow-up) — PASS
- [x] G35 / G8: PASS (86 milder form: "Under the India-UAE CEPA, the normal (MFN) rate is 7.5%"). Clean otherwise.

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — code PASS; **reading: FAIL on the key's must-not-say**
- [x] names the missing 6-digit HS code for BOM row 2 (Emollients), saving 12000.00 AED only-if — PASS
- [ ] **must not say "asks for a whole bill of materials" — FAIL by the letter.** "What's still needed": "Provide a bill of materials with the origin, 6-digit HS code and value of each input, especially for BOM row 2 (Emollients)…" — the user said the BOM is attached. **Sittings 3 and 4 had the same wording and their readings passed it as "wider than needed, not wrong"**; the baseline (25 Oct) asked only for row 2's code. The key says "asks only for row 2" → this is a fail, and the sitting 3–4 readings were lenient. For the cloud session to decide (re-mark sittings 3–4 or change the key's wording); not a stop rule (verdict unchanged). It's the Researcher's follow-up wording (identical in both rounds; QA approved).
- [x] **slip 72 confirmed:** step 3 "The Ministry of Foreign Trade issues the preferential certificate through the Certificate of Origin for India e-service" (that e-service page is MoET's; the record says requested through the e-service on moet.gov.ae). First anchor-72 hit in the repeats.
- G14: actor-first steps ("The Ministry of Economy and Tourism registers the factory…", "The issuing authority requires…", "The Ministry of Foreign Trade charges…").
- G35 minor (96-kind, no anchor): box note rewritten by the Builder (Gemini 3.6) as "India's origin rules and certificate form specify box 9, **which governs customs entry into India**" — in the KB it's India's *form* that governs entry, not box 9; "retrospective" dropped. No instruction ("must use"), so not slip 96.
- **QA round 1: wrong rejection (G32).** QA said step 7 "misstates the start point of the record-keeping period", but round 1's text ("no less than five years, starting from the end of the year of the date of its issue") is the agreement's own quoted wording in `P-AGR-RECORDS-VERIFICATION`. The 7.6g/7.6i shield covers caveats/gaps only, not steps. Harmless here: a code problem (`origin_rule.source_id` must be PSR-IN-R046) needed the revision anyway, and round 2 used the record's summary wording ("end of the calendar year of issue"), which is also right.
- 101 not repeated: the e-certificate note reworded ("based on secondary sources, not the official text"), qualifier kept, QA didn't touch it. Stale e-certificate note (LiveLaw source) in N2, N3, N10 as before.
- Code warning W1 ("40 not found in TOOL:rule_lookup") judged noise by QA — correct (40 is in the PSR record).

## Findings
1. **R1 works for Intake:** 1.2 s on Groq in 4/4 (was ~61 s in 12/21). No failovers; G17 streak under R1 = 4.
2. Verdicts = baseline 4/4. N2 FAIL on 97 (4 of 4 in repeats), the milder form this time (no ask-back).
3. **N10 reading fail on "whole bill of materials"** (3 of 3 repeats with this wording; earlier readings lenient) → key/reading decision for the cloud.
4. New small finding: QA false rejection of a verbatim agreement quote in a **step** (N10) — the KB shield doesn't cover steps.
5. Slips: 72 ×1 (N10, confirmed); 86 milder form ×4; N3 "may still be payable"; N10 box-9 meaning shift; no 95, no 96, no 67.
6. Router: one 429 after a 14.7 s pacing wait (recovered); N10 Builder routed straight to Gemini 3.6 (cause not visible in the DB).
