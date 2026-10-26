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

## Live results
**Sitting fix round 1, `runs/eval_set/20261026-213601`** (1050b4d; N2, N5, N10; C1 not run, Dots3 too low): 2/3 code PASS; N5 CHECKS_FAILED; LLM_ERROR 0; median 293.4 s.
- **97 FREE_ZONE works (N2):** anchor PASS, the first in 5 N2 runs; caution, step marker, phase log and `builder.json` as designed.
- **G9 works (N10):** anchor PASS. It exposed **finding 2**: Step 7.9 (`drop_hs_follow_ups`) dropped round 1's "the 6-digit HS code for Emollients (BOM row 2)", which forced a revision → fixed in 6bbea54.
- **N5 CHECKS_FAILED (finding 3):** a check-10 false positive on `P-IN-DUTY-SCOPE` (two "Inference:" notes merged under one leading qualifier; restore didn't apply) → fixed in 6bbea54. 97 INDIAN_INPUTS untested.
- P1 untested (no truncation). N10 slips: 72 again, garbled step 1, VA called "regional value content", free-zone note lost "confirm with MoET". Router chose Gemini 3.6 first with Dots3 available (2nd time).

**Sitting fix round 1b, `runs/eval_set/20261026-215953`** (6bbea54; N5 only, k = 1): **LLM_ERROR** in the Researcher (Gemini 3.6/3.5 503 "high demand" ×4, Dots3 429 `free-models-per-day`). Stop rule; no rerun. 97 INDIAN_INPUTS and 6bbea54 still untested live.

## New or changed problems / gaps
- **Budget accounting (new, fixed in da3ecee):** OpenRouter counts every request that reaches it (ok, error, timeout) per UTC day (resets 04:00 Dubai). The router's `rate_limit_usage` holds successes only, over a sliding 24 h (written only by `recordUpstreamSuccess`). The guard showed Dots3 47/50 when OpenRouter had counted 50. **Corrected sizing: Dots3 = 50 fresh at 04:00 Dubai daily** (the "12 left at 16:19" plan was wrong).
- **Capacity under R1:** `long` has no working backup when Dots3 is out and Gemini is overloaded. With A′, OpenRouter's 429 says "Add 5 credits to unlock 1000 free model requests per day" (docs said 10); Haris checks the limits page before buying.
- The guard still says OK on Gemini quota while Gemini returns 503s (by Haris's choice); the warning line is the signal.
- 97 gap: conditions are only set when the origin calculator reaches its notes; an incomplete BOM (early INSUFFICIENT_DATA) gets no caution (same as today's note). No current case has it.
- Finding 2 risk: input names are matched by substring (a common-word input could keep one extra question).
- G17 under R1: **8 runs, 1 LLM_ERROR** (215953; capacity). Streak 0.
- Registers: 97 (N2) 1 PASS after the fix in 1 run; G9 (N10) 1 PASS after the fix; 72 +1 (N10 213601).

## Next
1. **Rerun N5, N10, C1 (+N2 if Dots3 allows)** on da3ecee, any time after 04:00 Dubai on 27 Oct (or after A′, with the Dots3 RPD checked in the router DB). It tests 97 INDIAN_INPUTS, both 6bbea54 changes live, the C1 regression, and the new guard printout (Dots3 count = `request_attempts` since 00:00 UTC; warning line).
2. Then the fix-round order: KB batch (101 `P-IN-IMPORTER` rewrite from the primary CBIC Instruction 28/2022 text, which Haris supplies from the fact base; 72 actor fix; 96 note wording), then 100 + 98, step shield, 99.
3. Project update: agent_prompts.md gets the G9 line of `prompts/researcher.md`; CURRENT_STATE gets this handoff; llm_backend_setup.md gets the OpenRouter UTC-day accounting and the A′ 5-credit note.
