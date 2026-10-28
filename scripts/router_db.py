"""Read-only access to the router's database (freellmapi, server/data/freeapi.db), standard library only.

Shared by the budget guard (scripts/eval_set.py) and scripts/router_facts.py. Every connection is
opened read-only (mode=ro) with an authorizer that refuses any access to `settings` or `api_keys`
(problem 84: a broad query once printed the router key). Never open the router's .env.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

ROUTER_DB = Path(os.environ.get("MANSHA_ROUTER_DB",
                                Path.home() / "Projects/freellmapi/server/data/freeapi.db"))
CHAINS = ("long", "qa", "judge")
DAY_MS = 24 * 3600 * 1000
# Fix round 1b (26 Oct 21:59, N5 LLM_ERROR): OpenRouter counts EVERY request that reaches it (ok, error,
# timeout) per UTC day (resets 00:00 UTC = 04:00 Dubai), while rate_limit_usage holds the router's
# successes over a sliding 24 h. The guard showed Dots3 47/50 "3 left" when OpenRouter's count was 50.
# For OpenRouter :free models, used = max(router's sliding count, attempts since 00:00 UTC), read from
# request_attempts joined to requests (requests.created_at is SQLite datetime('now'), UTC text). Every
# outcome counts; a route the router skipped for a cooldown has no row, so it is never counted.
WARN_WINDOW_MS = 3600 * 1000


FORBIDDEN_TABLES = frozenset({"settings", "api_keys"})


def _authorizer(action, arg1, arg2, dbname, source):
    # SQLITE_READ: arg1 = table; SQLITE_PRAGMA: arg2 = the table a pragma names (e.g. table_info).
    if action == sqlite3.SQLITE_READ and (arg1 or "").lower() in FORBIDDEN_TABLES:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA and (arg2 or "").lower() in FORBIDDEN_TABLES:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def connect_ro(db: Path | str) -> sqlite3.Connection:
    """The router database, read-only, with settings/api_keys refused."""
    if not Path(db).exists():
        raise sqlite3.OperationalError(f"no such file: {db}")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.set_authorizer(_authorizer)
    return con


def utc_text(ms: float) -> str:
    """Epoch ms -> 'YYYY-MM-DD HH:MM:SS' in UTC, the format of requests.created_at."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ms / 1000))


def counts_attempts(platform: str, model_id: str) -> bool:
    return platform == "openrouter" and model_id.endswith(":free")


def chain_capacity(db: Path | None = None, now_ms: float | None = None) -> dict[str, list[dict]]:
    """Each chain's enabled models with their daily cap and the router's own sliding-24 h count
    (rate_limit_usage, the table the router enforces from); for OpenRouter :free models, also every
    attempt since 00:00 UTC (OpenRouter's own daily count), and each model's upstream errors in the
    last hour (a warning only). Read-only; selected columns only."""
    db, now_ms = db or ROUTER_DB, now_ms or time.time() * 1000
    con = connect_ro(db)
    try:
        rows = con.execute(
            "SELECT p.name, m.platform, m.model_id, m.rpd_limit FROM profiles p "
            "JOIN profile_models pm ON pm.profile_id = p.id JOIN models m ON m.id = pm.model_db_id "
            "WHERE pm.enabled = 1 AND m.enabled = 1 AND p.name IN (?, ?, ?)", CHAINS).fetchall()
        overrides = {(pl, mid): json.loads(o or "{}") for pl, mid, o in
                     con.execute("SELECT platform, model_id, overrides_json FROM model_overrides")}
        used = {(pl, mid): n for pl, mid, n in con.execute(
            "SELECT platform, model_id, COUNT(*) FROM rate_limit_usage WHERE kind = 'request' "
            "AND created_at_ms > ? GROUP BY platform, model_id", (now_ms - DAY_MS,))}
        # A model the router has benched (e.g. Google's project-wide daily quota, 24 Oct 19:22) has
        # nothing left until the bench expires, whatever its own request count says.
        benched = {(pl, mid): (exp, src) for pl, mid, exp, src in con.execute(
            "SELECT platform, model_id, MAX(expires_at_ms), source FROM rate_limit_cooldowns "
            "WHERE expires_at_ms > ? GROUP BY platform, model_id", (now_ms,))}
        day_start = utc_text(now_ms)[:10] + " 00:00:00"
        day_attempts = {(pl, mid): n for pl, mid, n in con.execute(
            "SELECT a.platform, a.model_id, COUNT(*) FROM request_attempts a JOIN requests r "
            "ON r.id = a.request_id WHERE r.created_at >= ? GROUP BY a.platform, a.model_id", (day_start,))}
        recent = {(pl, mid): (n, bad) for pl, mid, n, bad in con.execute(
            "SELECT a.platform, a.model_id, COUNT(*), SUM(a.outcome = 'upstream_error') FROM request_attempts a "
            "JOIN requests r ON r.id = a.request_id WHERE r.created_at >= ? GROUP BY a.platform, a.model_id",
            (utc_text(now_ms - WARN_WINDOW_MS),))}
    finally:
        con.close()
    out: dict[str, list[dict]] = {c: [] for c in CHAINS}
    for chain, pl, mid, rpd in rows:
        rpd = overrides.get((pl, mid), {}).get("rpdLimit", rpd)
        exp, src = benched.get((pl, mid), (None, None))
        # A provider's own daily quota is account- or project-wide (Google: one quota for the
        # project's models, 24 Oct 19:22), so its bench holds every model of that provider.
        pool = [e for (p2, _), (e, s2) in benched.items() if p2 == pl and s2 == "authoritative"]
        if pool and (exp is None or max(pool) > exp):
            exp, src = max(pool), "authoritative, provider-wide"
        router_used = used.get((pl, mid), 0)
        attempts = day_attempts.get((pl, mid), 0) if counts_attempts(pl, mid) else None
        n, bad = recent.get((pl, mid), (0, 0))
        out[chain].append({"model": f"{pl}/{mid}", "rpd": rpd,
                           "used": max(router_used, attempts or 0), "router_used": router_used,
                           "day_attempts": attempts,
                           "benched_min": round((exp - now_ms) / 60000, 1) if exp else None,
                           "bench_source": src,
                           "upstream_errors": (int(bad or 0), n)})
    return out
