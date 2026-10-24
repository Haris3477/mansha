# Mansha — working lessons

_Moved verbatim from progress.md (20 Oct 03:05 save) on 20 Oct 2026. Read before debugging the router, writing a new check, or planning live runs. **Lessons from 21–24 Oct (7.6f–k, 7.8, 7.9) added on 24 Oct (Step 7.7), at the end.**_

## Working lessons
- Copy code with the copy button; create/edit files in VS Code, not long terminal pastes.
- **Save all (⌥⌘S) before running**; "N unsaved" means a stale run.
- **When replacing a selected block, check the lines just after it; after pasting, check indentation.**
- **Paste heredocs (`<<'EOF'`) flush left** (problem 33).
- **At the end of each step, run `git status`**: any untracked file is either committed or deleted. **Then push.**
- **A push publishes the whole history**: check for secrets in every commit before the first push.
- Two commands pasted onto one line → "illegal option"; run them one by one. Terminal text pasted into chat loses spaces; attached files don't.
- A red ✗ next to a command = non-zero exit code, not necessarily an error.
- Keep the Problems panel at zero. A newer ruff than Haris's flags ISC004 at `document_builder.py` (old code); ignore unless his ruff shows it.
- Router errors: read the attempt trail. **502 "upstream_error … 503 high demand" = provider busy; 429 "All models exhausted … reset ~Ns" = the router's cooldown (no model tried); 429 "daily_quota_exhausted … ~7m" = quota; "timeout" at ~60 s on OpenRouter = the router's per-provider timeout; 413 "Request too large… TPM: Limit 8000, Requested N" = Groq's per-request size; router log "tpm/tpd-limit" = the router's own limit check (minutes on end: a daily cap or its cooldown ladder, problem 80); 400 "Profile 'x' not found" = the chain doesn't exist. None of these is our code.**
- Router dashboard: chains are "profiles"; the toggles edit **the active chain** only. Router settings in `.env` are read only at startup. **The router keeps its own copy of each model's limits: after a provider upgrade, raise them in the dashboard too.**
- **When the router misbehaves, read its source and its database** (`server/src`, `server/data/freeapi.db`, read-only). **The `requests` table gives real tokens per call; `server_logs` (time in `created_at_ms`) explains refusals.**
- **A provider's limits page isn't the whole story** (problem 62). Test a model in `trial` before relying on it.
- **Free tiers have daily budgets and penalty ladders: plan the day's runs** (problems 64, 80). Since 7.6k the client paces `auto:judge`, so back-to-back cases are fine for the per-minute limit; daily caps still need budgeting (see Dots3 below).
- Gemini quotas and Groq daily caps reset at 04:00 Dubai. Run live checks earlier in the day.
- **Don't let new work change what a pending check tests**: put it on a branch.
- **Upgrading a limit can hide a bug the limit would have shown.**
- Tariff data: never trust aggregators. **Official Indian hosts block automated fetching**: confirm them in a browser. Official sources move: re-check links before the demo.
- **A 429 in ~0.02 s never reached a provider: it's the router's own limit check.**
- **A judge's blind spot can be systematic** (18–19 Oct): GPT-OSS catches changed facts but misses changed strength of a claim. Where a fixed rule exists, put it in code (7.6b, 7.6e, 7.8); measure the rest with the evaluation set.
- **"Works as code" ≠ "passed"** (Haris, 18 Oct), **and one clean case ≠ passed** (19 Oct): a change that affects several verdicts must run live on each of them before a merge (7.6c–e passed chargers but failed on windows/windows_nodata for new reasons).
- **Check what a rule does to every sample before shipping it** (19 Oct, 7.6e): "mandatory if it has a qualifier" alone would have silently dropped 7 notes in windows_nodata; counting verbatim notes per sample found it before any file was written.
- **QA reviewing text the user will never see only adds ways to fail** (19 Oct, problem 76): make the judge review exactly what the report shows.
- **Verbatim is only as safe as its source** (34, 79): a mandatory note printed verbatim from the Researcher's paraphrase can carry an invented fact; take fixed facts from the KB.
- **A model that ignores a correction makes the single revision worthless** (77): the safe outcome is CHECKS_FAILED; the real fix is a better model or taking the fact away from the model.
- **We started coding around free-model weaknesses on 19 Oct**: code rules that protect against any model are worth it; workarounds for one free model's quirks are a sign to change the model.
- **Buy the fix for the problem you can measure, not the one you guess** (20 Oct): the judge budget was a measured wall; the writer's quality wasn't yet proven to be the bottleneck, so only Groq was bought.
- **Competitors existing is not a reason to restart** (20 Oct): check what they really do, claim only what we can prove, and let customer evidence pick the position.
- **Derive an evaluation's answer key from code, not by hand** (17 Oct).
- Always run a "break test" on a new check; **make missing items fail by name, not by crashing** (7.6; 19 Oct: a fake LLM with one queued answer crashed when the rule was off, fixed by queuing a second).
- Print the real schema/output before writing code against it.
- A "number appears in the cited record" check proves existence, not meaning. If no agent checks a text's meaning, render it verbatim, give the model fixed meanings in code, or match by source, never by wording.
- **A filter by source only works on fields that carry a source** (52). **What an agent isn't told, it can't respect** (53).
- A substring check can be fooled by a name inside a longer name; match full names, longest first.
- **KB notes are facts for the exporter; team reminders go in `dev_notes`** (9, 37).
- When a model keeps getting a number or a fixed fact (or a format) wrong, compute or fill it in code (10, 11, 44, 75, 79). **The same for a judge: don't ask it to re-judge what code already proves** (59).
- **Give a judge the facts its rules need** (55). **Give a judge exactly what the writer saw, and only what the reader will see** (7.6, 7.6d).
- **A judge's "false rejection" can be a real catch: read it before discounting it** (59, 60; 19 Oct: every QA rejection was real).
- When the model makes the mistake the prompt invites, fix the prompt wording first (20).
- **Research before declaring a gap** (16).
- Tests catch wiring bugs, not just logic (23).
- **A fallback that always produces a correct (if plain) answer turns an outage into a degraded demo instead of a broken one.** The same holds for QA: ERROR → report still produced, honestly marked "NOT reviewed by QA".
- A retry that hits a cooldown is wasted (8.6b). A fast provider-busy failure shouldn't use up the only retry (43).
- **Totals can leak individual values** (49).
- **Read the reports, not just OK/FALLBACK or the report check**: most problems from 30 to 79 passed every automatic check and were found by reading.
- **A code check on the finished output catches forms of mistakes in milliseconds; it can't judge meaning** (report check, 9.6b).
- f-strings: no same-type quotes nested inside an f-string before Python 3.12; avoid them anyway.

