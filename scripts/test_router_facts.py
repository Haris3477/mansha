"""Offline tests for scripts/router_facts.py (and the read-only guard in scripts/router_db.py).

A throwaway router database rebuilt from 27 Oct 14:21:39 UTC (sitting 180618, N2): the Dots3 Researcher call
timed out at 150 s and Gemini 3.6 served it at ordinal 1; the router benched Dots3 for 90 s (heuristic), so
both Builder calls went to Gemini at ordinal 0. N5 after it ran on Dots3 at ordinal 0 throughout.
The database also holds settings and api_keys with fake secrets: nothing may read or print them.
Run: python -m scripts.test_router_facts
"""

import calendar
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

os.environ["TZ"] = "Asia/Dubai"     # the run folder's name is Mac local time (Dubai, UTC+4)
time.tzset()

from scripts import router_db, router_facts

failures: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="mansha_router_facts_"))


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def utc_ms(text: str) -> float:
    return calendar.timegm(time.strptime(text, "%Y-%m-%d %H:%M:%S")) * 1000


DOTS, G36, G35 = ("openrouter", "dots3:free"), ("google", "gemini-3.6-flash"), ("google", "gemini-3.5-flash")
GROQ, CEREBRAS = ("groq", "openai/gpt-oss-120b"), ("cerebras", "gpt-oss-120b")


def name(m) -> str:
    return f"{m[0]}/{m[1]}"


# ---------- the run folder (two cases) ----------
run = TMP / "20261027-181000"          # 18:10:00 Dubai = 14:10:00 UTC
CASES = {
    "N2_furniture_freezone": [("Intake", GROQ, 1.3), ("Researcher (round 1)", G36, 176.64),
                              ("QA (round 1)", CEREBRAS, 1.72), ("QA (round 1)", CEREBRAS, 0.72),
                              ("Document Builder", G36, 13.23), ("Document Builder", G36, 7.76),
                              ("Prose QA (round 1)", CEREBRAS, 1.63)],
    "N5_paint_indian_resin": [("Intake", GROQ, 1.0), ("Researcher (round 1)", DOTS, 120.0),
                              ("QA (round 1)", CEREBRAS, 1.5), ("Document Builder", DOTS, 60.0),
                              ("Prose QA (round 1)", CEREBRAS, 1.2)],
}
FINISHED = {"N2_furniture_freezone": "2026-10-27 14:25:00", "N5_paint_indian_resin": "2026-10-27 14:30:00"}
for case, calls in CASES.items():
    phases = [{"name": ph, "calls": [{"ok": True, "served_by": name(m), "latency_s": s, "attempts": [
        {"attempt": 1, "chain": "auto:x", "routed_via": name(m), "latency_s": s, "ok": True}]}]}
        for ph, m, s in calls]
    (run / case).mkdir(parents=True)
    log = run / case / "phase_log.json"
    log.write_text(json.dumps({"status": "REPORT", "phases": phases}), encoding="utf-8")
    os.utime(log, (utc_ms(FINISHED[case]) / 1000,) * 2)
(run / "summary.json").write_text("{}", encoding="utf-8")
os.utime(run / "summary.json", (utc_ms("2026-10-27 14:30:00") / 1000,) * 2)
(run / "reading.md").write_text("edited later", encoding="utf-8")     # must not move the window

