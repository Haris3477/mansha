# Reading sheet: evaluation set run 20261027-183851 (KB batch follow-up, code b79231d)

Read by Claude (Mac chat), 27 Oct 18:55–19:15 Dubai. Every report and phase log read in full; router `requests` / `request_attempts` checked read-only. Router restarted 18:36:06 with `PROVIDER_TIMEOUT_OPENROUTER=210000` (Haris option A; was 150000).

**Code: 4/4 PASS, verdicts 4/4, CHECKS_FAILED 0, LLM_ERROR 0, QA (Researcher) rejections 0, router refusals 0, pacing waits 0. Anchor slips: 96 ×1 (N2).**
**Validity: 4 of 4 valid** — every Researcher and Builder call on Dots3 at ordinal 0.

## Serving models (router request_attempts)
| Case | Seconds | Intake | Researcher r1 | Builder |
|---|---|---|---|---|
| N2 | 272.5 | Groq 1.33 | **Dots3 170.6** (would have timed out at 150 s) | Dots3 77.5 + 12.7 (retry) |
| C1 | 195.4 | Groq 1.03 | Dots3 89.4 | Dots3 82.0 + 17.0 (retry) |
| N1 | 232.3 | Groq 1.27 | Dots3 146.4 | Dots3 80.6 |
| N4 | 275.4 | Groq 1.53 | Dots3: #1 HTTP 502 "OpenRouter returned 200 with a non-JSON body" at 74.0 s → client busy wait 30 s → #2 Dots3 107.3 s OK (both ordinal 0, separate router requests) | Dots3 57.5 |
- **First live sign of the 210 s timeout: N2's Researcher succeeded at 170.6 s.** No timeout, no bench, no Gemini call in the sitting.
- N4's 502 is the same OpenRouter non-JSON 200 seen in 172227 (network/provider glitch); the router did not bench Dots3 for it (the retry 30 s later went to Dots3).

## QA statuses
| Case | QA r1 | Prose QA |
|---|---|---|
| N2 | APPROVED (3 parts) | REJECTED r1 → APPROVED r2 |
| C1 | APPROVED (2 parts) | REJECTED r1 → APPROVED r2 |
| N1 | APPROVED (2 parts) | APPROVED r1 |
| N4 | APPROVED (3 parts) | APPROVED r1 |
- Both prose rejections were the "see/follow the checklist" sentence (N2 "Please follow the checklist in the report…", C1 "See the checklist below…"), called advice not in FACTS. **The Builder prompt requires it for ELIGIBLE ("point the reader to the checklist below")**, so prose QA rejects what the Builder is told to write: 4 of the last 6 ELIGIBLE reports (180618 C1, N2; 183851 C1, N2) spent the Builder's one retry on it; N1/N4 here and N5 in 180618 were approved with the same kind of sentence. Harmless now, but a fallback risk if a real problem lands in the same round. **New finding (prompt conflict).**
- No QA correction touched the e-certificate sentence (P-IN-IMPORTER). 0 overruled, 0 SETTLED.
- Planner: normal part labels; no cut-off.

