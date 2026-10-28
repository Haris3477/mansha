# Handoff: router facts and the new working loop (27–28 Oct 2026)

Branch `claude/handoff-kb-batch-qo03rj`, started from main at bdacef9 (KB batch merged). Follows `docs/cloud/handoff_2026-10-27_kb_batch.md`. Done as its own small task before the N5 duty-note re-cite (Haris, 27 Oct 20:08).

## Why (Haris)
The Mac chat bills Haris's plan; the cloud session bills the $100 cloud credit (about $50 left at 20:58, expires 5 Nov 11:59 Dubai). From now on the cloud also does the reading of live sittings; the Mac chat is used only for what the cloud can't do.

## Decisions (Haris)
- **1A:** the capacity code moves to a shared standard-library module `scripts/router_db.py`, used by the budget guard and router_facts (one source of truth). Option B (a copy in router_facts) could drift; a wrong count already cost us once.
- **2A:** Cerebras token columns are found with `PRAGMA table_info(requests)` from a known list; if none match, the line says so instead of a number. Option B was Haris naming the columns.
- **3A:** readings go to `docs/cloud/readings/<run>_reading.md` on the session branch; the cloud never pushes to `runs-snapshot`. Option B was a `mansha-runs` commit command after every reading.
- **CLAUDE.md wording:** yes as written, including G (the cloud credit rules).

## What changed
- `scripts/router_db.py` (new): `ROUTER_DB`, `CHAINS`, `DAY_MS`, `utc_text`, `counts_attempts`, `chain_capacity` moved from `eval_set.py` by script (no retyping, guard behaviour unchanged), plus `connect_ro`: `mode=ro` and an SQLite authorizer that refuses any read of `settings` / `api_keys`, including PRAGMA on them (problem 84). The guard now reads through it too.
- `scripts/router_facts.py` (new, Mac only, standard library): `python3 -m scripts.router_facts runs/eval_set/<run>` writes `router_facts.txt`: a) requests in the window with attempts, each matched to a case call or "not matched"; b) per-platform attempts, every Researcher/Builder call's served model and ordinal, validity per case (OpenRouter at ordinal 0), unmatched client calls; c) cooldowns in the window; d) router state now (active cooldowns, capacity per chain model, OpenRouter attempts since 00:00 UTC, OpenRouter timeouts in the window, Cerebras tokens and cost estimate at $0.35/$0.75 per 1M); e) chains. `--now` prints d) and e). Window: folder name (Mac local) to the newest phase_log/summary, ±5 min. Matching: time order, same served model, latency within max(2 s, 10 %); never guessed. A section that hits a schema surprise prints "cannot read: …" and the others still print.
- `scripts/test_router_facts.py` (new, 37 checks): the 27 Oct 14:21:39 UTC sitting rebuilt (Dots3 timeout 150 s → Gemini 3.6 ordinal 1, 90 s heuristic bench, two Gemini ordinal-0 Builder calls → N2 NOT VALID; N5 valid); an unmatchable call stays unmatched; settings/api_keys refused (SELECT and PRAGMA), read-only, no such query or `.env` path in the source; break test (without the authorizer the fake key is readable); CLI exit codes.
- `CLAUDE.md`: "Handover blocks" (🔀 + ➡️) replaced by "Live sittings and the Mac" (🖥️ RUN ON YOUR MAC (TERMINAL) template, 💾 SAVE PROGRESS IN MAC CHAT, ➡️ MOVE TO MAC CHAT for (a)–(d) only); new "Reading a sitting", "Router facts", "Cloud credit"; offline suite 20. The terminal block stops only on `eval_set` exit 2 (guard refused); exit 1 (a code check failed) still gets router facts and the snapshot. Template syntax checked with `bash -n`.
- `docs/runbook.md`: router_facts bullet; 20 tests.
- No pipeline or prompt change.

## Results
- All 20 offline suites pass (cloud).
- On the saved 180618 run folder: all 44 client attempts read; the long-call list matches the phase logs (N2 Researcher and both Builder calls on Gemini 3.6).

## Not yet proven (needs the Mac)
- Real column names (`set_at_ms`, `latency_ms`, `duration_ms`, `error_summary`, token columns), the outcome value of a successful attempt, and whether `requests.model_id` holds the served model. "Served" is read from the last attempt of a successful request, so it does not depend on the last two. The first `--now` on the Mac settles the rest; a wrong column shows as "cannot read" in that section.
- Matching assumes calls run one at a time (true of the pipeline today).

## Project update (Mac chat, 💾)
- CURRENT_STATE live addendum: the new working loop (cloud reads sittings; Mac chat only for 💾 and ➡️ a–d), router_facts, readings in `docs/cloud/readings/`, offline suite 20.
- agent_prompts: no change. llm_backend_setup: no backend change (router_facts only reads the DB). Fact base: no change.

## Next
1. Merge (Haris): this branch after review.
2. Optional, no LLM calls: `python3 -m scripts.router_facts --now` on the Mac to confirm the real schema before the next live sitting.
3. Next task: the N5 duty-note re-cite (option A) on paper, then 100 + 98, step shield (G32/G39, G14), 99, guard health check.
