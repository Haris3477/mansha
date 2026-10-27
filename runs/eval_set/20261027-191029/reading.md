# Reading sheet: evaluation set run 20261027-191029 (KB batch, last live check, code c196340)

Read by Claude (Mac chat), 27 Oct 19:24–19:40 Dubai. Every report and phase log read in full; router `requests` / `request_attempts` checked read-only. Router timeout 210 s (in effect since 18:36; no Dots3 timeout since).

**Code: 4/4 PASS, verdicts 4/4, CHECKS_FAILED 0, LLM_ERROR 0. QA (Researcher) rejections 1 (N5), overruled 1 (N5 r2). Router refusals 1 (Cerebras RPM, recovered). Anchor slips: G12 ×2 hits in 1 run (N5).**
**Validity: 4 of 4** — all 10 `long` calls on Dots3 at ordinal 0 (no Gemini call).

## Serving models / times
| Case | Seconds | Researcher r1 | Researcher r2 | Builder |
|---|---|---|---|---|
| C1 | 129.7 | Dots3 81.3 | – | Dots3 43.4 |
| N2 | 168.2 | Dots3 112.7 | – | Dots3 45.4 |
| N5 | 254.5 | Dots3 71.6 | Dots3 49.6 | Dots3 66.9 |
| N1 | 217.5 | Dots3 100.1 | Dots3 23.9 | Dots3 85.5 |
Intake on Groq 1.0–4.1 s.

## Targets
| Target | Result |
|---|---|
| 96 = 0 | **Met.** No box 8 in any report; box 9 once (N1 step 5: "…marked 'ISSUED RETROSPECTIVELY' in box 9", the record's own summary); no box-8/9 note |
| Code pointer | **Exactly once in 4/4 ELIGIBLE summaries**, last sentence, after the caution in N2 (FREE_ZONE) and N5 (INDIAN_INPUTS). **Builder-written pointers: 0** (the Builder obeyed the prompt change) |
| Prose QA | **0 rejections** (4/4 approved in round 1); Builder retries for "checklist below" = 0 |
| 72 | **0.** Application steps name the exporter; fee step = MoFT in 4/4. N5 also has "The Ministry of Foreign Trade issues the preferential certificate of origin." citing P-UAE-ISSUER = the issuer step under decision C (with the issuer note), not 72's merged e-service actor |
| 101 | Met (no hedge; N5 importer step "uploads the certificate to e-Sanchit") |
| SWS / labels | Met: no bare SWS, no "Inference:" / "Interpretation:" ("By interpretation, …" in N5), "likely" kept |
| C1 | No "What's still needed"; no caution |
| N2 | FREE_ZONE caution + bold step marker under Factory Registration (code); no free-zone question |
| N5 | INDIAN_INPUTS caution present |
| N1 | No AED-value question written (USD; fee shown as the AED 10–200 range): keep-path still not exercised live |

## QA
- **N5 QA r1 REJECTED — wrong-for-this-line correction followed by the Researcher (G12 / G39 kind, new path).** Round 1 caveats[1] was the duty tool's Table I note "CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare Surcharge (SWS) …" but cited **P-IN-DUTY-SCOPE** instead of `TOOL:duty:32091010` (Researcher mis-citation). QA compared it with P-IN-DUTY-SCOPE's summary ("reduces BCD, and the AIDC only for lines in Table II") and called "only" wrong; its fix added the AIDC clause. 32091010 is a **Table I** line. Round 2 copied the fix; QA r2 approved. Report note: "The CEPA rate reduces the Basic Customs Duty (BCD) and the Agriculture Infrastructure and Development Cess (AIDC) for lines in Table II, but other charges … still apply." → irrelevant Table II note (anchor G12), and the line-specific "BCD only" note is missing from Important notes. The duty section itself is right ("the Basic Customs Duty is reduced to 0% … IGST still apply"), so no wrong number or action, but the note is misleading for a Table I product. The KB shield does not cover this (P-IN-DUTY-SCOPE's notes carry qualifiers; the corrected text was not a note).
- N5 QA r2: one correction **overruled by the KB shield after a re-judge** (7.6i verbatim rule, live again): QA "fixed" the P-UAE-ISSUER note to "No official page reads names…" (a typo); overruled → APPROVED.
- N1 r1: code problem only (saving amount format) → round 2. N5 r1 also a code problem (raw name `build_down_pct` in the basis).
- Cerebras: 1 router 429 after pacing (26.5 s pacing in total), recovered.

## Per case
- **C1_windows: PASS.** VA 49% vs 45%, saving AED 10,000, steps, no "all duty removed". Step 1 actor-first "The Ministry of Economy and Tourism registers the factory" (G14). 7.9 dropped an HS question.
- **N2_furniture_freezone: PASS.** 20% → 12.5%; free-zone doubt in the summary (caution); bold step marker under Factory Registration present; no free-zone question; KB notes for free zone ×2 (tool note + KB note, both "likely"). Actor-first step 1 (G14).
- **N5_paint_indian_resin: PASS (code), reading FAIL on G12/G8 (QA-induced, above).** Indian-input proof condition in summary caution and note 3; VA 65% etc. as before. Step "Processing takes about one working day; the service runs 24/7." is a fact as a step (G14).
- **N1_biscuits_usd: PASS.** USD kept, saving 8100.00 USD, fee range AED 10–200 (no conversion), MFN-footnote note present. Step order puts direct shipment before applying (fine).

## Counts for the registers
- 96 = 0 (first time), pointer 4/4 code-only, prose rejections 0, 72 = 0.
- Slips: G12 ×1 run (N5, QA-induced); 86 milder ×4 ("Under the India-UAE CEPA, the normal (MFN) rate…" or similar, all 4); G14 actor-first / fact-as-step in 4/4 (pre-existing); G12 free-zone KB note in C1, N1, N5 (accepted).
- G17 under R1: 4 more counted runs, 0 LLM_ERROR → **streak 28** (36 counted runs, 1 LLM_ERROR).
