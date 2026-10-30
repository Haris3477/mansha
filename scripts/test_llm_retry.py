"""Offline tests for the wait-before-retry logic in mansha.llm_client (Steps 8.6, 8.6b, 9.5b).

No router, no real waiting: a fake client replays scripted replies, and the clock and
sleep are replaced. Run: python -m scripts.test_llm_retry
"""

import sys
import urllib.error
from types import SimpleNamespace

from openai import APIStatusError

import mansha.llm_client as lc

NOW = 1_800_000_000.0          # fake clock start (seconds)
failures: list[str] = []
slept: list[float] = []
clock = {"t": NOW, "advance": False}   # the clock moves only in the budget tests


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def http_error(status: int, body: dict | None = None, headers: dict | None = None) -> APIStatusError:
    response = SimpleNamespace(status_code=status, request=None, headers=headers or {})
    return APIStatusError(f"Error code: {status}", response=response, body=body)


def busy_429(seconds_from_now: float) -> APIStatusError:
    """The router's real 429 shape (seen 15 Oct); the SDK passes the inner "error" object as body."""
    return http_error(429, {"message": "All models exhausted: 4 routes checked (4 rate-limited or on "
                                       "cooldown). Soonest reset ~25s.",
                            "type": "rate_limit_error", "code": "rate_limit_exceeded",
                            "retryAtMs": int((NOW + seconds_from_now) * 1000)})


def ok_reply(text: str = "OK"):
    resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
        usage=None)
    return SimpleNamespace(headers={"x-routed-via": "fake/model"}, parse=lambda: resp)


class FakeClient:
    """Mimics client.chat.completions.with_raw_response.create(...).

    call_s: seconds each call takes on the fake clock (budget tests only).
    """

    def __init__(self, *replies, call_s: float = 0.0):
        self.replies, self.calls, self.call_s = list(replies), 0, call_s
        self.chat = SimpleNamespace(completions=SimpleNamespace(
            with_raw_response=SimpleNamespace(create=self._create)))

    def _create(self, **kwargs):
        self.calls += 1
        if clock["advance"]:
            clock["t"] += self.call_s
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def run(*replies, call_s: float = 0.0, chain: str = "auto:long"):
    """Call call_llm against scripted replies. Returns (result or error, fake client, waits)."""
    slept.clear()
    clock["t"] = NOW
    fake = FakeClient(*replies, call_s=call_s)
    lc._client = fake
    try:
        out = lc.call_llm("test", chain, [{"role": "user", "content": "hi"}])
    except lc.LLMCallError as e:
        out = e
    check("every attempt has an integer send timestamp",
          all(type(a.get("sent_at_ms")) is int for a in out.attempts))
    return out, fake, list(slept)


def fake_sleep(s: float) -> None:
    slept.append(s)
    if clock["advance"]:
        clock["t"] += s


lc._sleep = fake_sleep
lc._now = lambda: clock["t"]

print("\n1. Reading the router's hint")
check("retryAtMs 25 s ahead -> 26 s (with the 1 s margin)",
      abs(lc._router_wait_hint(busy_429(25)) - 26.0) < 1e-6, lc._router_wait_hint(busy_429(25)))
check("retryAtMs already past -> just the margin",
      abs(lc._router_wait_hint(busy_429(-5)) - lc.WAIT_MARGIN_S) < 1e-6)
nested = http_error(429, {"error": {"retryAtMs": int((NOW + 10) * 1000)}})
check("outer {'error': {...}} body also read", abs(lc._router_wait_hint(nested) - 11.0) < 1e-6)
check("Retry-After header used when there is no retryAtMs",
      lc._router_wait_hint(http_error(429, {}, {"retry-after": "7"})) == 7.0)
check("no hint -> None", lc._router_wait_hint(http_error(502, {"message": "upstream_failed"})) is None)
check("non-numeric retryAtMs ignored", lc._router_wait_hint(http_error(429, {"retryAtMs": "soon"})) is None)

print("\n2. Waiting before the retry")
out, fake, waits = run(busy_429(25), ok_reply())
check("429 then OK: succeeds on the retry", isinstance(out, lc.LLMResult) and fake.calls == 2)
check("429: waited until the router's reset (26 s)", waits == [26.0], waits)
check("429: wait recorded on attempt 1 for the phase log",
      isinstance(out, lc.LLMResult) and out.attempts[0].get("waited_before_retry_s") == 26.0)
