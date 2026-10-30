"""Local pipeline server, with replayable phase events and temporary uploads."""

import asyncio
import csv
import io
import json
import logging
import tempfile
import threading
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from markdown_it import MarkdownIt

from mansha.llm_client import call_llm, router_answering
from mansha.orchestrator import run_pipeline, served_by
from scripts.pipeline_cases import PIPELINE_CASES

RUN_LOCK = threading.Lock()
STATIC = Path(__file__).parent / "static"
log = logging.getLogger(__name__)


class Run:
    def __init__(self):
        self.condition = threading.Condition()
        self.events = []
        self.done = False
        self.output = None

    def publish(self, kind, data, *, done=False):
        with self.condition:
            self.events.append((kind, data))
            self.done = done
            self.condition.notify_all()

    async def stream(self, request):
        index = 0
        last_sent = asyncio.get_running_loop().time()
        while True:
            if request.app.state.shutting_down or await request.is_disconnected():
                return
            with self.condition:
                pending = self.events[index:]
                index += len(pending)
                done = self.done
            for kind, data in pending:
                yield f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                last_sent = asyncio.get_running_loop().time()
            if done:
                return
            if asyncio.get_running_loop().time() - last_sent >= 15:
                yield ": keep-alive\n\n"
                last_sent = asyncio.get_running_loop().time()
            await asyncio.sleep(0.5)


async def upload_text(upload, limit, kind):
    if upload is None:
        return None
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(400, f"{kind} upload is too large.")
    try:
        text = data.decode("utf-8-sig")
        if kind == "bom":
            if Path(upload.filename or "").suffix.lower() != ".csv":
                raise ValueError()
            header = next(csv.reader(io.StringIO(text), strict=True), [])
            if len(header) < 2 or any(not cell.strip() for cell in header):
                raise ValueError()
        elif not isinstance(json.loads(text), dict):
            raise ValueError()
    except (UnicodeError, ValueError, csv.Error):
        raise HTTPException(400, f"Invalid {kind} upload: use a UTF-8 CSV with a header row "
                            "for bom, or a JSON object for declaration.") from None
    return text


def create_app(*, llm=call_llm, fake: bool = False, runs_root=Path("runs/ui"),
               router_check=router_answering):
    @asynccontextmanager
    async def lifespan(app):
        app.state.shutting_down = False
        try:
            yield
        finally:
            app.state.shutting_down = True

    app = FastAPI(lifespan=lifespan)
    app.state.shutting_down = False
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    runs = OrderedDict()
    markdown = MarkdownIt("commonmark", {"html": False}).enable("table")

    def get_run(run_id):
        if run_id not in runs:
            raise HTTPException(404, "Run not found.")
        return runs[run_id]

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/samples")
    def samples():
        return [{"name": name, "message": case[0], "has_bom": bool(case[1])}
                for name, case in PIPELINE_CASES.items()]

    @app.post("/api/run")
    async def start(message: str = Form(""), sample: str | None = Form(None),
                    bom: UploadFile | None = File(None),
                    declaration: UploadFile | None = File(None)):
        if not message.strip():
            raise HTTPException(400, "Enter a message.")
        if sample is not None and sample not in PIPELINE_CASES:
            raise HTTPException(400, "Unknown sample.")
        if sample is not None and (bom is not None or declaration is not None):
            raise HTTPException(400, "Choose a sample or upload files, not both.")
        if fake and sample is None:
            raise HTTPException(400, "Fake mode only supports sample runs. Choose a sample.")
        bom_text = await upload_text(bom, 200 * 1024, "bom")
        declaration_text = await upload_text(declaration, 50 * 1024, "declaration")
        if not RUN_LOCK.acquire(blocking=False):
            raise HTTPException(409, "A check is already in progress. Please wait.")
        try:
            if not fake:
                up, _ = router_check()
                if not up:
                    raise HTTPException(503, "The router is not answering. Nothing was run.")
            selected_llm = llm
            if fake:
                from scripts.fake_llm import fake_for
                selected_llm = fake_for(sample)
            run_id = uuid.uuid4().hex
            run = Run()
            # Preserve timestamped names without overwriting a run started in the same second.
            stamp = datetime.now()
            out = Path(runs_root) / f"{stamp:%Y%m%d-%H%M%S}_{sample or 'msg'}"
            while out.exists():
                stamp += timedelta(seconds=1)
                out = Path(runs_root) / f"{stamp:%Y%m%d-%H%M%S}_{sample or 'msg'}"

            def work():
                phase_index = 0

                def on_phase(phase):
                    nonlocal phase_index
                    phase_index += 1
                    run.publish("phase", {
                        "index": phase_index, "name": phase.name, "status": phase.status,
                        "seconds": phase.seconds, "summary": phase.summary,
                        "served_by": served_by(phase.calls),
                        "attempts": sum(len(c.get("attempts", [])) for c in phase.calls),
                        "problems": phase.problems, "warnings": phase.warnings,
                    })

                try:
                    with tempfile.TemporaryDirectory(prefix="mansha_ui_") as temporary:
                        folder = PIPELINE_CASES[sample][1] if sample else None
                        if bom_text is not None or declaration_text is not None:
                            folder = Path(temporary)
                            for filename, content in (("bom.csv", bom_text),
                                                      ("declaration.json", declaration_text)):
                                if content is not None:
                                    (folder / filename).write_text(content, encoding="utf-8")
                        result = run_pipeline(message, case_folder=folder, llm=selected_llm,
                                              out_dir=out, on_phase=on_phase)
                    run.output = result.output
                    data = {"status": result.status, "verdict": result.verdict,
                            "language": result.language, "seconds": result.seconds,
                            "warnings": result.warnings, "report_markdown": result.output,
                            "report_html": markdown.render(result.output),
                            "dir": "rtl" if result.language == "ar" else "ltr"}
                    kind = "result"
                except Exception:
                    log.exception("UI run failed")
                    kind, data = "error", {"message": "The check could not finish. Please try again."}
                finally:
                    RUN_LOCK.release()
                run.publish(kind, data, done=True)

            runs[run_id] = run
            while len(runs) > 20:
                runs.popitem(last=False)
            threading.Thread(target=work, name=f"mansha-{run_id}", daemon=True).start()
        except BaseException:
            RUN_LOCK.release()
            raise
        return {"run_id": run_id}

    @app.get("/api/run/{run_id}/events")
    async def events(run_id: str, request: Request):
        return StreamingResponse(get_run(run_id).stream(request), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    @app.get("/api/run/{run_id}/report.md")
    def report(run_id: str):
        run = get_run(run_id)
        if not run.done or run.output is None:
            raise HTTPException(409, "The report is not available yet.")
        return Response(run.output, media_type="text/markdown",
                        headers={"Content-Disposition": 'attachment; filename="report.md"'})

    return app
