# Handoff: N5 duty-note re-cite (28 Oct 2026)

Branch `claude/n5-duty-note-recite-yioh0n`, started from main at d6f3efb (KB batch and router facts merged). Follows `docs/cloud/handoff_2026-10-28_router_facts.md` and `docs/cloud/handoff_2026-10-27_kb_batch.md` ("next task, option A"). **Task closed (Haris, 28 Oct).**

## Decisions (Haris)
- **A2** (Claude's recommendation): code re-cites a caveat that copies the duty tool's "BCD only" note under another record to `TOOL:duty:<line>`, writes it as the tool's note word for word, and keeps any sentence the note does not cover as its own caveat with the record it cited. Options were A1 (re-cite only, keep the Researcher's words: leaves mixed caveats such as the IGST-base sentence under the tool's ID, for QA to flag) and B (a Researcher or QA prompt rule: rules of this kind were ignored before, G39).
- **Router check in the terminal block:** Haris's terminal showed `/v1/models` answers 401 without a key (the router was up), so the template's "router 200" check stopped a working sitting. Claude proposed treating 200 or 401 as "answering" and stopping only on anything else (e.g. 000 = no answer). Haris: "if it works, yes, fix the template". It worked in the sitting, so the template was fixed.
- **Close the task (option 1)** with 7.6k on the live-unproven, offline-proven list (as for the AED-value keep path). The alternatives were another sitting just to see it fire (about 1 output in 11, not guaranteed), or closing and taking G14 first.

## What was found (design, on paper)
- The handoff counted 2 of 93 such caveats. The full sweep of 185 saved Researcher outputs (1,914 caveats) found **16 caveats saying "BCD only" while citing `P-IN-DUTY-SCOPE`**. All 16 were on Table I lines (76101000, 94036000, 33049990, 32091010, 85044030) whose duty result carries the note, so all 16 were the tool's note under the wrong ID.
- QA's Table II/AIDC "fix" was copied in C1 20261027-155659 (QA r1 correction "omitting the AIDC…") and N5 20261027-191029. The pipeline windows_nodata run of 23 Oct 19:07 shows the same r1 → r2 change.

## What changed (commits)
- **7e6608f** `mansha/researcher.py` `recite_duty_notes` (Step 7.6k), called in `run_researcher` after `plain_check_names` and before `restore_qualified_notes`, so it applies in round 1 and in the revision.
  - **When it acts:** only when the chosen line's duty result has the "BCD only" note (`BCD_ONLY_RE`), and the caveat does not cite `TOOL:duty:` and does not mention AIDC / Table II.
  - **Duplicates:** if the tool's note is already cited to the tool, the passage copy is dropped.
  - **What it leaves alone:** Table II lines, excluded lines, and no chosen line.
  - **Builder effect:** `TOOL:duty:` notes are mandatory, so the note is printed verbatim.
  - **Tests:** `scripts/test_researcher.py` has 13 new checks: the N5 and C1 live wordings, the IGST-base split, the duplicate drop, the untouched controls, and a `run_researcher` end-to-end check.
- **9ae2791** `CLAUDE.md`: the 🖥️ template's router line becomes `code=$(curl … || true); case "$code" in 200|401) …;; *) STOP …`. Checked with `bash -n`.
- **89b648b** `docs/cloud/readings/20261028-170121_reading.md`.
- No prompt change, no KB change, no backend change.

## Results
- All 20 offline suites pass.
- **Replay** over 184 saved outputs with their own evidence, with brackets removed first as `unbracket_ids` does: **16 re-cited, nothing else changed.** 4 of the 16 split off "Because the IGST base includes BCD, a lower BCD also lowers the IGST amount." with `P-IN-DUTY-SCOPE`.
- **Live 20261028-170121** (7e6608f; N5, C1, Dots3, k = 1):
  - 2/2 code PASS, valid 2/2 (5/5 `long` on Dots3 at ordinal 0).
  - **Outcome met 2/2:** 0 Table II/AIDC notes, the "BCD only" note in Important notes, no QA correction on it. **7.6k did not fire:** the Researcher cited the tool itself in all 3 outputs.
  - C1 QA r1 rejection was correct: the fee note had borrowed "no currency conversion is done by Mansha" from the duty note (G8); QA's fix was copied in r2.
  - Must-say / must-not-say met in both.
  - Slips: 94 ×1 (N5), 86 milder ×1, G14 in 2/2. Minor G35: N5 "it may be marked" on the retrospective box-9 sentence; C1 dropped the anti-dumping note's parenthesis but kept "likely".
- **First live `router_facts`:** every section read, no "cannot read", so the schema is confirmed. The one unmatched client call was the router's own 0.02 s 429 refusal (no provider attempt).
- **G17 under R1:** 38 counted runs, 1 LLM_ERROR (215953); **streak 30.**

## New or changed problems / gaps
- **N5 duty-note path:** fixed in code. **Live-unproven, offline-proven** (logs `re-cited to TOOL:duty:…` when it fires). Expected about 1 in 11 Researcher outputs.
- **Risks accepted:**
  - A future "BCD only" caveat that also makes a new claim is split; the extra sentence keeps its own citation, so nothing is lost.
  - A re-cited note takes a mandatory note slot (the normal case: 141 saved caveats already cite the tool).
- **New, small:** the Researcher merges notes across records (C1: the duty note's "never converted" into the fee note). QA caught it here; it is the G8 kind and needs no new work unless it recurs.
- **router_facts:** a router-side refusal (no provider attempt) shows only as "client call not matched". An idea for later, not needed now: label it as a refusal.
- Pre-existing, unchanged: G14 (actor-first and requirement-as-step steps; slip 94) in 2/2; 86 milder; G12 free-zone note (accepted); problem 98.

## Project update (Mac chat, 💾)
- **CURRENT_STATE live addendum:** N5 re-cite closed (7.6k, A2); the 16-of-185 finding; sitting 20261028-170121 results; 7.6k on the live-unproven list; router_facts schema confirmed live; terminal block router check (200 or 401); G17 streak 30.
- **agent_prompts:** no change. **llm_backend_setup:** no change (one fact noted: `/v1/models` answers 401 without a key). **Fact base:** no change.

## Next
1. **Merge (Haris):** `claude/n5-duty-note-recite-yioh0n` into main (7e6608f, 9ae2791, 89b648b and this handoff).
2. **Next task:** 100 + 98 (step 1 on paper), then the step shield (G32/G39; option C of 1d; G14 actor-first and slip 94), 99, and the guard health check (router down → not OK).