check("429: HTTP status recorded", isinstance(out, lc.LLMResult) and out.attempts[0].get("http_status") == 429)

out, fake, waits = run(http_error(502, {"message": "upstream_failed: 503 overloaded"}), ok_reply())
check(f"502 overload: fixed {lc.UPSTREAM_WAIT_S} s wait, then OK",
      waits == [lc.UPSTREAM_WAIT_S] and isinstance(out, lc.LLMResult), waits)

out, fake, waits = run(http_error(429, {"message": "rate limited"}), ok_reply())
check("429 without a time hint: fixed wait", waits == [lc.UPSTREAM_WAIT_S], waits)

out, fake, waits = run(busy_429(lc.RETRY_WAIT_CAP_S + 60), ok_reply())
check("cooldown longer than the cap: no retry, fails at once",
      isinstance(out, lc.LLMCallError) and fake.calls == 1 and waits == [], (fake.calls, waits))
check("cap failure says why", isinstance(out, lc.LLMCallError) and "cap" in str(out))

out, fake, waits = run(busy_429(lc.RETRY_WAIT_CAP_S - 2), ok_reply())
check("cooldown just under the cap: waits and retries", fake.calls == 2 and len(waits) == 1, waits)

out, fake, waits = run(http_error(400, {"message": "bad request"}), ok_reply())
check("400 (our request's fault): retries at once, no wait", waits == [] and fake.calls == 2, waits)

out, fake, waits = run(ok_reply(""), ok_reply())
check("non-HTTP failure (empty reply): retries at once, no wait", waits == [] and fake.calls == 2, waits)

out, fake, waits = run(ok_reply())
check("first attempt OK: no wait", waits == [] and fake.calls == 1)

print("\n3. Cooldown replies do not use up the retry (8.6b)")
out, fake, waits = run(busy_429(25), ok_reply())
check("cooldown reply is marked, and counts as no model attempt",
      isinstance(out, lc.LLMResult) and out.attempts[0].get("cooldown") is True)

out, fake, waits = run(http_error(502, {"message": "timeout"}), busy_429(30), ok_reply())
check("16 Oct pattern: 502 -> wait 30 s -> cooldown -> wait it out -> OK",
      isinstance(out, lc.LLMResult) and fake.calls == 3 and waits == [30.0, 31.0], (fake.calls, waits))

out, fake, waits = run(http_error(502, {"message": "timeout"}), busy_429(30),
                       http_error(502, {"message": "timeout"}), ok_reply())
check("502, cooldown, 502, OK: the busy budget allows a third model attempt (9.5b)",
      isinstance(out, lc.LLMResult) and fake.calls == 4 and waits == [30.0, 31.0, 30.0], (fake.calls, waits))

out, fake, waits = run(busy_429(10), busy_429(10), busy_429(10), ok_reply())
check(f"cooldown waits stop after {lc.MAX_COOLDOWN_WAITS}",
      isinstance(out, lc.LLMCallError) and fake.calls == lc.MAX_COOLDOWN_WAITS + 1
      and waits == [11.0] * lc.MAX_COOLDOWN_WAITS, (fake.calls, waits))
check("error message counts model attempts and cooldown waits",
      isinstance(out, lc.LLMCallError) and "0 model attempt(s)" in str(out)
      and f"{lc.MAX_COOLDOWN_WAITS} cooldown wait(s)" in str(out), str(out)[:120])

out, fake, waits = run(ok_reply(""), ok_reply(""), ok_reply())
check("two failures on our side (empty replies): no third call",
      isinstance(out, lc.LLMCallError) and fake.calls == 2)

out, fake, waits = run(busy_429(10), http_error(502, {"message": "x"}), busy_429(10), ok_reply())
check("cooldown, 502, cooldown, OK: retry still available after cooldowns",
      isinstance(out, lc.LLMResult) and fake.calls == 4 and waits == [11.0, 30.0, 11.0], (fake.calls, waits))

out, fake, waits = run(*[http_error(429, {"message": "rate limited"})] * lc.MAX_BUSY_ATTEMPTS, ok_reply())
check(f"429 without a time hint counts as a busy model attempt ({lc.MAX_BUSY_ATTEMPTS} calls max)",
      isinstance(out, lc.LLMCallError) and fake.calls == lc.MAX_BUSY_ATTEMPTS, fake.calls)

