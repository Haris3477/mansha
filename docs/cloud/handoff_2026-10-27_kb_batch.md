# Handoff: KB batch (27 Oct 2026)

Branch `claude/kb-batch-brief-step-1-gxvauj`, started from main at 3125d9e (fix round 1 merged). Follows `docs/cloud/handoff_2026-10-26_fix_round_1.md` and the design in `docs/cloud/kb_batch_brief.md`. **Task closed (Haris, 27 Oct).**

## Decisions (Haris)
- **72: A.** `P-MOET-COO-INDIA` actor → "the exporter"; the fee tool takes its actor from `P-UAE-ISSUER` (decision C of 15 Oct unchanged). Options were B (MoET, reopens decision C) and C (prompt rule, step shield).
- **96: A** (scope the note to retrospective certificates), then, after sitting 183851, **C: remove the note from the KB** (Claude's recommendation; option B′ was verbatim printing by code, which would take a mandatory note slot). Reason: the Builder, not the Researcher, turned the note into an instruction; the record's summary already gives box 9 of India's form.
- **101: B** (minimal): the e-certificate sentence stated plainly, the "secondary reports" note dropped, `CBIC-INSTR-28` PRIMARY. Option A (format/seal, bill-of-entry fields, no-reuse facts) left for the KB-URL step.
- **A6 row for CBIC Instruction 28/2022 (from Haris):** 27 Oct 2022, F. No. CBIC-15021/172/2022-ICD-CBEC, signed Neetisha Verma, Senior Technical Officer, International Customs Division; https://taxinformation.cbic.gov.in/view-pdf/1000447/ENG/Instructions; read 17 Oct 2026; PRIMARY. Matched `docs/archive/browser_checks_2026-10-17.md` item 6 (no conflict).
- **Item 4: a** (plain KB wording keeping a qualifier word) and **bundle together** with 72, 96, 101. Option b was a Builder rendering rule.
- **QA planner sizing: A** (a pre-existing bug exposed by the batch; option B, shortening KB text, would hide it).
- **After 180618:** 1A (count the batch as met on the 3 valid runs; N2 re-run in the next sitting), 2 both (item 4 leftovers), 3A (ELIGIBLE follow-ups dropped by code), 4 yes (router timeout, Mac chat).
- **Router (Mac chat, Haris option A):** `PROVIDER_TIMEOUT_OPENROUTER` 150000 → 210000, router restarted 18:36:06. Recorded in the Project (`claude/llm_backend_setup_addendum_2026-10-27.md`).
- **After 183851:** 1C (above), 2A (code writes the checklist pointer), 3 later (problem 98 → "100 + 98"), 4 closed (1A: N2 valid in 183851).
- **After 191029:** 1A in the next task (code re-cites a caveat restating a `TOOL:duty:` note), 2 close the KB batch, 3 the AED-value keep path stays on the live-unproven list (no dedicated sitting).

## What changed (commits)
- **eb630a1** KB batch:
  - 72: actor change; `mansha/tools/coo_fee.py` `ACTOR_PASSAGE = {"india": "P-UAE-ISSUER"}`.
  - 96: note scoped ("Only for a certificate issued retrospectively: …"); 96 anchor + "you must follow India's form" (saved hits 17 → 18 of 118, 0 false alarms).
  - 101: `P-IN-IMPORTER` summary "Electronic certificates from the UAE issuing authority are accepted and uploaded to e-Sanchit by the importer or customs broker."; note removed; provision "CBIC Instruction 28/2022-Customs (27 Oct 2022)"; `sources.json` `CBIC-INSTR-28` PRIMARY with the official title and view-pdf URL.
  - Item 4: no "Inference:" label; SWS note "The Social Welfare Surcharge (SWS) is likely charged on the reduced BCD (no CEPA-specific text on it was found)."; anti-dumping "…likely still apply (no CEPA exemption from them was found)."; free-zone note starts "A producer in a free zone is likely…". Two wordings differ from what Claude first showed Haris, both measured: BCD kept short (spelled out, a model's "SWS … BCD" drop scored 0.57 < 0.60 and would go unnoticed; kept short 0.73), and the "nothing found" part in parentheses (after a ";" it became its own unqualified clause and check 10 flagged the KB's own note). `check_data` guards the qualifiers.
  - QA planner: `plan_parts` sizes parts with the longest label they are sent with ("part 9/9" was 8 tokens short; windows_nodata part 1 measured 5596, sent 5604 > 5600).
  - Tests: fixtures on the old importer note use a synthetic copy of that record (test_researcher, test_kb_shield); the two eval_qa dropped-qualifier seeds moved to the free-zone caveat. The 17 Oct sample outputs keep their old hedge (historical; a stronger hedge than the record is not flagged).
- **b79231d** follow-up: `duty_scope` "the Social Welfare Surcharge (SWS)"; de minimis note "By interpretation, de minimis helps only…" (Claude had proposed "In Mansha's interpretation"; the extra word lowered drop detection 0.80 → 0.67, "By interpretation" keeps it unchanged); `check_data` also rejects "Interpretation:" labels. 3A: `drop_follow_ups` (7.6c) for ELIGIBLE keeps only an AED-value question (N1) or an HS-code question when the tariff lookup wrote a note (N4: it was that report's only mention of the given 76101090). Replay of 175 saved outputs: N1, N4 keep theirs; C1 27 Oct (2), the 18 Oct free-zone question dropped; the rest already dropped by 7.9 / 1c.
- **c196340** 1C + 2A: box-8/9 note removed, kept in `passages.json` `metadata.notes_kept_out` (not shown to agents; no article numbers, not verified); code adds "See the checklist below for the steps to claim the CEPA rate." (en/ar) at the end of an ELIGIBLE summary with a checklist, after the 97 cautions, at render time (after prose QA); **prompt change** in `prompts/document_builder.md`; 96 anchor matches a plain "follow India's form" (saved hits 19 → 20 of 126, 0 false alarms).
- All 19 offline suites pass at each commit (cloud and Mac).

## Live results (Dots3, k = 1)
- **20261027-180618** (eb630a1; N5, N10, C1, N2): 4/4 code PASS, verdicts 4/4, 0 CHECKS_FAILED, 0 LLM_ERROR, anchor slips 0. Valid 3 of 4 (N2: Dots3 Researcher timed out at 150 s, Gemini 3.6 served, router benched Dots3 90 s so both Builder calls went to Gemini). 72 = 0, 101 met (no hedge, no QA churn), "Inference:" 0, planner normal (largest part 6,795 < 7,600). Leftovers: bare "SWS" in the duty note, "Interpretation:" label (→ b79231d). New: C1 ELIGIBLE with "What's still needed" (→ 3A).
- **20261027-183851** (b79231d; N2, C1, N1, N4): 4/4 PASS, valid 4/4. 3A fired once (N4 free-zone question); N4 kept its HS question; C1 no "What's still needed". First live rescue at the 210 s timeout (N2 Researcher 170.6 s). 96 in 2 of 4 by reading: the Researcher kept the scoped note word for word; the Builder wrote "use box 9 …" (N2) and "follow India's form" (N1) (→ 1C). Prose QA rejected the prompt-required "checklist below" sentence in C1 and N2 (4 of the last 6 ELIGIBLE reports) (→ 2A). N4 must-say half met (problem 98).
- **20261027-191029** (c196340; C1, N2, N5, N1): 4/4 PASS, valid 4/4 (10/10 `long` on Dots3 at ordinal 0). 96 = 0 (no box 8 anywhere); the code pointer exactly once in 4/4 ELIGIBLE summaries, last, after the caution in N2 and N5; Builder-written pointers 0; prose QA 4/4 approved in round 1. 72 = 0, fee step MoFT 4/4, 101 met, SWS spelled out, no labels, C1 no "What's still needed", 97 cautions present. QA: N5 r1 rejected (the new duty-note path, below); N5 r2 one correction overruled by the KB shield (7.6i, a typo "fix" on `P-UAE-ISSUER`).
- G17 under R1: **36 counted runs, 1 LLM_ERROR (215953); streak 28.**

## New or changed problems / gaps
- **N5 duty-note path (new, G39 kind):** a caveat copying the duty tool's "CEPA rates reduce BCD only…" note cited `P-IN-DUTY-SCOPE`; QA judged it against that record and "fixed" it into the Table II AIDC sentence, wrong for a Table I line; round 2 copied it. Saved outputs: 2 of 93 such caveats cite `P-IN-DUTY-SCOPE` (1 old wording, 17 Oct chargers; 1 new, 191029 N5): not caused by the 2a wording. **Next task, option A** (code re-cites it to the duty tool before the checks).
- **Router timeout (Mac chat finding):** a provider timeout benches key+model for `TRANSIENT_COOLDOWN_MS` = 90 s plus an in-memory penalty (+1, decays 1 per 2 min). Worst case now 210 s + one hop ≤ 270 s < client 300 s; no client retry after 240 s (`CALL_BUDGET_S`).
- **Live-unproven, offline-proven:** the ELIGIBLE AED-value keep path (N1 asked it in 1 of 3 runs); 1c follow-up path; 1d (SETTLED). Each is logged by name when it fires.
- **Risks accepted:** an ELIGIBLE answer needing something other than a value or a code loses that question (none in 175 saved outputs); a Builder that still writes its own pointer would give two (0 in 191029).
- Pre-existing, unchanged: G14 (actor-first and requirement-as-step steps; code-filled "issuing authority" actor) in 4/4; 86 milder ×4; G12 free-zone note (accepted); problem 98 (N4 tool-note reason missing).
- Registers: 72 0 in all 12 runs since eb630a1 (11 valid; was 2–4 of 4 per sitting); 96 0 in 4 since c196340; 101 no churn in 12; 3A fired 1; code pointer 4/4.

## Project update
- **agent_prompts.md:** Document Builder, ELIGIBLE summary line: "…give the saving if FACTS gives one; point the reader to the checklist below." → "…give the saving if FACTS gives one. Do not mention the checklist: code adds that sentence." (already in `claude/agent_prompts_addendum_2026-10-27.md`). No other prompt changed in this task.
- **CURRENT_STATE:** this handoff (KB batch closed; streak 28; the registers above).
- **llm_backend_setup.md:** the 210 s timeout and the bench/penalty finding (already in `claude/llm_backend_setup_addendum_2026-10-27.md`).
- **Fact base:** A6 used as given; the box-8/9 fact now lives only in `passages.json` metadata (not in any agent's evidence).

## Next
1. **Merge (Haris):** Claude recommends merging `claude/kb-batch-brief-step-1-gxvauj` (c196340 + this handoff) into main: 3 Dots3 sittings, 11 valid runs, all 4/4 code PASS, no regression.
2. **Next task:** step 1 = the N5 duty-note re-cite (option A) on paper; then 100 + 98, step shield (G32/G39; option C of 1d, "keep" = "must keep"; G14 actor-first), 99; the guard health check (router down → not OK).
