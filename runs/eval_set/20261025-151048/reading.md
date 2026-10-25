# Reading sheet: evaluation set run 20261025-151048

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## N4_windows_exw: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `N4_windows_exw/report.md`

- [x] must say: Ex-Works threshold 40%: PASS ("43.0% on an Ex-Works basis, meeting the 40% threshold (45% minus 5 points on an Ex-Works basis)")
- [ ] must say: 8-digit codes differ between the UAE and India; confirm: **half met.** The confirm request is there (follow-up: "confirm … 76101000, as the closest match to the given HS code 76101090"; classification confidence medium + confirm advice), but the reason (8-digit codes are national and differ between the UAE and India, the tariff lookup's own note) is not in the report (minor)
- [x] must not say: 45% as the threshold applied: PASS
- [x] problem 56: PASS. The one follow-up is the HS confirmation; kept correctly by 7.9 because the tariff lookup wrote a note (no exact 8-digit match). QA round 1 rewrote it (the first version asked to confirm the code the user gave)
- [x] G35: PASS (notes "UAE law sets a shorter 3-year minimum … CEPA's 5 years govern" and the build-down/build-up note match the KB)
- [ ] G8 / 72: **FAIL, slip 72 confirmed** (step "The Ministry of Foreign Trade provides the Certificate of Origin for India e-service."), QA approved twice
- G14: **the checklist is only actor statements** ("The Ministry of Economy and Tourism registers the factory.", "The Ministry of Foreign Trade processes the application and issues the certificate."): no step tells the user what to do (log in, upload, documents)
- G12: free-zone note in a Sharjah report (as N1, N3)
- QA round 1 also sent an identical-text "fix" for the P-UAE-ISSUER note: **7.6i shield fired live** (overruled, re-judged, both rounds). **Pacing waited 27.3 s live** (QA round 2)
- Minor: "The product aluminium windows qualifies" (awkward)
- Timing: 257.8 s; Intake on Gemini 3.7 (35 s), Researcher 90.7 + 29.5 s and Builder 68.3 s on Dots3

## N5_paint_indian_resin: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `N5_paint_indian_resin/report.md`

- **Code result FAIL (privacy): a grader false alarm, not a leak.** The duty tool's saving 10000.00 AED (10% of the AED 100,000 shipment) equals the synthetic "Paint additives" input value (AED 10,000); `value_leaks` can't tell them apart. The evidence holds only counts and percentages from the bill of materials. Fix proposed to Haris 25 Oct (grader only)
- [x] must say: Indian inputs count only with proof: PASS (note "Indian inputs count as originating only with proof of their originating status under bilateral cumulation")
- [x] must not say: Indian inputs count automatically: PASS as worded, but see G35
- [x] problem 56: PASS (no "What's still needed")
- [ ] G35: **FAIL, problem 97's kind (second case).** The verdict depends on the Indian resin counting as originating: with it, non-originating inputs are 35% of the price and VA 65%; without proof of its Indian origin, VA would be about 35%, below the 40% threshold. The summary says "meets the rule of origin, so the CEPA rate can be claimed"; the proof condition is note 2 of 13. The origin tool counts Indian inputs as originating and says MEETS (with the note) — a design point for the fix
- [x] G8 / 72: PASS (steps "Log in to the ministry e-services portal" … no MoFT-provides claim; Authority MoFT written by code)
- G14: **over-split checklist** (log in / choose service / fill in / upload / submit / receive / print = 7 steps, each "Authority: The Ministry of Foreign Trade")
- G12: free-zone note in an Ajman report with no free-zone mention
- Notes: de minimis "Interpretation:" restored by 7.8 (fired live); direct-consignment note right
- Timing: 202.7 s; Intake 61.4 s (Gemini 3.7 timeout → Groq); Researcher 92 s and Builder 46 s on Dots3

## N7_wire_rods: REPORT / NOT_ELIGIBLE (got REPORT / NOT_ELIGIBLE)
Read: `N7_wire_rods/report.md`

- [x] must say: names only the VA failure: PASS ("The value addition check failed"; "only 30%, below the required 45%"; CTSH stated as passed)
- [x] must not say: claim steps / a saving / CTSH failed: PASS
- [x] problem 56: PASS (none)
- [x] G35: PASS apart from 86
- [x] G8 / 72: PASS (no steps; 4 notes, all match the origin record and KB)
- [x] **slip 86 confirmed:** "The India-UAE CEPA sets a normal (MFN) duty of 7.5%" (the MFN rate is India's own tariff); prose QA approved
- 7.6d dropped 9 claim notes for NOT_ELIGIBLE (incl. the free-zone note) as designed. The tariff lookup also offered two unrelated aluminium lines (windows, kitchenware); the Researcher picked the right one (G23 keyword search)
- Timing: 155.1 s; Intake 61.2 s (Gemini 3.7 timeout), Dots3 for Researcher and Builder

## Sitting summary (Claude, 25 Oct 15:40)
- Code: 2/3 PASS; N5's FAIL is a grader false alarm (privacy: the saving equals an input value). Verdicts 3/3 right; 0 CHECKS_FAILED, 0 LLM_ERROR; 1 QA rejection (N4, right), 1 KB overrule (7.6i, live), 1 pacing wait 27.3 s; slips 72 (N4), 86 (N7), both confirmed.
- Reading: **problem 97's kind again in N5** (cumulation proof decides the verdict, only in the notes); problem 72 (N4); 86 (N7); G14 checklist quality (N4 actor statements only, N5 over-split); G12 free-zone note (N4, N5); N4's "codes differ" reason missing (minor).
- Provider: Intake 61 s twice (Gemini 3.7 timeouts); no Dots3 timeout; all Researcher/Builder calls on Dots3.
- **Re-graded 25 Oct 15:50 with the grader fix (uncommitted):** privacy skips amounts the duty/fee tools printed; N5 case anchor for problem 97. N5 now FAILS on anchors only (must say the Indian-origin proof condition in the summary); privacy PASS. N4, N7 unchanged (PASS).