print("\n4. Busy budget (9.5b): provider outages get more attempts, our own failures do not")
E502 = http_error(502, {"message": "upstream_failed: Google API error 503"})
out, fake, waits = run(E502, E502, E502, ok_reply())
check("16 Oct 17:46 pattern: 502, 502, 502, OK -> succeeds on the 4th model attempt",
      isinstance(out, lc.LLMResult) and fake.calls == 4 and waits == [lc.UPSTREAM_WAIT_S] * 3,
      (fake.calls, waits))
out, fake, waits = run(*[E502] * (lc.MAX_BUSY_ATTEMPTS + 1))
check(f"busy every time: stops after {lc.MAX_BUSY_ATTEMPTS} model attempts",
      isinstance(out, lc.LLMCallError) and fake.calls == lc.MAX_BUSY_ATTEMPTS, fake.calls)
out, fake, waits = run(ok_reply(""), E502, ok_reply())
check("own failure, then busy, then OK: allowed (one own retry, busy ones extra)",
      isinstance(out, lc.LLMResult) and fake.calls == 3, fake.calls)
out, fake, waits = run(E502, ok_reply(""), ok_reply(""), ok_reply())
check("busy, then two own failures: stops after the second own failure",
      isinstance(out, lc.LLMCallError) and fake.calls == 3, fake.calls)

clock["advance"] = True
out, fake, waits = run(E502, E502, E502, ok_reply(), call_s=70)
check(f"slow outage (70 s per attempt): stops when the next try would pass {lc.CALL_BUDGET_S}s",
      isinstance(out, lc.LLMCallError) and fake.calls == 3, (fake.calls, waits))
check("budget failure says why and is recorded on the attempt",
      isinstance(out, lc.LLMCallError) and "call budget" in str(out)
      and "call budget" in out.attempts[-1].get("retry_skipped", ""), str(out)[:120])
out, fake, waits = run(E502, ok_reply(), call_s=70)
check("within the budget: retries normally", isinstance(out, lc.LLMResult) and fake.calls == 2)
clock["advance"] = False

print("\n5. Truncated judge answer: the retry gets double the room (P1, fix round 26 Oct)")


def truncated_reply():
    resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"cut'), finish_reason="length")],
        usage=None)
    return SimpleNamespace(headers={"x-routed-via": "fake/model"}, parse=lambda: resp)


sent_max: list[int] = []
fake = FakeClient(truncated_reply(), ok_reply('{"ok": 1}'))
create = fake._create
fake.chat.completions.with_raw_response.create = lambda **kw: (sent_max.append(kw["max_tokens"]), create(**kw))[1]
lc._client = fake
try:
    out = lc.call_llm("qa", "auto:judge", [{"role": "user", "content": "hi"}], expect_json=True)
except lc.LLMCallError as e:
    out = e
check("judge ceiling is above its default", lc.CHAIN_LIMITS["auto:judge"]["ceiling"] > lc.CHAIN_LIMITS["auto:judge"]["default"])
check("first try 3000, retry after truncation 6000", sent_max == [3000, 6000], sent_max)
check("the retry's answer is used", isinstance(out, lc.LLMResult) and fake.calls == 2, out)

lc._client = None

print("\n6. Fast failover on auto:arabic (router 502 after one Gemini's 503, 015311 r2)")
ROUTER_502 = ("All 1 routed attempt(s) failed with upstream provider errors (upstream_error x1). Last error: "
              "Google API error 503: This model is currently experiencing high demand.")
out, fake, waits = run(http_error(502, {"message": ROUTER_502}), ok_reply(), chain="auto:arabic")
check("arabic 502 then OK: the retry's answer is used", isinstance(out, lc.LLMResult) and fake.calls == 2, out)
check("arabic 502: waits 3 s, not 30 s", waits == [lc.FAST_FAILOVER_WAIT_S["auto:arabic"]] == [3.0], waits)
check("arabic 502: the 3 s is recorded for the phase log",
      isinstance(out, lc.LLMResult) and out.attempts[0].get("waited_before_retry_s") == 3.0, out)
out, fake, waits = run(http_error(502, {"message": ROUTER_502}), ok_reply())
check("long 502: still waits 30 s", waits == [lc.UPSTREAM_WAIT_S] == [30], waits)
out, fake, waits = run(http_error(503, {"message": "x"}), ok_reply(), chain="auto:arabic")
check("arabic 503 (not the router's 502): still 30 s", waits == [lc.UPSTREAM_WAIT_S], waits)
out, fake, waits = run(busy_429(25), ok_reply(), chain="auto:arabic")
check("arabic 429 with the router's time: that time wins (26 s)", waits == [26.0], waits)
out, fake, waits = run(*[http_error(502, {"message": ROUTER_502})] * lc.MAX_BUSY_ATTEMPTS, ok_reply(),
                       chain="auto:arabic")