# ---------- the router database ----------
db = TMP / "freeapi.db"
con = sqlite3.connect(db)
con.executescript("""
CREATE TABLE settings (key TEXT, value TEXT);
CREATE TABLE api_keys (id INTEGER, platform TEXT, key TEXT);
INSERT INTO settings VALUES ('router_key', 'sk-router-SECRET-1');
INSERT INTO api_keys VALUES (1, 'openrouter', 'sk-or-SECRET-2');
CREATE TABLE profiles (id INTEGER, name TEXT);
CREATE TABLE profile_models (profile_id INTEGER, model_db_id INTEGER, enabled INTEGER);
CREATE TABLE models (id INTEGER, platform TEXT, model_id TEXT, rpd_limit INTEGER, enabled INTEGER);
CREATE TABLE model_overrides (platform TEXT, model_id TEXT, overrides_json TEXT);
CREATE TABLE rate_limit_usage (platform TEXT, model_id TEXT, kind TEXT, created_at_ms INTEGER);
CREATE TABLE rate_limit_cooldowns (platform TEXT, model_id TEXT, key_id INTEGER, set_at_ms INTEGER,
                                   expires_at_ms INTEGER, source TEXT);
CREATE TABLE requests (id INTEGER PRIMARY KEY, created_at TEXT, platform TEXT, model_id TEXT, status TEXT,
                       latency_ms INTEGER, prompt_tokens INTEGER, completion_tokens INTEGER);
CREATE TABLE request_attempts (id INTEGER PRIMARY KEY, request_id INTEGER, ordinal INTEGER, platform TEXT,
                               model_id TEXT, outcome TEXT, duration_ms INTEGER, error_summary TEXT);
INSERT INTO profiles VALUES (3, 'long'), (4, 'qa'), (6, 'judge'), (7, 'arabic');
INSERT INTO models VALUES (1, 'openrouter', 'dots3:free', 1000, 1), (2, 'google', 'gemini-3.6-flash', 20, 1),
                          (3, 'google', 'gemini-3.5-flash', 20, 1), (4, 'groq', 'openai/gpt-oss-120b', 1000, 1),
                          (5, 'cerebras', 'gpt-oss-120b', 2400, 1);
INSERT INTO profile_models VALUES (3, 1, 1), (3, 2, 1), (3, 3, 1), (4, 4, 1), (6, 5, 1), (7, 3, 1), (7, 2, 1);
""")


