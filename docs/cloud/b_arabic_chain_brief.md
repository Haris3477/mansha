# Brief: B, a separate model chain for Arabic Builder calls (N15)

Branch `claude/arabic-gap-n15-yfk0w0`. Background: `docs/cloud/handoff_2026-10-28_arabic_n15.md` and `docs/cloud/readings/20261028-235858_reading.md`.

## Decision (Haris, 28 Oct)
"Go with the recommendation":
- **Option 1:** Arabic Builder calls use their own chain, with Gemini Flash first and Dots3 as the backup. English calls stay on `auto:long`.
- **In parallel:** Haris and his friend review Part 2 of `docs/cloud/arabic_review.md`, as the safety net (option 3).

**Rejected:** option 2 (Gemini first in `auto:long` for every case). It would change the English cases too and break comparison with earlier sittings.

**Why:**
- Dots3's round-1 Arabic was corrupt in 3 of 3 runs (222746, 235858 r1 and r2).
- Its retries were either truncated (182 s and 157 s) or passed the script check with wrong terms.
- The one Gemini Flash run (215427, a fallback after Dots3 failed) wrote clean Arabic for the same case.

## Step 1: Mac chat (➡️ case b, a router change)
1. **Create a router chain named `auto:arabic`:**
   - first, Gemini Flash: the model that served 215427's Builder, `google/gemini-3.5-flash`;
   - then `openrouter/dots-studio/dots-3-note-preview:free`.

   If the router can't hold another chain, or the Gemini model has a different id or no quota, stop and bring that back.
2. **Confirm in the router DB** that the chain exists, with its order.
3. **Bring back:**
   - the exact chain name;
   - the model ids in order;
   - Gemini's free-tier limits, if the dashboard shows them.
4. **Don't change** `auto:long`, `auto:qa` or `auto:judge`.

## Step 2: cloud session (after step 1 is confirmed)
1. **Chain by language:** `run_document_builder` uses `auto:arabic` when the report language is `ar`, else `auto:long`.
   - A test covers both languages.
   - The CLAUDE.md "Model chains" line gets the Arabic exception, with Haris's yes.
2. **Logging fix (from the reading):** `builder.json` saves each round's prose, not only the final one, so a reading can see a rejected round.
3. **Tests:** all 20 offline suites, then commit and push.
4. **🖥️ sitting:** N15 ×2.
   - **Valid:** the N15 Builder on Gemini at ordinal 0.
   - **Watch:** round-1 script-check problems, retries, the fallback, and the wrong-term list from the reading (الادخال, فاتورة مواد, إعلان, وأطرافها).
5. **Full reading,** then decide whether B holds.
