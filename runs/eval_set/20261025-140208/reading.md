# Reading sheet: evaluation set run 20261025-140208

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## C4_plastic: REPORT / NO_PREFERENCE (got REPORT / NO_PREFERENCE)
Read: `C4_plastic/report.md`

- [x] must say: excluded from CEPA preferences; the normal rate applies: PASS (headline, summary, duty, origin)
- [x] must not say: qualifies: PASS
- [x] must not say: claim steps: PASS (no checklist)
- [x] problem 56: PASS (no "What's still needed")
- [x] G35: PASS. Prose QA round 1 caught "The India-UAE CEPA applies" in the duty text (problem 86 kind) and the retry fixed it. The fix's own wording "The India-UAE CEPA does not apply to this tariff line" is a little loose (the line is listed as excluded in India's CEPA schedule) but correct in effect: no preference
- [x] G8 / 72: PASS (no steps; one note, matches TOOL:duty)
- Minor: summary starts lowercase ("this tariff line is excluded…"), new Builder slip, prose QA and report check don't look at it. Duty cell "tariff 15%, effective 15%" (G13). Source 1 leatherindia.org (G21)
- Timing: Intake 61.5 s (Gemini 3.7 timed out at 60 s, then Groq); Researcher and Builder Dots3

## N1_biscuits_usd: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `N1_biscuits_usd/report.md`

