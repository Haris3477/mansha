# Brief: G17 decision (reliability of the `long` chain) — 25 Oct 2026

Source: Haris's CURRENT_STATE (Project, last save 25 Oct 17:10) + router check in Haris's chat at 17:18 Dubai. This brief is the only context you get from the Project for this task.

## Where we are
- Evaluation-set baseline COMPLETE on one pipeline version (main at 2d8751f; only the grader changed since 17612d6): 20 of 20 cases + N14 once (expected failure). 16 of 20 pass every code check. Failures: N2, N5 (problem 97: a deciding condition reaches the user only as a note), N13 (wrong verdict, problem 100), N15 (safe CHECKS_FAILED, problem 99). Run folders: `runs/eval_set/20261024-190920`, `-192027`, `-203537`, `20261025-140208`, `-151048`, `-162526`, `-163540`, each with a filled `reading.md` (extract `runs/` from the `runs-snapshot` branch, see CLAUDE.md).
- Next after G17: repeats ×3 on the repeat group (C1–C4, N2, N3, N10; N7 question below), live on Haris's Mac, never `--force`. Then pipeline fixes (97, 100, 98, 99, 72, 96), each judged against the baseline and the repeats. Working rule 7: no pipeline change until the repeats are done.
- Design reference: `docs/archive/evaluation_set_design.md` ("Update 24 Oct", E6 = G17 decided after the baseline, before the repeats). Router/limits background: `docs/lessons.md`, `docs/runbook.md`.

## The gaps
- **G17:** free providers are unreliable. `long` = Gemini 3.5 Flash, 3.6 Flash, 3.7 Flash, Dots3 Note Preview (OpenRouter `:free`). 24 Oct: our own runs used up Dots3's 50 requests per sliding 24 h; Google's free quota is project-wide (refused at 3/20 and 10/20 in the router's count, benched until 11:00 Dubai) → LLM_ERRORs. Bar: 10 runs in a row without LLM_ERROR or QA ERROR.
- **G16:** run time. Bar: median run < 60 s over the evaluation set. Not met.

## Baseline numbers (25 Oct unless noted)
- ~2–3 `long` requests per report case (guard estimate 3–5).
- Median per sitting 108–208 s; runs 78–258 s; Intake 61 s in 7 runs (Gemini 3.7 timeouts), 1–11 s when Groq served.
- 0 LLM_ERROR on 25 Oct (15 runs, 4 sittings; Gemini back after 11:00, Dots3 refilling); 2 LLM_ERROR on 24 Oct (all of `long` benched or capped).
- Provider issues 25 Oct: Gemini 3.7 Intake timeouts ×7, one Gemini 3.7 503, one Dots3 150 s timeout (rescued by Gemini 3.5), one Cerebras 429 (busy wait recovered).
- Free capacity ≈ 7–11 report cases a day.
- Router at 25 Oct 17:18 Dubai: no cooldowns; Dots3 38/50 (frees +6 ~19:00, +2 ~20:00 Dubai, the rest tomorrow 14:00–17:00); Google since its 11:00 reset: 4 successes, 10 Gemini 3.7 errors (5 timeouts, 5 "high demand" 503), no quota refusal yet (~13 calls before refusal on 24 Oct); Cerebras judge 74/2,400.
- Repeats need 21–24 runs ≈ 50–70 `long` requests: ~3 days on free capacity; ~1 day with A′.
- Cerebras judge spend ≈ $0.55 of the $5 trial credit (expires ≈ 21–22 Nov).

## Options (Haris decides)
- **A:** keep as is; size sittings by real capacity (Dots3 count + ~9–13 Google calls), never `--force`.
- **A′:** A + Haris buys $10 OpenRouter credit (planned in ~2 days): `:free` models go 50 → 1,000 requests/day; Haris then sets Dots3 RPD 50 → 1000 in the router (checked in the router DB before the next run). Same model, so the baseline stays one version.
- **B:** add the Kilo copy of Dots3 or another free long-context model to `long` (setup chat; check its quota first). Adds a model the baseline didn't use.
- **C:** a paid writer first in `long` (Claude via OpenRouter, paid Gemini; Google Cloud trial unverified). Changes the model, so the baseline no longer describes the pipeline.
- Haris's current lean: **A now, A′ once the credit is bought.**

## Things to weigh (Claude's notes from the state check, not decisions)
- The baseline already mixed serving models per run (Gemini or Dots3 by availability): record the Researcher's and Builder's serving model per repeat so model-driven slips can be told apart from logic ones.
- Three of the four failures (97 ×2, 100) and problem 98 are pipeline logic, not model quality: evidence against C now.
- G16 (speed) is not fixed by A or A′; C is the only option that addresses it, so it may come back later as its own deliberate version change, measured against the baseline.

## Task for this session
1. Step 2: lay out A / A′ / B / C against these numbers (what each changes, cost, effect on the baseline and on G16/G17, risks), with a recommendation. Haris decides. STOP.
2. Step 3 (after his decision): N7's repeat flag — `scripts/eval_cases.py` marks N7 `repeat=True`, the design's repeat group (C1–C4, N2, N3, N10) does not. Show both and ask Haris. If he removes it, that's a grader/case-file change (allowed with his yes).
3. Write the handoff file (see CLAUDE.md).
