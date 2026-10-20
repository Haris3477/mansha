# Step 7 (QA Evaluator) — build details

_What QA receives, plan B, model tests, files and live results. Moved verbatim from progress.md (20 Oct 03:05 save) on 20 Oct 2026. Design decisions D1–D7, 7.6 as built, open problems and gaps live in the Project doc CURRENT_STATE.md. Read this when changing `mansha/qa.py`, `qa_evidence.py`, `prose_qa.py` or the eval scripts._

### What QA receives (mansha/qa.py `build_messages`)
1. **INTAKE JSON.**
2. **CHECKED BY CODE (correct; never correct these)** (`checked_facts`, 7.4): verdict, origin status (with "line excluded, no origin check" for NOT_APPLICABLE), rule of origin, duty saving status, and **what the user already gave** (shipment value; bill of materials and declaration GIVEN / NOT given or incomplete with the missing items / not needed for an excluded line; HS code).
3. **CODE WARNINGS** numbered W1, W2, … (global numbers, kept across parts).
4. **EVIDENCE** (`qa_evidence`, 7.2): candidate lines (non-chosen shortened to ID, code, description, rates), the chosen line's rule/origin/duty results, every other cited record word for word, uncited rules and passages as one line each (ID + title). Built only from what the Researcher saw (counts and percentages only).
5. **RESEARCHER JSON** (`research_for_qa`): classification reasoning step only; **without** `verdict`, step `authority`, `origin_result.status`, `origin_rule`, `estimated_saving` (code fills or verifies those exactly; 7.4, after GPT-OSS "corrected" correct values). **Since 7.6c–d** QA receives the Researcher JSON after code has unbracketed IDs and, for NOT_ELIGIBLE/NO_PREFERENCE, dropped follow-up questions and claim caveats.
- Validation (`check_qa`): exactly 3 scores, 0/1; every warning judged once (REAL/NOISE + reason), no unknown IDs; each correction names an existing field (index must exist) that is **not code-checked** and (plan B) is shown in that part, with problem, fix and an evidence ID or null; 0 ↔ corrections; REAL → factuality 0.
- Corrections reach the Researcher as "`field`: problem Fix: fix (see ID)", prefixed "QA:", in the single shared revision.
- Phase log: QA status OK / REJECTED / FAILED; scores; "Code warnings judged by QA: W1 REAL: … -> reason"; problems in QA's own answer; plan B parts. `qa_N.json` holds scores, corrections, judgements, answer problems, parts and every call.