check(f"both Geminis busy: stops after {lc.MAX_BUSY_ATTEMPTS} model attempts (LLMCallError -> code fallback)",
      isinstance(out, lc.LLMCallError) and fake.calls == lc.MAX_BUSY_ATTEMPTS
      and waits == [3.0] * (lc.MAX_BUSY_ATTEMPTS - 1), (type(out).__name__, fake.calls, waits))

print("\n7. Pre-flight: router_answering() (guard health check, 29 Oct)")


class FakeReply:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_for(outcome):
    seen = {}

    def opener(url, timeout):
        seen.update(url=url, timeout=timeout)
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeReply(outcome)
    return opener, seen


BASE = "http://localhost:3001/v1/"
op, seen = opener_for(200)
up, msg = lc.router_answering(BASE, opener=op)
check("200: up", up and "(200)" in msg, msg)
check("asks <base>/models (one slash) with the 5 s timeout",
      seen == {"url": "http://localhost:3001/v1/models", "timeout": lc.HEALTH_TIMEOUT_S}, seen)
op, _ = opener_for(urllib.error.HTTPError(BASE + "models", 401, "Unauthorized", {}, None))
up, msg = lc.router_answering(BASE, opener=op)
check("401 (asks for a key): up", up and "(401)" in msg, msg)
for status in (404, 503):
    op, _ = opener_for(urllib.error.HTTPError(BASE + "models", status, "x", {}, None))
    up, msg = lc.router_answering(BASE, opener=op)
    check(f"{status}: not ready, with the start hint", not up and str(status) in msg and "npm run dev" in msg, msg)
for name, err in (("connection refused", urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))),
                  ("timeout", TimeoutError("timed out"))):
    op, _ = opener_for(err)
    up, msg = lc.router_answering(BASE, opener=op)
    check(f"{name}: not answering, with the start hint", not up and "not answering" in msg
          and "npm run dev" in msg, msg)
real_load, real_env = lc.load_dotenv, lc.os.environ.pop("FREELLMAPI_BASE_URL", None)
lc.load_dotenv = lambda: None
try:
    up, msg = lc.router_answering(opener=opener_for(200)[0])
    check("no address set: not up (nothing sent)", not up and "FREELLMAPI_BASE_URL" in msg, msg)
finally:
    lc.load_dotenv = real_load
    if real_env is not None:
        lc.os.environ["FREELLMAPI_BASE_URL"] = real_env

print("\n8. Send timestamps follow pacing and retry waits; existing fields stay unchanged")
real_time, real_monotonic = lc.time.time, lc.time.monotonic
lc.time.time = lambda: clock["t"]
lc.time.monotonic = lambda: clock["t"]
clock["advance"] = True
lc._sent.clear()
try:
    out, fake, waits = run(http_error(502), ok_reply(), call_s=1.5)
    check("retry timestamp includes the request duration and retry wait",
          out.attempts[1]["sent_at_ms"] == out.attempts[0]["sent_at_ms"] + 31500)
    stripped = [{k: v for k, v in a.items() if k != "sent_at_ms"} for a in out.attempts]
    check("all existing attempt fields and values preserved", stripped == [
        {"attempt": 1, "chain": "auto:long", "max_tokens": 16000, "latency_s": 1.5,
         "ok": False, "http_status": 502, "problem": "HTTP 502: Error code: 502",
         "waited_before_retry_s": 30.0},
        {"attempt": 2, "chain": "auto:long", "max_tokens": 16000, "routed_via": "fake/model",
         "finish_reason": "stop", "latency_s": 1.5, "ok": True}], stripped)
    from collections import deque
    lc._sent["auto:judge"] = deque([NOW] * 4)
    out, fake, waits = run(ok_reply(), chain="auto:judge")
    check("timestamp is taken after pacing wait", out.attempts[0]["sent_at_ms"] == int((NOW + 61) * 1000)
          and out.attempts[0]["paced_wait_s"] == 61)
finally:
    lc.time.time, lc.time.monotonic = real_time, real_monotonic
    clock["advance"] = False
    lc._sent.clear()
    lc._client = None

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
