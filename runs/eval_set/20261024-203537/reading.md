# Reading sheet: evaluation set run 20261024-203537

Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.

## C3_windows_nodata: REPORT / NEEDS_MORE_DATA (got REPORT / NEEDS_MORE_DATA)
Read: `C3_windows_nodata/report.md`

- [x] PASS must say: asks for a bill of materials, a declaration and the shipment value (3 distinct items)
- [x] PASS must not say: how the saving is worked out (problem 67) ("cannot be estimated without the shipment value" only)
- [x] PASS must not say: a duplicate request (problem 85)
- [x] PASS (all three only the user can give, each changes the result) every "What's still needed" item is something only the user can give and could change the result (problem 56)
- [ ] FAIL no claim stated stronger or weaker than its source (G35): **problem 96 again**, "Since India's form governs entry into the country, you must use box 9 on your certificate" (2 of 4 windows reports today); prose QA approved
- [ ] FAIL (minor) every step and note says what its cited source says (G8, problem 72): step 2 "The Ministry of Foreign Trade issues the preferential certificate through its e-service: log in … choose the Certificate of Origin for India service" (the India service page is MoET's; the problem-72 merge in a wording the anchor doesn't match); step 1 "The Ministry of Economy and Tourism must register the factory" (actor-first, G14)

Read by Claude, 24 Oct 20:45. Code checks all PASS (QA 3/3 parts approved, prose QA approved, report check 0/0). 7.8 restored the de minimis note live again. Minor: the third follow-up asks for the shipment value "in AED" (Mansha accepts other currencies, e.g. N1 in USD; AED only matters for the certificate fee): watch in N1. Time 189 s: Intake 61 s (the router tried Gemini 3.7 first and it timed out, as on every Intake today: G16), Researcher 74 s and Builder 49 s on Dots3. The guard then stopped C4 correctly (4 left, worst case 5).
