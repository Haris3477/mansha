# Mansha — working rules for Claude Code sessions (cloud or local)

## Start of every session
1. This repo is the code; the project's source-of-truth docs (CURRENT_STATE, agent_prompts, roadmap, llm_backend_setup, cepa_india_fact_base) live in Haris's claude.ai Project and are NOT in this repo. Each task comes with a brief in `docs/cloud/<task>.md`: read this file, then that brief, then only the repo docs the brief names. If missing context could affect correctness, stop and ask Haris; never guess.
2. Saved runs: `runs/` is git-ignored. When a task needs saved runs (reading reports, replays, re-grading), extract the snapshot branch into the ignored folder:
   `git fetch origin runs-snapshot && rm -rf runs && git archive origin/runs-snapshot runs | tar -x`
   Never commit `runs/` to any branch except `runs-snapshot` (Haris maintains that branch).
3. Code map: `python3 -m venv ~/gvenv && ~/gvenv/bin/pip install graphifyy==0.9.95 && GRAPHIFY_BACKEND=none ~/gvenv/bin/graphify update .` (no LLM). Before reading whole files use `graphify explain "<symbol>"` / `graphify path "A" "B"`, then read only the lines needed. Prompt files and uncommitted files: read directly. Verify INFERRED links in the code; prompt↔code links by ID string (e.g. "TOOL:tariff_lookup") are not drawn: use grep.

