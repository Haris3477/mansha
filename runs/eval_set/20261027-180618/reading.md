# Reading sheet: evaluation set run 20261027-180618 (KB batch live check, code eb630a1)

Read by Claude (Mac chat), 27 Oct 18:22–18:45 Dubai. Every report and phase log read in full; router `requests` / `request_attempts` checked read-only.

**Code: 4/4 PASS, verdicts 4/4, CHECKS_FAILED 0, LLM_ERROR 0, slips 0 (anchors).**
**Validity: 3 of 4 runs valid.** N5, N10, C1: every Researcher and Builder call on Dots3 at ordinal 0. **N2 NOT valid for the KB-batch bar:** the Researcher's Dots3 attempt timed out at 150.0 s (ordinal 0), Gemini 3.6 served at ordinal 1 (176.6 s phase), and the router then sent both Builder calls straight to Gemini 3.6 at ordinal 0. N2's report is a Gemini report (7 notes vs ~13 on Dots3), not comparable.

## Serving models (router request_attempts)
| Case | Seconds | Intake | Researcher r1 | Researcher r2 | Builder |
|---|---|---|---|---|---|
| N5 | 253.0 | Groq 1.36 | Dots3 105.9 | Dots3 27.4 | Dots3 80.3 |
| N10 | 236.1 | Groq 1.11 | Dots3 110.6 | Dots3 25.7 | Dots3 55.8 |
| C1 | 280.8 | Groq 1.21 | Dots3 116.7 | Dots3 44.1 | Dots3 51.5 + 13.4 (retry) |
| N2 | 204.1 | Groq 1.30 | **Dots3 timeout 150.0 → Gemini 3.6 26.6** | – | **Gemini 3.6 13.2 + 7.8 (retry)** |
- The watched risk (Dots3 calls near `PROVIDER_TIMEOUT_OPENROUTER=150000`) happened: first Dots3 timeout since R1/A′. The failover hop worked (no LLM_ERROR; G17 streak continues).
- Judge: 26 Cerebras calls OK; 1 router 429 (C1 QA r2 part 2, after an 11.8 s pacing wait; retry after 30 s OK). Pacing waits 69.3 s in total.

## QA statuses per round
| Case | QA r1 | QA r2 | Prose QA |
|---|---|---|---|
| N5 | APPROVED (code problem: saving amount format → r2) | APPROVED | APPROVED r1 |
| N10 | REJECTED (1, minor real) | APPROVED | APPROVED r1 |
| C1 | REJECTED (1, right) + code problem (PSR-IN-R118 in a caveat) | APPROVED | REJECTED r1 → APPROVED r2 |
| N2 | APPROVED | – | REJECTED r1 → APPROVED r2 |
- N10 r1: step 0 "the Ministry registers the factory" vs the record "registered through the Ministry's service" → minor real (actor-first, G14); fixed.
- C1 r1: caveat said the CTSH and VA checks rest on the exporter's declaration; the origin tool says only final manufacture and minimal operations do → right; fixed.
- Prose QA C1 and N2: "See/Please follow the checklist below…" called advice not in FACTS → borderline/harmless; the same sentence was approved in N5 (judge inconsistency, no harm).
- **No QA correction touched P-IN-IMPORTER in any round (101: no churn).** 0 overruled, 0 SETTLED. **1c and 1d not exercised.**
- Planner: every QA review split as usual with normal labels ("part 1/3: findings + steps and notes", …); largest real part prompt 5,128 tokens + 1,924 out = 6,795 (< 7,600); 0 cut-offs, no P1 retry, no 413.

