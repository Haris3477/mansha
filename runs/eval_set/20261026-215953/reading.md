# Reading sheet: evaluation set run 20261026-215953 (fix round 1b: N5 only, k = 1; branch claude/fix-round-candidates-design-rz44re at 6bbea54)

Read by Claude (Mac chat), 26 Oct 22:10 Dubai. Offline suite on the Mac: 19/19 pass. Guard said OK (long left 41: Dots3 47/50, Gemini 3.6 2/20, Gemini 3.5 0/20).

## N5_paint_indian_resin: LLM_ERROR — FAIL (provider capacity; STOP RULE → no rerun tonight)
- Nothing to read: the Researcher never got an answer (notice.md only). 97 INDIAN_INPUTS and the 6bbea54 shield change are still **untested live**.
- Intake Groq 1.31 s OK. Researcher: 4 model attempts + 1 cooldown wait, 128.7 s, all failed:
  1. Gemini 3.6 503 "high demand" → Dots3 **429 `free-models-per-day`** (OpenRouter's own daily cap)
  2. Gemini 3.5 503 → 3. Gemini 3.6 503 → 4. Gemini 3.5 503
- Router cooldowns set: Dots3 until **27 Oct 04:00 Dubai** (authoritative, = 00:00 UTC); Gemini 3.6 until 22:11 (heuristic).

## Why the guard said OK (new finding, budget accounting)
- OpenRouter counts **every request that reaches it, per UTC day** (resets 04:00 Dubai). Since 04:00 Dubai today the router sent 50 Dots3 attempts: 47 ok + 1 non-JSON error + 2 timeouts (N10 of run 20261026-213601). The 51st got 429.
- The router's sliding-24 h count (what the guard reads) counts only the 47 successes, so it showed "3 left". Two errors in our accounting: failed/timed-out calls count at OpenRouter, and the window is the UTC day, not a sliding 24 h.
- Consequence: the "12 left at 16:19 tomorrow" plan was wrong. All 50 Dots3 come back at **04:00 Dubai** each day.
- OpenRouter's 429 text now says "Add 5 credits to unlock 1000 free model requests per day" (OpenRouter's docs pages found earlier say 10). Check the limits page before buying.
- Google: Gemini 3.6 and 3.5 both 503 "high demand" on every attempt 21:59–22:02 (also 3.6 at 21:47); no Google quota used (3.6 2/20). Gemini is not a usable backup right now.

## G17 under R1
8 runs, 1 LLM_ERROR (this one; cause: Dots3 daily cap at OpenRouter + Gemini 503 overload; the retry/cooldown logic worked as designed). Streak resets to 0.
