# Brief: repeats, sitting 6 (pass 3 N2, N3, N7, N10), the first under R1 (26 Oct 2026)

For Haris's Mac chat. Decisions and history: `docs/cloud/handoff_2026-10-25_g17.md` (sections "Repeats sitting 4" for R1 and the stop rule, "Repeats sitting 5" for the R1 setting and the registers). Method as in `docs/cloud/repeats_sitting1_brief.md`.

## Goal
The last 4 repeat runs: **pass 3 N2, N3, N7, N10**, in that order. Pipeline frozen at 2d8751f (working rule 7), grader eb8098d. This is the **first sitting under R1**, so it also measures R1 and starts the G17 streak under R1 at 0 (sitting 5's 4 clean runs were pre-R1 and don't count: Haris, 26 Oct).

## Before the run (router, read-only, `mode=ro`, only the columns needed)
1. **R1 is in effect:** `long` = Dots3, Gemini 3.6, Gemini 3.5; `qa` = Groq GPT-OSS 120B; `judge` = Cerebras; no Gemini 3.7 in any of them. If not, don't start: report what the router shows.
2. **Dots3 left** (cap 50 per 24 h) and when the next requests free up. After sitting 5 Dots3 was at about 47/50; 25 Oct's sitting 1 (10 requests) frees ~19:31–19:50 and sitting 2 (7) ~21:09–21:30 Dubai, so expect ~13 left after ~19:50 and ~20 after ~21:30. The router decides, not this estimate.
3. **Groq:** tokens used in the last 24 h (cap 400,000; 16,845 before sitting 5) and no cooldown. `qa` now has no fallback, so a benched Groq = no Intake.
4. **Cooldowns** (`rate_limit_cooldowns`): none on Dots3, Gemini 3.6, Gemini 3.5, Groq, Cerebras.

## Sizing (unchanged; never `--force`)
k = the most cases in the order above with **3 × k ≤ Dots3 left** (Dots3 alone covers the typical case), and **5 × k** passing the guard. Guard SHORT → drop the last case and retry. Dropped cases go to a sitting 7, same order. If A′ is live (credit bought), check the Dots3 RPD = 1000 in the router DB first (addition b).

## Command (k = 4)
```
python -m scripts.eval_set --case N2 --case N3 --case N7 --case N10
```
Dry run first (must be clean), then the budget guard, then the cases.

## Baseline to compare (verdict; result)
| Case | Verdict | Result in baseline and repeats | Note |
|---|---|---|---|
| N2 | ELIGIBLE | FAIL on anchor 97 (3 of 3) | an anchor-97 FAIL is the known result, **not** a stop |
| N3 | ELIGIBLE | PASS (sitting 4: QA part NOT reviewed, judge truncation) | |
| N7 | NOT_ELIGIBLE | PASS | |
| N10 | NEEDS_MORE_DATA | PASS | |

## Stop rules
- **Recorded, not a stop:** (a) a problem 101 repeat (QA correction on the `P-IN-IMPORTER` e-certificate caveat → "keep that qualifier" check fails → CHECKS_FAILED); (b) a judge truncation at 3,000 completion tokens (`finish_reason=length`, the N3 kind; fix P1 after the repeats).
- **Stop the sitting and report:** any **LLM_ERROR** (note which providers were tried; after R1 this points to R2); any **other verdict difference** from the table above; any QA ERROR not of kind (b); a dry run that isn't clean.

## After the sitting
1. Fill `reading.md` in the new run folder as before: per case status, verdict, PASS/FAIL, slips (confirmed by reading), LLM_ERROR / QA ERROR, seconds, `long` and `judge` requests, serving models (from `phase_log.json`).
2. **R1 measurements:**
   - **Intake seconds per case** (before R1: ~61 s in 12 of 21 repeat runs; expected now: a few seconds every time, served by Groq).
   - Every `long` failover in the router's requests table: which model failed (Dots3 timeout or error), which hop was tried next (Gemini 3.6, then 3.5?), and how it ended. Gemini 3.6 returned 503 twice in sitting 5.
   - Median report time (G16; sitting 5: 178.7 s).
3. G17 streak under R1 (LLM_ERROR or QA ERROR of any kind, including (b), breaks it).
4. Router after the run: Dots3 used/50, Groq tokens, cooldowns.
5. Add the run folder to `runs-snapshot` and push it.
6. Paste a ⬅️ BACK TO CLOUD block in the cloud session naming the run folder and its `reading.md`.