## KB-batch targets
| Target | Result |
|---|---|
| 72 ≈ 0 | **0** (anchor 0, reading 0). Certificate-application steps name **the exporter** in N5, N10, C1, N2; fee step names **the Ministry of Foreign Trade** in all 4 |
| 96 = 0 | **0.** Box-9 note in 1 of 4 reports (N5), scoped "For a retrospective certificate … India's form uses box 9. India's form governs entry into India." with no "must/should use". C1's Researcher kept it but the Builder left it out (optional) |
| 101 | **Met.** No "reportedly / unconfirmed / secondary / LiveLaw / taxmann" in any report; e-certificates stated plainly ("Electronic certificates from the UAE issuing authority are accepted and uploaded to e-Sanchit…", C1; N10 step 8); source [13] is now CBIC Instruction 28/2022 (taxinformation.cbic.gov.in) |
| Item 4 | **"Inference:" 0 in 4.** "Social Welfare Surcharge (SWS)" spelled out in every P-IN-DUTY-SCOPE note; "likely" kept (2–3 per report). **Left over (outside item 4's scope as written):** (a) bare "SWS" in the duty tool's note "…IGST, GST compensation cess, SWS and any anti-dumping…" (N5, N10; text from `data/india/tariff_lines.json` `duty_scope`; C1's and N2's Researchers reworded it); (b) "Interpretation: de minimis helps only…" label printed verbatim (N10, C1; P-AGR-3.4-DEMINIMIS, restored by 7.8) |
| Planner | **Met** (above) |
| 97 cautions | N5 INDIAN_INPUTS present (condition + consequence + action); N2 FREE_ZONE present + bold step marker (Gemini run); **C1 no caution** |
| G9 | N10: one narrow question, "6-digit HS code for the emollients input (BOM row 2)", both rounds |

## N5_paint_indian_resin: REPORT / ELIGIBLE — PASS
- [x] must say: Indian inputs count as originating only with proof of their origin — PASS (note 2 + summary caution)
- [x] must say: the summary says the result depends on proof that the Indian resin is originating (97) — PASS
- [x] must not say: Indian inputs count automatically — PASS
- [x] "What's still needed" items (56) — PASS (none)
- [x] no claim stronger or weaker than its source (G35) — PASS
- [x] steps and notes say what their source says (G8, 72) — PASS; step 4 "The certificate is issued … Authority: The competent authority" is a requirement as a step (G14, pre-existing)
- Bare "SWS" in the duty tool note (item 4 leftover). Summary "See the checklist below for the steps to claim." (approved here).

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS
- [x] asks only for the 6-digit HS code of BOM row 2 (G9) — PASS
- [x] does not ask for a whole bill of materials — PASS
- [x] "What's still needed" items (56) — PASS
- [x] G35 — PASS
- [x] G8 / 72 — PASS for 72; step 5 "The issuing authority requires the application to include…" is a requirement as a step (G14, pre-existing: 22 of 59 saved reports have an "issuing authority" step)
- "Interpretation:" label and bare "SWS" (item 4 leftovers). Free-zone KB note for a user who said nothing about free zones (G12, accepted).

## C1_windows: REPORT / ELIGIBLE — PASS (code), one reading FAIL
- [x] qualifies: value added 49% against 45% — PASS
- [x] saving AED 10,000 — PASS
- [x] steps to claim — PASS (11 steps)
- [x] must not say all customs duty removed — PASS
- [ ] **"What's still needed" (56) — FAIL (new for C1: 0 in the 9 earlier C1 reports).** An ELIGIBLE report ends with a "What's still needed" section with two Researcher follow-ups (both rounds, Dots3): "Is your factory located in a free zone?" (the user said Sharjah, no free zone; could change the result: acceptable on its own) and "Can you confirm that the final manufacture in the UAE went beyond the minimal operations…?" (re-asks the declaration the result already rests on: useless). Code drops follow-ups only for NOT_ELIGIBLE/NO_PREFERENCE (7.6c) and the free-zone one only when the user declared a free zone (1c). Not caused by the KB batch (no prompt change; Researcher wording); QA approved.
- [x] G35 — PASS ("e.g., simple assembly, packaging, labelling" matches Art. 3.5 items (n), (k), (l))
- [x] G8 / 72 — PASS for 72; step 3 "Complete the application form …" carries "Authority: The issuing authority" (code-filled from P-AGR-3.17-APPLICATION's actor; the exporter does it; G14, pre-existing)
- "Interpretation:" label (item 4 leftover). SWS spelled out.

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS (code) — Gemini-served, not valid for the bar
- [x] duty reduced 20% → 12.5%, not removed — PASS
- [x] likely not eligible for factory registration; confirm with MoET (57) — PASS
- [x] the summary carries the free-zone doubt (97) — PASS (code caution + step marker)
- [x] must not say duty-free / eliminates / no duty / cannot claim — PASS ("does not eliminate it completely" is negated)
- [x] 56 — PASS (none)
- [x] G35, G8/72 — PASS
- Thin Gemini report (7 notes); 1c's free-zone drop not needed (no question written).

## Counts for the registers
- Slips: 72 = 0, 96 = 0, 95 = 0, 86 milder ×3 ("Under the India-UAE CEPA, the normal (MFN) rate…", N10, C1, N2), G14 requirement-as-step / wrong actor in 4/4 (pre-existing), G12 free-zone note ×3 (accepted).
- New: ELIGIBLE report with "What's still needed" (C1); first Dots3 150 s timeout under A′ (N2) and the router's Gemini routing for the Builder after it.
- G17 under R1: 4 more counted runs, 0 LLM_ERROR → **streak 20** (28 counted runs, 1 LLM_ERROR).
