# Mansha — runbook and code map

_How to run things and where the code is. Moved verbatim from progress.md (20 Oct 03:05 save) on 20 Oct 2026. **Updated 24 Oct 2026 (Step 7.7)** for 7.6–7.9 and the Cerebras judge; the current git and router state is always in the Project doc CURRENT_STATE.md._

## How to run
- VS Code terminal (bash), prompt shows `(.venv)`; else `source .venv/bin/activate`.
- Router: second terminal `cd ~/Projects/freellmapi && npm run dev` (not needed for offline tests).
- From project root: `python -m scripts.<name>`; exception `python scripts/smoke_test.py`.
- **Full pipeline (live):** `python -m scripts.run_pipeline` (all 6 cases), `python -m scripts.run_pipeline windows chargers`, or `python -m scripts.run_pipeline --message "..." [--bom samples/windows_qualifies]`. The usual live set: `python -m scripts.run_pipeline windows windows_nodata windows_nodata windows_nodata` (~10–15 min; ~20–30 Cerebras calls ≈ $0.07). Since 7.6k the client paces `auto:judge` (4 requests / 60 s), so cases can run back to back. **Budget the day:** Dots3 (the Researcher's fallback in `long`) allows 50 requests per rolling 24 h; on 24 Oct our own live sets used it up (52 in 24 h) and a Gemini outage then ended a run in LLM_ERROR (G17). Check the router's `requests` table before a live set.
- **Evaluation set (since 24 Oct; design and decisions in `docs/archive/evaluation_set_design.md`):** `python -m scripts.eval_set --dry-run` (tools only, no LLM: re-derives the answer key; `--group reserve` for the reserves, `-v` for every fact); live: `python -m scripts.eval_set [--group core --group stop | --case N4 --case N7] [--only-repeat --repeat 3] [--force]`; re-grade saved runs without the LLM: `python -m scripts.eval_set --grade runs/eval_set/<time>`. A live run does the dry run first, then the **budget guard** (reads the router's own sliding-24 h counts in `rate_limit_usage` and its benches in `rate_limit_cooldowns`, read-only; a benched model counts 0, a provider's daily-quota bench covers all its models), then each case through the pipeline in one process. Output in `runs/eval_set/<time>/`: one folder per run, `summary.md`/`summary.json` (code checks, slips, requests and tokens), `reading.md` (what code can't judge; Haris and Claude fill it in). Free capacity is the limit: about 6–8 report cases a day on free `long` (24 Oct: Google's free quota is project-wide and ran out after ~15 Gemini calls; Dots3 50 per 24 h); runs take 2–5 min each on Dots3. Don't pass `--force` to get around a SHORT budget.
- **QA evaluation (live):** `python -m scripts.eval_qa --pause 65 [cases]`, `--chain trial`, `--repeat 2`. The judge is GPT-OSS 120B on Cerebras (trial: 5 RPM, 1M uncached tokens/day; ≈ $0.003 per call); `--pause` is no longer needed with the client's pacing.
- **Prose-check evaluation (live):** `python -m scripts.eval_prose_qa --dry-run` first, then `python -m scripts.eval_prose_qa [--pause 30] [cases]`.
- **Try a new model:** put it alone in the `trial` chain, then `python -m scripts.try_chain trial [case ...] [--agents researcher document_builder qa]`.
- **Edit a chain in the dashboard:** Activate it, toggle models, re-Activate Default. A new chain: name box + **tick "Start empty"** + Create.
- **Re-check saved reports:** `python -m scripts.check_reports [folders]`.
- **Router facts (since 27 Oct; Mac only, standard library, read-only):** `python3 -m scripts.router_facts runs/eval_set/<run>` writes `<run>/router_facts.txt` and prints it: a) every router request in the sitting's window (folder name = Mac local start, to the newest log file, ±5 min) with its attempts, each matched to a case call or marked not matched (since 30 Oct, dba0e16: attempts carry `sent_at_ms`, so a call matches the router row that finished inside its send window, whatever the phase-log order; a router 429 "All models exhausted" tried no provider and is shown as "refused by the router (no row expected)"; runs from before 30 Oct 19:40 have no stamps and are matched best effort; the "Matching:" line says which); b) per-platform attempts, every Researcher/Builder call's served model and ordinal, validity per case (OpenRouter at ordinal 0); c) cooldowns set or expiring in the window; d) router state now (active cooldowns, 24 h counts and capacity per chain model, OpenRouter attempts since 00:00 UTC, OpenRouter timeouts in the window, Cerebras tokens and cost in 24 h); e) the chains. `python3 -m scripts.router_facts --now` prints d) and e) only. Both the guard and router_facts read through `scripts/router_db.py`: mode=ro, and an authorizer refuses `settings`/`api_keys` (problem 84).
- **Web UI (since 31 Oct, local only):** `python -m scripts.serve_ui` (needs the router; `--fake` runs the 6 samples offline with the fake LLM; `--port N`, default 8000), then open http://127.0.0.1:8000. It binds 127.0.0.1 only and runs one check at a time (a second gets 409; router down gets 503, nothing runs). Phases stream live (server-sent events). An uploaded `bom.csv` / `declaration.json` goes to a temporary folder deleted after the run, never to `runs/`. Each run is saved in `runs/ui/<YYYYmmdd-HHMMSS>_<sample or msg>/` like a pipeline run. **Ctrl+C stops the server within about 3 s and ends any check in progress** (a check otherwise keeps running after the page is closed and uses quota). If port 8000 is taken: `lsof -ti :8000 | xargs kill -9`. `router_facts` expects the eval_set layout, so for a UI run copy it as `/tmp/rf/<YYYYmmdd-HHMMSS>/<case>/` and run `TZ=Asia/Dubai python3 -m scripts.router_facts /tmp/rf/<stamp>`.
- **All offline tests in one go (21 since test_ui, 31 Oct):**
  `for t in check_data test_tariff_lookup test_rule_lookup test_origin_calculator test_duty_estimate test_coo_fee test_evidence test_researcher "test_intake --offline" test_document_builder test_llm_retry test_pipeline test_report_check test_qa_evidence test_qa test_prose_qa test_kb_shield test_pacing test_eval_set test_router_facts test_ui; do echo "=== $t ==="; python -m scripts.$t > /tmp/mansha_test.log 2>&1; echo "exit code: $?"; tail -1 /tmp/mansha_test.log; done`
  (`usage: … error: 'long'` lines and a "FAIL vague" line inside test output are expected: tests check that bad arguments are refused and that the runner reports a mismatch. Replays of saved runs in `test_researcher`/`test_kb_shield` print SKIP when the git-ignored `runs/` folders are absent. `test_llm_retry` passes only on the Mac: Claude's scratch copy uses a stand-in `openai` package.)
- Branches: `git switch -c <name>`, `git switch <name>`, `git push -u origin <name>`; merge with `git switch main && git merge --ff-only <name> && git push`.
- **Commit by file name, check `git status` first** (an unexpected untracked file would slip into a `git add -A`). No AI attribution lines in commits.
- **A repo file that refuses writes ("Permission denied") is read-only on the Mac** (`prompts/researcher.md` 23 Oct, `mansha/llm_client.py` 24 Oct): Claude saves the tested file as `<name>.new` with its hash; then `chmod 644 <file> && mv <file>.new <file>` and check the hash.
- End of a step: `git add <files>`, `git commit -m "…"`, `git push`, `git status`.
- Preview a report: `code <path>/report.md`, then ⌘⇧V.

## Repo: ~/Projects/mansha
```
.env, .env.example, .gitignore (runs/, graphify-out/, .wheels-linux/, .venv-linux/, .archify/, docs/architecture* ignored), requirements.txt
data/india/          # sources, tariff_lines, psr_rules, passages (.json)
samples/             # windows_qualifies/, chargers_repacked/, researcher_outputs/, builder_outputs/ (7.6), qa_replays/ (7.6g), eval/ (12 synthetic BOM folders, evaluation set)
mansha/
  llm_client.py      # CHAIN_LIMITS (long 16000/16000, qa 1000/1000, judge 3000/6000 since P1, 26 Oct); timeout 300 s; busy waits, cooldown waits, busy budget; RATE_LIMITS pacing of auto:judge 4/60 s (7.6k)
  prompts.py, intake.py, kb.py (CORRIDORS)
  evidence.py        # build_evidence() -> EvidencePack (+ corridor 7.6d, fixed_notes 7.6f); counts and percentages only
  researcher.py      # run_researcher(), check_researcher() and the code normalizations, in run order: normalize_gaps, unbracket_ids, move_note_gaps (7.6g), drop_user_data_gaps (7.6h), plain_check_names (7.6j), restore_qualified_notes (7.8), drop_hs_follow_ups (7.9), fill_authorities, fill_tariff_line, fill_fixed_notes (7.6f), drop_caveat_gaps; then drop_follow_ups / drop_claim_caveats (7.6c-d); strip_list_markers(), the claim-note rule
  qa_evidence.py     # qa_evidence(), research_for_qa(), checked_facts(): what QA reads (Step 7)
  qa.py              # run_qa(), plan_parts(), check_qa(), kb_shield(): the QA Evaluator (Step 7, plan B, KB shield 7.6g/i, OVERRULED)
  prose_qa.py        # review_prose(), check_prose_qa(): the Builder prose check (7.6)
  document_builder.py # 7.6b all_duty_gone(); 7.6e QUALIFIER_RE, is_mandatory(sid, text), MIN_LLM_NOTES; 7.6h saving_how()
  orchestrator.py    # run_pipeline() (qa=run_qa, prose_qa=review_prose), qa_passthrough(), render_phase_log()
  report_check.py    # check_report(): form checks on the finished report (flag only)
  tools/             # tariff_lookup, rule_lookup, origin_calculator, duty_estimate, coo_fee
prompts/             # shared_rules.md, intake.md, researcher.md, qa.md, document_builder.md, prose_qa.md (= agent_prompts.md, kept identical)
scripts/
  smoke_test, test_llm_client (live), check_data
  test_tariff_lookup, test_rule_lookup, test_origin_calculator, test_duty_estimate, test_coo_fee
  test_evidence, test_researcher, test_intake (--offline), test_document_builder, test_llm_retry,
  test_pipeline, test_report_check, test_qa_evidence, test_qa, test_prose_qa, test_kb_shield, test_pacing, test_eval_set, test_router_facts
  pipeline_cases.py, run_pipeline.py, try_chain.py, eval_qa.py, eval_prose_qa.py, check_reports.py
  eval_cases.py (25 cases + answer key), eval_set.py (dry run, budget guard, live runner, summary), eval_grade.py (grading, anchors)
runs/                # git-ignored
graphify-out/        # git-ignored code map, rebuilt by git hooks after every commit (see "Code map" below)
docs/                # step7_qa.md, runbook.md, lessons.md, pre_demo_retest.md, archive/ (history)
```
Archify output (`.archify/`, `docs/architecture*.{html,json}`, an architecture diagram drawn 19 Oct at d651902) is git-ignored since f47dbce (Haris, 25 Oct, option A): kept locally, never committed; regenerate a current diagram before the pitch and commit only that HTML, deliberately.

### Code map (Graphify, since 25 Oct)
- **Auto-refresh:** `graphify hook install` put post-commit, post-checkout, post-merge and post-rewrite hooks in `.git/hooks`; each rebuilds the **code layer** in the background (no LLM, no quota), log `~/.cache/graphify-rebuild.log`. Verified live 25 Oct: commit f47dbce → graph rebuilt at f47dbce (953 nodes, 2,295 links). Hooks live in `.git/` and are not pushed: a fresh clone needs `graphify hook install` again.
- **Session start:** `./scripts/graph_status.sh` (read-only): FRESH/STALE (graph commit vs HEAD), uncommitted files the graph doesn't reflect (read those directly), last rebuild line. Exit 0 fresh, 1 stale, 2 no graph. STALE → `tail -20 ~/.cache/graphify-rebuild.log`, then `GRAPHIFY_BACKEND=none graphify update .`.
- **Querying (offline, no LLM):** `graphify explain "run_pipeline"` (a node + its links, ~2K characters vs ~79K for orchestrator.py + researcher.py), `graphify path "run_pipeline" "tariff_lookup"`, `graphify query "…"` (keyword BFS; broad and noisy, prefer explain/path). Claude's Mac-side shell (Linux VM) has no graphify: install with `python3 -m venv ~/work/gvenv && ~/work/gvenv/bin/pip install graphifyy==0.9.95` (same version as the Mac), then run it from the repo with `GRAPHIFY_BACKEND=none`.
- **Limits:** the hooks refresh code only. The 25 doc nodes from `prompts/*.md` come from an LLM pass and are kept but not refreshed; after a prompt edit, `/graphify --update` in an assistant (uses LLM quota) or read the prompt file itself. ~12% of links are INFERRED: verify in the code. Prompt↔code links by ID string (e.g. "TOOL:tariff_lookup") are not drawn: use grep. The graph reflects the last commit only. `graphify-out/2026-10-25/` holds the 951-node graph of 25 Oct, not the older 633-node one.

Git (24 Oct, 17:45): `main` at **17612d6** (7.9), in sync with `origin/main`; no other branches. Step 7 commits: fc03c35 (7.2), 811fea5 (7.3), 248c5d0 (7.4), a697f5b + 784ff16 (plan B), 1d51e30 (7.6), 85ba0e2 (7.6b), d651902 (.gitignore), 6b63537 (7.6c–e), c97de08 (docs), bbbf77c (7.6f), c1151c7 (7.6g), 584afa5 (7.6h–j), 7140e2c (7.6k), 17d9d0b (7.8), 17612d6 (7.9). Identity Haris3477 with his existing commit email, no AI attribution (Claude commits with `git -c user.name=… -c user.email=…`, after asking). `gh` signed in on the Mac.

Router (dashboard at **localhost:5173** and `.env`, not in git; details in llm_backend_setup.md). Chains since 23 Oct: `long` = Gemini 3.5 Flash, Gemini 3.6 Flash, Gemini 3.7 Flash, Dots3 Note Preview (OpenRouter free: RPM 20, **RPD 50**); `qa` = GPT-OSS 120B (Groq), Gemini 3.7 Flash (Intake); **`judge` = GPT-OSS 120B (Cerebras) only** (trial credit; RPM 5, RPD 2400, TPM 30000, TPD 1000000); `trial` = Cerebras only; Default chain active; global strategy `smartest`. GPT-OSS 120B (Groq) TPD override 400,000 since 18 Oct (problem 70). `PROVIDER_TIMEOUT_OPENROUTER=150000`. Router cooldown ladder (`ratelimit.ts`): 2 min after the 1st limit hit in 24 h, 10 min after the 2nd, … a day from the 4th (problem 80). Query the router DB read-only (`mode=ro`) and only the columns needed (23 Oct: a broad `settings` query printed the router key).

### Files
- `mansha/orchestrator.py`, `mansha/report_check.py`, `mansha/kb.py`, `mansha/intake.py`, `mansha/researcher.py`, `mansha/document_builder.py`, `mansha/tools/duty_estimate.py`.
- `scripts/pipeline_cases.py`, `scripts/run_pipeline.py`, `scripts/check_reports.py`, `scripts/try_chain.py`.
- Saved per run: `message.txt`, `intake.json`, `evidence.txt`, `researcher_N.json`, `qa_N.json`, `builder.json`, `prose_qa_N.json`, `report.md` or `notice.md`, `phase_log.json`, `phase_log.md`.

### `mansha/document_builder.py`
- `run_document_builder(research, intake, id_sources, *, corridor="india", llm=call_llm, review=None) -> BuilderResult(...)`. Chain `auto:long`. Always returns a report.
- `build_facts`, `build_notes`, `is_mandatory`, `max_llm_notes`, `check_prose`, `fallback_prose`, `render_report`, `still_needed`, `cite`, `chosen_line`. The claim-note rule is imported from `mansha/researcher.py` (7.6d). Prompt `prompts/document_builder.md`. Test `scripts/test_document_builder.py` (7.6e section "qualifier rule (problem 78)"; the prose-check sections use windows + one plain cumulation note, because the real windows answer has no optional note left).

### LLM client changes in Step 8
- 8.6: wait before the retry when the router is busy (502/503/504 → 30 s; cap 90 s). 8.6b: router cooldown replies waited out without using the retry, at most 2 per call. Test `scripts/test_llm_retry.py`.

## Step 3 as built (14 Oct 2026)
- `prompts/shared_rules.md` + `prompts/intake.md`; `mansha/prompts.py` (`load_prompt`, `build_system_prompt`).
- `mansha/intake.py`: `run_intake(message, *, llm=call_llm) -> IntakeResult(data, changes, llm)`, `.blocking_missing`; `normalize(raw, message)` pure code. `scripts/test_intake.py` (`--offline`).

### Knowledge base (`data/india/`; `mansha/kb.py` `load_corridor()` cached, read-only; `KBError`)
- `sources.json` (21 keys; several non-government hosts, G21); `tariff_lines.json` (metadata, `heading_exclusions` 3923/3924/3925/3303, 14 lines, all preferential lines Table I; all 12 CEPA rates confirmed on the official 09/2026, G22; metadata `open_risks` stale since 17 Oct); `psr_rules.json` (3 general rules, 9 chapter rules: 19, 32, 33, 39, 73, 76, 84, 85, 94); `passages.json` (16 `P-...`: title, kind, actor, tags, source_keys, provision, quotes, items, summary, params, notes, `dev_notes`; kinds used by the 7.6d claim rule: duty, procedure, authority); `kb.validate()`.

### Tools (`mansha/tools/`, pure Python)
- `tariff_lookup`, `rule_lookup`, `calculate_origin` / `origin_from_folder`, `duty_estimate` (+ `reduces_bcd_only`), `certificate_fee`.
- Samples: `samples/windows_qualifies/` (MEETS, VA 49% ≥ 45%), `samples/chargers_repacked/` (FAILS on all four checks), `samples/researcher_outputs/` (Builder, pipeline and QA fixtures), `samples/builder_outputs/` (prose-check fixtures, migrated to 7.6e numbering on 19 Oct, each change in its `edits`), `samples/qa_replays/` (23 Oct live QA corrections, 7.6g).

### Research and history docs
- Project: `claude/cepa_india_fact_base.md` (source of truth for facts), `claude/roadmap.md` (updated 20 Oct: positioning option A, milestones renumbered), `claude/llm_backend_setup.md`, `agent_prompts.md`, `claude/CURRENT_STATE.md`.
- Repo `docs/archive/` (moved 20 Oct): `research_paid_models_data_checks.md` (paid models, data checks, browser to-do list), `browser_checks_2026-10-17.md`, `evaluation_set_design.md` (the approved evaluation-set design), `progress_2026-10-20.md`, `project_instructions_2026-10-20.md`; index in `ARCHIVE_INDEX.md`.

### 9.5 / 9.6e fixes (summary)
- Researcher hard check: no evidence IDs and no "intake" in exporter-visible text; `fill_tariff_line()`; `drop_caveat_gaps()` (52).
- KB notes rewritten as exporter facts; team to-dos in `dev_notes`.
- Origin calculator: failed minimal operations named with Art. 3.5.1 wording.
- Evidence totals in words, counts and percentages only.
- Duty tool "BCD only" note only for Table I lines; Builder drops claim notes by source when no CEPA rate applies; TERMS `CEPA_BCD` (53).
- LLM client: busy budget; `auto:long` 16000.
- Router (not in git): Nemotron off in `long` and `qa`; `PROVIDER_TIMEOUT_OPENROUTER=150000`.
