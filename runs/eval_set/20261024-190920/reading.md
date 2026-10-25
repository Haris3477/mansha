# Reading sheet: evaluation set run 20261024-190920

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## C1_windows: REPORT / ELIGIBLE (got REPORT / ELIGIBLE)
Read: `C1_windows/report.md`

- [x] PASS must say: qualifies: value added 49% against 45% ("build-down of 49.0% against the 45% threshold")
- [x] PASS must say: saving AED 10,000 ("10000.00 AED", matches the duty tool)
- [x] PASS must say: steps to claim (8 steps; fee AED 50 matches the fee tool)
- [x] PASS must not say: all customs duty removed (note says BCD only; IGST etc. still apply)
- [x] PASS (no section: 7.9 dropped the only follow-up, an HS-code confirmation, live for the first time) every "What's still needed" item is something only the user can give and could change the result (problem 56)
- [ ] FAIL no claim stated stronger or weaker than its source (G35): last note adds "you must use box 9 on your certificate"; the KB note only says India's form uses box 9 and governs entry (the box matters for the 'ISSUED RETROSPECTIVELY' mark). Builder addition, prose QA approved. Minor (new problem 96)
- [x] PASS every step and note says what its cited source says (problem 72 absent). Minor wording: Duty section "Under the India-UAE CEPA agreement, the normal (MFN) duty rate for this product is 10%" (problem 86 kind: MFN is India's own rate; the anchor's pattern doesn't match this wording, reading only)

Read by Claude, 24 Oct 19:20. Also seen: classification confidence 'medium' (earlier windows runs said 'high'; the report says so and asks to confirm the code, so no defect); 7.8 restored the de minimis 'Interpretation:' note live; run time 279 s (Intake 61 s from a Gemini 3.7 timeout before Groq served, Researcher 95 s and Builder 117 s on Dots3: G16).
