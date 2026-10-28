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

## Step 1 result (Mac chat, 28 Oct; Haris chose option 1)
- **Chain `arabic` (call as `auto:arabic`), Gemini only:** `google/gemini-3.5-flash` (priority 23), then `google/gemini-3.6-flash` (priority 133). Each RPD 20, RPM 10, TPM 250000. Router DB profiles id 7, custom. long / qa / judge / trial unchanged.
- **Why Dots3 is not in it:** the router orders every chain by one global setting (smartest, a sampled score); a chain's manual priority only breaks ties (`services/router.ts` `orderChain`; no per-chain or per-request override). Dots3 ranks 35 against Gemini 3.5's 41, so a mixed chain would mostly serve Dots3 (as `auto:long` does, although Gemini 3.5 has its first priority). The backup moves into code.
- **Open (Claude's note):** because the order is global, Gemini 3.6 may rank above 3.5 and serve first in `auto:arabic`. The 215427 clean run was 3.5. Haris chose to count either Gemini at ordinal 0 as valid; the reading names which one served.

## Step 2: cloud session (design agreed by Haris, 28 Oct: "yes to all recommendations")
1. **Chain by language:** `run_document_builder` uses `auto:arabic` when the report language is `ar`, else `auto:long`.
2. **Code fallback, once per run:** if an `auto:arabic` call still fails after the client's own retry rules (`LLMCallError`), that same round goes to `auto:long`, and so does any later round. Prose that only fails the checks is not a call failure: round 2 stays on `auto:arabic`. If `auto:long` fails too: the code-only report, as before. The fallback lives in `run_document_builder` only (`llm_client` unchanged).
3. **Recorded:** `builder.json` gets `chain` on every call and round, each round's raw `prose` (the rejected round too: the gap from the 235858 reading), and `chain_fallback` (`null` or `{from, to, round, reason}`); the phase log names the fallback. A fallback run is NOT valid for judging B.
4. **Guard and router facts:** `auto:arabic` in `CHAIN_LIMITS` (same as long) and in `router_db.CHAINS`. Arabic cases put the Builder's share (typical 2, worst 3) on `arabic`, and `long` keeps its full worst case (a fallback lands there). New shared check long + arabic (Gemini 3.5; Google's quota is project-wide). N15 ×2: arabic 4-6 of 40 a day. `router_facts` validity by chain: `auto:long` on OpenRouter at ordinal 0 (unchanged), `auto:arabic` on a Gemini model at ordinal 0; a chain fallback is "NOT VALID for judging B".
5. **Tests:** all 20 offline suites, then commit and push.
6. **🖥️ sitting:** N15 ×2.
   - **Valid:** the N15 Builder on Gemini at ordinal 0 in `auto:arabic`, no chain fallback.
   - **Watch:** which Gemini served, round-1 script-check problems, retries, the fallback, and the wrong-term list from the reading (الادخال, فاتورة مواد, إعلان, وأطرافها).
7. **Full reading,** then decide whether B holds.

## Project docs at the next save
- llm_backend_setup: the `arabic` chain, and the finding that routing order is global.
