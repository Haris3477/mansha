"""Offline tests for the wait-before-retry logic in mansha.llm_client (Step 8.6).

No router, no real waiting: a fake client replays scripted replies, and the clock and
sleep are replaced. Run: python -m scripts.test_llm_retry
"""

import sys
from types import SimpleNamespace

from openai import APIStatusError

import mansha.llm_client as lc

NOW = 1_800_000_000.0          # fixed fake clock (seconds)
failures: list[str] = []
slept: list[float] = []


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
    """Mimics client.chat.completions.with_raw_response.create(...)."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(
            with_raw_response=SimpleNamespace(create=self._create)))

    def _create(self, **kwargs):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def run(*replies):
    """Call call_llm against scripted replies. Returns (result or error, fake client, waits)."""
    slept.clear()
    fake = FakeClient(*replies)
    lc._client = fake
    try:
        out = lc.call_llm("test", "auto:long", [{"role": "user", "content": "hi"}])
    except lc.LLMCallError as e:
        out = e
    return out, fake, list(slept)


lc._sleep = slept.append
lc._now = lambda: NOW

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

out, fake, waits = run(busy_429(10), busy_429(10))
check("two busy replies: one wait only, then LLMCallError",
      isinstance(out, lc.LLMCallError) and waits == [11.0] and fake.calls == 2, (waits, fake.calls))

out, fake, waits = run(ok_reply())
check("first attempt OK: no wait", waits == [] and fake.calls == 1)

lc._client = None
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
