# Mansha — working rules for Claude (Mac chat)

## Start of every session
1. This repo is the code. The source-of-truth docs (CURRENT_STATE and its addenda, agent_prompts, roadmap, llm_backend_setup, cepa_india_fact_base) live in Haris's claude.ai Project, not in this repo. Read the newest CURRENT_STATE addendum first, then judge its "Next" list against the North Star before starting. If missing context could affect correctness, stop and ask Haris; never guess.
2. Run `./scripts/graph_status.sh` (expect FRESH; if STALE, read `~/.cache/graphify-rebuild.log` on the Mac and explain before fixing).
3. Code map: Claude's shell installs graphify once per session: `python3 -m venv ~/work/gvenv && ~/work/gvenv/bin/pip install graphifyy==0.9.95`, then run it from the repo with `GRAPHIFY_BACKEND=none`. Before reading whole files use `graphify explain "<symbol>"` / `graphify path "A" "B"`, then read only the lines needed. Prompt files and uncommitted files: read directly. Verify INFERRED links in the code; prompt↔code links by ID string (e.g. "TOOL:tariff_lookup") are not drawn: use grep.
4. Saved runs are in the repo's git-ignored `runs/` folder on the Mac; read them there. Never commit `runs/`. The `runs-snapshot` branch is an archive of the cloud period (last 414c894) and is no longer updated.

## What Claude's shell can and cannot do
- Claude's shell is a Linux VM on Haris's Mac with two connected folders: this repo (`~/mnt/mansha`) and the router source (`~/mnt/freellmapi`, its SQLite database read-only).
- CAN: design on paper, edit code, run the offline tests (venv outside the repo), re-grade and replay saved runs, read reports and phase logs, run `router_facts` against the database, write readings, update repo docs, read and write the Project docs.
- CANNOT: reach the router (`localhost:3001` on the Mac is not reachable from the VM), so live sittings run from a terminal block Haris pastes (below). Never try to expose the router, never ask for keys.
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
4. Run the offline tests (command below). Read actual outputs, not just OK/FAIL. If the change touches the pipeline, a live sitting follows (next section).
5. Summarize results and review the change: what changed, what it should improve, how we know, risks or gaps.
6. Suggest a commit message. Do NOT commit or push: Haris reviews, commits and pushes. **No AI attribution in commit messages (no co-author lines).** Work happens on `main`, except work that must not mix with a pending check, which goes on its own branch.
7. At the end of every step, ask Haris what the next step should be, with options and a recommendation (with reasons).

## Live sittings
Before a live run, say what will run and why (it uses Haris's router and free-model quotas), and check the day's real usage first with router_facts (below). Size the sitting to the cases the change can affect (k = 1 unless a repeat is the point). Haris pastes one block into his VS Code terminal; it runs inside `( … )` so a STOP ends the block, not his shell. `eval_set` exits 1 when a run fails a code check and 2 when the budget guard refused (nothing ran). Template:
```
(
set -e
cd ~/Projects/mansha
test "$(git rev-parse --short HEAD)" = "<hash>" || { echo "STOP: expected <hash>"; exit 1; }
test "$(grep -c '^PROVIDER_TIMEOUT_OPENROUTER=210000$' ~/Projects/freellmapi/.env)" = 1 || { echo "STOP: router timeout is not 210000"; exit 1; }
code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/v1/models || true); case "$code" in 200|401) echo "router answering ($code)";; *) echo "STOP: router not answering ($code). Start it: cd ~/Projects/freellmapi && npm run dev"; exit 1;; esac
source .venv/bin/activate
python3 -m scripts.router_facts --now
rc=0; python -m scripts.eval_set --case <A> --case <B> || rc=$?
[ "$rc" != 2 ] || { echo "STOP: budget guard refused (nothing ran)"; exit 1; }
RUN=$(ls -t runs/eval_set | head -1)
python3 -m scripts.router_facts runs/eval_set/$RUN
echo "DONE: $RUN"
)
```
Uncommitted work can be run live when Haris agrees (then drop the hash check and say so). Say what to paste back if it stops (the STOP line, or the last 30 lines). When Haris says "done", read `runs/eval_set/<run>` directly and do the full reading (below).

## Reading a sitting
First sweep anchors, labels, serving models and seconds with one script, against the run's `router_facts.txt`; then read every report.md and phase_log in full (no shortcut). Write `docs/readings/<run>_reading.md`: validity per run (every Researcher/Builder call on the expected model at ordinal 0, from `router_facts.txt`; an unmatched call is "unknown", never "valid"); serving-model table with seconds; targets table; QA statuses and every rejection/overrule with why (corrections checked against the KB records); must-say / must-not-say per case marked from reading; slip counts; G17 streak. Standard: the reading.md of 180618, 183851, 191029. Older readings and briefs stay in `docs/cloud/` as the record.

## Router facts
`scripts/router_facts.py` (on `scripts/router_db.py`) opens the router DB read-only, and an authorizer refuses `settings` and `api_keys` (problem 84). Select named columns only; never add a query on those two tables; never open any `.env` in a script or command (the terminal block's count-only `grep -c` is the one exception). From Claude's shell: `python -m scripts.router_facts --now --db ~/mnt/freellmapi/server/data/freeapi.db` (the default path is the Mac's home).

## Save progress
Only when Haris says "save progress": write the Project docs directly. A new CURRENT_STATE live addendum (decisions Haris made with his reasons, results, new or changed problems/gaps, commits, what's next; what Haris said vs what Claude recommended), plus the agent_prompts addendum if a prompt changed (old → new), the llm_backend_setup addendum if the backend changed, and the fact-base addendum if a KB fact moved.

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
- `prompts/*.md` must stay identical to agent_prompts.md in the Project: if a prompt changes, update the Project's agent_prompts (addendum) and the `prompts/` file in the same step.
- Model chains: Intake `auto:qa`; QA and prose check `auto:judge`; Researcher and Builder `auto:long`, except Arabic Builder calls: `auto:arabic` (Gemini only); if it fails, the code-only report, no LLM backup (F1, Haris, 30 Oct; B 28 Oct; the router's model order is global, so the backup can't live inside a chain). Never plain `auto`. Every agent call logs the serving model (x-routed-via). Validate every JSON response.
- Priority: simple end to end first, then accuracy, then demo polish.
- When Haris pastes an error, explain the cause before the fix.

## Offline tests (all 20)
```
for t in check_data test_tariff_lookup test_rule_lookup test_origin_calculator test_duty_estimate test_coo_fee test_evidence test_researcher "test_intake --offline" test_document_builder test_llm_retry test_pipeline test_report_check test_qa_evidence test_qa test_prose_qa test_kb_shield test_pacing test_eval_set test_router_facts; do echo "=== $t ==="; python -m scripts.$t > /tmp/mansha_test.log 2>&1; echo "exit code: $?"; tail -1 /tmp/mansha_test.log; done
```
(`usage: … error: 'long'` lines and a "FAIL vague" line inside test output are expected.) Details: `docs/runbook.md`. Claude's shell runs them with a venv outside the repo (`~/work/venv/bin/python`, `PYTHONDONTWRITEBYTECODE=1`).

## Prompt refinement shortcut
When Haris's message starts with "pm:", turn it into a refined prompt for Claude in this session, show only the prompt in a copyable block and STOP. Execute only after "go"/"yes" (or "go" plus edits).
