"""Offline tests for the wait-before-retry logic in mansha.llm_client (Steps 8.6, 8.6b, 9.5b).

No router, no real waiting: a fake client replays scripted replies, and the clock and
sleep are replaced. Run: python -m scripts.test_llm_retry
"""

import sys
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


def run(*replies, call_s: float = 0.0):
    """Call call_llm against scripted replies. Returns (result or error, fake client, waits)."""
    slept.clear()
    clock["t"] = NOW
    fake = FakeClient(*replies, call_s=call_s)
    lc._client = fake
    try:
        out = lc.call_llm("test", "auto:long", [{"role": "user", "content": "hi"}])
    except lc.LLMCallError as e:
        out = e
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

lc._client = None
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
