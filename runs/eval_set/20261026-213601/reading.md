# Reading sheet: evaluation set run 20261026-213601 (fix round 1: 97 + G9 + P1; branch claude/fix-round-candidates-design-rz44re at 1050b4d)

Read by Claude (Mac chat), 26 Oct ~21:55 Dubai: every report.md / notice.md, phase_log.md, the researcher and builder JSON where something changed, and the router's `requests` + `request_attempts`. Offline suite on the Mac: all pass (before the run). Option A: N2, N5, N10 (Dots3 10 left at 21:36); **C1 not run** (needs ≥ 3 Dots3; tomorrow after 16:19 or once the OpenRouter $10 credit is in).

**Router before (21:36):** R1 in effect (`long` = Dots3, Gemini 3.6, Gemini 3.5; `qa` = Groq; `judge` = Cerebras); Dots3 10 left; Groq 20,856; no cooldowns.
**Router after (~21:50):** Dots3 3 left; Groq 20,887; no cooldowns.

**Result:** 2/3 pass every code check; N5 CHECKS_FAILED (not a fix-round effect, see below); LLM_ERROR 0; QA ERROR 0; QA rejections 1 (right); router refusals 0; median 293.4 s (N10 430.8 s from two provider failures).

## Serving models
| Case | Seconds | Intake | Researcher | Builder | Provider failures (recovered) |
|---|---|---|---|---|---|
| N2 | 156.0 | Groq 1.15 s | Dots3 84.2 + 20.5 | Dots3 43.6 | none |
| N5 | 172.9 | Groq 1.17 s | Dots3 127.5 + 40.6 | not reached | none |
| N10 | 430.8 | Groq 1.37 s | R1: Dots3 non-JSON 502 after 76.6 s → retry: Dots3 timeout 150 s → **Gemini 3.6** 59.8 s (phase 316.6 s). R2: Gemini 3.6 503 "high demand" after 20.4 s → retry Dots3 27.3 s | Dots3 29.8 | 3 (counted, G17: no LLM_ERROR) |

Note: N10's round-2 log line says "upstream_error"; the router's attempts table shows it was **Gemini 3.6's 503**, not Dots3. The router again picked Gemini 3.6 first for a `long` call with Dots3 available (as in sitting 6's N10 Builder).

## N2_furniture_freezone: REPORT / ELIGIBLE — PASS (anchor 97 now PASS; first time in 5 runs)
- [x] duty reduced 20% → 12.5%, not removed — PASS
- [x] likely not eligible for factory registration; confirm with MoET (57) — PASS (summary caution + note + step line)
- [x] **summary says the free-zone factory may not be able to register (97) — PASS.** Summary ends with the code caution: "Caution: your factory is in a free zone, so it is likely not eligible for the factory registration needed before applying for the certificate of origin; confirm with the Ministry of Economy and Tourism before relying on this result." Step 1 carries the bold line "**Your factory is in a free zone: see the caution in the summary.**" Phase log: "summary cautions (code): FREE_ZONE"; builder.json `conditions: ['FREE_ZONE']`.
- [x] must not: duty-free / eliminates / no duty / "cannot claim" — PASS
- [x] 56: no "What's still needed" — PASS
- [x] G35 / G8 — PASS (86 milder form: "Under the India-UAE CEPA, the normal import duty rate (MFN rate) … is 20%"; the retrospective step keeps "of India's certificate form").
- **Reading question: clear, or a contradiction?** Clear enough to act on, with one weakness. The order is "meets the rule … CEPA rate can be claimed … saving 7500 … refer to the checklist … **Caution:** … likely not eligible … confirm … before relying on this result". A reader gets both facts and the action (confirm with MoET first). It reads as a strong conditional, not a contradiction, because "before relying on this result" ties the caution to the claim. Weakness: the first sentence is unconditional ("can be claimed") and the caution is last, after "refer to the checklist", so a skimmer may stop early. Optional polish (not needed for the anchor): put the caution right after the first sentence, or make it conditional ("can be claimed if the factory can register").
- QA round 1 rejection (caveats[0] cited `TOOL:rule_lookup` for the '+'-as-'and' note; fix: cite `TOOL:origin:94036000`) — right.

