"""Shared LLM client for all Mansha agents.

call_llm() wraps every model call so each agent gets the same behaviour:
- routing through a named FreeLLMAPI chain (never plain "auto")
- logging of which model served the call (x-routed-via header)
- truncation check (finish_reason == "length")
- JSON parsing + required-key validation (independent of finish_reason)
- at most ONE retry per call, for any failure
- before that retry, a wait when the router says it is busy (Step 8.6):
  HTTP 429 -> wait until the router's retryAtMs; HTTP 502/503/504 -> a fixed short
  wait. If the router's cooldown is longer than RETRY_WAIT_CAP_S, fail at once
  instead of retrying into a cooldown that has not ended.
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

logger = logging.getLogger("mansha.llm")

# Output-token budgets per chain.
# auto:qa may route to Groq (free tier: 1000 output tokens/min), so it never exceeds 1000.
# auto:long has no Groq models, so it can grow on a truncation retry.
CHAIN_LIMITS: dict[str, dict[str, int]] = {
    "auto:qa": {"default": 1000, "ceiling": 1000},
    "auto:long": {"default": 8000, "ceiling": 16000},
}

# The router's own fallback budget is 45 s; leave headroom on top of it.
REQUEST_TIMEOUT_S = 300  # Nemotron (reasoning model) needs ~100-200 s for long JSON; Gemini ~20 s

# Waiting before the one retry (problem 24).
RETRY_WAIT_CAP_S = 90      # longest wait we accept; a longer cooldown fails at once
UPSTREAM_WAIT_S = 30       # wait after 502/503/504, or a 429 without a time hint
                           # (our choice: the router's cooldown resets seen on 15 Oct were ~25 s)
WAIT_MARGIN_S = 1.0        # added to the router's retryAtMs, so we arrive just after the reset
BUSY_STATUSES = {429, 502, 503, 504}

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

    for attempt_no in (1, 2):
        record: dict[str, Any] = {"attempt": attempt_no, "chain": chain, "max_tokens": tokens}
        start = time.monotonic()
        problem: str | None = None
        status: int | None = None
        hint_s: float | None = None
        text = ""
        data: dict[str, Any] | None = None

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

        record["latency_s"] = round(time.monotonic() - start, 2)
        record["ok"] = problem is None
        if status is not None:
            record["http_status"] = status
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

        if attempt_no == 2:
            break

        # Router busy? Wait before the retry, or give up now if its cooldown is too long.
        wait_s = _wait_before_retry(status, hint_s)
        if wait_s > RETRY_WAIT_CAP_S:
            record["retry_skipped"] = f"router busy for ~{wait_s:.0f}s (> {RETRY_WAIT_CAP_S}s cap)"
            logger.warning("[%s] not retrying: router busy for ~%.0fs, longer than the %ds cap",
                           agent, wait_s, RETRY_WAIT_CAP_S)
            raise LLMCallError(
                f"[{agent}] failed after 1 attempt; router busy for ~{wait_s:.0f}s "
                f"(longer than the {RETRY_WAIT_CAP_S}s cap). Last problem: {problem}",
                attempts,
            )
        if wait_s > 0:
            record["waited_before_retry_s"] = round(wait_s, 1)
            logger.info("[%s] router busy (HTTP %s): waiting %.0fs before the retry",
                        agent, status, wait_s)
            _sleep(wait_s)

        # Truncated? Give the retry a bigger budget, if the chain allows it.
        if problem.startswith("truncated") and tokens < limits["ceiling"]:
            tokens = min(tokens * 2, limits["ceiling"])

    raise LLMCallError(
        f"[{agent}] failed after {len(attempts)} attempts. Last problem: {attempts[-1].get('problem')}",
        attempts,
    )