## Added 24 Oct (21–24 Oct work)
- **A correction is itself a claim: check it against the source before acting on it** (7.6g, problems 81–82). On 23 Oct a QA "fix" contradicted the KB and the writer copied it; the KB shield now overrules such fixes, re-judges once, and records OVERRULED instead of pretending the review approved.
- **Before shipping a rule, run it over every saved run and read each hit** (7.8: 47 hits, 44 real drops, 3 false alarms that shaped the rule; 7.9: exactly the 14 real cases, 0 of 39 look-alike questions). A rule tuned on one example misfires on the next wording.
- **When a model keeps adding or dropping something the facts already settle, code does it** (7.6j check names, 7.8 qualifiers restored from the KB, 7.9 HS follow-ups dropped). Restore from the source rather than asking the model again: a revision spent on a known fix is a revision lost for a real one.
- **Never rewrite a text that also says other things** (7.8): code replaces an item only when it is the source note and nothing more; anything mixed becomes a hard problem, so no fact is silently lost.
- **A rule that never fires live is proven offline, not disproven** (7.6k pacing, 7.9): record it as "offline only, watch live" and keep the replays that prove it.
- **Our own testing can use up a fallback's daily cap** (24 Oct 17:16): Dots3 allows 50 requests per rolling 24 h; four live sets used 52, so `long` was Gemini-only when Gemini returned 503s, and the run ended LLM_ERROR. Count the day's requests before a live set, and spread evaluation-set runs over days.
- **Reasoning models spend the answer budget on hidden reasoning** (problem 83): GPT-OSS on Cerebras cut off at 2,000 tokens in half the part calls; send 3,000 while planning parts with 2,000.
- **Pace requests on your side when a provider has a per-minute limit** (7.6k): the router's cooldown escalates (2 min, 10 min, 1 h, a day), so one burst can cost a whole session.
- **Query a database for the columns you need only** (23 Oct): a broad `settings` query printed the router's key into tool output; the key was regenerated.
- **A repo file can be read-only on the Mac** (`prompts/researcher.md`, `mansha/llm_client.py`): write the tested file as `.new` with its hash, then `chmod 644` and move it; check the hash.
- **Read the terms of free credits before signing up** (24 Oct): forum reports say Google Cloud's $300 trial no longer pays for Gemini through AI Studio (the route our router uses), and the 90-day clock starts at sign-up. Sign up only when the credit is needed and its route is verified.
- **A small clean sample can hide a rare failure** (24 Oct sets 1–2 each found a new one): judge a step's bar on several runs of every verdict it touches, and move rare-failure measurement to the evaluation set's repeats.
