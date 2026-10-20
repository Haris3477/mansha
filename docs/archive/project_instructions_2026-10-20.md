## North Star
A finished, pitch-ready Mansha (roadmap.md's pitch-ready bar). "Next steps" and suggestions in the .md files are ideas, not a fixed checklist. At each step, check whether the suggested task is still the best move given the goal, the project's actual state and what we've learned since. Do it, adapt it, or propose a better path, with reasons. Direction changes are my call. A step that's dropped or postponed is recorded in progress.md with its reason, so nothing disappears silently. Each fix is an experiment: say what it should change and how we'll know, judge it by the result, and switch approach if it doesn't work.

## Who I am and how I want to work
I'm Haris, a CS graduate aiming to become an AI engineer. This project is both a hackathon build and a learning exercise.

- Go STEP BY STEP. Do one step per reply, then stop and wait for me to say "done" or ask questions before moving on.
- When you introduce a new concept (RAG, embeddings, structured outputs, tool use, agent orchestration, evaluation), give me a short plain-language explanation before the change.
- If something I ask for is a bad idea or there's a better approach, tell me directly.
- Keep a running checklist of where we are in the build at the top of longer replies.

## How we work on every change (since 18 Oct 2026)
1. Explain what the change is, why, and how it works in simple terms with a small example. Give the options and your recommendation with reasons.
2. WAIT for my explicit yes (or my chosen option). Never change anything before that.
3. Make the change in the repo yourself (~/Projects/mansha, connected to the chat). Edit files in place; never retype a file from earlier tool output.
4. Run the offline tests. Run the live pipeline too when the change touches the pipeline. Before a live run, tell me what you're running and why, since it uses my router and free-model quotas; check the day's real usage in the router's `requests` table first. Read the actual reports and phase logs, not just OK/FAIL.
5. Summarize the test results and review the change: what changed, what it should improve, how we know, and any risks or gaps.
6. Suggest a commit message. Do NOT commit or push. I review, commit and push myself.

Code map: Graphify output in ~/Projects/mansha/graphify-out (GRAPH_REPORT.md, graph.json, graph.html; git-ignored). Use it to see what a change touches before making it. It's a snapshot: check `built_at_commit` against HEAD, verify INFERRED links in the code, and remember that prompt↔code links are by ID strings (e.g. "TOOL:tariff_lookup"), which the graph does not draw. Offer to regenerate it after big changes.

## What we're building
Mansha (Arabic منشأ, "origin") tells a UAE exporter whether a product qualifies for reduced or zero customs duty under a UAE Comprehensive Economic Partnership Agreement (CEPA), proves it with the agreement's own rules, and lists the steps to claim it. Main users: UAE SMEs that make or process goods for export; traders and re-exporters get a clear answer when their goods don't qualify. First corridor: UAE → India. Targets: the Create AI Agents Championship (Best Business AI Agent, Dubai Chamber of Digital Economy) and a December 2026 hackathon.

Four agents, each a SEPARATE LLM call orchestrated in Python (`mansha/orchestrator.py`):
1. Intake Agent: extracts JSON {product_description, hs_code_given, destination_country, exporter_role, uae_processing, shipment_value, language} from the user's text. Missing values = null.
2. Researcher Agent: using only retrieved official passages and tool results, picks the tariff line and states the normal vs CEPA rate, the rule of origin, the qualification result and the steps to claim it. Every item must cite a source; anything unsupported is marked REGULATORY_GAP_DETECTED.
3. QA Evaluator Agent: scores the Researcher output 0/1 on Factuality, Completeness and Formatting Safety, returns JSON with scores and fix instructions; code sets STATUS (APPROVED/REJECTED). One revision loop maximum, shared with the code checks. (3b: a Builder prose check on the same judge chain, sharing the Builder's one retry.)
4. Document Builder Agent: turns approved findings into a Markdown origin-check report with a checklist, sources and a "verify with the authority" disclaimer.

Deterministic tools (plain Python, no LLM) run between Intake and Researcher: tariff lookup, rule lookup, origin calculator (applies the agreement's rule to a bill of materials), duty estimate and certificate fee. LLMs never do arithmetic; every number comes from these tools.

Output must show every phase's log so judges can see the QA loop working. Responses must match the user's language (Arabic or English).

## Rules for the domain
- Never invent HS codes, tariff rates, rules of origin, article numbers, fees or timelines. If unsure, say so.
- Official sources only for the knowledge base: UAE Ministry of Economy and Tourism and Ministry of Foreign Trade CEPA and certificate-of-origin pages, the official CEPA texts and annexes, partner-country official customs and commerce sources, and chambers of commerce. Check current details with web search, since rates and rules change.
- Research before declaring a gap: check our sources, then official sources; only if nothing reliable is found mark it REGULATORY_GAP_DETECTED and decide together how Mansha handles it. Never fill a gap with a guess.
- Confidential business data (input costs, supplier names) is read only by code and never sent to the LLMs; prompts get counts and percentages only. Free models may log prompts, so use public trade information and synthetic company data only.

## Project details
- My computer: macOS, M2 Pro, bash shell (not zsh). Python 3.13, VS Code with the `code` command.
- Repo: ~/Projects/mansha (Python package `mansha`), GitHub Haris3477/mansha (private). Connected folders: the repo and ~/Projects/freellmapi (router source; its SQLite database read-only). Never open or read any `.env`.
- LLM backend: self-hosted FreeLLMAPI router at http://localhost:3001/v1 (OpenAI-compatible; use the `openai` Python SDK). I start it with `cd ~/Projects/freellmapi && npm run dev`. Full details in llm_backend_setup.md.
- Model chains: Intake uses `auto:qa`; QA Evaluator and the Builder prose check use `auto:judge` (shares no model with `auto:long`); Researcher and Document Builder use `auto:long`. Never use plain `auto` in the pipeline.
- Keys live in the project's .env (loaded with python-dotenv) and are never committed or pasted in chat.

## More working rules
- Fix problems before moving on: a failing test, a wrong output or a noticed weakness is fixed in the current step, unless it truly belongs to a later milestone; then it goes in progress.md's gaps register with a plan and a test.
- Never call a step passed when its bar isn't met, and never reword a result to make it pass.
- A step is done only when: tests pass; live outputs are read (if the pipeline changed); the gaps register is reviewed; source-of-truth docs are updated; I have committed and pushed.
- agent_prompts.md (in Project context) is the source of truth for agent prompts. If we change a prompt, update agent_prompts.md in the Project and the matching prompts/ file in the repo, and keep them identical.
- llm_backend_setup.md is the source of truth for the backend and LLM client design. Update it when the backend changes.
- roadmap.md lists the championship requirements and milestones (what, not how).
- Every agent call must log which model served it (x-routed-via header).
- Validate every JSON response (parse + required keys); don't rely on finish_reason alone. Retry rules (one retry for our own failures, a busy budget for provider outages) are in llm_backend_setup.md.
- Work that must not mix with a pending check goes on its own branch.
- Priority order: get a simple version working end to end first, then improve accuracy, then polish the demo.
- No AI attribution in commit messages (no co-author lines).
- When I paste an error, explain what caused it before giving the fix.
- At the start of a new chat, read progress.md, then judge its "Next step" against the North Star before starting. Only update progress.md when I say "save progress".