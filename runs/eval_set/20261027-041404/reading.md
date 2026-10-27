# Reading sheet: evaluation set run 20261027-041404 — VOID (router not running)

Read by Claude (Mac chat), 27 Oct. All 4 cases LLM_ERROR in 0.0–0.1 s at Intake: "connection error … Is the router running?". The router was started a minute later and the same list ran as 20261027-041503.
Not a provider or pipeline failure: do not count toward G17 (operator setup). Zero LLM calls, zero quota used.
Finding: the budget guard reads the router's SQLite file directly, so it said OK with the router down. Suggest a one-call health check (GET /v1/models) before the guard says OK.
