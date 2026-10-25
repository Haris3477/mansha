# Brief: repeats, sitting 1 under option A (25 Oct 2026)

For Haris's Mac chat. Decisions behind it: `docs/cloud/handoff_2026-10-25_g17.md` (G17 = A now, A′ after the OpenRouter credit; N7 in the repeat group).

## Goal
Start the repeats ×3 on the repeat group: **C1, C2, C3, C4, N2, N3, N7, N10** (24 runs in all). Pipeline frozen at `main` 2d8751f (working rule 7: no pipeline change until the repeats are done). The repeats are also the G17 measurement: 10 runs in a row without LLM_ERROR or QA ERROR.

## Plan: passes, not cases
Run the group in **three passes** (pass 1 = each case once, then pass 2, then pass 3), spread over sittings. One pass per case before any case's second run keeps every sitting balanced and makes a stopped day lose nothing. Use `--case` lists with the default `--repeat 1`; each sitting gets its own `runs/eval_set/<time>/` folder. Don't use `--only-repeat --repeat 3` under A: it needs 24 runs at once.

Fixed order (take the next cases in this order, continuing where the last sitting stopped):
`C1, C2, C3, C4, N2, N3, N7, N10`, then again for pass 2 and pass 3.

## Sizing a sitting (option A, never `--force`)
All eight are report cases: typical 3 `long` requests each, worst 5 (the guard's tables).
1. Read the router first (read-only, `mode=ro`, only the columns needed): Dots3 requests in the last 24 h (cap 50) and when the next ones free up; Google calls since the 11:00 Dubai reset and whether Google or any `long` model is benched (`rate_limit_cooldowns`).
2. **Real `long` left** = Dots3 left + Google left, with Google counted as at most ~9–13 calls a day in total (project-wide quota, refused after ~13 on 24 Oct), minus the Google calls already used today.
3. Pick **k** = the most cases in the order above with **3 × k ≤ real `long` left**, and **5 × k** still fitting the guard. If the guard says SHORT, drop one case and retry; never `--force`.
4. At 17:18 Dubai there were Dots3 38/50 used (+6 frees ~19:00, +2 ~20:00) and 14 Google calls since 11:00 (4 OK, 10 errors). So expect **k ≈ 3–4 tonight after ~19:00 (C1, C2, C3, maybe C4)**. The router decides, not this estimate.

## Command (example for k = 4)
```
python -m scripts.eval_set --case C1 --case C2 --case C3 --case C4
```
It runs the dry run first (must be clean), then the budget guard, then the cases.

## After the sitting
1. Fill `reading.md` in the new run folder as in the baseline.
2. Note per run: status, verdict, PASS/FAIL, slips, LLM_ERROR / QA ERROR, seconds, `long` requests. The Researcher's and Builder's serving model is already saved in each run's `phase_log.md` / `phase_log.json` ("served by"), so nothing new to record by hand (addition c).
3. Add the sitting's run folder to `runs-snapshot` and push it.

## Stop and report if
- any LLM_ERROR or QA ERROR (it breaks the G17 streak; note which provider failed);
- a verdict differs from the baseline for the same case;
- the dry run isn't clean.