## Follow-up handling (b79231d)
- **"dropped for verdict ELIGIBLE": 1 line** — N4: 'Is your factory located outside a free zone? Factory registration requires the factory to be outside a free zone.'
- 7.9 drops (HS confirmation, no tariff-lookup note): N2, C1, N1 (one each). 1c drop (free-zone question, user declared one): N2 (2nd live firing).
- N4 kept its HS-code question ("The given HS code 76101090 does not exactly match any tariff line; the closest match is 76101000. Please confirm…") in "What's still needed": the tariff lookup wrote a note, as designed.
- **N1: the Researcher wrote no AED-value question**, so that keep-path was not exercised live (fee shown as the AED 10–200 range for a USD value, correct).
- C1: no "What's still needed" (fixes 180618's reading FAIL).

## Targets
| Target | Result |
|---|---|
| 72 = 0 | **0** (anchor 0, reading 0). Application steps name the exporter in 4/4; fee step = Ministry of Foreign Trade in 4/4 (N4 also names MoFT's "Issue a Certificate Of Origin" service as an alternative, which P-MOET-COO-INDIA's summary supports) |
| 96 = 0 | **Not met: 2 of 4 by reading.** N2 note "For retrospective certificate issuance, use box 9 for the 'ISSUED RETROSPECTIVELY' mark, as India's form governs entry into India." (anchor hit; drops the agreement's box 8); N1 note "…India's form uses box 9; follow India's form." (anchor miss; "follow India's form" is not in the KB note). C1 printed the KB note faithfully. Both are limited to retrospective certificates (the KB fix holds), but the Builder/Researcher still turns the note into an instruction |
| 101 | **Met.** No hedge; e-certificate plain where mentioned (N1 importer step, N4 "uploads the certificate to e-Sanchit"); no QA churn |
| SWS / labels | **Met.** "the Social Welfare Surcharge (SWS)" in every duty-scope note (4/4, incl. the duty tool note); no bare "SWS"; "Inference:" 0; "Interpretation:" 0 (N2 prints "By interpretation, de minimis helps only…"); "likely" kept |
| 97 | N2 FREE_ZONE caution + bold step marker present; no free-zone question (1c drop). C1, N1, N4 no caution |

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS (code), counts toward 1A
- [x] duty reduced 20% → 12.5%, not removed — PASS
- [x] likely not eligible for factory registration; confirm with MoET (57) — PASS
- [x] summary carries the free-zone doubt (97) — PASS
- [x] must not say duty-free / eliminates / no duty / cannot claim — PASS
- [x] 56 — PASS (no "What's still needed")
- [ ] G35 — slip 96 (above)
- [x] G8/72 — PASS for 72. Checklist over-split into 18 steps, several requirement-as-step / actor-first ("The Ministry of Economy and Tourism requires…", "The competent authority states that…") (G14, pre-existing)

## C1_windows: REPORT / ELIGIBLE — PASS
- [x] VA 49% vs 45%; saving AED 10,000; steps to claim; not "all duty removed" — PASS
- [x] 56 — PASS (no "What's still needed")
- [ ] G35 — minor: step 4 "The issuing authority **may** require the application to include the HS code, description, quantity and value…" (P-AGR-3.17-APPLICATION: the application "must include" them); QA approved
- [x] G8/72 — PASS for 72; step 1 actor-first "The Ministry of Economy and Tourism registers the factory…" (G14; QA rejected the same wording in 180618 N10, approved here)
- Box-9 note faithful to the KB.

## N1_biscuits_usd: REPORT / ELIGIBLE — PASS
- USD value kept; saving 8100.00 USD; fee as the AED 10–200 range (never converted) — correct.
- [ ] G35 — slip 96 milder ("follow India's form", anchor miss).
- 30% MFN footnote note present. Summary "Follow the checklist below to claim the preference." approved by prose QA (cf. C1/N2).
- Checklist steps combine several actions (G14), facts per step match their cited records.

## N4_windows_exw: REPORT / ELIGIBLE — PASS (code)
- [x] must say: Ex-Works threshold 40% (45 minus 5) — PASS ("43.0%, which exceeds the required 40% after the 5-point reduction for Ex-Works")
- [~] must say: 8-digit codes differ between the UAE and India; confirm — **half met**: "does not match any tariff line exactly; the closest match is 76101000 … confirm" (note + "What's still needed") and confidence medium; the tool note's reason "8-digit codes are national and differ between the UAE and India" is not in the report (problem 98 kind; same as the 25 Oct baseline reading)
- [x] must not say: 45% as the threshold applied — PASS
- [x] 56 — PASS (the HS question can change the result; the free-zone question was dropped by code)
- [x] G35, G8/72 — PASS; step 4 "The application must include…" credited to "The issuing authority" (G14, pre-existing)

## Counts for the registers
- Slips: 72 = 0; 96 = 2 by reading (1 anchor); 86 milder ×4 ("Under the India-UAE CEPA, the normal (MFN) rate…": N2, C1, N1, N4); G14 in 4/4 (pre-existing); G12 free-zone note in C1, N1, N4 (accepted); G35 minor ×1 (C1 "may require").
- New: prose-QA vs Builder-prompt conflict on the ELIGIBLE "checklist below" sentence.
- Timeout 210 s: first rescue live (N2 170.6 s). Dots3 Researcher r1 times this sitting: 89–171 s.
- G17 under R1: 4 more counted runs, 0 LLM_ERROR → **streak 24** (32 counted runs, 1 LLM_ERROR).
