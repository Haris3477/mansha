# Reading sheet: evaluation set run 20261025-163540

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## N13_wooden_doors: REPORT / REGULATORY_GAP_DETECTED (got REPORT / NEEDS_MORE_DATA)
Read: `N13_wooden_doors/report.md`

- **Code result FAIL, real:** verdict NEEDS_MORE_DATA, expected REGULATORY_GAP_DETECTED (and so a claim checklist in a report whose expected verdict allows no claim)
- [ ] must say: no result, not covered: **FAIL**
- [ ] must not say: picks either candidate: **FAIL (problem 1 kind).** The Researcher chose TL-IN-94036000 "Other wooden furniture" at medium confidence; wooden doors are builders' joinery (HS 4418), in neither candidate. Its prompt says "If no candidate fits, set the classification values to REGULATORY_GAP_DETECTED"; it judged furniture a fit. QA approved (3 parts), prose QA approved
- [ ] **Code (7.9) dropped the Researcher's own confirm-the-code question** ("Please confirm the HS code for wooden doors; the best match found is 94036000 (Other wooden furniture)") because the tariff lookup noted no conflict: a medium-confidence pick reaches the user with no question about the code. Same drop in N15. Ties to proposed problem 98
- [x] problem 56: the two remaining items (shipment value; bill of materials + declaration) are user-only and could change the result, but they rest on the wrong line
- [x] G35: nothing stronger than its source apart from the classification itself
- [ ] G8 / 72: **slip 72 confirmed** ("applies … through the Ministry of Foreign Trade's 'Certificate of Origin for India' e-service")
- Keyword search (G23) offered TL-IN-76101000 (aluminium doors/windows) and TL-IN-94036000 (wooden furniture): both share a word with "wooden doors", neither fits
- Timing: 203.9 s; Intake 61.1 s (Gemini 3.7 timeout → Groq); Dots3 102.7 + 36.2 s

## N14_windows_wrong_hs: REPORT / ELIGIBLE (got CHECKS_FAILED / -)
Read: `N14_windows_wrong_hs/notice.md`

- **XFAIL as predicted (G34):** the tariff lookup offered only TL-IN-39239090 (the given code's plastic line). Round 1 picked it (low confidence) → NO_PREFERENCE; QA rejected the classification (right); round 2 left it empty → code checks failed → CHECKS_FAILED, safe notice. No wrong report shown
- [ ] must say: 76101000 at medium: not reachable until G34 (the line isn't a candidate)
- [ ] must say: confirm the HS code: **7.6d dropped the Researcher's exactly-right question** ("The HS code 39239090 corresponds to plastic articles for packing, not aluminium window frames. Please confirm…") as "the result does not depend on more information" for NO_PREFERENCE. When the verdict rests on a doubtful classification it does. Note for G34 / problem 98
- [x] must not say: plastic / NO_PREFERENCE for windows: PASS (no report)
- Timing: 78.3 s, Dots3 34 + 32 s

## N15_arabic_windows_nodata: REPORT / NEEDS_MORE_DATA (got CHECKS_FAILED / -)
Read: `N15_arabic_windows_nodata/notice.md`

- **Code result FAIL, real but safe:** CHECKS_FAILED after the one revision; the user got the Arabic notice ("لم يتمكن منشأ من التحقق من هذه النتيجة…"), no report
- **Cause, proposed problem 99: a code-check correction made the Researcher write a new error.** Round 1 `origin_result.basis` copied the tool line (`rule: PSR-IN-R118 "CTSH + VA 45%"…`); the code check asked for plain words. Round 2 wrote "requires both a **change in tariff heading** and at least 45% value addition" (CTSH is a change in tariff *sub*heading). QA round 2 caught it (factuality 0, right); no revision left. QA's round-1 parts approved the findings and the 7.6i shield overruled two e-Sanchit "fixes" (identical/KB text) in both rounds
- [ ] must say: fully Arabic / digits / value: not reachable (no report). Intake read value=100000 AED from Arabic-Indic digits ١٠٠٬٠٠٠ and language=ar: PASS
- [x] must not say: English fallback: PASS (notice in Arabic)
- 7.9 dropped the HS confirmation question (no lookup conflict; line 76101000 high) — right here
- Provider: one live Cerebras 429 ("All models exhausted") → busy wait 30 s → OK; pacing waited 27.1 s and 26.9 s. Timing: 234.2 s; Intake 1.2 s Groq; Dots3 110.4 + 29.1 s

## Sitting summary (Claude, 25 Oct 17:05)
- Code: N13 FAIL (wrong verdict: furniture line picked for wooden doors instead of a gap), N14 XFAIL as predicted (G34), N15 FAIL (CHECKS_FAILED, safe: QA caught a new error made in the revision). 0 wrong reports reached a user apart from N13.
- Reading: **N13 problem 1 kind** (a candidate picked that doesn't fit) + 7.9 dropping the confirm-code question; **proposed problem 99** (N15: a plain-words correction made the Researcher mis-expand CTSH); 7.6d dropped N14's right question; slip 72 (N13).
- Provider: live Cerebras 429 handled by the busy wait; Intake 61 s once (N13).
