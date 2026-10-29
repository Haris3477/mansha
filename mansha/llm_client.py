"""Shared LLM client for all Mansha agents.

call_llm() wraps every model call so each agent gets the same behaviour:
- routing through a named FreeLLMAPI chain (never plain "auto")
- logging of which model served the call (x-routed-via header)
- truncation check (finish_reason == "length")
- JSON parsing + required-key validation (independent of finish_reason)
- at most ONE retry per call, for any failure in which a model was tried
- before that retry, a wait when the router says it is busy (Step 8.6):
  HTTP 502/503/504 -> a fixed short wait. If a wait would be longer than
  RETRY_WAIT_CAP_S, fail at once instead of retrying into a cooldown.
- a router COOLDOWN reply (HTTP 429 with a retry time: no model was tried) does not
  use up the retry: wait until that time and send again, at most
  MAX_COOLDOWN_WAITS times per call (Step 8.6b)
- BUSY BUDGET (Step 9.5b): when the provider side is busy (HTTP 502/503/504, or 429
  without a time), the call may try up to MAX_BUSY_ATTEMPTS models in total, each after
  the usual wait. Our own failures (bad JSON, truncation, empty reply, 400, timeout)
  keep the one-retry rule. Nothing is sent again once CALL_BUDGET_S has passed.
- PACING (Step 7.6k): a chain with a per-minute limit (RATE_LIMITS; today auto:judge, the
  Cerebras trial's 5 requests a minute) gets at most N requests in any window: before a send
  that would be one too many, the client waits until the oldest send leaves the window. The
  router refuses the extra request otherwise, and its escalating cooldown (5-9 min on 24 Oct)
  left QA parts unreviewed. Counts sends from this process only.
- PRE-FLIGHT (guard health check, 29 Oct): router_answering() asks the router for its model
  list (GET <base>/models; no model runs, no quota). eval_set and run_pipeline call it before
  anything else, so a stopped router gives one clear line instead of LLM_ERRORs at Intake.
"""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

logger = logging.getLogger("mansha.llm")

# Output-token budgets per chain.
# auto:qa (Intake) may route to Groq (free tier: 8,000 tokens per minute, prompt and answer
# together; checked 17 Oct 2026). Intake's answer is short, so it never exceeds 1000.
# auto:long has no Groq models. It starts at its ceiling (Step 9.5): its reasoning models
# (Dots3) hit 8000 tokens on the Researcher, and each truncated attempt cost ~90 s.
# auto:judge (QA Evaluator, Step 7) shares no model with auto:long. Its Groq models allow
# 8,000 tokens per minute, prompt and answer together, so the answer budget stays small;
# QA's JSON is short, the rest is room for a reasoning model's thinking (tuned in Step 7.4).
# P1 (fix round, 26 Oct): judge = Cerebras since 7.7 (30,000 tokens per minute). Ceiling 6000 so a
# truncated answer is retried with double the room; with default = ceiling = 3000 the retry was cut
# off at 3000 again and the QA part was NOT reviewed (N3, sitting 4: two attempts, 3000 each).
CHAIN_LIMITS: dict[str, dict[str, int]] = {
    "auto:qa": {"default": 1000, "ceiling": 1000},
    "auto:long": {"default": 16000, "ceiling": 16000},
    "auto:judge": {"default": 3000, "ceiling": 6000},
    # B (28 Oct): Arabic Builder calls only (Gemini 3.5 / 3.6 Flash); the same room as auto:long.
    "auto:arabic": {"default": 16000, "ceiling": 16000},
}

# The router's own fallback budget is 45 s; leave headroom on top of it.
REQUEST_TIMEOUT_S = 300  # Nemotron (reasoning model) needs ~100-200 s for long JSON; Gemini ~20 s

# Waiting before the one retry (problem 24).
RETRY_WAIT_CAP_S = 90      # longest wait we accept; a longer cooldown fails at once
UPSTREAM_WAIT_S = 30       # wait after 502/503/504, or a 429 without a time hint
                           # (our choice: the router's cooldown resets seen on 15 Oct were ~25 s)
