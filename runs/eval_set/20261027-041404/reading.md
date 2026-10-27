# Reading sheet: evaluation set run 20261027-041404

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## N5_paint_indian_resin: REPORT / ELIGIBLE (got LLM_ERROR / -)
Read: `N5_paint_indian_resin/notice.md`

- [ ] must say: Indian inputs count as originating only with proof of their origin
- [ ] must say: the summary says the result depends on proof that the Indian resin is originating (problem 97; case anchor)
- [ ] must not say: that Indian inputs count automatically

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA (got LLM_ERROR / -)
Read: `N10_cosmetics_missing_hs/notice.md`

- [ ] must say: asks only for the 6-digit HS code of BOM row 2 (G9)
- [ ] must not say: asks for a whole bill of materials

## C1_windows: REPORT / ELIGIBLE (got LLM_ERROR / -)
Read: `C1_windows/notice.md`

- [ ] must say: qualifies: value added 49% against 45%
- [ ] must say: saving AED 10,000
- [ ] must say: steps to claim
- [ ] must not say: all customs duty removed

## N2_furniture_freezone: REPORT / ELIGIBLE (got LLM_ERROR / -)
Read: `N2_furniture_freezone/notice.md`

- [ ] must say: duty reduced (20% to 12.5%), not removed
- [ ] must say: likely not eligible for factory registration; confirm with the Ministry of Economy and Tourism (problem 57)
- [ ] must say: the summary says the free-zone factory may not be able to register, so the claim is in doubt (problem 97; case anchor)
- [ ] must not say: duty-free
- [ ] must not say: eliminates
- [ ] must not say: no duty
- [ ] must not say: that the free zone factory cannot claim
