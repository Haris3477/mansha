"""Offline UI tests: fake replies only, no router or external network."""

import csv
import signal
import socket
import subprocess
import time
import json
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import httpx

from fastapi.testclient import TestClient

from mansha.llm_client import LLMCallError
from mansha.orchestrator import PipelineResult, run_pipeline
from mansha.researcher import number_keys
from mansha.web.app import create_app
from scripts.fake_llm import builder_prose, fake_for
from scripts.pipeline_cases import DEV_INTAKES, PIPELINE_CASES
from scripts import serve_ui

failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def events(client, run_id):
    response = client.get(f"/api/run/{run_id}/events")
    return [(block.splitlines()[0][7:], json.loads(block.splitlines()[1][6:]))
            for block in response.text.strip().split("\n\n") if block.startswith("event:")]


def start(client, case="windows", **kwargs):
    data = kwargs.pop("data", {"message": PIPELINE_CASES[case][0], "sample": case})
    response = client.post("/api/run", data=data, **kwargs)
    check("run accepted", response.status_code == 200, response.text)
    return response.json()["run_id"]


with tempfile.TemporaryDirectory(prefix="mansha_ui_test_") as temporary:
    root = Path(temporary)
    client = TestClient(create_app(fake=True, runs_root=root / "samples"))
    check("GET / is HTML", client.get("/").headers["content-type"].startswith("text/html"))
    samples = client.get("/api/samples").json()
    check("all six samples and BOM flags", len(samples) == 6 and
          {s["name"] for s in samples} == set(PIPELINE_CASES) and
          all(s["has_bom"] == bool(PIPELINE_CASES[s["name"]][1]) for s in samples))
    for case, (message, folder, status, verdict) in PIPELINE_CASES.items():
        run_id = start(client, case)
        history = events(client, run_id)
        result = history[-1][1]
        check(f"{case}: expected status/verdict", history[-1][0] == "result" and
              (result["status"], result["verdict"]) == (status, verdict), result)
        if case == "windows":
            direct = run_pipeline(message, case_folder=folder, llm=fake_for(case))
            check("phase order, names and statuses match direct pipeline",
                  [(p[1]["name"], p[1]["status"]) for p in history[:-1]] ==
                  [(p.name, p.status) for p in direct.phases])
            check("phase indices and metadata", [p[1]["index"] for p in history[:-1]] ==
                  list(range(1, len(direct.phases) + 1)) and
                  all(set(p[1]) == {"index", "name", "status", "seconds", "summary", "served_by",
                                       "attempts", "problems", "warnings"} for p in history[:-1]))
            check("HTML has duty table", "<table>" in result["report_html"])
            download = client.get(f"/api/run/{run_id}/report.md")
            check("download equals output", download.text == direct.output == result["report_markdown"]
                  and "attachment" in download.headers["content-disposition"])
            check("late connection replays every event", events(client, run_id) == history)

    llm = fake_for("windows", intake=[dict(DEV_INTAKES["windows"][0], language="ar")],
                   document_builder=[LLMCallError("offline test", []),
                                     builder_prose("windows"), builder_prose("windows")])
    arabic = TestClient(create_app(llm=llm, runs_root=root / "arabic", router_check=lambda: (True, "")))
    result = events(arabic, start(arabic))[-1][1]
    check("Arabic result direction and language", result["dir"] == "rtl" and result["language"] == "ar")

    llm = fake_for("windows")
    upload_client = TestClient(create_app(llm=llm, runs_root=root / "uploads",
                                         router_check=lambda: (True, "")))
    folder = Path(PIPELINE_CASES["windows"][1])
    files = {name: (name + suffix, (folder / (name + suffix)).read_bytes())
             for name, suffix in (("bom", ".csv"), ("declaration", ".json"))}
    real_pipeline = run_pipeline
    case_folders = []

    def capture(*args, **kwargs):
        case_folders.append(Path(kwargs["case_folder"]))
        return real_pipeline(*args, **kwargs)

    with patch("mansha.web.app.run_pipeline", capture):
        result = events(upload_client, start(upload_client, data={"message": PIPELINE_CASES["windows"][0]},
                                              files=files))[-1][1]
    check("uploaded BOM gives same verdict", result["verdict"] == "ELIGIBLE")
    check("temporary case folder deleted", len(case_folders) == 1 and not case_folders[0].exists())
    with (folder / "bom.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    values = {v for row in rows for v in number_keys(row["value"])}
    saved = "\n".join(p.read_text() for p in (root / "uploads").rglob("*") if p.is_file())
    for where, text in (("LLM prompts", llm.sent_text()), ("saved run files", saved)):
        check(f"privacy: no supplier names in {where}",
              all(row["supplier"].split(" (")[0] not in text for row in rows))
        check(f"privacy: no input values in {where}", not values & number_keys(text))

    llm = fake_for("windows")
    bad_client = TestClient(create_app(llm=llm, runs_root=root / "bad", router_check=lambda: (True, "")))
    bad_files = [
        {"bom": ("bom.csv", b"x" * (200 * 1024 + 1))},
        {"bom": ("bom.csv", b"a,b\n\xff,1")},
        {"bom": ("bom.txt", b"a,b\nx,1")},
        {"bom": ("bom.csv", b"")},
        {"declaration": ("declaration.json", b"[]")},
        {"declaration": ("declaration.json", b"{")},
        {"declaration": ("declaration.json", b"x" * (50 * 1024 + 1))},
    ]
    for index, bad in enumerate(bad_files):
        response = bad_client.post("/api/run", data={"message": "windows"}, files=bad)
        check(f"bad upload {index + 1} rejected", response.status_code == 400)
    check("sample plus upload rejected", bad_client.post("/api/run", data={"message": "x", "sample": "windows"},
                                                         files=files).status_code == 400)
    check("empty message rejected", bad_client.post("/api/run", data={"message": " "}).status_code == 400)
    check("unknown sample rejected", bad_client.post("/api/run", data={"message": "x", "sample": "unknown"}).status_code == 400)
    check("bad requests never call LLM", not llm.seen)
    check("fake mode rejects free message clearly", "sample" in client.post("/api/run", data={"message": "x"}).json()["detail"])

    entered, release = threading.Event(), threading.Event()
    fake = fake_for("vague")

    def blocked(*args, **kwargs):
        entered.set()
        if not release.wait(10):
            raise RuntimeError("test release timed out")
        return fake(*args, **kwargs)

    busy = TestClient(create_app(llm=blocked, runs_root=root / "busy", router_check=lambda: (True, "")))
    run_id = start(busy, "vague")
    try:
        check("first run is waiting", entered.wait(5))
        check("second run rejected while busy", busy.post("/api/run", data={"message": "x"}).status_code == 409)
        other = TestClient(create_app(fake=True, runs_root=root / "other"))
        check("busy lock is global", other.post("/api/run", data={"message": "x", "sample": "vague"}).status_code == 409)
    finally:
        release.set()
    events(busy, run_id)
    check("new run works after release", events(client, start(client, "vague"))[-1][0] == "result")

    llm = fake_for("windows")
    down = TestClient(create_app(llm=llm, runs_root=root / "down", router_check=lambda: (False, "down")))
    check("router down: 503 without calls", down.post("/api/run", data={"message": "x"}).status_code == 503 and not llm.seen)

    with patch("mansha.web.app.run_pipeline", return_value=PipelineResult(
            status="REPORT", output="<script>alert(1)</script>", language="en", phases=[])):
        result = events(client, start(client, "vague"))[-1][1]
    check("XSS escaped", "&lt;script&gt;alert(1)&lt;/script&gt;" in result["report_html"]
          and "<script>" not in result["report_html"])

    with patch("mansha.web.app.run_pipeline", side_effect=RuntimeError("private traceback detail")):
        error = events(client, start(client, "vague"))[-1]
    check("crashes return message only", error[0] == "error" and set(error[1]) == {"message"}
          and "private" not in error[1]["message"])
    check("crash releases lock", events(client, start(client, "vague"))[-1][0] == "result")

    # Freeze timing so callback equality covers the entire log, not just selected fields.
    with patch("mansha.orchestrator.time.monotonic", return_value=1):
        direct = run_pipeline(PIPELINE_CASES["windows"][0], case_folder=folder, llm=fake_for("windows"))
        seen = []
        callback = run_pipeline(PIPELINE_CASES["windows"][0], case_folder=folder,
                                llm=fake_for("windows"), on_phase=seen.append)

        def raises(phase):
            raise RuntimeError("callback test")

        broken = run_pipeline(PIPELINE_CASES["windows"][0], case_folder=folder,
                              llm=fake_for("windows"), on_phase=raises)
    check("callback receives each phase once in order", len(seen) == len(callback.phases)
          and all(a is b for a, b in zip(seen, callback.phases)))
    check("callback leaves output and entire log unchanged", direct.output == callback.output == broken.output
          and direct.log_dict() == callback.log_dict() == broken.log_dict())

    with patch.object(serve_ui.uvicorn, "run") as server:
        serve_ui.main(["--fake", "--port", "8765"])
    check("server binds only 127.0.0.1", server.call_args.kwargs ==
          {"host": "127.0.0.1", "port": 8765, "timeout_graceful_shutdown": 3})

    # Exercise actual sockets: TestClient buffers streams and cannot model a tab closing.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    closed = root / "stream_closed.txt"
    child_code = r"""
import sys
import time
from pathlib import Path

import uvicorn

from mansha.web.app import Run, create_app
from scripts.fake_llm import fake_for

root = Path(sys.argv[1])
original_stream = Run.stream

async def tracked_stream(self, request):
    stream = original_stream(self, request)
    try:
        async for event in stream:
            yield event
    finally:
        await stream.aclose()
        with (root / "stream_closed.txt").open("a") as handle:
            handle.write("closed\n")

Run.stream = tracked_stream
fake = None

def slow_llm(agent, *args, **kwargs):
    global fake
    if agent == "intake":
        fake = fake_for("windows")
    time.sleep(2)
    return fake(agent, *args, **kwargs)

app = create_app(llm=slow_llm, runs_root=root / "process_runs",
                 router_check=lambda: (True, "offline fake"))
uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[2]), timeout_graceful_shutdown=3)
"""

    def first_phase(response):
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        raise AssertionError("stream ended before its first phase")

    with (root / "server.log").open("w+") as server_log:
        process = subprocess.Popen([sys.executable, "-c", child_code, str(root), str(port)],
                                   stdout=server_log, stderr=subprocess.STDOUT,
                                   cwd=Path(__file__).resolve().parents[1])
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=4,
                              trust_env=False) as live:
                deadline = time.monotonic() + 8
                while True:
                    try:
                        if live.get("/").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if process.poll() is not None or time.monotonic() >= deadline:
                        server_log.seek(0)
                        raise AssertionError("test server did not start: " + server_log.read())
                    time.sleep(0.1)

                run_id = start(live)
                with live.stream("GET", f"/api/run/{run_id}/events") as response:
                    check("disconnect: first phase received while run active",
                          first_phase(response)["name"] == "Intake" and
                          live.get(f"/api/run/{run_id}/report.md").status_code == 409)
                deadline = time.monotonic() + 3
                while not closed.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                check("disconnect: stream generator stopped before run finished", closed.exists() and
                      live.get(f"/api/run/{run_id}/report.md").status_code == 409)
                deadline = time.monotonic() + 20
                while live.get(f"/api/run/{run_id}/report.md").status_code == 409:
                    if time.monotonic() >= deadline:
                        raise AssertionError("disconnected run did not finish")
                    time.sleep(0.1)

                # Keep the second connection open while interrupting the real server.
                run_id = start(live)
                with live.stream("GET", f"/api/run/{run_id}/events") as response:
                    check("disconnect: next run accepted and producing phases",
                          first_phase(response)["name"] == "Intake")
                    started = time.monotonic()
                    process.send_signal(signal.SIGINT)
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        check("SIGINT: server exits within 8 seconds during an active stream", False)
                    else:
                        check("SIGINT: server exits within 8 seconds during an active stream",
                              time.monotonic() - started < 8)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