WAIT_MARGIN_S = 1.0        # added to the router's retryAtMs, so we arrive just after the reset
BUSY_STATUSES = {429, 502, 503, 504}
MAX_COOLDOWN_WAITS = 2     # cooldown replies (429 + retry time) waited out per call; they ask no model
MAX_BUSY_ATTEMPTS = 4      # model attempts per call while every failure is provider-busy (Step 9.5b)
CALL_BUDGET_S = 240        # no new attempt starts after this (seconds since the call began)

# Pacing (Step 7.6k): chain -> (max requests, window in seconds). auto:judge = Cerebras trial,
# 5 requests a minute (console Limits page, 23 Oct); 4 leaves one request of margin. Raise or
# remove after a pay-as-you-go purchase.
RATE_LIMITS: dict[str, tuple[int, float]] = {"auto:judge": (4, 60.0)}
PACE_MARGIN_S = 1.0        # added to the wait, so the oldest send is surely out of the window
_sent: dict[str, deque] = {}   # chain -> times of recent sends (this process)

# Replaceable in tests (no real waiting, fixed clock).
_sleep = time.sleep
_now = time.time


class LLMCallError(Exception):
    """Raised when a call still fails after its one retry."""

    def __init__(self, message: str, attempts: list[dict[str, Any]]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class LLMResult:
    text: str                         # raw model reply
    data: dict[str, Any] | None       # parsed JSON when expect_json=True, else None
    routed_via: str | None            # model that served the successful attempt
    finish_reason: str | None
    latency_s: float
    attempts: list[dict[str, Any]] = field(default_factory=list)  # every attempt, for the phase log


_client: OpenAI | None = None

HEALTH_TIMEOUT_S = 5.0          # pre-flight: no answer within this = not answering
HEALTH_OK_STATUSES = {200, 401}  # 401 = the router is up and asks for a key (same rule as the curl check)
START_HINT = "Start it: cd ~/Projects/freellmapi && npm run dev"


def router_answering(base_url: str | None = None, *, timeout: float = HEALTH_TIMEOUT_S,
                     opener=urllib.request.urlopen) -> tuple[bool, str]:
    """Pre-flight check: is the router up? GET <base>/models, no key, no model, no quota.
    Returns (up, one line for the console)."""
    if base_url is None:
        load_dotenv()
        base_url = os.environ.get("FREELLMAPI_BASE_URL")
    if not base_url:
        return False, "router address unknown: FREELLMAPI_BASE_URL is not set"
    url = base_url.rstrip("/") + "/models"
    try:
        with opener(url, timeout=timeout) as reply:
            status = reply.status
    except urllib.error.HTTPError as e:      # an HTTP answer with an error status: the router is there
        status = e.code
    except (urllib.error.URLError, OSError) as e:   # refused, unknown host, timeout
        return False, f"router not answering at {url} ({getattr(e, 'reason', e)}). {START_HINT}"
    if status in HEALTH_OK_STATUSES:
        return True, f"router answering at {url} ({status})"
    return False, f"router at {url} answered {status}, not ready. {START_HINT}"


def _get_client() -> OpenAI:
    """Create the OpenAI client once, on first use."""
    global _client
    if _client is None:
        load_dotenv()
        _client = OpenAI(
            base_url=os.environ["FREELLMAPI_BASE_URL"],
            api_key=os.environ["FREELLMAPI_KEY"],
            timeout=REQUEST_TIMEOUT_S,
            max_retries=0,  # we retry explicitly below, so every attempt is logged
        )
    return _client


def _strip_code_fence(text: str) -> str:
    """Remove a ```json ... ``` wrapper if the model added one."""
    t = text.strip()
    if t.startswith("```") and t.endswith("```"):
        first_newline = t.find("\n")
        if first_newline != -1:
            t = t[first_newline + 1 : -3].strip()
    return t


def _parse_json(text: str, required_keys: tuple[str, ...]) -> tuple[dict[str, Any] | None, str | None]:
    """Return (data, None) if valid, or (None, problem description) if not."""
    try:
        data = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e.msg} (line {e.lineno}, col {e.colno})"
    if not isinstance(data, dict):
        return None, f"expected a JSON object, got {type(data).__name__}"
    missing = [k for k in required_keys if k not in data]
    if missing:
        return None, f"missing required keys: {missing}"
    return data, None


