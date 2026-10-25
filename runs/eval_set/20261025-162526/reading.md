# Reading sheet: evaluation set run 20261025-162526

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## N8_cookware_handles: REPORT / NOT_ELIGIBLE (got REPORT / NOT_ELIGIBLE)
Read: `N8_cookware_handles/report.md`

- [x] must say: same-subheading input above 10% de minimis: PASS ("cookware handles … same subheading (761510) … 12.0% of the price, which exceeds the 10% de minimis limit")
- [x] must not say: VA failed: PASS (VA 53% passed in the tool; the report doesn't mention VA's result)
- [x] problem 56: PASS (none)
- [x] G35: PASS
- [x] G8 / 72: PASS (no steps; 5 notes match the origin record and KB)
- Minor: the duty text re-adds the BCD-only scope sentence that 7.6d dropped for NOT_ELIGIBLE ("other import charges (such as IGST) are still paid even if the rate is 0%": true but irrelevant, G12); problem 86 milder form
- Timing: 93.8 s; Intake 2.6 s on Groq (no Gemini timeout); Dots3 36 + 53 s

## N9_smartphones_kits: REPORT / NOT_ELIGIBLE (got REPORT / NOT_ELIGIBLE)
Read: `N9_smartphones_kits/report.md`

- [x] must say: simple assembly never confers origin: PASS (summary + note)
- [ ] must say: confirm the code (HS 2017 vs 2022): **FAIL.** Only the generic "confirm this code with Indian customs". The line record's note ("India's CEPA tariff schedule (Annex 2A) lists this product under its older HS 2017 code 8517 12 11") was in the evidence but no caveat carried it; the user gave 8517 12 11 and gets 85171300 with no word on why
- [ ] must say: medium confidence: **FAIL, but the key is ahead of the prompt.** The Researcher said "high"; its prompt asks for medium only when TOOL:tariff_lookup notes a conflict, and the lookup matched the HS 2017 code exactly (hs_exact_8) with "notes: none". The old-code fact sits only on the line record. Proposed problem 98 (see summary)
- [x] must not say: assembly counts as manufacturing: PASS
- [x] problem 56: PASS (none)
- [x] G35: PASS (88.89% / 11.11% match the tool; all three failed checks named)
- [x] G8 / 72: PASS (no steps)
- Minor: problem 86 milder form ("Under the India-UAE CEPA, the normal (MFN) rate … is 20%")
- Timing: 120.1 s; Intake 3.4 s on Groq; Dots3 50 + 65 s

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA (got REPORT / NEEDS_MORE_DATA)
Read: `N10_cosmetics_missing_hs/report.md`

- [x] must say: asks only for row 2's 6-digit HS code: PASS (summary + one follow-up)
- [x] must not say: a whole bill of materials: PASS
- [x] problem 56: PASS
- [x] G35: PASS. Box note "The agreement specifies box 8 for remarks, but India's certificate form uses box 9" is descriptive, no instruction (not 96), though "for remarks" drops "retrospective" (minor)
- [x] G8 / 72: PASS after the loop. **Round 1 merged "the Ministry of Foreign Trade issues" into the P-AGR-COO-RULES timing step; the 7.4b actor check flagged it, QA marked it REAL and rejected, round 2 fixed it.** Steps (documents, one working day, 5-year records from the calendar year) all match P-UAE-INDIA-COO / P-AGR-RECORDS
- Full claim checklist in a NEEDS_MORE_DATA report (as C3; allowed by design)
- G12: free-zone note in a Dubai report with no free-zone mention; problem 86 milder form
- Timing: 138.7 s; Intake 4.5 s on Groq; Dots3 68 + 25 + 35 s

## N11_perfume: REPORT / NO_PREFERENCE (got REPORT / NO_PREFERENCE)
Read: `N11_perfume/report.md`

- [x] must say: excluded even if the rule of origin is met: PASS (summary + note)
- [x] must not say: qualifies / claim steps: PASS
- [x] problem 56: PASS (none)
- [x] G35: PASS (minor looseness: "the line is excluded from the agreement"; it is excluded from India's concessions)
- [x] G8 / 72: PASS
- Minor: "the CEPA rate is excluded" (awkward); 7.6d dropped 2 claim notes as designed
- Timing: 77.9 s; Intake 1.1 s on Groq

## Sitting summary (Claude, 25 Oct 16:50)
- Code: 4/4 PASS (grader at 2d8751f), verdicts 4/4 right, 1 QA rejection (N10, right: merged actor caught by 7.4b), 0 slips, 0 provider failures; Intake fast on Groq every time (no Gemini 3.7 in the path); median 108 s.
- Reading: **proposed problem 98: notes about the code itself don't reach the report** — N9 (HS 2017 code; must-says "confirm the code (HS 2017 vs 2022)" and "medium confidence" FAIL) and N4 earlier today ("8-digit codes differ between the UAE and India"). Causes: the tariff lookup writes no note for an HS 2017 exact match, and the Researcher has no rule to carry tariff/line notes into caveats (7.6e covers qualifier notes only). G12 free-zone note (N10); 86 milder form (N8–N10). N8, N11 clean.