# Reading sheet: evaluation set run 20261025-193126 (repeats, pass 1, sitting 1: C1–C4)

Read by Claude (Mac chat), 25 Oct 2026 ~19:50 Dubai: every report.md and phase_log.md, plus evidence/QA JSON where a sentence needed checking. Pipeline at main d0e5fb1 (code = 2d8751f, docs-only commits since).

Serving models: Intake groq/gpt-oss-120b ×4; Researcher and Builder openrouter Dots3 in all 4 runs (no Gemini); judge cerebras ×all. LLM_ERROR 0, QA ERROR 0, verdicts = baseline in all 4. G17 streak (repeats): 4 runs clean.

## C1_windows: REPORT / ELIGIBLE — PASS
- [x] qualifies: value added 49.0% against 45% (FOB) — PASS
- [x] saving 10000.00 AED — PASS (fee step: AED 50 for 100,000, matches the band)
- [x] steps to claim — PASS
- [x] no "all customs duty removed" — PASS
- [x] "What's still needed": none (ELIGIBLE) — PASS
- [x] no claim stronger/weaker than its source — PASS
- [x] steps/notes match cited sources — PASS. Step 2 names the "Certificate of Origin for India" e-service with the code-filled authority MoFT (decision C design; no anchor-72 wording)
- Other: Researcher round 1 had 1 code problem (rule ID PSR-IN-R118 in a caveat), fixed in round 2. **QA round 2 glitch:** claimed the P-UAE-ISSUER note had a ".au" domain; the note was written from the KB by code; the 7.6i verbatim shield overruled it, the re-judge approved (correct behaviour, G32/problem 61 kind). The re-judge call hit one router 429 after a 14.9 s pacing wait; the retry served it (problem 80 kind, counted not failed under E3). Milder slip-86 form ("Under the India-UAE CEPA, the normal (MFN) rate is 10%"). G12: free-zone note for a Sharjah user who did not mention a free zone. KB staleness (see Findings).

## C2_chargers: REPORT / NOT_ELIGIBLE — PASS
- [x] does not qualify — PASS
- [x] every failed check named — PASS in "Rule of origin and result" (final manufacture, minimal operations, CTH with 88.0% same-heading input above the 10% de minimis, VA 12.0% < 40%; all match TOOL:origin). The summary names only the final-manufacture failure ("the main failed check")
- [x] no claim steps — PASS
- [x] no saving — PASS
- [x] no useless "What's still needed" (problem 56) — PASS (section absent)
- [x] no claim stronger/weaker — PASS apart from slip 86
- [x] notes match sources — PASS (7.6d dropped 3 claim notes, as designed)
- [x] **slip 86 confirmed:** "The India-UAE CEPA provides a normal (MFN) rate of 20%" (baseline C2 was clean here: model variance)
- Other: Intake 61.11 s although Groq is the listed model (check attempts in phase_log.json; G16).

## C3_windows_nodata: REPORT / NEEDS_MORE_DATA — PASS
- [x] asks for a bill of materials, a declaration and the shipment value — PASS
- [x] no explanation of how the saving is worked out (problem 67) — PASS
- [x] no duplicate request (problem 85) — PASS
- [x] "What's still needed": all three are user data that change the result — PASS
- [ ] **no claim stronger/weaker — one small slip:** note "Because IGST is calculated on the BCD amount, a lower BCD also reduces the IGST" — the source (P-IN-DUTY-SCOPE summary) says "the IGST base includes BCD". The Builder narrowed the base to BCD alone; prose QA approved (G7/G35 kind, new wording, no wrong number)
- [x] steps/notes match sources — PASS (step 2 same pattern as C1; last step merges record keeping with the 90 (+60)-day verification answer, both from AGR/R39)
- [x] **slip 96 confirmed:** "Since India's form governs entry into India, box 9 should be used." Note: prose QA round 1 rejected a garbled version ("entry into the product") and **its own fix text wrote the "box 9 should be used" advice**; the Builder's retry copied it → prose QA endorsed problem 96's wording
- Other: Researcher 90 s on Dots3. G12 free-zone note again. KB staleness (see Findings).

## C4_plastic: REPORT / NO_PREFERENCE — PASS
- [x] excluded; the normal rate (15%) applies — PASS
- [x] does not say qualifies — PASS
- [x] no claim steps — PASS
- [x] "What's still needed": none — PASS
- [x] no claim stronger/weaker — PASS (milder 86 form "Under the India-UAE CEPA, the normal (MFN) duty rate … is 15%")
- [x] notes match sources — PASS (7.6d dropped 3 claim notes)

## Findings for the registers
1. **KB note out of date vs the fact base (C1, C3; likely every claim report):** the e-certificate note says acceptance is "reportedly" true, "seen only in secondary sources (CBIC Instruction 28/2022 read through LiveLaw and taxmann), not the official text", and source [13] is the LiveLaw report. The fact base marks Instruction 28/2022 PRIMARY since 17 Oct (read on the CBIC portal, view-pdf/1000447). The report understates a confirmed fact and cites a non-government source. Belongs to the KB-URL step (G21/G22); not a pipeline change, not allowed during the repeats either (it changes evidence text).
2. Slip 86 ×1 (C2, full form) + milder form in C1, C3, C4. Slip 96 ×1 (C3), with prose QA's fix producing it.
3. New small Builder slip (G7): "IGST is calculated on the BCD amount".
4. QA glitch overruled correctly by the 7.6i shield (C1): live evidence the shield matters.
5. Medians: 171.8 s (G16 not met); Dots3 served every Researcher/Builder call.
