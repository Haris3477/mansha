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

## Sitting result (reading `docs/cloud/readings/20261028-235858_reading.md`)
Sittings 235858 (N15 ×2) and 001258 (N2), both on `89e0d82`.
- **Verdicts:** 3/3 correct. N2 passes and is unchanged.
- **N15 r1:** the round-1 Arabic was caught, and the retry was truncated twice → English fallback with the Arabic notice.
- **N15 r2:** the round-1 Arabic was caught, and the retry passed. The Arabic title and "still needed" came through (D works live). The text still has wrong terms that code can't catch ("الادخال", "فاتورة مواد", "إعلان").
- **Dots3's round-1 Arabic:** corrupt in 3 of 3 runs → the evidence for B.
- **G17 streak (rule A):** 6.
- **New gap:** rejected rounds' prose is not saved in `builder.json`.

## Decision after the sitting (Haris)
"Go with the recommendation" (Claude's): **B option 1.**
- A separate chain `auto:arabic` for Arabic Builder calls, with Gemini Flash first and Dots3 as the backup.
- Part 2 of `arabic_review.md` is reviewed in parallel as the safety net.
- Option 2 (Gemini first in `auto:long`) was rejected.

Plan: `docs/cloud/b_arabic_chain_brief.md`. First the Mac chat (router), then a new cloud session (code and sitting).

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

## B: auto:arabic (session on `claude/arabic-router-chain-tvwgx1`, 28–29 Oct)
**Router (Mac chat, Haris):** chain `arabic` (`auto:arabic`), Gemini only: 3.5 Flash (priority 23), then 3.6 Flash (priority 133); RPD 20 / RPM 10 / TPM 250000 each. Dots3 left out because the router's model order is one global setting (priority only breaks ties), so in a mixed chain Dots3 would serve.

**Design (Haris: "yes to all recommendations"):** Claude's recommendations, all accepted:
- the fallback to `auto:long` fires once per run and stays for later rounds;
- it lives in `run_document_builder` only;
- either Gemini at ordinal 0 counts as valid.

**Commit `0ed8ac7`:**
- **The Builder's chain by language,** with one code fallback to `auto:long` on `LLMCallError`.
- **`builder.json`:** `chain` on every call and round, each round's raw `prose`, and `chain_fallback`.
- **The guard:** `arabic` in `CHAIN_LIMITS` and `router_db.CHAINS`, Arabic cases sized on `arabic`, and a long + arabic shared check.
- **`router_facts` validity by chain:** a chain fallback is not valid for B.
- **Tests and docs:** new tests, the CLAUDE.md chain line, step 2 of the brief. All 20 suites pass.
- **No prompt change.**

**Sitting 20261029-015311 (N15 ×2):**
- **Clean round 1:** Gemini wrote clean round-1 Arabic in 2 of 2 runs (Dots3: 0 of 3), with no retry and no chain fallback. Prose QA approved both.
- **Speed:** the Builder took 14 s (Dots3: 66–101 s).
- **Validity:** r1 is valid (Gemini 3.6). r2 is NOT VALID by the rule: 3.6 returned a 503, and the client's retry was then served by 3.5 at ordinal 0. Whether r2 counts as evidence for B is Haris's call.
- **The global order is confirmed:** 3.6 is asked first.
- **G17 streak:** 8.
- **Full reading:** `docs/cloud/readings/20261029-015311_reading.md`.

**New gaps:**
- the brand name "منشأة" instead of "منشأ" in the LLM prose (both runs);
- "effective N%" is code-printed English;
- the router didn't fail over to 3.5 on the 503 (➡️ a, not blocking);
- new term choices for the native review (listed in the reading).

**Project docs at the next save:** llm_backend_setup (the arabic chain; routing order is global; 3.6 serves first; no failover inside the chain on a 503). CURRENT_STATE (B result). There's no agent_prompts change from B.

**Decision after the reading (Haris, 29 Oct):** "yes to both recommendations, go with (a) if it's safe to do so, if not then go with (b)".
- **r2 counts as evidence for B,** labeled "Gemini 3.5, after one 503".
- **B is closed as holding (option a).**

Claude judged (a) safe, for two reasons:
- B's question (clean Arabic from Gemini) had a clear answer: 2 of 2 clean round-1 runs against Dots3's 0 of 3;
- the next fix needs an N15 ×2 sitting anyway, which adds to the sample. If those runs regress, B is reopened.

Option (b), a repeat sitting now, was not needed.

**Next task:** the brand name "منشأة" → "منشأ", brief `docs/cloud/brand_name_brief.md`. Then the Part 2 review texts once Haris and his friend have reviewed them.
