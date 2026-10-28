# Handoff: 7.6n source_id fix (28 Oct 2026)

Branch `claude/fix-source-id-fill-gap-86nr8m`, started from main at cb8879e (problems 100 + 98 merged). Follows `docs/cloud/handoff_2026-10-28_100_98.md` ("Next 2: the 7.6n source_id fix"). **Task closed.**

## Decision (Haris)
- **Option B** (Claude's recommendation): fix by key, keep a gap basis.
  - Rejected: A (write the whole fixed shape every time) and C (fill only `source_id`).
  - Why B: replaying the fixed shape over the 8 saved gap outputs showed the Researcher's own `origin_result.basis` differs from `GAP_BASIS` in 7 of 8. Under A, every gap report's basis sentence would change, which needs a live sitting. B changes only the buggy run.

## What was found
- **205332 N13 r2, round 1:** `origin_rule` and `estimated_saving` were already the gap but had `source_id: null`.
- `fill_gap` skipped any field whose status, rule or agreement was already the gap. That left 2 code problems and one wasted Researcher round (20.5 s).

## What changed (commit 818cc9b)
- **`mansha/researcher.py` `fill_gap`:**
  - A field that isn't the gap is still rewritten whole, as before (the 194334 case).
  - A field that is already the gap gets each fixed key written when it differs: `source_id`, rates, `amount`, `currency`. Each change is logged as `<field>.<key>: old -> new for a gap`.
  - A non-empty `basis` is kept. An empty one gets `GAP_BASIS`.
- **`scripts/test_researcher.py`:** 6 new checks built from the r2 output:
  - two `source_id`s filled (2 changes), basis kept, idempotent
  - other wrong fixed keys written
  - an empty basis gets the code's sentence
  - `run_researcher` passes in round 1 with no problems
- **No prompt change, no KB change, no backend change.**

## Results
- **Offline:** all 20 suites pass.
- **Replay** (old vs new `fill_gap` over 202 saved Researcher outputs): only `20261028-205332/N13_wooden_doors_r2/researcher_1.json` changes, with exactly the two `source_id` fills.
- **No live sitting** (offline-proven, as planned in the 100 + 98 handoff). The next sitting with a gap answer shows it live; it is logged by name when it fires.

## Problems / gaps
- **7.6n source_id bug:** fixed.
- Everything else in `handoff_2026-10-28_100_98.md` stands unchanged: the G17 question, the judge-chain 429 / 90 s cap, problem-1 wrong-material lines, the terminal-paste idea.

## Project update (Mac chat, 💾)
- **CURRENT_STATE live addendum:** 7.6n now fixes each fixed key of a gap object and keeps the Researcher's basis (818cc9b). Offline and replay proven.
- **agent_prompts, llm_backend_setup, fact base:** no change.

## Next
- **Merge (Haris):** `claude/fix-source-id-fill-gap-86nr8m` into main.
- **Next task:** the step shield (G32/G39; option C of 1d; G14 actor-first and slip 94). Then 99, then the guard health check.