## N5_paint_indian_resin: CHECKS_FAILED — FAIL (expected REPORT / ELIGIBLE); the 97 fix is NOT tested here
- [ ] Indian inputs need proof of origin — not shown (no report; notice.md only)
- [ ] **anchor 97 (summary caution INDIAN_INPUTS) — not tested**
- [x] no "Indian inputs count automatically" — n/a
- **Cause (check 10, Step 7.8 qualifier check; code unchanged by this branch):** caveats[15] cites `P-IN-DUTY-SCOPE`, whose record has two "Inference:" notes (SWS on reduced BCD; anti-dumping/safeguard still apply).
  - Round 1 (Dots3) merged both as plain fact → a real problem, rightly flagged.
  - Round 2 (Dots3) wrote "Inference: the SWS is charged on the reduced BCD (no CEPA-specific text found); anti-dumping and safeguard duties still apply (no exemption found)." That keeps the qualifier for the whole note, but check 10 matched the second clause on its own and flagged it again (**false positive** on a merged two-inference note). QA round 2 skipped → CHECKS_FAILED.
  - The KB shield (`restore_qualified_notes`) didn't restore caveats[15] because the note merges two KB notes, so it matches neither.
- First time this problem has fired in any saved run (grep across runs/). It's a pre-existing gap, not a fix-round regression. Fix candidates: (a) check 10 treats one leading qualifier as covering the whole note, or (b) the shield splits or restores a note that merges several qualified notes of one record. **N5 needs a rerun to test 97 (INDIAN_INPUTS).**

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — PASS (G9 anchor now PASS)
- [x] **asks only for the 6-digit HS code of BOM row 2 — PASS:** "Please provide the 6-digit HS code for the non-originating input 'Emollients' (BOM row 2) to verify the tariff sub-heading change rule." Summary and saving (12000.00 AED, only if) correct.
- [x] no whole bill of materials — PASS
- [x] 56 — PASS
- **New bug (fix interaction G9 × Step 7.9), passed by luck of wording:** round 1 (Gemini 3.6) wrote the right narrow question, "Please provide the 6-digit HS code for Emollients (BOM row 2) so that compliance with the CTSH rule can be determined". Code (7.9 `drop_hs_follow_ups`) **dropped it as a product-HS confirmation**: it has "HS code" and none of "bill of materials / input / material / component / declaration". Check 7 then flagged empty follow-ups → a forced revision. Round 2 (Dots3) happened to write "non-originating **input**" → kept. G9 makes these narrow questions likely, so 7.9 must exempt them (e.g. "BOM row", "row \d", a BOM item's name, or any question when `TOOL:origin` lists a missing input HS). Cost here: one revision (~78 s).
- [ ] G35 / G8 — **minor slips:** **slip 72** (2nd N10 in a row): step 2 "'Certificate of Origin for India' e-service provided by the Ministry of Foreign Trade". Step 1 "The factory must be registered outside a free zone" (garbled: must be *located* outside). Rule paragraph calls VA "a regional value content of at least 40% (VA)". The free-zone note lost "Confirm with the Ministry of Economy and Tourism" (shortened KB note; 4 mandatory notes "verbatim"). Free-zone note shown in a non-free-zone report (G12, known). No 95/96/67/86-full.
- 101 not repeated (e-cert step keeps "reportedly … (unconfirmed)").

## P1 (judge ceiling 6000)
Not exercised: no judge call hit finish_reason=length in this run (all judge calls max_tokens 3000; no 6000 retry). Still untested live.

## Findings
1. **97 fix works in N2** (anchor PASS, first in 5 runs); the summary caution reads as a clear conditional (polish optional). **Untested for INDIAN_INPUTS** (N5 blocked).
2. **G9 fix works in N10** (narrow question), but **it collides with Step 7.9**, which drops narrow input-HS questions with no "input/material" word. Fix before the next sitting, with an offline test using round 1's exact wording.
3. **N5 CHECKS_FAILED: check 10 false positive** on a note that merges two "Inference" notes of one record (round 2 kept the qualifier up front). Pre-existing, first occurrence.
4. P1 untested (no truncation).
5. Router: 3 recovered provider failures in N10 (Dots3 non-JSON 502, Dots3 150 s timeout, Gemini 3.6 503); router chose Gemini 3.6 first for a `long` call again. G17 under R1: 7 runs, 0 LLM_ERROR.
6. Still to run: C1 (regression), N5 rerun.