### Plan B (7.4b, decided with Haris 17 Oct): split big reviews
- **Why:** Groq's free tier refuses a request whose prompt + answer budget exceeds 8,000 tokens (17 Oct 16:57 windows: "Limit 8000, Requested 8779"), and the router skips a model whose limit is too small. ELIGIBLE and NEEDS_MORE_DATA reports were unreviewed, i.e. half the branches. No other free model qualified (see 7.4).
- **How:** code estimates the prompt (characters ÷ 3.6; ran ~10% high vs Groq's counts). If prompt + 3,000 ≤ 7,600 → one call as before. Else: the findings first, then the steps and notes in order, packed into as few parts as fit (prompt + 2,000 ≤ 7,600 each). Each part: "REVIEW PART i/n" header, intake, CHECKED BY CODE, its own warnings (a warning goes to the part holding its field, else part 1), only the records its fields cite; part 1 also gets candidates, chosen-line tools and the uncited index; a part without the findings gets the origin basis as context only. Steps and notes appear under `items`, keyed by field name (`procedure[4]`).
- **Merge:** lowest score per metric; all corrections and judgements kept; APPROVED only if every part approves; REJECTED if any part rejects (its corrections used even if another part failed); ERROR ("NOT reviewed by QA in full") if a part failed and none rejected; > 6 parts → ERROR without calls.
- **Sizes:** chargers, plastic 1 call (chargers 2 on 19 Oct 04:16 with 17 caveats → 1 again after 7.6d); windows 2–3; windows_nodata 2–3. On Groq each extra call waits ~1 minute; **back-to-back multi-part runs trigger the router's escalating cooldown (problem 80)**.
- **Status:** offline tests pass. **Verified live 18 Oct 16:19–16:56.** After the paid judge (250k TPM) the split stops being needed but stays as the safety net for the free tier.

### 7.4 model tests (17 Oct, `eval_qa`)
| Candidate | Result | Decision |
|---|---|---|
| **GPT-OSS 120B (Groq)** | after fixes: 6/6 seeds caught on the right field, clean cases approved (one "false rejection" was a real catch, problem 59); answers 1–5 s | **`judge` = GPT-OSS 120B only** |
| Qwen3.8 27B (Groq) | Groq "output tokens per minute (OTPM): Limit 1000" → every call refused | dropped: 1,000 answer tokens/min too small for QA |
| Gemma 4 31B IT (Google) | 3/3 failed (500 Internal error ×2, 60 s timeout) | dropped for now; also shares Google with the Researcher |
| Gemma 4 31B (NV) | switched off by the router's own migration ("every chat probe hangs 90s+… re-asserted each boot"); not in the dashboard | not usable |
| Gemma / Laguna (OpenRouter free) | 50 requests/day, rate-limited after the first call | not usable |

**Groq limits for GPT-OSS 120B (Haris's console, 17 Oct):** 30 RPM, 1,000 RPD, **8,000 TPM, 200,000 TPD**. On 17 Oct GPT-OSS used 202,430 tokens and hit the daily cap at ~17:30 Dubai; it resets at 00:00 UTC = **04:00 Dubai**.

### Files (Step 7)
- `mansha/qa.py`: `run_qa`, `plan_parts`, `Part`, `_review`, `check_qa`, `build_messages`, `checked_facts` use, `QAOutcome(status, corrections, scores, llm, note, judgements, llm_calls, failed_attempts, output_problems, parts)`, statuses APPROVED / REJECTED / SKIPPED / ERROR, `QA_CHAIN = "auto:judge"`, `SPLIT_LIMIT 7600`, `PART_BUDGET 2000`, `MAX_PARTS 6`.
- `mansha/qa_evidence.py`: `qa_evidence(pack, research, part=None)`, `research_for_qa(research, part=None)`, `checked_facts`, `item_keys`, `CODE_OWNED`, `FINDINGS_KEYS`.
- `prompts/qa.md` (= agent_prompts.md Agent 3).
- `mansha/orchestrator.py`: default `qa=run_qa`; QA statuses imported from `mansha/qa.py`; QA ERROR continues with a warning; phase log shows judgements, answer problems and parts.
- `mansha/llm_client.py`: `CHAIN_LIMITS["auto:judge"] = 3000/3000`; comment on Groq corrected (8,000 tokens/min, prompt + answer).
- `mansha/researcher.py`: `strip_list_markers()` (7.2); **on `step-7.6`, uncommitted (7.6c–d):** `unbracket_ids()`, `drop_follow_ups()`, `drop_claim_caveats()`, `NO_CEPA_RATE_VERDICTS`, `CLAIM_PASSAGE_KINDS`, `CLAIM_TOOL_PREFIXES`, `claim_source_ids()`, `is_claim_note()`; `run_researcher` order: unbracket → fill authorities → fill tariff line → drop caveat gaps → check → (NOT_ELIGIBLE/NO_PREFERENCE) drop follow-ups and claim caveats → check again → log every change as "researcher normalized".
- `mansha/evidence.py` (7.6d): `EvidencePack.corridor` (default "india").
- `scripts/eval_qa.py` (live): 4 clean + 9 seeded cases, `--chain`, `--repeat`, `--pause`; saves each answer (incl. parts) in `runs/eval_qa/<time>[_chain]/`; exit 0 only if every seed is caught on its field and every clean case approved.
- `scripts/try_chain.py`: `--agents qa`; each switched agent keeps its own chain's budget; refuses `judge` as a trial chain.
- Tests: `scripts/test_qa.py`, `scripts/test_qa_evidence.py`, `scripts/test_pipeline.py` (real `run_qa` with a fake judge; **7.6c–d checks**: NOT_ELIGIBLE follow-ups and bracketed IDs fixed in round 1; claim notes never reach QA), `scripts/test_researcher.py` (list markers; **7.6c–d sections** `unbracket_ids`, `drop_follow_ups`, `drop_claim_caveats` with the live 19 Oct follow-ups and 17 caveats).
- Samples fixed (QA found the mistakes, problems 58–60): `plastic.json`, `windows.json`, `windows_nodata.json`.

### eval_qa cases
| Case | Planted mistake | Field |
|---|---|---|
| clean_windows / clean_chargers / clean_windows_nodata / clean_plastic | none | approve |
| flip_failed_check | "Final manufacture took place in the UAE" (problem 30) | origin_result.basis |
| merged_step | factory-registration step + "issued within five working days" (G8) | procedure[0] |
| dropped_qualifier | "reportedly uploaded" → "uploaded" (problem 6) | procedure[5] |
| invented_timeline | "Processing takes 14 working days" (code warns; QA must judge REAL) | procedure[1] |
| bom_already_given | asks for a bill of materials already used (problem 55) | follow_up_questions |
| irrelevant_caveat | HS 71 note on battery chargers (G12) | caveats[6] |
| useless_gap | 17 Oct live chargers gap about build-up VA (problem 56) | gaps |
| nodata_dropped_qualifier | "reportedly… (unconfirmed…)" removed, in part 3/3 | caveats[11] |
| nodata_merged_step | factory-visit fact in a direct-consignment step, part 1/3 | procedure[4] |

Note (19 Oct): `irrelevant_caveat` and `bom_already_given` are on chargers (NOT_ELIGIBLE). `eval_qa` calls `run_qa` directly on fixtures, so 7.6c–d (which run inside `run_researcher`) don't remove them there; in a real pipeline run the chargers follow-up would now be dropped by code. Re-check these two cases' meaning when the evaluation set is built.

### Live results (17 Oct)
- **eval_qa, GPT-OSS on `trial`, 16:19–16:30:** 6/6 seeds caught on the right field; clean_chargers, clean_plastic approved; clean_windows "rejected" for a dropped "unconfirmed" → real catch (problem 59). Retry worked live.
- **`judge` check 16:47:** clean_plastic APPROVED 1.5 s, flip_failed_check CAUGHT 2.7 s.
- **7.5 full pipeline 16:56–17:05:** 6/6 expected statuses, report check 0P/0W everywhere. QA: chargers APPROVED (missed problem 56), plastic APPROVED; windows 413, windows_nodata 413 → "NOT reviewed by QA", reports still produced. Reports read: problem 57.
- **eval_qa all 13, `judge`, 17:21 →** cap hit (problem 64); clean_windows (2 parts) rejected with nonsense (problem 61); clean_windows_nodata rejected for "countervailing" → real catch (problem 60).