def _router_wait_hint(e: APIStatusError) -> float | None:
    """Seconds until the router says it can serve again, or None if it gives no hint.

    FreeLLMAPI's 429 body: {"error": {..., "retryAtMs": <epoch ms>}}. The SDK puts the
    inner "error" object in e.body; both shapes are accepted. A Retry-After header
    (seconds) is used if there is no retryAtMs.
    """
    body = e.body if isinstance(e.body, dict) else {}
    if isinstance(body.get("error"), dict):
        body = body["error"]
    at_ms = body.get("retryAtMs")
    if isinstance(at_ms, (int, float)) and not isinstance(at_ms, bool):
        return max(0.0, at_ms / 1000 - _now()) + WAIT_MARGIN_S
    headers = getattr(getattr(e, "response", None), "headers", None) or {}
    try:
        return float(headers.get("retry-after")) if headers.get("retry-after") else None
    except (TypeError, ValueError):
        return None


def _wait_before_retry(status: int | None, hint_s: float | None) -> float:
    """Seconds to wait before the retry (0 = retry now). May exceed the cap; the caller checks."""
    if status not in BUSY_STATUSES:
        return 0.0
    if hint_s is not None:
        return hint_s
    return UPSTREAM_WAIT_S


def _pace(chain: str) -> float:
    """Wait if one more send on `chain` would exceed its RATE_LIMITS; record the send.

    Returns the seconds waited (0.0 when no wait was needed or the chain has no limit).
    """
    limit = RATE_LIMITS.get(chain)
    if not limit:
        return 0.0
    n, window = limit
    sent = _sent.setdefault(chain, deque())
    now = _now()
    while sent and now - sent[0] >= window:
        sent.popleft()
    waited = 0.0
    if len(sent) >= n:
        waited = max(0.0, sent[0] + window + PACE_MARGIN_S - now)
        if waited:
            logger.info("[pacing] %s: %d request(s) in the last %.0fs; waiting %.0fs for the per-minute "
                        "limit", chain, len(sent), window, waited)
            _sleep(waited)
        now = max(_now(), now + waited)
        while sent and now - sent[0] >= window:
            sent.popleft()
    sent.append(now)
    return round(waited, 1)


