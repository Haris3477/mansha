# Handoff: the Arabic gap, N15 (28 Oct 2026)

Branch `claude/arabic-gap-n15-yfk0w0`, from main at 5657754. The code is done offline. **Not closed:** the live sitting (N15 ×2, N2 ×1) and its full reading are still due (credit rule: no step closed before its sitting).

Note: `claude/claude-md-credit-rules-9popkb` (CLAUDE.md credit rules and its handoff) is not merged into main yet. This session read it there and followed it.

## The problem (reading 222746)
N15's Arabic report had three separate causes:
1. **The Builder's prose on Dots3:** Chinese letters, English glued onto Arabic words, English words and misspellings. The same case on Gemini Flash (215427) was clean.
2. **English printed by code:** the title's product, "still needed", the `Authority:` lines, the table cell and 5 verbatim notes. Also, the code-only fallback prose is English only.
3. **No check looked at the script:** neither `check_prose`, the report check, prose QA nor the grader.

## Decisions (Haris)
- **Order:** A, then D, then decide B from the data. This was Claude's recommendation.
- **Arabic wording (Haris's own plan):** push only the Arabic that can be confirmed. New Arabic sentences wait in `docs/cloud/arabic_review.md` until Haris and a friend who reads Arabic have reviewed them. Claude agreed, and added an Arabic notice to the English fallback so nothing unreviewed is printed.
- **D:** option 1 (the Builder writes them, checked by code, with the English originals as the fallback), rather than option 2 (English under an Arabic label). This was Claude's recommendation.

## Commits
- **`5335a6a` Step 1 (A1 + A4):** `script_problems` / `script_corrections` in `mansha/document_builder.py`.
  - **Any report:** letters of a third script are flagged.
  - **Arabic reports:** words mixing Arabic and Latin are flagged, and so are English words outside `LATIN_TERMS`. English in brackets that holds no Arabic (a gloss) and web addresses are allowed.
  - **In `check_prose`:** the problems become corrections in the one retry.
  - **In `eval_grade`:** the same check runs on the whole report, without the sources list or [n].
  - **Replay:** every fault in 222746 N15 is flagged; 215427 has no false alarms.
- **`7dcda06` Step 2:**
  - `AUTHORITY_TEXT`: the Arabic authority lines. A test fails if any KB actor has no Arabic name.
  - `FALLBACK_NOTICE`: an Arabic report on the English code-only prose starts with an Arabic line saying so.
  - `docs/cloud/arabic_review.md`:
    - Part 1: in the code now, for Haris to check;
    - Part 2: drafts, not in the code (saving cell, 5 notes, Arabic fallback prose);
    - Part 3: Arabic already live that no native reader has checked.
- **`1f936ee` Step 3 (D):**
  - Arabic reports only: the Builder also returns `product` and `needed`.
  - **Code checks them:** script check, numbers, IDs and code words, item count.
  - **If only these still fail after the retry:** the Arabic prose is kept, and the English originals are printed (`BuilderResult.untranslated`, in the phase log and `builder.json`).
  - **Prose QA:** still receives only summary, classification, duty, origin and notes.
- **Tests:** all 20 offline suites pass after each step.

## Prompt change (Project's agent_prompts must be updated)
`prompts/document_builder.md`, old → new:
- **JSON schema:** `"notes": [...]` → `"notes": [...], "product": "string", "needed": ["string"]`, plus the line "`product` and `needed` only when you write in a language other than English; in English, leave both out."
- **Two new field bullets after `notes`:**
  - "`product`: the PRODUCT line of FACTS in {language}, as a short name. Add nothing."
  - "`needed`: each STILL NEEDED item of FACTS in {language}, in the same order, one string per item (an empty list if FACTS says nothing is needed). Keep every detail of the item and add none."

## What the sitting should show (how we'll know)
- **N15:** the summary, classification, duty, origin and notes have no third-script letters, no mixed words, and no English outside the allowed terms. If they do, the phase log shows the retry, or the code-only prose with the Arabic notice.
- **Still English in N15, expected and not a regression:** the 5 verbatim notes (until Part 2 is reviewed), and the grader's language check will still FAIL on them.
- **Title and "still needed":** in Arabic, or `untranslated` logged.
- **N2 (English):** unchanged. The title and "still needed" stay the English originals; no `product`/`needed` in `builder.json`.
- **B (another model for Arabic):** if N15 falls back to the English prose in both runs, that is the evidence for moving Arabic Builder calls to another model. It would be a router change, which is a ➡️ (b) job on the Mac.

## Gaps (recorded, not fixed)
- **Spelling:** not checked by code ("الجمره").
- **Faithfulness of `needed` and `product`:** only counts and numbers are checked by code, and prose QA doesn't read them.
- **Part 2 of the review file:** the 5 notes, the saving cell and the Arabic fallback prose. Other tool notes that can reach an Arabic report have no draft yet.
- **Arabic fallback prose:** it would still contain English data from the KB and tools (description, agreement, basis). To be decided when Part 2 goes into the code.

## Next
1. **Live sitting (🖥️):** N15 ×2 (the repeat is the point: how often the fallback fires), then N2 ×1. Then the full reading here.
2. **B:** decide from the reading.
3. **Review:** Haris (and his friend) review `docs/cloud/arabic_review.md`; then code switches to the reviewed Part 2 texts (offline tests only).
4. **Save progress (Mac chat):** the CURRENT_STATE addendum and the agent_prompts addendum (the prompt change above).
