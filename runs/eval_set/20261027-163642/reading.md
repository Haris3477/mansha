# Reading sheet: evaluation set run 20261027-163642 (fix round 1c live check; code under test b4c4c92, branch claude/fix-round-1-handoff-vluyq2)

Read by Claude (Mac chat), 27 Oct ~16:55–17:15 Dubai: all 3 report.md + N10 notice.md, every phase_log.md, researcher_1/2.json (N10, N2), N10 evidence.txt (P-IN-IMPORTER, P-AGR-RECORDS-VERIFICATION), `mansha/qa_evidence.py` (1c line), the router's `requests` + `request_attempts` (ids 1184–1221). Offline suite 19/19 at b4c4c92 (runbook list, `test_intake --offline`; new 1c checks pass in test_qa, test_researcher, test_qa_evidence), 27 Oct 16:37.

**Router before (16:37):** R1 in effect; no cooldowns (Cerebras included); Dots3 RPD 1000, router 24 h 48, OpenRouter UTC day 12 attempts; Gemini 3.6 8/20; Groq 25 req / 25,048 tokens; Cerebras 96 req.
**Guard printout:** `long need 12-20, left 984 OK (gemini-3.5 0/20, gemini-3.6 8/20, dots-3 48/1000 (OpenRouter UTC day: 12 attempts; router 24 h: 48))`; `qa need 4-8, left 975 OK (groq 25/1000)`; `judge need 16-56, left 2304 OK (cerebras 96/2400)`.
**Router after (~16:55):** Dots3 58/1000 (24 h), UTC day 22 attempts, all ok; Gemini 3.6 8/20 (unused); Groq 29 req / 29,057 tokens; Cerebras 120 req; no cooldowns.
**Haris's Wi-Fi dropped during the run:** no effect seen: 38 router requests, every attempt `ok` at ordinal 0, no client errors in the phase logs.