def call_llm(
    agent: str,
    chain: str,
    messages: list[dict[str, str]],
    *,
    expect_json: bool = False,
    required_keys: tuple[str, ...] = (),
    max_tokens: int | None = None,
    temperature: float = 0.0,
) -> LLMResult:
    """Call a FreeLLMAPI chain with logging, validation and at most one retry."""
    if chain not in CHAIN_LIMITS:
        raise ValueError(f"Unknown chain {chain!r}. Use one of {list(CHAIN_LIMITS)}, never plain 'auto'.")

    limits = CHAIN_LIMITS[chain]
    tokens = min(max_tokens or limits["default"], limits["ceiling"])
    client = _get_client()
    attempts: list[dict[str, Any]] = []
    model_attempts = 0     # requests in which the router tried a model
    own_failures = 0       # failures on our side (bad JSON, truncation, 400, ...): one retry only
    cooldown_waits = 0     # router cooldown replies waited out (max MAX_COOLDOWN_WAITS)
    started = _now()

    while True:
        attempt_no = len(attempts) + 1
        record: dict[str, Any] = {"attempt": attempt_no, "chain": chain, "max_tokens": tokens}
        problem: str | None = None
        status: int | None = None
        hint_s: float | None = None
        text = ""
        data: dict[str, Any] | None = None

        paced = _pace(chain)   # Step 7.6k: stay under the chain's per-minute limit
        if paced:
            record["paced_wait_s"] = paced
        start = time.monotonic()
        try:
            raw = client.chat.completions.with_raw_response.create(
                model=chain,
                messages=messages,
                max_tokens=tokens,
                temperature=temperature,
            )
        except APIConnectionError as e:  # includes timeouts
            problem = (f"connection error: {e}. Is the router running? "
                       "(cd ~/Projects/freellmapi && npm run dev)")
        except APIStatusError as e:  # router returned an HTTP error (includes its attempt trail)
            status = e.status_code
            hint_s = _router_wait_hint(e)
            problem = f"HTTP {e.status_code}: {e.message}"
        else:
            resp = raw.parse()
            record["routed_via"] = raw.headers.get("x-routed-via")
            if resp.usage:
                record["usage"] = {"prompt": resp.usage.prompt_tokens, "completion": resp.usage.completion_tokens}

            if not resp.choices:
                problem = "response had no choices"
            else:
                choice = resp.choices[0]
                text = choice.message.content or ""
                record["finish_reason"] = choice.finish_reason
                if choice.finish_reason == "length":
                    problem = "truncated (finish_reason=length)"
                elif not text.strip():
                    problem = "empty reply"
                elif expect_json:
                    data, problem = _parse_json(text, required_keys)

        # A 429 with a retry time is the router's cooldown answer: no model was asked.
        cooldown = status == 429 and hint_s is not None
        if not cooldown:
            model_attempts += 1

        record["latency_s"] = round(time.monotonic() - start, 2)
        record["ok"] = problem is None
        if status is not None:
            record["http_status"] = status
        if cooldown:
            record["cooldown"] = True
        if problem:
            record["problem"] = problem
        attempts.append(record)

        logger.info(
            "[%s] attempt %d | %s | served_by=%s | finish=%s | %.1fs | %s",
            agent, attempt_no, chain, record.get("routed_via"), record.get("finish_reason"),
            record["latency_s"], "OK" if problem is None else f"FAILED: {problem}",
        )

        if problem is None:
            return LLMResult(
                text=text,
                data=data,
                routed_via=record.get("routed_via"),
                finish_reason=record.get("finish_reason"),
                latency_s=record["latency_s"],
                attempts=attempts,
            )

        # How long to wait before sending again (cooldown: the router's time; busy: fixed).
        wait_s = _wait_before_retry(status, hint_s)
        busy = status in BUSY_STATUSES and not cooldown   # provider side busy; a model was tried
        if wait_s > RETRY_WAIT_CAP_S:
            record["retry_skipped"] = f"router busy for ~{wait_s:.0f}s (> {RETRY_WAIT_CAP_S}s cap)"
            logger.warning("[%s] not retrying: router busy for ~%.0fs, longer than the %ds cap",
                           agent, wait_s, RETRY_WAIT_CAP_S)
            raise LLMCallError(
                f"[{agent}] gave up: router busy for ~{wait_s:.0f}s (longer than the "
                f"{RETRY_WAIT_CAP_S}s cap). Last problem: {problem}",
                attempts,
            )

        if cooldown:
            if cooldown_waits >= MAX_COOLDOWN_WAITS:
                break
            cooldown_waits += 1
            label = "router cooldown (no model tried)"
        else:
            if not busy:
                own_failures += 1
            if own_failures >= 2 or model_attempts >= MAX_BUSY_ATTEMPTS:
                break
            label = f"router busy (HTTP {status})" if wait_s > 0 else None
            # Truncated? Give the retry a bigger budget, if the chain allows it.
            if problem.startswith("truncated") and tokens < limits["ceiling"]:
                tokens = min(tokens * 2, limits["ceiling"])

        elapsed = _now() - started
        if elapsed + wait_s > CALL_BUDGET_S:
            record["retry_skipped"] = f"call budget: {elapsed:.0f}s used of {CALL_BUDGET_S}s"
            logger.warning("[%s] not retrying: %.0fs used, the call budget is %ds", agent, elapsed, CALL_BUDGET_S)
            raise LLMCallError(
                f"[{agent}] gave up after {elapsed:.0f}s ({model_attempts} model attempt(s)): the call budget "
                f"is {CALL_BUDGET_S}s. Last problem: {problem}",
                attempts,
            )

        if wait_s > 0:
            record["waited_before_retry_s"] = round(wait_s, 1)
            logger.info("[%s] %s: waiting %.0fs before sending again", agent, label, wait_s)
            _sleep(wait_s)

    raise LLMCallError(
        f"[{agent}] failed after {model_attempts} model attempt(s) and {cooldown_waits} cooldown "
        f"wait(s). Last problem: {attempts[-1].get('problem')}",
        attempts,
    )
