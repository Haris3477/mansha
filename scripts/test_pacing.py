"""Offline tests for pacing in mansha.llm_client (Step 7.6k): a chain with a per-minute limit
(auto:judge, the Cerebras trial's 5 requests a minute) never gets more than RATE_LIMITS allows.

No router, no real waiting: a fake client answers, and the clock and sleep are replaced.
Run: python -m scripts.test_pacing
"""

import sys
from types import SimpleNamespace

import mansha.llm_client as lc
from mansha.orchestrator import attempt_text, call_text

failures: list[str] = []
clock = {"t": 1_800_000_000.0}
slept: list[float] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def fake_sleep(s: float) -> None:
    slept.append(round(s, 1))
    clock["t"] += s


class FakeClient:
    """Answers every call with `text` (an empty text makes the client retry)."""

    def __init__(self, *texts):
        self.texts, self.sent = list(texts), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(
            with_raw_response=SimpleNamespace(create=self._create)))

    def _create(self, **kwargs):
        self.sent.append((kwargs["model"], clock["t"]))
        text = self.texts.pop(0) if self.texts else "OK"
        resp = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")], usage=None)
        return SimpleNamespace(headers={"x-routed-via": "fake/model"}, parse=lambda: resp)


lc._sleep = fake_sleep
lc._now = lambda: clock["t"]


def fresh(*texts) -> FakeClient:
    lc._sent.clear()
    slept.clear()
    fake = FakeClient(*texts)
    lc._get_client = lambda: fake
    return fake


def call(chain: str = "auto:judge"):
    return lc.call_llm("test", chain, [{"role": "user", "content": "hi"}])


def in_any_window(sent: list[tuple[str, float]], chain: str, window: float = 60.0) -> int:
    """The most sends on `chain` inside any `window` seconds (what the router counts)."""
    times = [t for c, t in sent if c == chain]
    return max((sum(1 for u in times if t <= u < t + window) for t in times), default=0)


print("1. The limit")
check("auto:judge is paced at 4 a minute (one under Cerebras's 5)", lc.RATE_LIMITS.get("auto:judge") == (4, 60.0),
      lc.RATE_LIMITS)
check("auto:long and auto:qa are not paced", "auto:long" not in lc.RATE_LIMITS and "auto:qa" not in lc.RATE_LIMITS)

print("\n2. Six judge calls in a row (a QA round 2 after round 1, as on 24 Oct)")
fake = fresh()
results = [call() for _ in range(6)]
check("the first 4 go at once, the 5th waits ~61 s, the 6th goes at once", slept == [61.0], slept)
check("never more than 4 sends in any 60 s", in_any_window(fake.sent, "auto:judge") <= 4,
      in_any_window(fake.sent, "auto:judge"))
check("the wait is recorded on the 5th call's attempt", results[4].attempts[0].get("paced_wait_s") == 61.0
      and not any(r.attempts[0].get("paced_wait_s") for i, r in enumerate(results) if i != 4),
      [r.attempts[0].get("paced_wait_s") for r in results])
check("latency does not include the wait", results[4].latency_s < 5, results[4].latency_s)

print("\n3. Calls spread out never wait")
fake = fresh()
for _ in range(8):
    call()
    clock["t"] += 20          # QA parts spaced 20 s apart: at most 3 in any minute
check("8 calls 20 s apart: no wait", slept == [], slept)

print("\n4. Other chains")
fake = fresh()
for _ in range(10):
    call("auto:long")
    call("auto:qa")
check("10 + 10 calls on auto:long / auto:qa: no wait", slept == [], slept)
for _ in range(4):
    call()
check("judge calls are counted on their own (4 judge calls after 20 others: no wait)", slept == [], slept)

print("\n5. A retry is a send too")
fake = fresh("OK", "OK", "OK", "", "OK")   # the 4th call's first answer is empty -> one retry
for _ in range(4):
    r = call()
check("the 4th call's retry (5th send) waits for the window", slept == [61.0] and len(r.attempts) == 2
      and r.attempts[1].get("paced_wait_s") == 61.0, (slept, r.attempts))
check("never more than 4 sends in any 60 s, retries included", in_any_window(fake.sent, "auto:judge") <= 4)

print("\n6. Shown in the phase log")
a = results[4].attempts[0]
txt = attempt_text(a)
check("attempt text names the wait", "waited 61.0 s for the per-minute limit" in txt, txt)
c = {"ok": True, "served_by": "fake/model", "latency_s": 0.0, "attempts": [a]}
check("a single OK call that waited still shows its attempt", "per-minute limit" in call_text(c), call_text(c))
c2 = {"ok": True, "served_by": "fake/model", "latency_s": 0.0, "attempts": [results[0].attempts[0]]}
check("a single OK call without a wait stays short", call_text(c2) == "served by fake/model (0.0 s)", call_text(c2))

print("\n7. Break test: with pacing off, six calls overrun the limit")
saved = dict(lc.RATE_LIMITS)
lc.RATE_LIMITS.clear()
fake = fresh()
for _ in range(6):
    call()
check("no pacing: 6 sends in one minute (what the router refused on 24 Oct)",
      in_any_window(fake.sent, "auto:judge") == 6 and slept == [])
lc.RATE_LIMITS.update(saved)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