**Result:** 2/4 pass every code check (N2's FAIL is a grader false alarm, see below; true 3/4); verdicts 3/4; CHECKS_FAILED 1 (N10); LLM_ERROR 0; QA rejections 4, overruled 0; router refusals 1 (Cerebras RPM in N2 QA r2, recovered); median 221.3 s.

## Serving models — valid 1c check
| Case | Seconds | Intake | Researcher r1 | Researcher r2 | Builder |
|---|---|---|---|---|---|
| N10 | 151.2 | Groq 1.40 | Dots3 85.7 | Dots3 25.6 | – (CHECKS_FAILED) |
| N2 | 221.3 | Groq 1.24 | Dots3 62.8 | Dots3 49.5 | Dots3 63.2 |
| N5 | 337.1 | Groq 1.13 | Dots3 92.7 | Dots3 95.6 | Dots3 137.0 |
| C1 | 155.7 | Groq 1.15 | Dots3 74.9 | – | Dots3 73.9 |
- Dots3 served 10/10 `long` calls at ordinal 0; every Researcher is Dots3 → all 4 count as 1c checks. N5 Builder 137 s (long, under 150 s).

## N10_cosmetics_missing_hs: REPORT / NEEDS_MORE_DATA — FAIL (CHECKS_FAILED) — 1c NOT exercised; new failure path
- [x] asks only for the 6-digit HS code of BOM row 2 — PASS in both rounds: "What is the 6-digit HS code for the non-originating input 'Emollients' (row 2 of the bill of materials)? The origin check cannot run without it." (G9 obeyed by Dots3 this time)
- [x] no whole bill of materials — PASS
- **1c follow-up path not exercised:** QA made no correction on `follow_up_questions` and Dots3 returned plain strings; no "object turned into its text" line (none needed).
- **What failed:** QA r1 rejected only `origin_result.basis` (Dots3 added "which is required to apply the tariff-shift part of the rule; the value-addition test could not be evaluated either": an inference, QA right). Round 2 fixed it. **QA r2 then rejected two steps that were unchanged since round 1 and approved by QA r1** (part 2/3), with no revision left → CHECKS_FAILED:
  - `procedure[7]` (P-IN-IMPORTER): "claims the CEPA rate … and **holds** origin information" vs KB "**must hold**". Real but minor (an obligation written as a fact). The step otherwise copies the KB summary word for word (and drops the e-certificate sentence).
  - `procedure[8]` (P-AGR-RECORDS-VERIFICATION): "The exporter: **keep** origin records … for no less than five (5) years…" (imperative, KB quote verbatim) vs QA's "must keep". **False rejection**: an instruction to keep = must keep.
- Pattern: round-2 QA judges the whole output again and can reject items it approved in round 1; the shared revision is already spent (same family as 101's "no revision left"; QA strictness on step wording, the open "QA false rejections of verbatim quotes in steps" item). Not caused by 1c.

## N2_furniture_freezone: REPORT / ELIGIBLE — code FAIL is a GRADER FALSE ALARM; reading PASS
- [x] duty reduced 20% → 12.5%, not removed — PASS ("tariff 20%, effective 20%" in the table)
- [x] likely not eligible for factory registration; confirm with MoET — PASS
- [x] anchor 97 FREE_ZONE — PASS (summary caution as in 155659; step marker present)
- [ ] must not say "eliminates" — **grader false alarm**: the matched note is "The CEPA reduces the duty but does not eliminate it." (correct, negated). `scripts/eval_grade.py:287` regex `\beliminat\w*` has no negation guard. Fix the anchor (e.g. skip "not eliminat…" / "does not eliminate"), re-grade with `--grade`.
- [x] "What's still needed": **none** — PASS. The Researcher wrote no free-zone question in either round (r1 and r2 `follow_up_questions` = []), so the 1c drop path ("free-zone question dropped") was NOT exercised; 7.9 dropped an HS-code confirmation correctly.
- [~] QA evidence "factory location: in a free zone": not saved in the run folder (qa_*.json hold QA's answer, not its evidence). The FREE_ZONE condition fired in this run (summary caution), and `qa_evidence.py:246` adds the line on that same condition; offline test_qa_evidence checks it. Live text not directly seen.
- [ ] slip 72 confirmed: "…Certificate of Origin for India through the Ministry of Foreign Trade". No 96 this time.
- QA r1 rejected 2 (reasoning[0] tariff-match wording; caveat '+' cited to rule_lookup with no notes → cite TOOL:origin): both reasonable. Round 2 approved.

## N5_paint_indian_resin: REPORT / ELIGIBLE — PASS (unchanged)
- [x] anchor 97 INDIAN_INPUTS — PASS (same caution as 155659: condition + consequence + action)
- [x] "What's still needed": none — PASS
- [ ] slip 72 confirmed ("The Ministry of Foreign Trade provides the 'Certificate of Origin for India'…").
- [ ] slip 96-like, not caught by the anchor: "The agreement refers to box 8, but India's origin rules and certificate form use box 9; **you must follow India's form** when entering the country." (adds "must"; prose QA approved).
- QA r1 rejected step 6 ("Indian importer" named; P-AGR-3.12-DIRECT names the exporter): right. Round 2 approved. Builder 137 s.

## C1_windows: REPORT / ELIGIBLE — PASS (unchanged)
- [x] VA 49% vs 45%, saving 10000.00 AED, steps, no "duty removed" — PASS
- [x] no "Caution:", no step marker, no "What's still needed" — PASS
- No slips; no G12 (no AIDC claim this time); box-9 note neutral. QA approved round 1.

## P1
Not exercised (no finish_reason=length).

## Findings
1. Valid Dots3 sitting (10/10 `long` on Dots3); Wi-Fi drop had no effect.
2. **1c not exercised in either case:** N10 had no follow-up correction (Dots3 obeyed G9), N2 had no free-zone question. Offline tests are the only evidence for 1c so far.
3. **N10 CHECKS_FAILED, new path:** QA round 2 rejected two unchanged steps it approved in round 1 (one minor real "holds" vs "must hold", one false "keep" vs "must keep"), with no revision left. N10 has now failed 2 sittings in a row for different QA/revision reasons.
4. **N2 code FAIL is a grader false alarm** ("does not eliminate it" matched `\beliminat\w*`): fix the anchor; reading PASS.
5. N5 and C1 unchanged and clean apart from slip 72 (N2, N5) and a 96-like "you must follow India's form" (N5).
6. Cerebras router 429 once (N2 QA r2), recovered after 30 s.
7. **G17 under R1: 20 counted runs, 1 LLM_ERROR (215953); streak 12.**
