# Handoff: fix round 1 (26 Oct 2026)

Branch `claude/fix-round-candidates-design-rz44re`, started from `claude/handoff-sitting-5-r1-it3xu0` (84cf801; not on main yet). Follows `docs/cloud/handoff_2026-10-25_g17.md` (repeats complete, 25 runs; working rule 7 ended).

## Decisions (Haris)
- **Fix-round order** (Claude's proposal, Haris: "your order is fine"): 1) 97, 2) G9 whole-BOM ask, 3) KB batch (101 `P-IN-IMPORTER` rewrite + 72 + 96), 4) P1, 5) 100 + 98, 6) step shield (G32/G39), 7) 99. **First bundle: 97 + G9 + P1** (Claude's recommendation: different cases and anchors, so results stay separable).
- **97: option A**, code writes the caution (options were A code-written sentences, B a FACTS line + prompt rule + code check; B would spend the shared revision).
- **G9: prompt change + N10 case anchor** (a code check on follow-ups kept in reserve).
- **P1: judge ceiling 6,000.**
- **Handover format** (Haris, 26 Oct; reason: he kept pasting the MOVE block before the Mac had the branch): two blocks, 🔀 GET THE BRANCH ON THE MAC (git only) then ➡️ MOVE TO MAC CHAT (first line = branch and commit, no git). In CLAUDE.md "Handover blocks" (881e0e4).
- **Finding 2: option B** (BOM / row words plus the origin tool's missing-input names; option A was the words only). **Finding 3: option A** (restore rewrites a merged caveat from the KB notes; option B, one leading qualifier accepted by check 10, was rejected: it loosens the check).
- **Budget guard: A + B, guard fix before the rerun; no to counting upstream errors as 0 capacity** (Claude's recommendation: a 503 burst often ends in minutes).
- **N2 caution placement: left as is** (Haris's reading: clear conditional, not a contradiction; polish recorded as an option).

## What changed (commits)
- **1050b4d** fix round 1:
  - 97: `origin_calculator` returns `conditions` (FREE_ZONE, INDIAN_INPUTS); the orchestrator passes the chosen line's conditions from the tool result (not the Researcher's caveats); the Builder's code adds a fixed caution (en/ar) at the end of the summary for ELIGIBLE and NEEDS_MORE_DATA, and a bold line under the `P-MOET-FACTORY-REG` step for FREE_ZONE; logged in `builder.json` and the phase summary. Root cause found: `TOOL:origin:` notes are mandatory, so the Builder never saw the free-zone note.
  - G9: `prompts/researcher.md` follow-up rule: ask only for the origin tool's `missing` items; a whole bill of materials only when `missing` asks for one. **Prompt change: agent_prompts.md in the Project needs the same edit.**
  - Grader: N10 case anchor "must not say a whole bill of materials asked for" (N10 only: the same ask is right in C3/windows_nodata, 18 saved reports).
  - P1: `auto:judge` ceiling 3000 → 6000 (default stays 3000). N3 sitting 4 had retried at 3000 again.
  - Offline replay: the 5 saved N2/N5 reports re-rendered with the new code: anchors FAIL → PASS ×5, report check 0 → 0, only the summary line and the step changed.
- **881e0e4** CLAUDE.md handover blocks.
- **6bbea54** fix round 1b: Step 7.9 keeps a follow-up naming a missing BOM input (finding 2); `restore_qualified_notes` rewrites a caveat merging several qualified notes of one record (finding 3), with the 23 Oct 19:56 rule kept. 55 saved Researcher outputs: 0 changed.
- **da3ecee** budget guard: OpenRouter `:free` used = max(router's sliding-24 h successes, `request_attempts` since 00:00 UTC); a non-blocking upstream-error warning.
- Tests: +40 checks in total; all 19 offline suites pass at da3ecee.
- **907d5f1** (27 Oct, Haris: option a, from the 041503 N5 reading): the INDIAN_INPUTS caution adds the consequence and the action ("without that proof they count as non-originating inputs. Keep that proof before relying on this result."; en + ar). Offline suite 19/19 at 907d5f1 on the Mac. **Not yet tested live** (041503 ran on da3ecee).

## Live results
**Sitting fix round 1, `runs/eval_set/20261026-213601`** (1050b4d; N2, N5, N10; C1 not run, Dots3 too low): 2/3 code PASS; N5 CHECKS_FAILED; LLM_ERROR 0; median 293.4 s.
- **97 FREE_ZONE works (N2):** anchor PASS, the first in 5 N2 runs; caution, step marker, phase log and `builder.json` as designed.
- **G9 works (N10):** anchor PASS. It exposed **finding 2**: Step 7.9 (`drop_hs_follow_ups`) dropped round 1's "the 6-digit HS code for Emollients (BOM row 2)", which forced a revision → fixed in 6bbea54.
- **N5 CHECKS_FAILED (finding 3):** a check-10 false positive on `P-IN-DUTY-SCOPE` (two "Inference:" notes merged under one leading qualifier; restore didn't apply) → fixed in 6bbea54. 97 INDIAN_INPUTS untested.
- P1 untested (no truncation). N10 slips: 72 again, garbled step 1, VA called "regional value content", free-zone note lost "confirm with MoET". Router chose Gemini 3.6 first with Dots3 available (2nd time).

**Sitting fix round 1b, `runs/eval_set/20261026-215953`** (6bbea54; N5 only, k = 1): **LLM_ERROR** in the Researcher (Gemini 3.6/3.5 503 "high demand" ×4, Dots3 429 `free-models-per-day`). Stop rule; no rerun. 97 INDIAN_INPUTS and 6bbea54 still untested live.

**Sitting rerun, `runs/eval_set/20261027-041404`: VOID.** The router was down: all 4 cases LLM_ERROR at Intake in 0.0–0.1 s ("connection error … Is the router running?"), 0 tokens. Not a Mansha result; not counted in G17. It shows the guard has no router health check (to propose: router down → not OK).

**Sitting rerun, `runs/eval_set/20261027-041503`** (da3ecee; N5, N10, C1, N2; reading by the Mac chat in `reading.md`): **4/4 code PASS, verdicts 4/4**, CHECKS_FAILED 0, LLM_ERROR 0, QA rejections 0, router refusals 0, median 92.5 s. One recovered provider failure (Gemini 3.6 503 in N10's Builder → Dots3).
- **97 INDIAN_INPUTS first live PASS (N5)**; reading: clear as a condition, no consequence or action → 907d5f1.
- **97 FREE_ZONE 2nd live PASS (N2)**; **G9 PASS (N10)**: only the BOM row 2 HS code asked, no revision; **C1 regression clean** (no caution, no step marker).
- Guard printout matched `request_attempts` (Dots3 0 attempts since 00:00 UTC; used = max(router 24 h 47, 0) → 3 left, by design).
- **Not comparable to the Dots3 baseline:** the router put **Gemini 3.6 first in 7 of 8 `long` calls** (Researcher on Gemini 3.6 in N5, N10, N2; only C1's Researcher on Dots3). Likely cause (not verified): the router's own sliding-24 h RPD still counted Dots3 47/50, plus a possible leftover 429 penalty. Gemini 3.6 Researcher outputs are thinner (N5 5 notes, N2 6, vs 14–15 on Dots3; no retrospective / direct-shipment items). Finding 3 (merged inference notes) and the 7.9 path for a question without an input word were not exercised.
- Slips: **72 in 4 of 4** (actor-first steps reuse `P-MOET-COO-INDIA`'s actor "Ministry of Foreign Trade" next to the "Certificate of Origin for India" service name; Gemini writes every step actor-first and lower-case), 94 ×1 (C1). P1 not exercised (no judge truncation).
- **Haris holds "fix round 1 done"** until one sitting with Dots3 serving the Researcher.

**A′ live (27 Oct):** OpenRouter credit bought 15:43 Dubai ($5.22; $10.22 lifetime with June's $5, over the 1000/day line). Router DB checked 15:47: Dots3 RPD = 1000, 24 h count 49/1000, no cooldowns, R1 in effect. Expectation: with Dots3 headroom restored in the router's own window, `smartest` routing should pick Dots3 first again for `long`; the Dots3 sitting (N5, N10, C1, N2 at 907d5f1, Mac chat) checks it.

**Dots3 confirmation sitting, `runs/eval_set/20261027-155659`** (907d5f1; N5, N10, C1, N2; reading by the Mac chat in `reading.md`). Guard before: long left 983 OK (dots-3 49/1000). **Dots3 served 10/10 `long` calls at ordinal 0** (no failover, no Gemini): this is the Dots3 check. N2 Researcher r1 took 147.8 s (timeout 150 s). Router refused Cerebras twice (RPM) in QA r2 of C1/N2 despite client pacing; +30 s each, recovered.
- **3/4 code PASS, verdicts 3/4**, CHECKS_FAILED 1 (N10), LLM_ERROR 0, QA rejections 3 (all right on reading), median 238 s.
- **N5 PASS:** 97 INDIAN_INPUTS with the 907d5f1 wording; reading question YES (condition, consequence, action). Dots3 output full again (12 notes, 11 steps). Finding 3 not exercised (no Researcher wrote the `P-IN-DUTY-SCOPE` "Inference:" notes).
- **C1 PASS:** no caution or marker. **P1 first live PASS:** QA r1 part 2 `finish_reason=length` at 3000 → retry at 6000 OK. G12 confirmed (Builder dropped "only for lines in Table II" from the AIDC note; prose QA approved). Slips 72, 86.
- **N2 PASS** (97 FREE_ZONE 3rd live PASS), but reading FAIL on "What's still needed": "Is the factory located in a free zone?" although the user said so (2 of the last 4 Dots3 N2 runs; also 172224). Researcher r1 + r2 wrote it, QA approved twice. The free-zone point appears 4 times. Slips 72, 96.
- **N10 CHECKS_FAILED (new, code cause, verified in the cloud):** Dots3 r1 broadened the follow-up ("…and for any other non-originating inputs"; G9 not fully obeyed); QA rejected rightly. `mansha/qa.py` `correction_text()` appends "Cite TOOL:origin:33049990 in source_id, not in the text." to every correction with a source_id, including `follow_up_questions[0]`, a plain-string field. Dots3 r2 returned `{"step": "...", "source_id": "TOOL:origin:33049990"}`; the exporter-text check read the dict as text, found "TOOL:origin:33049990'}" → CHECKS_FAILED, QA r2 skipped. Pre-existing since 7.6g; first exposed now.
- QA pedantry (twice): "CTSH + VA nn%" in a `TOOL:rule_lookup` note flagged (the % is in `TOOL:origin`) → an extra revision round.
- G17 under R1: 16 counted runs, 1 LLM_ERROR (215953); streak 8.

## New or changed problems / gaps
- **Budget accounting (new, fixed in da3ecee):** OpenRouter counts every request that reaches it (ok, error, timeout) per UTC day (resets 04:00 Dubai). The router's `rate_limit_usage` holds successes only, over a sliding 24 h (written only by `recordUpstreamSuccess`). The guard showed Dots3 47/50 when OpenRouter had counted 50. **Corrected sizing: Dots3 = 50 fresh at 04:00 Dubai daily** (the "12 left at 16:19" plan was wrong).
- **Capacity under R1:** `long` has no working backup when Dots3 is out and Gemini is overloaded. With A′, OpenRouter's 429 says "Add 5 credits to unlock 1000 free model requests per day" (docs said 10); Haris checks the limits page before buying.
- The guard still says OK on Gemini quota while Gemini returns 503s (by Haris's choice); the warning line is the signal.
- 97 gap: conditions are only set when the origin calculator reaches its notes; an incomplete BOM (early INSUFFICIENT_DATA) gets no caution (same as today's note). No current case has it.
- Finding 2 risk: input names are matched by substring (a common-word input could keep one extra question).
- G17 under R1: **16 runs, 1 LLM_ERROR** (215953; capacity); 041404 void (router down), not counted. Streak 8 (041503, 155659).
- Registers: 97 FREE_ZONE (N2) 3 PASS in 3 runs after the fix; 97 INDIAN_INPUTS (N5) 2 PASS; G9 (N10) 2 PASS + 1 broadened on Dots3 (caught by QA, 155659); P1 1 live PASS; 72 +7 (N10 213601; 4 of 041503; C1, N2 155659); 94 +1; 96 +1 (N2 155659); 86 +1, G12 +1 (C1 155659); N2 free-zone follow-up 2 of the last 4 Dots3 N2 runs.
- **New (1c): correction/follow-up bug** (N10 155659): a "Cite X in source_id" sentence on a string-only field makes the Researcher return an object → exporter-text check fails.
- **Model mix (new):** `smartest` routing can serve `long` from Gemini 3.6 while Dots3 is listed first, when the router's own 24 h window says Dots3 is near its RPD. A sitting's serving models must be checked before its results are compared with the Dots3 baseline.
- **Guard (new):** says OK when the router is down (041404). Proposal to come.

## Next
1. **Dots3 sitting done (155659, above).** 97 (both conditions), G9 (with QA), P1 pass on Dots3. Open before merging to main: fix 1c (N10 correction/follow-up bug; N2 free-zone follow-up), designed on paper 27 Oct, waiting for Haris's choice.
2. KB batch design on paper (in progress, 27 Oct): 72 (actor of `P-MOET-COO-INDIA`), then 96 (box-9 note), then 101 (`P-IN-IMPORTER` rewrite from CBIC Instruction 28/2022, fact base A6, PRIMARY since 17 Oct). Then 100 + 98, step shield, 99.
3. Guard health check (router down → not OK): to propose.
4. Project update: agent_prompts.md gets the G9 line of `prompts/researcher.md`; CURRENT_STATE gets this handoff; llm_backend_setup.md gets the OpenRouter UTC-day accounting, A′ done (27 Oct 15:43, $5.22, Dots3 RPD 1000) and the `smartest`-routing finding.