- [x] must say: amounts in USD: PASS (saving 8100.00 USD = 27,000 x 30%)
- [x] must say: fee only as a range: PASS ("ranges from AED 10 to AED 200 depending on the invoice value in AED")
- [x] must say: 30% footnote caveat: PASS
- [x] must not say: AED figure for shipment or saving: PASS
- [x] problem 56: PASS. One item: "Provide the invoice value in AED to determine the exact certificate fee". The user can give it and it changes the fee band; no conversion or exchange rate asked (answers C3's "in AED" watch: not problem 93)
- [ ] G35: **FAIL (minor), problem 96 again.** KB note "The agreement says box 8 … India's form says box 9; India's form governs entry into India" became the Builder's instruction "For the retrospective mark, use box 9 on the certificate as per India's form … rather than box 8". The Researcher kept the KB text; the Builder changed it; prose QA approved
- [x] G8 / 72: PASS. Step 2 says "logging into the ministry e-services portal" with authority MoFT (code); no MoFT-provides-the-India-service claim
- G14: step 4 "Issue the certificate before, at, or within 5 working days of export" is written as the exporter's action (the authority issues it); Authority "The competent authority"
- G12: free-zone note ("A producer in a free zone is likely not eligible…") in a report for a Sharjah bakery that never mentioned a free zone (qualified note → mandatory under 7.6e, so the Builder can't drop it)
- Minor: "Registration takes about 3 working day" (KB: days); problem 86 milder form "Under the India-UAE CEPA, the normal (MFN) rate … is 30%" (reading only)
- Timing: Researcher 123.8 s on Dots3

## N2_furniture_freezone: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `N2_furniture_freezone/report.md`

- [x] must say: reduced 20% → 12.5%, not removed: PASS ("does not remove it entirely"; saving 7500.00 AED = 100,000 x 7.5%)
- [x] must say: free zone likely not eligible, confirm with the ministry: PASS, but only as note 3 of 12 ("Factory declared in a free zone: likely not eligible for the ministry's factory registration; confirm with the ministry.")
- [x] must not say: duty-free / eliminates / no duty: PASS
- [x] must not say: the free zone factory cannot claim: PASS
- [x] problem 56: PASS (no "What's still needed")
- [ ] G35: **FAIL. New problem 97 (proposed): the free-zone caution never reaches the summary or the checklist.** Summary: "meets the rule of origin, so the CEPA rate can be claimed … estimated saving of 7500.00 AED". Checklist step 1 lists "requires location outside a free zone" without saying this user's factory is in one. The KB says registration is needed before the certificate, so for this user the claim path is likely blocked. An exporter reading the summary would expect 12.5%. The key's must-say passes because the note exists; the bar (problem 57) was "don't say it cannot claim", not "say the claim path is in doubt"
- [ ] G35: **FAIL (minor), problem 96 again, worse form:** "While the agreement text mentions box 8, India's certificate form requires box 9 to be completed for entry into India" (drops "for the retrospective mark": reads as a general requirement)
- [ ] G8 / 72: **FAIL, problem 72 in C3's new wording:** step 2 "The Ministry of Foreign Trade issues the Certificate of Origin for India through its e-service: log in to the ministry e-services portal, choose the Certificate of Origin for India service…" (the India e-service page is MoET's). Anchor 72 didn't match; QA approved twice
- G14: actor-first steps "The Ministry of Economy and Tourism registers the factory (…)", "The competent authority issues the certificate…"
- Minor: problem 86 milder form ("Under the India-UAE CEPA, the normal (MFN) rate …")
- Researcher round 1 failed a code check (evidence ID `PSR-IN-R136` in a note), fixed in round 2; QA approved both rounds
- Timing: 245.7 s; Intake 61.1 s (Gemini 3.7 timeout); Researcher 60 + 54 s, Builder 64 s, all Dots3

## N3_steel_structures: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `N3_steel_structures/report.md`

- [x] must say: both rates: PASS (table "tariff 15%, effective 10%" + the exemption note)
- [x] must say: saving from 10%: PASS (10000.00 AED)
- [x] must not say: AED 15,000: PASS
- [x] problem 56: PASS (no "What's still needed")
- [x] G35: PASS after prose QA. Round 1 "reduce the import duty in India to 0%" was caught (only BCD goes to 0%) and fixed in the retry. One word slipped through: "a regional Value Addition (VA)": "regional" is not in FACTS or TERMS (Builder on Gemini 3.6); approved
- [ ] G8 / 72: **FAIL, problem 72 in a third wording:** step 2 "The Ministry of Foreign Trade receives applications through the Certificate of Origin for India e-service portal". QA approved
- G14: "The competent authority issues…" and "The issuing authority may apply risk management, including asking for detailed cost sheets and visiting the factory" as checklist steps (not the user's actions; the second is right for its source P-AGR-3.17-APPLICATION, but it isn't a step)
- G12: free-zone note in a report for an Abu Dhabi factory with no free-zone mention (as N1)
- No box 8/9 note in this report
- Timing: Dots3 timed out at 150 s on the Researcher (router 14:14), Gemini 3.5 served (171.6 s in total); Builder on Gemini 3.6

## Sitting summary (Claude, 25 Oct 14:25)
- 4/4 code checks PASS, 4/4 verdicts right, 0 QA rejections, 0 router refusals, 0 pacing waits. Prose QA caught and fixed two duty-wording slips (C4, N3).
- Reading: **problem 97 (new, proposed): free-zone caution missing from N2's summary and checklist**; problem 96 in 2 of 2 reports that carried the box note (N1, N2); problem 72 in 2 of 3 reports with claim steps (N2, N3), both wordings the anchor misses; G12 free-zone note in N1 and N3; G14 actor-first steps in N1–N3; minor: lowercase summary (C4), "3 working day" (N1), "regional" (N3), problem 86 milder form (N1–N3).
- Provider: 2 Gemini 3.7 timeouts on Intake (61 s each), one Gemini 3.7 503, one Dots3 150 s timeout (N3 Researcher, recovered by Gemini 3.5). Median 184.8 s (G16).
- **Re-graded 25 Oct 14:45 with the updated grader** (anchors 72 widened, 96 added, N2 case anchor for problem 97, Haris option ii; uncommitted): C4 PASS, N1 PASS (slip 96), **N2 FAIL** (anchors: must say the free-zone caution in the summary; slips 72, 96), N3 PASS (slip 72). summary.md above still shows the original grading.
