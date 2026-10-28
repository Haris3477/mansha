# Brief: step shield, S3 (28 Oct 2026)

Branch `claude/fix-source-id-fill-gap-86nr8m`, from main at de658a8 (7.6n merged). Follows `docs/cloud/handoff_2026-10-28_100_98.md` ("Next: the step shield").

## Decisions (Haris, 28 Oct)
- **S3: code writes the claim checklist** (Claude's recommendation).
  - Rejected: S1 (a prompt rule: steps say what the exporter does) and S2 (S1 plus a code check sending bad steps back for revision).
- **QA side is part of S3, not postponed.** Haris asked why Claude first proposed postponing it. Claude's answer: under S3 a QA correction on a step can't be applied by the Researcher, so it must not count. That covers G32/G39 for steps and "keep" = "must keep" (option C of 1d).
- **English step texts approved as drafted.**
- **Arabic texts ship as drafted;** Haris confirms them after the N15 sitting.
- **Storage C:** a `step: {en, ar}` field on each KB record.
- **Left out of the checklist:** retrospective issue (box 9, the source of slip 96) and amendment (`P-MOET-AMEND-COO`). Both facts stay in the KB.
- **Haris:** live tests are needed, not only offline tests. Claude: the Mac can only pull pushed code, so the order is commit → push to this branch → live sitting → reading → merge.

## Why (evidence)
- The checklist prints the Researcher's steps word for word. Of 949 saved steps, only about 415 start with the exporter or an action verb, and 85 are "X requires…".
- **Root cause:** the prompt rule "name who acts only as the cited record's `actor:` line does" produced "The Ministry of Economy and Tourism registers the factory" (G14, the same cause as 72).
- In 33 of 33 claim runs since 27 Oct, all 8 step records were in the evidence. The models were re-wording the same steps, not choosing them.
- Only 7 QA corrections ever touched a step. 5 were real, mostly caused by actor-first wording; 1 false one was settled by 1d; 1 false one was uncovered (194504 N10).

## What changed
- **`data/india/passages.json`:** a `step: {en, ar}` field on 7 records (factory registration, e-service application, application content, certificate timing, direct shipment, importer, records).
- **`mansha/evidence.py`:** `EvidencePack.steps` (record ID → step texts).
- **`mansha/researcher.py`:**
  - `CLAIM_STEPS` (the fixed order), `FEE_STEP` (the fee template, EN/AR), `fee_step`, `claim_steps`.
  - `fill_steps`: when the chosen line's origin status is QUALIFIES or NEEDS_MORE_DATA, code writes the 8 steps in the intake's language and replaces any the model wrote; otherwise `procedure` is emptied.
  - Skipped: a record missing from the evidence, and a fee GAP.
  - Revisions show the model an empty `procedure`.
  - The issuer caveat stays the model's to cite (check 6, unchanged).
- **`prompts/researcher.md` (PROMPT CHANGE):** section 6 becomes "Always write `procedure` as an empty list: code writes the steps … If the origin status is QUALIFIES or NEEDS_MORE_DATA, add the `P-UAE-ISSUER` note to `caveats` …". The schema becomes `"procedure": []`, and the shown-text rule no longer names steps.
- **`mansha/qa.py`:** a QA correction on `procedure…` is not sent to the Researcher. It is logged in `overruled_by_kb` with why "code step" ("not counted: the claim steps are written by code from the knowledge base"). Only step corrections → OVERRULED. The QA prompt is unchanged.
- **`scripts/check_data.py`:** `check_steps` checks three things: EN and AR present, no evidence IDs, and no number missing from the record's summary.
- **QA eval (`scripts/eval_qa.py`):** `merged_step` and `nodata_merged_step` are retired (G8 in a step no longer exists). `invented_timeline` moves to the registration caveat.

## Results (offline)
- All 20 suites pass. New tests: test_researcher +20 (fill_steps), test_qa +4 (step corrections), check_data step check.
- **Replay** of 80 saved Researcher outputs (25–28 Oct) through the new code:
  - 58 claim runs get exactly 8 steps; 22 others get 0.
  - **No step warnings.**
  - 1 new problem, from the earlier tariff split rule (25 Oct N13, pre-100 output), not from this change.
  - Fee steps: 40 + 10 band texts and 7 range texts, all from the tool.
  - N15 gets the Arabic steps.

## Live sitting (to run)
- **Cases:** N4 (ELIGIBLE), N2 (free zone), N10 (NEEDS_MORE_DATA), N15 (Arabic), k = 1.
- **Expect:** the 8 checklist items identical to the KB text, no "The Ministry … registers" (G14) and no slip 94. No QA step correction counted (if one appears, it is listed as "not counted"). Researcher output possibly shorter.

## Known gaps
- The `Authority:` line stays in English in Arabic reports: it is copied from the record's English `actor` (pre-existing).
- The grader's N4 must-say "Ex-Works threshold of 40%" also matches the factory step's "40% domestic value added" (pre-existing: the model's steps said it too). The reading checks the 40% by eye.
- QA still sees the steps (its prompt is unchanged), so it may spend words on them; only the counting changed.
