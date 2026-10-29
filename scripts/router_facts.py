"""Router facts for a live sitting, read from the router's own database (read-only, standard library only).

    python3 -m scripts.router_facts runs/eval_set/<run>   # writes <run>/router_facts.txt and prints it
    python3 -m scripts.router_facts --now                 # cooldowns, 24 h counts and capacity right now

Runs on Haris's Mac (the database is ~/Projects/freellmapi/server/data/freeapi.db, or MANSHA_ROUTER_DB).
Lets the cloud session judge each run's validity (every Researcher/Builder call on the expected model at
ordinal 0) without a look at the Mac. Only named columns are selected; the connection refuses settings and
api_keys (scripts/router_db.py, problem 84). Never opens any .env.

Window: from the run folder's name (Mac local time, when the sitting started) to the newest phase_log.json /
summary.json in it, padded PAD_S each side; requests.created_at is UTC text written when the router's attempt
ladder finishes. Calls are matched to cases in time order by served model and latency; a call that can't be
matched is listed as unmatched, never guessed.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

from scripts.router_db import (
    CHAINS,
    DAY_MS,
    ROUTER_DB,
    chain_capacity,
    connect_ro,
    utc_text,
)

PAD_S = 300
OUT_NAME = "router_facts.txt"
# R1 (27 Oct): the long chain is Dots3 (OpenRouter), Gemini 3.6, Gemini 3.5. A run is valid only when every
# Researcher and Builder call was served by OpenRouter at ordinal 0 (a Dots3 timeout or bench sends it to Gemini).
EXPECTED_LONG_PLATFORM = "openrouter"
# B (28 Oct): Arabic Builder calls ask auto:arabic (Gemini 3.5 / 3.6 Flash; the router's global order picks
# which). Valid there = a Gemini model at ordinal 0. A Builder call that fell back in code to auto:long makes
# the case NOT VALID for judging B, whatever served it.
EXPECTED_SERVING = {"auto:long": EXPECTED_LONG_PLATFORM + "/", "auto:arabic": "google/gemini-"}
LONG_PHASES = ("Researcher", "Document Builder")
SUCCESS = ("success", "ok")
MATCH_ABS_S, MATCH_REL = 2.0, 0.10      # router latency vs the client's: within max(2 s, 10 %)
LOOKAHEAD = 12                          # router requests searched ahead of the last match
CEREBRAS_PRICE = (0.35, 0.75)           # $ per 1M input / output tokens (estimate)
TOKEN_COLUMNS = (("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens"))


def hms(text: str) -> str:
    return text[11:19] if text and len(text) >= 19 else str(text)


def short(text, n: int = 90) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------- the run folder ----------

def run_window(run: Path) -> tuple[float, float]:
    """(start_ms, end_ms), padded: the folder name is Mac local time; the end is the newest log file."""
    start = time.mktime(time.strptime(run.name, "%Y%m%d-%H%M%S")) * 1000
    logs = [f for pat in ("*/phase_log.json", "summary.json") for f in run.glob(pat)]
    end = max([f.stat().st_mtime * 1000 for f in logs] or [start])
    return start - PAD_S * 1000, end + PAD_S * 1000


def client_calls(run: Path) -> list[dict]:
    """Every client attempt of every case, cases in the order they finished."""
    cases = sorted(run.glob("*/phase_log.json"), key=lambda f: f.stat().st_mtime)
    out = []
    for log in cases:
        data = json.loads(log.read_text(encoding="utf-8"))
        for phase in data.get("phases", []):
            for call in phase.get("calls", []):
                for a in call.get("attempts", []):
                    out.append({"case": log.parent.name, "phase": phase.get("name", "?"),
                                "attempt": a.get("attempt"), "chain": a.get("chain"),
                                "served": a.get("routed_via"), "latency_s": a.get("latency_s"),
                                "ok": bool(a.get("ok")), "req": None})
    return out


# ---------- the router database ----------

def requests_in(con: sqlite3.Connection, start_ms: float, end_ms: float) -> list[dict]:
    rows = con.execute(
        "SELECT id, created_at, platform, model_id, status, latency_ms FROM requests "
        "WHERE created_at >= ? AND created_at <= ? ORDER BY id", (utc_text(start_ms), utc_text(end_ms))).fetchall()
    reqs = [{"id": r[0], "created_at": r[1], "model": f"{r[2]}/{r[3]}", "status": r[4], "latency_ms": r[5],
             "attempts": [], "call": None} for r in rows]
    if reqs:
        by_id = {r["id"]: r for r in reqs}
        for rid, ordinal, pl, mid, outcome, dur, err in con.execute(
                "SELECT request_id, ordinal, platform, model_id, outcome, duration_ms, error_summary "
                "FROM request_attempts WHERE request_id >= ? AND request_id <= ? ORDER BY request_id, ordinal",
                (reqs[0]["id"], reqs[-1]["id"])):
            if rid in by_id:
                by_id[rid]["attempts"].append({"ordinal": ordinal, "model": f"{pl}/{mid}", "outcome": outcome,
                                               "duration_ms": dur, "error": err})
    return reqs


def serving(req: dict) -> dict | None:
    """The attempt that served a successful request: the last one in its ladder (whatever requests.model_id
    holds, the served model is read from the attempts)."""
    if req["status"] not in SUCCESS or not req["attempts"]:
        return None
    return req["attempts"][-1]


def close(req: dict, call: dict) -> bool:
    if req["latency_ms"] is None or call["latency_s"] is None:
        return False
    r, c = req["latency_ms"] / 1000, float(call["latency_s"])
    return abs(r - c) <= max(MATCH_ABS_S, MATCH_REL * c)


def match(calls: list[dict], reqs: list[dict]) -> None:
    """Pair each client attempt with the next router request on the same served model and latency."""
    i = 0
    for call in calls:
        for j in range(i, min(i + LOOKAHEAD, len(reqs))):
            req = reqs[j]
            if req["call"] is not None or not close(req, call):
                continue
            s = serving(req)
            same = (s is not None and s["model"] == call["served"]) if call["ok"] \
                else req["status"] not in SUCCESS
            if same:
                req["call"], call["req"] = call, req
                i = j + 1
                break


def label(call: dict) -> str:
    return f"{call['case']} {call['phase']} attempt {call['attempt']}"


def long_line(call: dict) -> str:
    req = call["req"]
    if req is None:
        return f"  {call['case']} {call['phase']}: served {call['served']} (client), NOT MATCHED in the router"
    s = serving(req)
    if s is None:
        return f"  {call['case']} {call['phase']}: router request #{req['id']} {req['status']} (no serving attempt)"
    before = [f"{a['model']} {a['outcome']} {(a['duration_ms'] or 0) / 1000:.1f} s"
              for a in req["attempts"] if a["ordinal"] < s["ordinal"]]
    chain = f" ({call['chain']})" if call["chain"] in EXPECTED_SERVING and call["chain"] != "auto:long" else ""
    return (f"  {call['case']} {call['phase']}{chain}: {s['model']} at ordinal {s['ordinal']}"
            + (f" (after {'; '.join(before)})" if before else ""))


def is_long(call: dict) -> bool:
    return call["phase"].startswith(LONG_PHASES)


def validity(calls: list[dict]) -> list[str]:
    out, cases = [], list(dict.fromkeys(c["case"] for c in calls))
    for case in cases:
        bad = []
        for call in (c for c in calls if c["case"] == case and is_long(c) and c["ok"]):
            s = serving(call["req"]) if call["req"] else None
            if s is None:
                bad.append(f"{call['phase']} not matched")
            elif not (s["model"].startswith(EXPECTED_SERVING.get(call["chain"], EXPECTED_LONG_PLATFORM + "/"))
                      and s["ordinal"] == 0):
                bad.append(f"{call['phase']} {s['model']} ordinal {s['ordinal']}")
        builder = {c["chain"] for c in calls if c["case"] == case and c["phase"].startswith("Document Builder")}
        if "auto:arabic" in builder and "auto:long" in builder:
            bad.append("chain fallback auto:arabic -> auto:long (not valid for judging B)")
        failed = [c for c in calls if c["case"] == case and is_long(c) and not c["ok"]]
        bad += [f"{c['phase']} attempt {c['attempt']} failed at the client" for c in failed]
        n = sum(1 for c in calls if c["case"] == case and is_long(c))
        out.append(f"  {case}: " + ("valid" if not bad else "NOT VALID: " + "; ".join(bad))
                   + f" ({n} long calls)")
    return out


# ---------- sections ----------

def section_requests(reqs: list[dict]) -> list[str]:
    out = [f"a) Router requests in the window ({len(reqs)})"]
    for r in reqs:
        who = f"  <- {label(r['call'])}" if r["call"] else "  <- not matched to a case"
        out.append(f"  #{r['id']} {hms(r['created_at'])} {r['model']} {r['status']} {r['latency_ms']} ms{who}")
        for a in r["attempts"]:
            err = f'  "{short(a["error"])}"' if a["error"] else ""
            out.append(f"      {a['ordinal']} {a['model']} {a['outcome']} {a['duration_ms']} ms{err}")
    return out


def section_platforms(calls: list[dict], reqs: list[dict]) -> list[str]:
    out = ["b) Per platform (attempts in the window, by outcome)"]
    plats: dict[str, dict[str, int]] = {}
    for r in reqs:
        for a in r["attempts"]:
            d = plats.setdefault(a["model"].split("/", 1)[0], {})
            d[a["outcome"]] = d.get(a["outcome"], 0) + 1
    for pl, d in sorted(plats.items()):
        out.append(f"  {pl}: {sum(d.values())} attempts (" + ", ".join(f"{k} {v}" for k, v in sorted(d.items())) + ")")
    bad = [r for r in reqs if r["status"] not in SUCCESS]
    out.append("  non-success requests: " + (", ".join(f"#{r['id']} {r['model']} {r['status']}" for r in bad) or "none"))
    out += ["", "  Long-chain calls (Researcher / Builder): served model at the serving attempt's ordinal"]
    out += [long_line(c) for c in calls if is_long(c)] or ["  none"]
    out += ["", (f"  Validity (every Researcher/Builder call at ordinal 0 on {EXPECTED_LONG_PLATFORM} (auto:long) "
                "or Gemini (auto:arabic); no chain fallback)")]
    out += validity(calls) or ["  no cases"]
    lost = [c for c in calls if c["req"] is None]
    out += ["", "  Client calls not matched in the router: " + (", ".join(label(c) for c in lost) or "none")]
    return out


def section_cooldowns(con: sqlite3.Connection, start_ms: float, end_ms: float) -> list[str]:
    rows = con.execute(
        "SELECT platform, model_id, set_at_ms, expires_at_ms, source FROM rate_limit_cooldowns "
        "WHERE (set_at_ms BETWEEN ? AND ?) OR (expires_at_ms BETWEEN ? AND ?) ORDER BY set_at_ms",
        (start_ms, end_ms, start_ms, end_ms)).fetchall()
    out = [f"c) Cooldowns set or expiring in the window ({len(rows)})"]
    for pl, mid, s, e, src in rows:
        out.append(f"  {pl}/{mid}: set {hms(utc_text(s))}, expires {hms(utc_text(e))} "
                   f"({(e - s) / 1000:.0f} s, {src})")
    return out


def token_columns(con: sqlite3.Connection) -> tuple[str | None, str | None, list[str]]:
    names = [r[1] for r in con.execute("PRAGMA table_info(requests)")]
    pick = [next((c for c in opts if c in names), None) for opts in TOKEN_COLUMNS]
    return pick[0], pick[1], names


def section_now(con: sqlite3.Connection, db: Path, now_ms: float, window: tuple[float, float] | None) -> list[str]:
    out = [f"d) Router state at {utc_text(now_ms)} UTC"]
    rows = con.execute("SELECT platform, model_id, expires_at_ms, source FROM rate_limit_cooldowns "
                       "WHERE expires_at_ms > ? ORDER BY expires_at_ms", (now_ms,)).fetchall()
    out.append("  active cooldowns: " + ("; ".join(
        f"{pl}/{mid} {(e - now_ms) / 60000:.1f} min left ({src})" for pl, mid, e, src in rows) or "none"))
    cap = chain_capacity(db, now_ms)
    out.append("  capacity (router 24 h successes = rate_limit_usage; OpenRouter :free used = max with UTC-day attempts):")
    for ch in CHAINS:
        for m in cap[ch]:
            rpd = m["rpd"] if m["rpd"] is not None else "no cap"
            left = "unlimited" if m["rpd"] is None else max(m["rpd"] - m["used"], 0)
            if m.get("benched_min"):
                left = f"0 (benched {m['benched_min']:g} min, {m['bench_source']})"
            day = f", UTC-day attempts {m['day_attempts']}" if m.get("day_attempts") is not None else ""
            out.append(f"    {ch:5} {m['model']}: router 24 h {m['router_used']}{day}; used {m['used']}/{rpd}; left {left}")
    day_start = utc_text(now_ms)[:10] + " 00:00:00"
    rows = con.execute(
        "SELECT a.model_id, a.outcome, COUNT(*) FROM request_attempts a JOIN requests r ON r.id = a.request_id "
        "WHERE a.platform = 'openrouter' AND r.created_at >= ? GROUP BY a.model_id, a.outcome", (day_start,)).fetchall()
    per: dict[str, dict[str, int]] = {}
    for mid, oc, n in rows:
        per.setdefault(mid, {})[oc] = n
    out.append("  OpenRouter attempts since 00:00 UTC (04:00 Dubai): " + ("; ".join(
        f"{mid} {sum(d.values())} (" + ", ".join(f"{k} {v}" for k, v in sorted(d.items())) + ")"
        for mid, d in sorted(per.items())) or "none"))
    if window:
        rows = con.execute(
            "SELECT r.id, r.created_at, a.model_id, a.duration_ms FROM request_attempts a "
            "JOIN requests r ON r.id = a.request_id WHERE a.platform = 'openrouter' AND a.outcome = 'timeout' "
            "AND r.created_at >= ? AND r.created_at <= ? ORDER BY r.id",
            (utc_text(window[0]), utc_text(window[1]))).fetchall()
        out.append("  OpenRouter timeouts in the window: " + ("; ".join(
            f"#{rid} {hms(ts)} {mid} {(d or 0) / 1000:.1f} s" for rid, ts, mid, d in rows) or "none"))
    tin, tout, names = token_columns(con)
    if tin and tout:
        n, a, b = con.execute(f"SELECT COUNT(*), COALESCE(SUM({tin}), 0), COALESCE(SUM({tout}), 0) FROM requests "
                              "WHERE platform = 'cerebras' AND created_at >= ?", (utc_text(now_ms - DAY_MS),)).fetchone()
        cost = a / 1e6 * CEREBRAS_PRICE[0] + b / 1e6 * CEREBRAS_PRICE[1]
        out.append(f"  Cerebras last 24 h: {n} requests, {a} input + {b} output tokens, "
                   f"about ${cost:.2f} at ${CEREBRAS_PRICE[0]}/${CEREBRAS_PRICE[1]} per 1M")
    else:
        out.append(f"  Cerebras tokens: token columns not found in requests ({', '.join(names)})")
    return out


def section_chains(db: Path, now_ms: float) -> list[str]:
    cap = chain_capacity(db, now_ms)
    out = ["e) Chains (enabled models, order as stored; rpd_limit with overrides)"]
    for ch in CHAINS:
        out.append(f"  {ch}: " + (", ".join(
            f"{m['model']} (rpd {m['rpd'] if m['rpd'] is not None else 'no cap'})" for m in cap[ch]) or "none"))
    return out


def guarded(name: str, fn, *args) -> list[str]:
    """One section; a schema surprise prints the error instead of stopping the others."""
    try:
        return fn(*args)
    except sqlite3.Error as exc:
        return [f"{name}) cannot read: {exc}"]


def facts(run: Path | None, db: Path | None = None, now_ms: float | None = None) -> str:
    db, now_ms = Path(db or ROUTER_DB), now_ms or time.time() * 1000
    con = connect_ro(db)
    try:
        lines = [(f"Router facts ({'run ' + str(run) if run else 'now'}), read-only from {db.name} "
                 "(settings and api_keys refused)")]
        window = None
        if run is not None:
            window = run_window(run)
            lines.append(f"Window (UTC): {utc_text(window[0])} to {utc_text(window[1])} "
                         f"(folder start and last log file, padded {PAD_S // 60} min)")
            calls = client_calls(run)
            reqs = requests_in(con, *window)
            match(calls, reqs)
            lines += [""] + section_requests(reqs) + [""] + section_platforms(calls, reqs) + [""]
            lines += guarded("c", section_cooldowns, con, *window)
        lines += [""] + guarded("d", section_now, con, db, now_ms, window)
        lines += [""] + guarded("e", section_chains, db, now_ms)
    finally:
        con.close()
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run", nargs="?", help="runs/eval_set/<run>")
    ap.add_argument("--now", action="store_true", help="router state now (no run folder)")
    ap.add_argument("--db", default=None, help="router database (default: MANSHA_ROUTER_DB or freellmapi's)")
    a = ap.parse_args(argv)
    if bool(a.run) == a.now:
        ap.error("give a run folder or --now")
    run = Path(a.run) if a.run else None
    if run is not None and not run.is_dir():
        print(f"no such run folder: {run}")
        return 2
    try:
        text = facts(run, a.db)
    except sqlite3.Error as exc:
        print(f"cannot read the router database: {exc}")
        return 2
    if run is not None:
        (run / OUT_NAME).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
