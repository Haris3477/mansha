# Handoff: step shield (28 Oct 2026)

Branch `claude/fix-source-id-fill-gap-86nr8m`, from main at de658a8 (7.6n merged). Design and decisions: `docs/cloud/step_shield_brief.md`. **Task closed after the 222746 sitting (pending Haris's merge).**

## Decisions (Haris)
- **S3: code writes the claim checklist from the KB** (Claude's recommendation; the options were S1 a prompt rule, S2 a prompt rule plus a code check).
- **QA side:** Haris asked why Claude first proposed postponing it. Claude: under S3 it becomes part of S3, because a QA correction on a step is not counted.
- **English step texts approved;** the Arabic ships as drafted and Haris confirms it later.
- **Storage:** a `step` field on the KB records.
- **Left out of the checklist:** retrospective issue and amendment.
- **Haris:** "not only offline tests, if live tests are needed also we'll do that before committing and pushing." Claude: the Mac needs pushed code, so the order is push to the session branch → sitting → reading → merge.
- **After 215427: option 1, F1 + F2** (Claude's recommendation; the options were a prompt line only, or merging as is).
- **Haris:** add the Arabic gap as its own task.

## Commits
- **818cc9b / 6f4494d:** 7.6n source_id fix and its handoff (merged as de658a8).
- **c4722fe:** step shield S3, covering the KB step texts, `fill_steps`, the prompt change, the QA step filter, `check_data` and the QA eval.
- **f097cb5:** reading 20261028-215427.
- **b0f135c:** F1 (`drop_step_caveats`) and F2 (PASS/FAIL in plain words).
- **This commit:** reading 20261028-222746 and this handoff.

## Results
- **Offline:** all 20 suites pass (test_researcher +28 checks, test_qa +4, check_data step check).
- **Replay** over 84 saved outputs: every claim run gets exactly 8 steps, with no step warnings; F1 changes 53, with no KB note dropped.
- **Live, 215427 (c4722fe):**
  - The checklist is right in 4/4 runs, and the Researcher left `procedure` empty in 5/5 calls.
  - N4 fell back to code-only after a prose-QA false rejection; N15 was not valid (network outage).
  - Found: notes repeating the steps, which led to F1.
- **Live, 222746 (b0f135c):** 3/3 PASS, 3/3 valid; 0 notes repeating steps; the free-zone note kept.

## PROMPT CHANGE (Project agent_prompts must be updated)
`prompts/researcher.md`:
- **Step 6, old:** the steps to claim, with rules: cite the passage; name who acts as the record's `actor:` line; keep qualifiers; timelines only if given; the fee step from `TOOL:coo_fee`; the `P-UAE-ISSUER` caveat.
- **Step 6, new:** "Always write `procedure` as an empty list: code writes the steps to claim the CEPA rate from the knowledge base. If the origin status is QUALIFIES or NEEDS_MORE_DATA, add the `P-UAE-ISSUER` note to `caveats`: who issues the certificate, and what no source confirms."
- **Schema:** `"procedure": []`.
- **Shown-text rule:** "the `procedure` steps," removed.

## KB change (fact-base addendum)
`data/india/passages.json`: a `step: {en, ar}` field on P-MOET-FACTORY-REG, P-MOET-COO-INDIA, P-AGR-3.17-APPLICATION, P-AGR-COO-RULES, P-AGR-3.12-DIRECT, P-IN-IMPORTER and P-AGR-RECORDS-VERIFICATION. Each step rewords that record's own summary, so no fact moved.

## Problems / gaps
- **Fixed:** G14 (actor-first and requirement-as-step steps), slip 94, slip 72 in steps, G32/G39 for steps, "keep" = "must keep".
- **New, Arabic task (next):**
  - N15's Arabic prose (Builder, Dots3) has Chinese characters, English fragments inside words and misspellings.
  - Prose QA approved it and the report check has no script check.
  - Notes, "What's still needed", the `Authority:` lines, the title and table cells are English.
- **Recorded, not fixed:**
  - The prose-QA judge falsely rejected N4's correct 40% Ex-Works sentence, and its fix led to a wrong 45% one (215427).
  - QA inconsistency on N15's "simple assembly might apply" speculation: rejected in 215427, approved in 222746.
  - The grader's N4 40% anchor also matches the factory step.
  - The router_facts matcher missed calls in 215427.
  - Terminal paste garbling: split blocks worked in 222746.
- **Live-unproven, offline-proven:** F2 (fires only on a code-only fallback); the "replaced N model steps" path (the model obeyed the prompt every time).

## Next
1. **Merge (Haris):** this branch into main.
2. **Save progress (Mac chat), when Haris wants:** the CURRENT_STATE addendum (this handoff), the agent_prompts addendum (the prompt change above) and the fact-base addendum (step texts).
3. **Next task: the Arabic gap** (recommended now: N15 isn't demo-safe). Then 99, then the guard health check.
