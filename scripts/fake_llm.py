"""Shared offline pipeline fixtures and fake LLM (no router)."""

import copy
import json
import re
from pathlib import Path

from mansha.document_builder import build_facts, fallback_prose, max_llm_notes
from mansha.llm_client import LLMResult
from scripts.pipeline_cases import DEV_INTAKES as INTAKES

FIXTURES = Path("samples/researcher_outputs")


def research_fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


def builder_prose(case: str) -> dict:
    """Prose that passes the Builder's checks (code fallback text, notes cut to the limit)."""
    research = research_fixture(case)
    _, notes = build_facts(research, INTAKES[case][0])
    prose = fallback_prose(research, notes)
    prose["notes"] = prose["notes"][:max_llm_notes(notes)]
    return prose


NULL_INTAKE = {"product_description": None, "hs_code_given": None, "destination_country": None,
               "exporter_role": None, "uae_processing": None, "shipment_value": None,
               "language": "en", "missing_fields": []}
EXTRA_INTAKES = {
    "vague": NULL_INTAKE,
    "brazil": dict(NULL_INTAKE, product_description="polyethylene shopping bags",
                   destination_country="Brazil", exporter_role="manufacturer"),
}


class FakeLLM:
    """Stands in for call_llm. Per agent, a queue of replies (dict, or an exception to raise)."""

    def __init__(self, **queues):
        self.queues = {k: list(v) for k, v in queues.items()}
        self.seen: list[tuple[str, list[dict]]] = []

    def __call__(self, agent, chain, messages, **kwargs):
        self.seen.append((agent, messages))
        r = self.queues[agent].pop(0)
        if callable(r):          # a reply built from the prompt (fake QA judging the warnings it got)
            r = r(messages)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via=f"fake/{agent}",
                         finish_reason="stop", latency_s=0.1,
                         attempts=[{"attempt": 1, "chain": chain, "ok": True, "routed_via": f"fake/{agent}"}])

    def agents(self) -> list[str]:
        return [a for a, _ in self.seen]

    def sent_text(self) -> str:
        return "\n".join(m["content"] for _, msgs in self.seen for m in msgs)


def qa_approves(messages) -> dict:
    """A QA answer that approves and judges every code warning in the prompt as NOISE."""
    ids = re.findall(r"^(W\d+): ", messages[1]["content"], re.MULTILINE)
    return {"warnings": [{"id": w, "judgement": "NOISE", "reason": "fake"} for w in ids],
            "corrections": [], "scores": {"factuality": 1, "completeness": 1, "formatting_safety": 1}}


def qa_rejects(messages) -> dict:
    ans = qa_approves(messages)
    ans["corrections"] = [{"field": "follow_up_questions", "problem": "asks for data already given.",
                           "fix": "remove it.", "source_id": None}]
    ans["scores"]["completeness"] = 0
    return ans


PROSE_APPROVES = {"corrections": [], "scores": {"factuality": 1, "completeness": 1}}
PROSE_REJECTS = {"corrections": [{"field": "summary", "problem": "'eliminates your customs duty' is wider "
                                  "than the CEPA rate term.", "fix": "Say it cuts Basic Customs Duty only.",
                                  "based_on": "FACTS"}],
                 "scores": {"factuality": 0, "completeness": 1}}


def fake_for(case: str, **overrides) -> FakeLLM:
    queues = {"intake": [EXTRA_INTAKES.get(case) or INTAKES[case][0]]}
    if case in INTAKES:
        queues["researcher"] = [research_fixture(case)]
        queues["qa"] = [qa_approves] * 8   # windows splits into 2 QA parts, windows_nodata into 3
        queues["document_builder"] = [builder_prose(case)]
        queues["prose_qa"] = [PROSE_APPROVES] * 2   # Step 7.6: the Builder prose check, one per round
    queues.update(overrides)
    return FakeLLM(**queues)


