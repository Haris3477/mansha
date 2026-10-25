# Reading sheet: evaluation set run 20261024-192027

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## C1_windows: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `C1_windows/report.md`

- [x] PASS must say: qualifies: value added 49% against 45% ("value addition is 49.0% … above the 45% threshold")
- [x] PASS must say: saving AED 10,000 (10000.00 AED)
- [x] PASS must say: steps to claim
- [x] PASS must not say: all customs duty removed (summary says the CEPA rate applies only to Basic Customs Duty)
- [x] PASS every "What's still needed" item (none) is something only the user can give and could change the result (problem 56)
- [x] PASS no claim stated stronger or weaker than its source (G35) (free-zone note keeps "Inference:")
- [ ] FAIL every step and note says what its cited source says (problem 72 again: "The Ministry of Foreign Trade provides the Certificate of Origin for India e-service" (that page is MoET's); QA approved), no merged facts (G8, problem 72)
- [x] PASS slip 72 confirmed? (confirmed) 'Ministry of Foreign Trade provides the Certificate of Origin for India'

## C2_chargers: REPORT / NOT_ELIGIBLE (got REPORT / NOT_ELIGIBLE)
Read: `C2_chargers/report.md`

- [x] PASS must say: does not qualify
- [x] PASS must say: every failed check named (final manufacture, minimal operations, CTH (88% in heading 8504 > 10% de minimis), VA 12% < 40%) (final manufacture, minimal operations, heading change, value added)
- [x] PASS must not say: claim steps (no checklist)
- [x] PASS must not say: a saving ("No saving applies")
- [x] PASS must not say: a useless 'what's still needed' item (problem 56) (no section)
- [x] PASS every "What's still needed" item (none) is something only the user can give and could change the result (problem 56)
- [x] PASS no claim stated stronger or weaker than its source (G35)
- [x] PASS every step and note says what its cited source says (the 15% EV-manufacture note matches its record), no merged facts (G8, problem 72)

## C3_windows_nodata: REPORT / NEEDS_MORE_DATA (got LLM_ERROR / -)
Read: `C3_windows_nodata/notice.md`

- [ ] must say: asks for a bill of materials, a declaration and the shipment value
- [ ] must not say: how the saving is worked out (problem 67)
- [ ] must not say: a duplicate request (problem 85)

## C4_plastic: REPORT / NO_PREFERENCE (got LLM_ERROR / -)
Read: `C4_plastic/notice.md`

- [ ] must say: excluded from CEPA preferences; the normal rate applies
- [ ] must not say: qualifies
- [ ] must not say: claim steps

## S1_vague: NEEDS_INPUT / - (got NEEDS_INPUT / -)
Read: `S1_vague/notice.md`

- [x] PASS must say: asks for the product and the destination

## S2_dates: NOT_COVERED / - (got NOT_COVERED / -)
Read: `S2_dates/notice.md`

- [x] PASS must say: the product is not in Mansha's data yet
- [x] PASS must say: suggests giving an HS code
- [x] PASS must not say: that dates don't qualify

## S3_arabic_turkiye: NOT_COVERED / - (got NOT_COVERED / -)
Read: `S3_arabic_turkiye/notice.md`

- [x] PASS must say: Arabic notice (minor G19: the country names India and Türkiye stay in English inside the Arabic text)
- [x] PASS must say: not covered by Mansha does not mean no agreement
- [x] PASS must say: the Ministry of Foreign Trade's CEPA list link

Read by Claude, 24 Oct 19:40. C3 and C4: LLM_ERROR, not a Mansha defect: Google returned 'exceeded your current quota' (project-wide) at 19:22-19:23 although the router counted 3/20 and 10/20, the router benched Gemini until 11:00 Dubai, Gemini 3.7 timed out again, and Dots3 was at 50/50. To be re-run; they count as G17 evidence, not as baseline results. C1 classification confidence 'high' this time (the smoke run said 'medium'). Duty sections in C1 again say "Under the India-UAE CEPA, the normal (MFN) rate … is 10%" (problem 86 kind, minor).