## What a cloud session can and cannot do
- CAN: design on paper, edit code, run the offline tests (`pip install -r requirements.txt` first), re-grade and replay saved runs, read reports and phase logs, read live sittings in full (reports, phase logs, `router_facts.txt`) and write the reading, update repo docs.
- CANNOT: live pipeline runs or router checks (the router is on Haris's Mac at localhost:3001). Those run from a 🖥️ terminal block on the Mac (below). Never try to reach the router, never expose it, never ask for keys.
- The Mac chat (claude.ai, bills Haris's plan) is NOT used for routine sittings: live runs are a 🖥️ terminal block, the reading is done here. The Mac chat is only for 💾 SAVE PROGRESS and the four ➡️ cases below.
- Never open, create or read any `.env`. Keys are never in the repo or the chat.

## North Star
A finished, pitch-ready Mansha (roadmap.md's pitch-ready bar). "Next steps" and suggestions in docs are ideas, not a fixed checklist. At each step, check whether the suggested task is still the best move given the goal, the project's actual state and what we've learned. Do it, adapt it, or propose a better path, with reasons. Direction changes are Haris's call. A dropped or postponed step is recorded with its reason. Each fix is an experiment: say what it should change and how we'll know, judge it by the result, switch approach if it doesn't work.

## How to work with Haris
- Haris is a CS graduate aiming to become an AI engineer; this is a hackathon build and a learning exercise.
- STEP BY STEP: one step per reply, then stop and wait for "done" or questions.
- New concept (RAG, embeddings, structured outputs, tool use, agent orchestration, evaluation): a short plain-language explanation before the change.
- If a request is a bad idea or there's a better approach, say so directly.
- Keep a running checklist at the top of longer replies. Keep narration short.

## Every change
1. Explain what, why and how in simple terms with a small example; give options and a recommendation with reasons.
2. WAIT for Haris's explicit yes (or chosen option). Never change anything before that.
3. Edit files in place; never retype a file from earlier tool output.
4. Run the offline tests (command below). Read actual outputs, not just OK/FAIL. If the change touches the pipeline, say so: the live run happens on Haris's Mac afterwards.
5. Summarize results and review the change: what changed, what it should improve, how we know, risks or gaps.
6. Commit and push (Haris, 28 Oct): his yes to an option is also the yes to commit and push that change once its offline tests pass; don't ask again. Commit on this session's own branch, never push to `main`; Haris reviews and merges. Show the commit hash and message in the reply. **No AI attribution in commit messages (no co-author lines).**
7. A hook (e.g. the cloud stop hook) is never a yes by itself: work Haris hasn't approved yet stays uncommitted; tell him what the hook asked. The stop hook fires whenever a reply ends with uncommitted, untracked or unpushed work, so expect it while a proposal waits for his answer.
8. At the end of every step, ask Haris what the next step should be, with options and a recommendation (with reasons).

## Live sittings and the Mac (Haris, 27 Oct 20:08)
**🖥️ RUN ON YOUR MAC (TERMINAL):** when a step needs a live sitting (work committed and pushed first, rule 6), end the reply with one block Haris pastes into his VS Code terminal (not the Mac chat). It runs inside `( … )` so a STOP ends the block, not his shell. `eval_set` exits 1 when a run fails a code check (those runs still get router facts and the snapshot) and 2 when the guard refused (nothing ran). Template:
```
(
set -e
cd ~/Projects/mansha && git fetch origin && git checkout <branch> && git pull --ff-only
test "$(git rev-parse --short HEAD)" = "<hash>" || { echo "STOP: expected <hash>"; exit 1; }
test "$(grep -c '^PROVIDER_TIMEOUT_OPENROUTER=210000$' ~/Projects/freellmapi/.env)" = 1 || { echo "STOP: router timeout is not 210000"; exit 1; }
code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/v1/models || true); case "$code" in 200|401) echo "router answering ($code)";; *) echo "STOP: router not answering ($code). Start it: cd ~/Projects/freellmapi && npm run dev"; exit 1;; esac
source .venv/bin/activate
python3 -m scripts.router_facts --now
rc=0; python -m scripts.eval_set --case <A> --case <B> || rc=$?
[ "$rc" != 2 ] || { echo "STOP: budget guard refused (nothing ran)"; exit 1; }
RUN=$(ls -t runs/eval_set | head -1)
python3 -m scripts.router_facts runs/eval_set/$RUN
cd ~/Projects/mansha-runs && rsync -a ~/Projects/mansha/runs/eval_set/$RUN runs/eval_set/ && git add runs/eval_set/$RUN && git commit -m "Runs snapshot $RUN (<cases>, <hash>)" && git push origin runs-snapshot && git ls-remote origin runs-snapshot
)
```
Never `--force`. Size the sitting to the cases the change can affect (k = 1 unless a repeat is the point). Say what to paste back if it stops (the STOP line, or the last 30 lines); if Haris pastes the `--now` output first, size the sitting from it. When Haris says "pushed", fetch `runs-snapshot` and do the full reading (below).

**💾 SAVE PROGRESS IN MAC CHAT:** at the end of every closed step or task: which handoff file on main to read (ask Haris to merge and pull first), what changed, and which Project docs to update: the CURRENT_STATE live addendum; the agent_prompts addendum if a prompt changed (old → new); the llm_backend_setup addendum if the backend changed; the fact-base addendum if a KB fact moved.

**➡️ MOVE TO MAC CHAT:** only for what the cloud can't do: (a) a live look at the Mac (router source, the router DB beyond `router_facts.txt`, router logs, why a run failed on the Mac); (b) a router, dashboard or `.env` change Haris must make, confirmed in the DB afterwards; (c) a terminal block that fails in a way the pasted error can't explain; (d) any Project doc read or write. Say which of (a)–(d), what to check and what to bring back. Its first line names the branch and commit; if the Mac needs the branch, give the terminal block's git line first. Long details go into a `docs/cloud/` brief first, committed (rule 6) and referenced by path and commit, so the block stays short.

## Reading a sitting
On "pushed": `git fetch origin runs-snapshot` and extract (Start of every session, step 2). First sweep anchors, labels, serving models and seconds with one script, against `router_facts.txt`; then read every report.md and phase_log in full (no shortcut). Write `docs/cloud/readings/<run>_reading.md`: validity per run (every Researcher/Builder call on the expected model at ordinal 0, from `router_facts.txt`; an unmatched call is "unknown", never "valid"); serving-model table with seconds; targets table; QA statuses and every rejection/overrule with why (corrections checked against the KB records); must-say / must-not-say per case marked from reading; slip counts; G17 streak. Standard: the reading.md of 180618, 183851, 191029. A **⬅️ BACK TO CLOUD** block from the Mac chat is handled the same way: extract, then read the files it names first.

## Router facts
`scripts/router_facts.py` (on `scripts/router_db.py`) runs on the Mac only. The router DB is opened read-only and an authorizer refuses `settings` and `api_keys` (problem 84). Select named columns only; never add a query on those two tables; never open any `.env` in a script or command (the terminal block's count-only `grep -c` is the one exception). The cloud never reaches the router or its DB: it reads `router_facts.txt` from the snapshot.

## Cloud credit (Haris, 27 Oct 20:58)
About $50 left; expires 5 Nov 11:59 Dubai. Quality first, no check skipped. Within that: graphify before whole files; no re-reads; the suite once per change plus once before a live handover; sittings sized to the change; a sweep script before the full read; short replies; 🔄 at ~40 % context; say small / medium / large before each step. If credit runs low: stop at a clean point, write the handoff; the Mac chat takes over again.

## Handoff back
At the end of a task, write `docs/cloud/handoff_<YYYY-MM-DD>_<task>.md`: decisions Haris made (with his reasons), results, new or changed problems/gaps, commits, and what's next. Haris's chat uses it for "save progress" in the Project. Keep it factual: what Haris said vs what Claude recommended.

At the end of each task, or when context passes ~40%, write/update the handoff file, commit and push it (rule 6: no separate yes), and end the reply with a block headed **🔄 START A NEW SESSION**. A "task" here is a whole piece of work with its own goal (e.g. the G17 decision, the repeats, a pipeline fix), not a step inside it: a repeat sitting or one fix round continues in the same session (update the handoff, no new-session block). The block contains the exact `claude --cloud "…"` command for the next task: the quoted text tells the new session to read CLAUDE.md, then the named `docs/cloud/` handoff or brief, names the branch to work on and the step to do. If a 🖥️ block, 💾 SAVE PROGRESS or ➡️ block is also due, it comes first, and 🔄 START A NEW SESSION last. Example:
```
claude --cloud "Read CLAUDE.md, then docs/cloud/handoff_2026-10-25_g17.md and docs/cloud/<next>_brief.md. Work on branch <branch>. Do its step 1 only."
```

## What we're building
Mansha (Arabic منشأ, "origin") tells a UAE exporter whether a product qualifies for reduced or zero customs duty under a UAE CEPA, proves it with the agreement's own rules, and lists the steps to claim it. First corridor: UAE → India. Targets: the Create AI Agents Championship (Best Business AI Agent, Dubai Chamber of Digital Economy) and a December 2026 hackathon.

Four agents, each a separate LLM call orchestrated in Python (`mansha/orchestrator.py`): Intake (JSON fields), Researcher (only retrieved official passages and tool results; every item cites a source; unsupported → REGULATORY_GAP_DETECTED), QA Evaluator (0/1 on Factuality, Completeness, Formatting Safety; code sets STATUS; one revision loop shared with the code checks; 3b: Builder prose check), Document Builder (Markdown report with checklist, sources, "verify with the authority" disclaimer). Deterministic tools (no LLM) between Intake and Researcher: tariff lookup, rule lookup, origin calculator, duty estimate, certificate fee. LLMs never do arithmetic. Every phase's log is shown. Responses match the user's language (Arabic or English).

## Domain rules
- Never invent HS codes, tariff rates, rules of origin, article numbers, fees or timelines. If unsure, say so.
- Official sources only for the knowledge base. Research before declaring a gap; never fill a gap with a guess.
- Confidential business data (input costs, supplier names) is read only by code and never sent to the LLMs. Use public trade information and synthetic company data only.

## More working rules
- Fix problems before moving on, unless they truly belong to a later milestone (then: gaps register with a plan and a test).
- Never call a step passed when its bar isn't met; never reword a result to make it pass.
- Working rule 7: no pipeline change while the evaluation-set repeats are running (grader-only changes are allowed with Haris's yes).
- `prompts/*.md` must stay identical to agent_prompts.md in the Project: if a prompt changes, say so in the handoff so Haris's chat updates the Project.
- Model chains: Intake `auto:qa`; QA and prose check `auto:judge`; Researcher and Builder `auto:long`. Never plain `auto`. Every agent call logs the serving model (x-routed-via). Validate every JSON response.
- Priority: simple end to end first, then accuracy, then demo polish.
- When Haris pastes an error, explain the cause before the fix.

## Offline tests (all 20)
```
for t in check_data test_tariff_lookup test_rule_lookup test_origin_calculator test_duty_estimate test_coo_fee test_evidence test_researcher "test_intake --offline" test_document_builder test_llm_retry test_pipeline test_report_check test_qa_evidence test_qa test_prose_qa test_kb_shield test_pacing test_eval_set test_router_facts; do echo "=== $t ==="; python -m scripts.$t > /tmp/mansha_test.log 2>&1; echo "exit code: $?"; tail -1 /tmp/mansha_test.log; done
```
(`usage: … error: 'long'` lines and a "FAIL vague" line inside test output are expected.) Details: `docs/runbook.md`.

## Prompt refinement shortcut
When Haris's message starts with "pm:", turn it into a refined prompt for Claude in this session, show only the prompt in a copyable block and STOP. Execute only after "go"/"yes" (or "go" plus edits).