def request(created, model, status, latency_ms, attempts, tokens=(100, 50)):
    rid = con.execute("INSERT INTO requests (created_at, platform, model_id, status, latency_ms, prompt_tokens, "
                      "completion_tokens) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (created, *model, status, latency_ms, *tokens)).lastrowid
    for i, (m, outcome, dur, err) in enumerate(attempts):
        con.execute("INSERT INTO request_attempts (request_id, ordinal, platform, model_id, outcome, duration_ms, "
                    "error_summary) VALUES (?, ?, ?, ?, ?, ?, ?)", (rid, i, *m, outcome, dur, err))
    if status == "success":
        con.execute("INSERT INTO rate_limit_usage VALUES (?, ?, 'request', ?)", (*model, utc_ms(created)))
    return rid


def ok(created, model, latency_ms):
    return request(created, model, "success", latency_ms, [(model, "ok", latency_ms, None)])


request("2026-10-27 13:00:00", DOTS, "success", 90000, [(DOTS, "ok", 90000, None)])     # before the window
ok("2026-10-27 14:18:41", GROQ, 1250)                                                    # N2 Intake
TIMEOUT_ID = request("2026-10-27 14:21:39", G36, "success", 176400,
                     [(DOTS, "timeout", 150000, "Provider timeout after 150000ms (openrouter)"),
                      (G36, "ok", 26300, None)])                                         # N2 Researcher
con.execute("INSERT INTO rate_limit_cooldowns VALUES ('openrouter', 'dots3:free', 1, ?, ?, 'heuristic')",
            (utc_ms("2026-10-27 14:21:39"), utc_ms("2026-10-27 14:21:39") + 90000))
ok("2026-10-27 14:21:41", CEREBRAS, 1700)
ok("2026-10-27 14:21:43", CEREBRAS, 700)
ok("2026-10-27 14:21:57", G36, 13100)                                                    # N2 Builder: Dots3 benched
ok("2026-10-27 14:22:05", G36, 7700)
ok("2026-10-27 14:22:07", CEREBRAS, 1600)
ok("2026-10-27 14:22:30", GROQ, 5000)                                                    # another app's call
ok("2026-10-27 14:25:20", GROQ, 980)                                                     # N5
ok("2026-10-27 14:27:21", DOTS, 119500)
ok("2026-10-27 14:27:23", CEREBRAS, 1450)
ok("2026-10-27 14:28:24", DOTS, 59600)
ok("2026-10-27 14:28:26", CEREBRAS, 1150)
con.commit()
con.close()
NOW = utc_ms("2026-10-27 14:40:00")

print("1. Sitting 180618 N2 rebuilt (Dots3 timeout -> Gemini 3.6 at ordinal 1, then a 90 s bench)")
text = router_facts.facts(run, db, NOW)
lines = text.splitlines()


def has(line: str) -> bool:
    return line in lines


check("window: folder name in Dubai time -> UTC, padded 5 min; reading.md ignored",
      has("Window (UTC): 2026-10-27 14:05:00 to 2026-10-27 14:35:00 (folder start and last log file, padded 5 min)"),
      next((x for x in lines if x.startswith("Window")), ""))
check("the request before the window is left out", "13:00:00" not in text)
check("a) the Researcher request with both attempts and the shortened error",
      has(f"  #{TIMEOUT_ID} 14:21:39 google/gemini-3.6-flash success 176400 ms  <- N2_furniture_freezone "
          "Researcher (round 1) attempt 1")
      and has('      0 openrouter/dots3:free timeout 150000 ms  "Provider timeout after 150000ms (openrouter)"')
      and has("      1 google/gemini-3.6-flash ok 26300 ms"), text)
check("a) another app's call is listed as not matched, not guessed",
      any(x.endswith("groq/openai/gpt-oss-120b success 5000 ms  <- not matched to a case") for x in lines))
check("b) per platform counts", has("  openrouter: 3 attempts (ok 2, timeout 1)") and has("  google: 3 attempts (ok 3)"))
check("b) long call: Gemini 3.6 at ordinal 1 after the Dots3 timeout",
      has("  N2_furniture_freezone Researcher (round 1): google/gemini-3.6-flash at ordinal 1 "
          "(after openrouter/dots3:free timeout 150.0 s)"))
check("b) long call: Builder on Gemini at ordinal 0 (Dots3 benched, no attempt row)",
      lines.count("  N2_furniture_freezone Document Builder: google/gemini-3.6-flash at ordinal 0") == 2)
check("b) N5 on Dots3 at ordinal 0", has("  N5_paint_indian_resin Researcher (round 1): openrouter/dots3:free at ordinal 0"))
check("b) validity: N2 not valid, with the reason",
      has("  N2_furniture_freezone: NOT VALID: Researcher (round 1) google/gemini-3.6-flash ordinal 1; "
          "Document Builder google/gemini-3.6-flash ordinal 0; Document Builder google/gemini-3.6-flash ordinal 0 "
          "(3 long calls)"), "\n".join(x for x in lines if "VALID" in x or "valid" in x))
check("b) validity: N5 valid", has("  N5_paint_indian_resin: valid (2 long calls)"))
check("b) every client call matched", has("  Client calls not matched in the router: none"), text)
check("c) the 90 s heuristic bench", has("  openrouter/dots3:free: set 14:21:39, expires 14:23:09 (90 s, heuristic)"))
check("d) OpenRouter timeout in the window with its duration",
      has(f"  OpenRouter timeouts in the window: #{TIMEOUT_ID} 14:21:39 dots3:free 150.0 s"))
check("d) OpenRouter attempts since 00:00 UTC (all outcomes)",
      has("  OpenRouter attempts since 00:00 UTC (04:00 Dubai): dots3:free 4 (ok 3, timeout 1)"), text)
check("d) no active cooldown at 14:40", has("  active cooldowns: none"))
check("d) capacity line for Dots3 (router 24 h successes, UTC-day attempts)",
      has("    long  openrouter/dots3:free: router 24 h 3, UTC-day attempts 4; used 4/1000; left 996"), text)
check("d) Cerebras tokens and cost estimate",
      has("  Cerebras last 24 h: 5 requests, 500 input + 250 output tokens, about $0.00 at $0.35/$0.75 per 1M"), text)
check("e) chains", has("  long: openrouter/dots3:free (rpd 1000), google/gemini-3.6-flash (rpd 20), "
                       "google/gemini-3.5-flash (rpd 20)"))
check("e) the arabic chain (B) is listed", has("  arabic: google/gemini-3.5-flash (rpd 20), google/gemini-3.6-flash (rpd 20)"),
      "\n".join(x for x in lines if x.startswith("  arabic")))
check("d) capacity: the arabic chain sees Gemini 3.6's use by the long chain (counted per model)",
      has("    arabic google/gemini-3.6-flash: router 24 h 3; used 3/20; left 17"), text)

print("\n2. Matching never guesses")
calls = router_facts.client_calls(run)
calls[1]["latency_s"] = 60.0          # the Researcher's latency no longer fits any router request
reqs = router_facts.requests_in(router_db.connect_ro(db), utc_ms("2026-10-27 14:05:00"), utc_ms("2026-10-27 14:35:00"))
router_facts.match(calls, reqs)
check("an unmatchable call stays unmatched", calls[1]["req"] is None)
check("and its case is not valid", "Researcher (round 1) not matched" in router_facts.validity(calls)[0],
      router_facts.validity(calls)[0])
check("the calls after it still match", all(c["req"] for c in calls[2:]))

print("\n3. Never settings / api_keys (problem 84), never .env")
check("no secret in the output", "SECRET" not in text)
for table in ("settings", "api_keys"):
    try:
        router_db.connect_ro(db).execute(f"SELECT * FROM {table}").fetchall()
        check(f"reading {table} is refused", False)
    except sqlite3.DatabaseError as exc:
        check(f"reading {table} is refused", "prohibited" in str(exc) or "not authorized" in str(exc), str(exc))
    try:
        router_db.connect_ro(db).execute(f"PRAGMA table_info({table})").fetchall()
        check(f"PRAGMA on {table} is refused", False)
    except sqlite3.DatabaseError:
        check(f"PRAGMA on {table} is refused", True)
try:
    router_db.connect_ro(db).execute("INSERT INTO models VALUES (9, 'x', 'y', 1, 1)")
    check("the connection is read-only", False)
except sqlite3.OperationalError as exc:
    check("the connection is read-only", "readonly" in str(exc), str(exc))
for f in ("scripts/router_facts.py", "scripts/router_db.py"):
    src = Path(f).read_text(encoding="utf-8")
    check(f"{f}: no query names settings/api_keys",
          not re.search(r"\b(FROM|JOIN|INTO|UPDATE|TABLE)\s+(settings|api_keys)\b", src, re.IGNORECASE))
    check(f"{f}: no .env path in a string", not re.search(r"[\"'/]\.env", src))

print("\n4. Break test: without the authorizer the key would be readable (the guard is what stops it)")
real = router_db._authorizer
router_db._authorizer = lambda *a: sqlite3.SQLITE_OK
try:
    leaked = router_db.connect_ro(db).execute("SELECT key FROM api_keys").fetchone()[0]
    check("break test: the secret is reachable once the guard is removed", leaked == "sk-or-SECRET-2")
finally:
    router_db._authorizer = real
try:
    router_db.connect_ro(db).execute("SELECT key FROM api_keys").fetchone()
    check("guard restored", False)
except sqlite3.DatabaseError:
    check("guard restored", True)

print("\n5. Command line")
out = StringIO()
with redirect_stdout(out):
    rc = router_facts.main([str(run), "--db", str(db)])
saved = (run / "router_facts.txt").read_text(encoding="utf-8") if (run / "router_facts.txt").exists() else ""
check("a run folder: exit 0, router_facts.txt written and printed", rc == 0 and saved and saved == out.getvalue())
with redirect_stdout(StringIO()) as out:
    rc = router_facts.main(["--now", "--db", str(db)])
check("--now: exit 0, state and chains, no run sections", rc == 0 and "d) Router state" in out.getvalue()
      and "e) Chains" in out.getvalue() and "a) Router requests" not in out.getvalue())
with redirect_stdout(StringIO()) as out:
    rc = router_facts.main(["--now", "--db", str(TMP / "missing.db")])
check("no database -> exit 2 with a plain message", rc == 2 and "cannot read the router database" in out.getvalue())
with redirect_stdout(StringIO()) as out:
    rc = router_facts.main([str(TMP / "no_such_run"), "--db", str(db)])
check("no run folder -> exit 2", rc == 2)

print("\n6. B (28 Oct): validity by chain, and the chain fallback")


def b_call(case, phase, chain, served, ordinal_models, ok=True):
    att = [{"ordinal": i, "model": name(m), "outcome": "ok" if i == len(ordinal_models) - 1 else "timeout",
            "duration_ms": 1000, "error": None} for i, m in enumerate(ordinal_models)]
    req = {"id": 1, "status": "success" if ok else "error", "attempts": att} if ordinal_models else None
    return {"case": case, "phase": phase, "attempt": 1, "chain": chain, "served": served, "latency_s": 1.0,
            "ok": ok, "req": req}


good = [b_call("N15_r1", "Researcher (round 1)", "auto:long", name(DOTS), [DOTS]),
        b_call("N15_r1", "Document Builder", "auto:arabic", name(G35), [G35]),
        b_call("N15_r1", "Document Builder", "auto:arabic", name(G36), [G36])]
v = router_facts.validity(good)
check("arabic Builder on Gemini 3.5 or 3.6 at ordinal 0: valid", v == ["  N15_r1: valid (3 long calls)"], v)
check("the long-chain line names the arabic chain",
      router_facts.long_line(good[1]) == "  N15_r1 Document Builder (auto:arabic): google/gemini-3.5-flash at ordinal 0",
      router_facts.long_line(good[1]))
v = router_facts.validity([b_call("N15_r1", "Document Builder", "auto:arabic", name(DOTS), [DOTS])])
check("arabic Builder served by Dots3: not valid", v[0].startswith("  N15_r1: NOT VALID: Document Builder "
                                                                   "openrouter/dots3:free ordinal 0"), v)
v = router_facts.validity([b_call("N15_r1", "Document Builder", "auto:arabic", name(G36), [G35, G36])])
check("arabic Builder on Gemini 3.6 after a 3.5 timeout (ordinal 1): not valid", "ordinal 1" in v[0], v)
fell = [b_call("N15_r2", "Researcher (round 1)", "auto:long", name(DOTS), [DOTS]),
        b_call("N15_r2", "Document Builder", "auto:long", name(DOTS), [DOTS]),
        b_call("N15_r2", "Document Builder", "auto:arabic", None, [], ok=False)]
v = router_facts.validity(fell)
check("chain fallback: NOT VALID for judging B, even with Dots3 at ordinal 0",
      "chain fallback auto:arabic -> auto:long (not valid for judging B)" in v[0] and "NOT VALID" in v[0], v)
check("an English case on auto:long is unchanged (Dots3 at ordinal 0: valid)",
      router_facts.validity(good[:1]) == ["  N15_r1: valid (1 long calls)"])

print("\n7. Timestamp windows and router refusals (143500 pattern)")
con = sqlite3.connect(db)
new_run = TMP / "20261030-143500"
base = utc_ms("2026-10-30 10:35:00")
expected = []
for case_no, case in enumerate(("N15", "N16")):
    offset = case_no * 120
    phases = []
    # Builder 2 and its failure appear before Prose QA 1 in the log.
    specs = [("Document Builder", 0, G35, 10, True, None),
             ("Document Builder", 30, G35, 10, True, None),
             ("Document Builder", 60, None, .02, False, 429),
             ("Document Builder", 65, None, 1.5, False, 502),
             ("Prose QA (round 1)", 15, CEREBRAS, 1.5, True, None),
             ("Prose QA (round 2)", 45, CEREBRAS, 1.5, True, None),
             ("Document Builder", 75, None, .3, False, 429)]
    ids = []
    for ph, sec, model, latency, success, status in specs:
        stamp = int(base + (offset + sec) * 1000)
        a = {"attempt": len(phases) + 1, "chain": "auto:arabic", "latency_s": latency,
             "ok": success, "sent_at_ms": stamp}
        if model:
            a["routed_via"] = name(model)
        if status:
            a["http_status"] = status
        if status == 429:
            a["problem"] = ("HTTP 429: All models exhausted: 2 routes checked "
                            "(2 rate-limited or on cooldown)" if latency == .02 else
                            "HTTP 429: All models rate-limited after 1 attempt")
        phases.append({"name": ph, "calls": [{"attempts": [a]}]})
        rid = None
        if status != 429 or latency == .3:
            m = model or G35
            rid = request(router_db.utc_text(stamp + latency * 1000), m,
                          "success" if success else "error", int(latency * 1000),
                          [(m, "ok" if success else "error", int(latency * 1000), None)])
        ids.append(rid)
    expected.extend(ids)
    folder = new_run / case
    folder.mkdir(parents=True)
    log = folder / "phase_log.json"
    log.write_text(json.dumps({"phases": phases}))
    os.utime(log, ((base / 1000 + offset + 90),) * 2)
con.commit()
con.close()
text = router_facts.facts(new_run, db, base + 300000)
calls = router_facts.client_calls(new_run)
with router_db.connect_ro(db) as ro:
    reqs = router_facts.requests_in(ro, base - 1000, base + 300000)
router_facts.match(calls, reqs)
check("out-of-order calls in both cases get exactly their own rows",
      [c["req"]["id"] if c["req"] else None for c in calls] == expected)
check("fast refusals are explicit, never NOT MATCHED",
      text.count("refused by the router (no row expected)") == 2 and "NOT MATCHED" not in text
      and "Client calls not matched in the router: none" in text)
check("refusals still fail validity", "attempt 3 failed at the client" in text)
check("502 at 1.5 seconds still matches an error row", calls[3]["req"]["id"] == expected[3])
check("fast provider 429 matches its error row and is never shown as refused",
      calls[6]["req"] is not None and calls[6]["req"]["id"] == expected[6]
      and "refused by the router" not in router_facts.long_line(calls[6])
      and calls[13]["req"] is not None and calls[13]["req"]["id"] == expected[13]
      and "refused by the router" not in router_facts.long_line(calls[13]))
check("exhausted wording decides refusal even when latency exceeds one second",
      router_facts.refused(dict(calls[2], latency_s=2.0)))
check("stamped matching line", "Matching: by time window" in text)
# Strip all stamps: a refusal before a real failure must not steal that failure's row.
legacy = [dict(calls[2], req=None), dict(calls[3], req=None)]
for c in legacy:
    c.pop("sent_at_ms")
for r in reqs:
    r["call"] = None
router_facts.match(legacy, reqs)
check("unstamped refusal leaves the real error row for the following call",
      legacy[0]["req"] is None and legacy[1]["req"] is not None)
check("unstamped matching line", "Matching: best effort (this run's attempts have no timestamps)"
      in router_facts.facts(run, db, NOW))
log = new_run / "N15" / "phase_log.json"
data = json.loads(log.read_text())
del data["phases"][0]["calls"][0]["attempts"][0]["sent_at_ms"]
log.write_text(json.dumps(data))
text = router_facts.facts(new_run, db, base + 300000)
check("mixed matching line and all remaining calls matched", "Matching: mixed" in text
      and "Client calls not matched in the router: none" in text)

shutil.rmtree(TMP, ignore_errors=True)
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
