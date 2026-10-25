# Mansha — working rules for Claude Code sessions (cloud or local)

## Start of every session
1. This repo is the code; the project's source-of-truth docs (CURRENT_STATE, agent_prompts, roadmap, llm_backend_setup, cepa_india_fact_base) live in Haris's claude.ai Project and are NOT in this repo. Each task comes with a brief in `docs/cloud/<task>.md`: read this file, then that brief, then only the repo docs the brief names. If missing context could affect correctness, stop and ask Haris; never guess.
2. Saved runs: `runs/` is git-ignored. When a task needs saved runs (reading reports, replays, re-grading), extract the snapshot branch into the ignored folder:
   `git fetch origin runs-snapshot && rm -rf runs && git archive origin/runs-snapshot runs | tar -x`
   Never commit `runs/` to any branch except `runs-snapshot` (Haris maintains that branch).
3. Code map: `python3 -m venv ~/gvenv && ~/gvenv/bin/pip install graphifyy==0.9.95 && GRAPHIFY_BACKEND=none ~/gvenv/bin/graphify update .` (no LLM). Before reading whole files use `graphify explain "<symbol>"` / `graphify path "A" "B"`, then read only the lines needed. Prompt files and uncommitted files: read directly. Verify INFERRED links in the code; prompt↔code links by ID string (e.g. "TOOL:tariff_lookup") are not drawn: use grep.

## What a cloud session can and cannot do
- CAN: design on paper, edit code, run the offline tests (`pip install -r requirements.txt` first), re-grade and replay saved runs, read reports and phase logs, update repo docs.
- CANNOT: live pipeline runs or router checks (the router is on Haris's Mac at localhost:3001). Those happen in Haris's claude.ai chat. Never try to reach the router, never expose it, never ask for keys.
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
6. Suggest a commit message, ask before committing, commit on this session's own branch, never push to `main`. Haris reviews and merges. **No AI attribution in commit messages (no co-author lines).**
7. If a hook (e.g. the cloud stop hook) asks you to commit or push, don't: tell Haris what it asked and wait for his yes. The cloud stop hook fires whenever a reply ends with uncommitted, untracked or unpushed work, so expect it while waiting for a yes.

## Handover to the Mac chat
Whenever the next step needs Haris's Mac (live run, router or quota check, budget guard, refreshing `runs-snapshot`), stop and end the reply with a block headed **➡️ MOVE TO MAC CHAT**: a ready-to-paste message with what to run (exact cases and commands), what to check first in the router, which `docs/cloud/` file to read, and what to report back. Long details go into a `docs/cloud/` brief first, committed (after Haris's yes) and referenced by path and commit, so the block stays short.

## Coming back from the Mac chat
When Haris pastes a **⬅️ BACK TO CLOUD** block, first extract runs from `runs-snapshot` (Start of every session, step 2), then read the files the block names before anything else.

## Handoff back
At the end of a task, write `docs/cloud/handoff_<YYYY-MM-DD>_<task>.md`: decisions Haris made (with his reasons), results, new or changed problems/gaps, commits, and what's next. Haris's chat uses it for "save progress" in the Project. Keep it factual: what Haris said vs what Claude recommended.

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

## Offline tests (all 19)
```
for t in check_data test_tariff_lookup test_rule_lookup test_origin_calculator test_duty_estimate test_coo_fee test_evidence test_researcher "test_intake --offline" test_document_builder test_llm_retry test_pipeline test_report_check test_qa_evidence test_qa test_prose_qa test_kb_shield test_pacing test_eval_set; do echo "=== $t ==="; python -m scripts.$t > /tmp/mansha_test.log 2>&1; echo "exit code: $?"; tail -1 /tmp/mansha_test.log; done
```
(`usage: … error: 'long'` lines and a "FAIL vague" line inside test output are expected.) Details: `docs/runbook.md`.

## Prompt refinement shortcut
When Haris's message starts with "pm:", turn it into a refined prompt for Claude in this session, show only the prompt in a copyable block and STOP. Execute only after "go"/"yes" (or "go" plus edits).
