"""FastAPI web UI with SSE streaming + Langfuse tracing.

Run with: uvicorn app:app --host 0.0.0.0 --port 8000
Endpoints:
  GET  /            — Web UI
  GET  /api/info    — version + model metadata
  GET  /api/run     — SSE: run pipeline for a user story
  POST /api/approve — resume HITL interrupt (approve/reject spec)
  GET  /api/files   — list workspace files
  GET  /api/files/{path} — read a workspace file
  POST /api/reset   — reset session
"""

import asyncio
import json
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler
from langgraph.types import Command

from config import APP_VERSION, Settings
from graph import build_graph
from output_manager import clean_workspace, package_results
from token_tracker import TokenTrackingHandler, pipeline_usage

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("logs/web.log", maxBytes=5_000_000, backupCount=3),
    ],
)
logger = logging.getLogger("web")

settings = Settings()
app = FastAPI(title="AI Dev Team", version=APP_VERSION)

graph = build_graph()
current_thread_id: str = str(uuid.uuid4())
current_session_id: str = str(uuid.uuid4())
pending_interrupt: dict | None = None

USER_ID = "web-user"
_last_user_story: str = ""


def _make_config(thread_id: str, handler: CallbackHandler) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100,
        "callbacks": [handler, TokenTrackingHandler(pipeline_usage)],
        "metadata": {
            "langfuse_session_id": current_session_id,
            "langfuse_user_id": USER_ID,
            "langfuse_tags": ["dev-team", "web"],
        },
    }


def _serialize_state(result: dict) -> dict:
    """Extract serializable state from graph result."""
    out = {}
    spec = result.get("spec")
    if spec:
        out["spec"] = {
            "title": spec.title,
            "requirements": spec.requirements,
            "acceptance_criteria": spec.acceptance_criteria,
            "estimated_complexity": spec.estimated_complexity,
        }
    code = result.get("code")
    if code:
        out["code"] = {
            "source_code": code.source_code,
            "description": code.description,
            "files_created": code.files_created,
        }
    review = result.get("review")
    if review:
        out["review"] = {
            "verdict": review.verdict,
            "score": review.score,
            "issues": review.issues,
            "suggestions": review.suggestions,
        }
    out["iteration"] = result.get("iteration", 0)
    history = result.get("review_history", [])
    out["review_history"] = [
        {"verdict": r.verdict, "score": r.score, "issues": r.issues, "suggestions": r.suggestions}
        for r in history
    ]
    return out


_last_result: dict = {}


def _sync_stream(thread_id: str, input_data, handler: CallbackHandler):
    """Run graph.stream synchronously, yielding SSE events."""
    global pending_interrupt, _last_result
    config = _make_config(thread_id, handler)

    # Map node names to pipeline stages
    stage_map = {
        "ba_node": {"stage": "ba", "label": "Business Analyst"},
        "hitl_gate": {"stage": "hitl", "label": "Spec Review"},
        "dev_node": {"stage": "dev", "label": "Developer"},
        "qa_node": {"stage": "qa", "label": "QA Engineer"},
        "github_node": {"stage": "github", "label": "GitHub PR"},
    }

    with propagate_attributes(
        session_id=current_session_id,
        user_id=USER_ID,
        tags=["dev-team", "web"],
    ):
        for chunk in graph.stream(input_data, config=config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name == "__interrupt__":
                    for intr in node_output:
                        pending_interrupt = {
                            "thread_id": thread_id,
                            "value": intr.value,
                        }
                        yield {"type": "interrupt", "data": intr.value}
                    return

                # Track raw state for output packaging
                if node_output is not None:
                    _last_result.update(node_output)

                stage_info = stage_map.get(node_name)
                if stage_info and node_output is not None:
                    event = {"type": "stage", **stage_info}

                    # Attach data for completed stages
                    if node_name == "ba_node" and node_output.get("spec"):
                        s = node_output["spec"]
                        event["spec"] = {
                            "title": s.title,
                            "requirements": s.requirements,
                            "acceptance_criteria": s.acceptance_criteria,
                            "estimated_complexity": s.estimated_complexity,
                        }
                    elif node_name == "dev_node" and node_output.get("code"):
                        c = node_output["code"]
                        event["code"] = {
                            "source_code": c.source_code,
                            "description": c.description,
                            "files_created": c.files_created,
                        }
                    elif node_name == "qa_node" and node_output.get("review"):
                        r = node_output["review"]
                        event["review"] = {
                            "verdict": r.verdict,
                            "score": r.score,
                            "issues": r.issues,
                            "suggestions": r.suggestions,
                        }
                        event["iteration"] = node_output.get("iteration", 0)
                    elif node_name == "github_node":
                        pr_url = node_output.get("pr_url")
                        if pr_url:
                            event["pr_url"] = pr_url

                    yield event

    # Log final cost summary
    logger.info("Pipeline total: %s", pipeline_usage.summary())

    # Package results if pipeline completed (has code)
    if _last_result.get("code"):
        output_path = package_results(
            user_story=_last_user_story,
            session_id=current_session_id,
            spec=_last_result.get("spec"),
            code=_last_result.get("code"),
            review=_last_result.get("review"),
            iteration=_last_result.get("iteration", 0),
            review_history=_last_result.get("review_history", []),
        )
        done_event = {"type": "done", "output_path": output_path}
        if _last_result.get("pr_url"):
            done_event["pr_url"] = _last_result["pr_url"]
        yield done_event
    else:
        yield {"type": "done"}


async def _sse_generator(user_story: str):
    global current_thread_id, _last_user_story
    current_thread_id = str(uuid.uuid4())
    _last_user_story = user_story
    handler = CallbackHandler()
    pipeline_usage.reset()
    clean_workspace()

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    async def _produce():
        def _run():
            try:
                initial_state = {
                    "user_story": user_story,
                    "spec": None,
                    "spec_approved": False,
                    "spec_feedback": "",
                    "code": None,
                    "review": None,
                    "iteration": 0,
                    "review_history": [],
                }
                for event in _sync_stream(current_thread_id, initial_state, handler):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception as e:
                logger.exception("Pipeline error")
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"type": "error", "message": str(e)}
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        await loop.run_in_executor(None, _run)

    task = asyncio.create_task(_produce())

    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=5.0)
        except TimeoutError:
            yield ": heartbeat\n\n"
            continue
        if event is None:
            break
        yield f"data: {json.dumps(event)}\n\n"

    await task
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def _sse_resume(resume_data: dict):
    global pending_interrupt
    thread_id = pending_interrupt["thread_id"] if pending_interrupt else current_thread_id
    pending_interrupt = None
    handler = CallbackHandler()

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    async def _produce():
        def _run():
            try:
                for event in _sync_stream(thread_id, Command(resume=resume_data), handler):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception as e:
                logger.exception("Resume error")
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"type": "error", "message": str(e)}
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        await loop.run_in_executor(None, _run)

    task = asyncio.create_task(_produce())

    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=5.0)
        except TimeoutError:
            yield ": heartbeat\n\n"
            continue
        if event is None:
            break
        yield f"data: {json.dumps(event)}\n\n"

    await task
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ── API endpoints ──────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return UI_HTML


@app.get("/api/info")
async def info():
    return {
        "app": settings.app_name,
        "version": APP_VERSION,
        "models": {"ba": settings.model_fast, "dev": settings.model_powerful, "qa": settings.model_mid},
        "session_id": current_session_id[:8],
        "max_qa_iterations": settings.max_qa_iterations,
    }


@app.get("/api/run")
async def run(q: str):
    logger.info("User story: %s", q[:80])
    return StreamingResponse(_sse_generator(q), media_type="text/event-stream")


@app.post("/api/approve")
async def approve(body: dict):
    if not pending_interrupt:
        raise HTTPException(400, "No pending interrupt")
    approved = body.get("approved", False)
    feedback = body.get("feedback", "")
    logger.info("HITL decision: approved=%s feedback=%s", approved, feedback[:60])
    resume_data = {"approved": approved, "feedback": feedback}
    return StreamingResponse(_sse_resume(resume_data), media_type="text/event-stream")


@app.get("/api/files")
async def list_files():
    ws = Path(settings.workspace_dir)
    if not ws.exists():
        return []
    files = []
    for p in sorted(ws.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(ws))
            files.append({"path": rel, "size": p.stat().st_size})
    return files


@app.get("/api/files/{filepath:path}")
async def read_file(filepath: str):
    ws = Path(settings.workspace_dir).resolve()
    target = (ws / filepath).resolve()
    if not target.is_relative_to(ws):
        raise HTTPException(403, "Access denied")
    if not target.exists():
        raise HTTPException(404, "File not found")
    return PlainTextResponse(target.read_text(encoding="utf-8"))


@app.get("/api/outputs")
async def list_outputs():
    """List all output folders."""
    out = Path(settings.output_dir)
    if not out.exists():
        return []
    folders = sorted(
        (d for d in out.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    results = []
    for d in folders:
        readme = d / "README.md"
        files = [f.name for f in d.rglob("*") if f.is_file() and f.name != "README.md"]
        results.append({
            "name": d.name,
            "has_readme": readme.exists(),
            "files": files,
        })
    return results


@app.post("/api/reset")
async def reset():
    global current_thread_id, current_session_id, pending_interrupt
    current_thread_id = str(uuid.uuid4())
    current_session_id = str(uuid.uuid4())
    pending_interrupt = None
    return {"status": "ok"}


# ── HTML/CSS/JS UI ────────────────────────────────────────

UI_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Dev Team</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #242736;
    --border: #2e3348; --text: #e1e4ed; --text2: #8b90a0;
    --blue: #4f8ff7; --green: #34d399; --amber: #fbbf24;
    --red: #f87171; --purple: #a78bfa;
    --gradient: linear-gradient(135deg, #4f8ff7 0%, #a78bfa 100%);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg);
         color: var(--text); display: flex; height: 100vh; overflow: hidden; }

  /* ── Sidebar ── */
  .sidebar { width: 280px; min-width: 280px; background: var(--surface);
             border-right: 1px solid var(--border); display: flex; flex-direction: column; }
  .sidebar-header { padding: 24px 20px 16px; border-bottom: 1px solid var(--border); }
  .sidebar-header h1 { font-size: 18px; background: var(--gradient);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .sidebar-header .meta { font-size: 11px; color: var(--text2); margin-top: 8px; line-height: 1.6; }
  .sidebar-section { padding: 16px 20px; border-bottom: 1px solid var(--border); }
  .sidebar-section h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
                         color: var(--text2); margin-bottom: 10px; }

  /* Pipeline steps */
  .pipeline { display: flex; flex-direction: column; gap: 2px; }
  .pipeline-step { display: flex; align-items: center; gap: 10px; padding: 8px 10px;
                   border-radius: 8px; font-size: 13px; transition: all 0.3s; }
  .pipeline-step .dot { width: 10px; height: 10px; border-radius: 50%;
                        background: var(--border); transition: all 0.3s; flex-shrink: 0; }
  .pipeline-step.active { background: rgba(79,143,247,0.1); }
  .pipeline-step.active .dot { background: var(--blue); box-shadow: 0 0 8px var(--blue); }
  .pipeline-step.done .dot { background: var(--green); }
  .pipeline-step.error .dot { background: var(--red); }
  .pipeline-step .label { flex: 1; }
  .pipeline-step .badge { font-size: 10px; padding: 2px 6px; border-radius: 4px;
                          font-weight: 600; }
  .badge-approved { background: rgba(52,211,153,0.15); color: var(--green); }
  .badge-revision { background: rgba(248,113,113,0.15); color: var(--red); }

  /* Files list */
  .files-list { display: flex; flex-direction: column; gap: 2px; max-height: 200px; overflow-y: auto; }
  .file-item { font-size: 12px; color: var(--text2); padding: 5px 8px; border-radius: 4px;
               cursor: pointer; font-family: 'SF Mono', monospace; display: flex; align-items: center; gap: 6px; }
  .file-item:hover { background: var(--surface2); color: var(--text); }
  .file-icon { font-size: 14px; }

  .btn-reset { width: 100%; padding: 10px; background: var(--surface2); color: var(--text2);
               border: 1px solid var(--border); border-radius: 8px; cursor: pointer;
               font-size: 13px; margin-top: auto; }
  .btn-reset:hover { background: var(--border); color: var(--text); }
  .sidebar-footer { padding: 16px 20px; margin-top: auto; }

  /* ── Main area ── */
  .main { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }

  /* Input bar */
  .input-area { padding: 20px 24px; border-bottom: 1px solid var(--border); background: var(--surface); flex-shrink: 0; }
  .input-row { display: flex; gap: 10px; }
  .input-row input { flex: 1; padding: 12px 16px; background: var(--bg); border: 1px solid var(--border);
                     border-radius: 10px; color: var(--text); font-size: 14px; outline: none; }
  .input-row input:focus { border-color: var(--blue); }
  .input-row input::placeholder { color: var(--text2); }
  .btn-run { padding: 12px 24px; background: var(--gradient); color: white; border: none;
             border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600;
             transition: opacity 0.2s; }
  .btn-run:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-run:hover:not(:disabled) { opacity: 0.9; }

  /* Content area */
  .content { flex: 1; min-height: 0; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }

  /* Cards */
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
          overflow: hidden; animation: fadeIn 0.3s ease; flex-shrink: 0; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  .card-header { padding: 14px 18px; border-bottom: 1px solid var(--border);
                 display: flex; align-items: center; gap: 10px; }
  .card-header .icon { font-size: 18px; }
  .card-header h3 { font-size: 14px; font-weight: 600; }
  .card-header .tag { font-size: 11px; margin-left: auto; padding: 3px 8px;
                      border-radius: 4px; font-weight: 600; }
  .card-body { padding: 18px; }

  /* Spec card */
  .spec-field { margin-bottom: 14px; }
  .spec-field label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
                      color: var(--text2); display: block; margin-bottom: 6px; }
  .spec-list { list-style: none; }
  .spec-list li { padding: 4px 0; font-size: 13px; display: flex; align-items: flex-start; gap: 8px; }
  .spec-list li::before { content: ''; width: 6px; height: 6px; border-radius: 50%;
                          background: var(--blue); margin-top: 6px; flex-shrink: 0; }
  .complexity-badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
                      font-size: 12px; font-weight: 600; }
  .complexity-simple { background: rgba(52,211,153,0.15); color: var(--green); }
  .complexity-medium { background: rgba(251,191,36,0.15); color: var(--amber); }
  .complexity-complex { background: rgba(248,113,113,0.15); color: var(--red); }

  /* HITL dialog */
  .hitl-actions { display: flex; gap: 10px; margin-top: 16px; align-items: flex-end; }
  .hitl-actions textarea { flex: 1; padding: 10px; background: var(--bg); border: 1px solid var(--border);
                           border-radius: 8px; color: var(--text); font-size: 13px;
                           resize: vertical; min-height: 40px; display: none; }
  .btn-approve { padding: 10px 20px; background: var(--green); color: #000; border: none;
                 border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px; }
  .btn-reject { padding: 10px 20px; background: transparent; color: var(--red);
                border: 1px solid var(--red); border-radius: 8px; cursor: pointer;
                font-weight: 600; font-size: 13px; }

  /* Code card */
  .code-block { border-radius: 8px; overflow: auto; max-height: 400px; }
  .code-block pre { margin: 0 !important; font-size: 13px !important; }
  .code-block code { font-family: 'SF Mono', 'Fira Code', monospace !important; }
  .code-files { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  .code-file-tag { font-size: 11px; padding: 3px 8px; background: var(--surface2);
                   border-radius: 4px; color: var(--text2); font-family: monospace; }

  /* Review card */
  .review-score { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .score-bar { flex: 1; height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
  .score-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
  .score-value { font-size: 20px; font-weight: 700; min-width: 50px; }
  .review-items { list-style: none; }
  .review-items li { padding: 6px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
  .review-items li:last-child { border: none; }

  /* Iteration history */
  .iteration-row { display: flex; align-items: center; gap: 10px; padding: 8px 0;
                   border-bottom: 1px solid var(--border); font-size: 13px; }
  .iteration-row:last-child { border: none; }
  .iter-num { font-weight: 700; color: var(--text2); min-width: 20px; }

  /* Status bar */
  .status-bar { padding: 8px 24px; background: var(--surface); border-top: 1px solid var(--border);
                font-size: 12px; color: var(--text2); display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; }
  .status-dot.idle { background: var(--text2); }
  .status-dot.running { background: var(--blue); animation: pulse 1.5s infinite; }
  .status-dot.done { background: var(--green); }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  /* Empty state */
  .empty-state { flex: 1; display: flex; flex-direction: column; align-items: center;
                 justify-content: center; color: var(--text2); gap: 12px; }
  .empty-state .icon { font-size: 48px; opacity: 0.3; }
  .empty-state p { font-size: 14px; }
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>AI Dev Team</h1>
    <div class="meta" id="meta">Loading...</div>
  </div>

  <div class="sidebar-section">
    <h3>Pipeline</h3>
    <div class="pipeline" id="pipeline">
      <div class="pipeline-step" id="step-ba">
        <div class="dot"></div>
        <span class="label">Business Analyst</span>
      </div>
      <div class="pipeline-step" id="step-hitl">
        <div class="dot"></div>
        <span class="label">Spec Review (HITL)</span>
      </div>
      <div class="pipeline-step" id="step-dev">
        <div class="dot"></div>
        <span class="label">Developer</span>
      </div>
      <div class="pipeline-step" id="step-qa">
        <div class="dot"></div>
        <span class="label">QA Engineer</span>
        <span class="badge" id="qa-badge" style="display:none"></span>
      </div>
      <div class="pipeline-step" id="step-github">
        <div class="dot"></div>
        <span class="label">GitHub PR</span>
      </div>
    </div>
  </div>

  <div class="sidebar-section">
    <h3>Workspace Files</h3>
    <div class="files-list" id="files-list">
      <span style="font-size:12px;color:var(--text2)">No files yet</span>
    </div>
  </div>

  <div class="sidebar-section">
    <h3>Saved Outputs</h3>
    <div class="files-list" id="outputs-list">
      <span style="font-size:12px;color:var(--text2)">No outputs yet</span>
    </div>
  </div>

  <div class="sidebar-footer">
    <button class="btn-reset" onclick="resetSession()">New Session</button>
  </div>
</div>

<div class="main">
  <div class="input-area">
    <div class="input-row">
      <input type="text" id="input" placeholder="Describe your user story... e.g. 'Write a CLI todo app in Python'" autofocus />
      <button class="btn-run" id="btn-run" onclick="run()">Run Pipeline</button>
    </div>
  </div>

  <div class="content" id="content">
    <div class="empty-state" id="empty">
      <div class="icon">&#x1f6e0;</div>
      <p>Enter a user story to start the AI development pipeline</p>
      <p style="font-size:12px">BA analyzes requirements &rarr; You approve the spec &rarr; Developer writes code &rarr; QA reviews</p>
    </div>
  </div>

  <div class="status-bar">
    <div class="status-dot idle" id="status-dot"></div>
    <span id="status-text">Ready</span>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
const content = $('content');
const input = $('input');
const btnRun = $('btn-run');
let activeSource = null;

// Load info
fetch('/api/info').then(r=>r.json()).then(d => {
  $('meta').innerHTML = `v${d.version}<br>BA: <b>${d.models.ba.split(':')[1]}</b><br>Dev: <b>${d.models.dev.split(':')[1]}</b><br>QA: <b>${d.models.qa.split(':')[1]}</b><br>Session: <code>${d.session_id}</code>`;
});

input.addEventListener('keydown', e => { if(e.key==='Enter' && !btnRun.disabled) run(); });

function setStatus(state, text) {
  $('status-dot').className = 'status-dot ' + state;
  $('status-text').textContent = text;
}

function setStep(id, cls) {
  const el = $('step-'+id);
  el.className = 'pipeline-step ' + cls;
}

function resetSteps() {
  ['ba','hitl','dev','qa','github'].forEach(s => setStep(s, ''));
  const qb = $('qa-badge');
  qb.style.display = 'none';
}

function loadFiles() {
  fetch('/api/files').then(r=>r.json()).then(files => {
    const el = $('files-list');
    if(!files.length) { el.innerHTML = '<span style="font-size:12px;color:var(--text2)">No files yet</span>'; return; }
    el.innerHTML = files.map(f =>
      `<div class="file-item" onclick="viewFile('${f.path}')"><span class="file-icon">&#x1f4c4;</span>${f.path}</div>`
    ).join('');
  });
}

function loadOutputs() {
  fetch('/api/outputs').then(r=>r.json()).then(outputs => {
    const el = $('outputs-list');
    if(!outputs.length) { el.innerHTML = '<span style="font-size:12px;color:var(--text2)">No outputs yet</span>'; return; }
    el.innerHTML = outputs.map(o =>
      `<div class="file-item" title="${o.files.join(', ')}"><span class="file-icon">&#x1f4c1;</span>${o.name}</div>`
    ).join('');
  });
}

function addCard(html) {
  if($('empty')) $('empty').style.display = 'none';
  const div = document.createElement('div');
  div.innerHTML = html;
  content.appendChild(div.firstElementChild);
  content.scrollTop = content.scrollHeight;
  return content.lastElementChild;
}

function makeSpecCard(spec, showActions) {
  const cx = spec.estimated_complexity;
  const cxClass = cx === 'simple' ? 'complexity-simple' : cx === 'medium' ? 'complexity-medium' : 'complexity-complex';
  let html = `<div class="card" id="spec-card">
    <div class="card-header">
      <span class="icon">&#x1f4cb;</span>
      <h3>Specification: ${spec.title}</h3>
      <span class="tag ${cxClass}">${cx}</span>
    </div>
    <div class="card-body">
      <div class="spec-field">
        <label>Requirements</label>
        <ul class="spec-list">${spec.requirements.map(r => `<li>${r}</li>`).join('')}</ul>
      </div>
      <div class="spec-field">
        <label>Acceptance Criteria</label>
        <ul class="spec-list">${spec.acceptance_criteria.map(a => `<li>${a}</li>`).join('')}</ul>
      </div>`;
  if (showActions) {
    html += `<div class="hitl-actions">
        <textarea id="hitl-feedback" placeholder="Feedback for revision (optional)..."></textarea>
        <button class="btn-approve" onclick="approveSpec(true)">Approve</button>
        <button class="btn-reject" onclick="toggleFeedback()">Reject</button>
      </div>`;
  }
  html += `</div></div>`;
  return html;
}

function makeCodeCard(code) {
  const escaped = code.source_code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return `<div class="card" id="code-card">
    <div class="card-header">
      <span class="icon">&#x1f4bb;</span>
      <h3>Generated Code</h3>
      <span class="tag" style="background:rgba(79,143,247,0.15);color:var(--blue)">${code.files_created.length} file(s)</span>
    </div>
    <div class="card-body">
      <p style="font-size:13px;color:var(--text2);margin-bottom:12px">${code.description}</p>
      <div class="code-files">${code.files_created.map(f => `<span class="code-file-tag">${f}</span>`).join('')}</div>
      <div class="code-block"><pre><code class="language-python">${escaped}</code></pre></div>
    </div>
  </div>`;
}

function makeReviewCard(review, iteration) {
  const isApproved = review.verdict === 'APPROVED';
  const scoreColor = review.score >= 0.8 ? 'var(--green)' : review.score >= 0.5 ? 'var(--amber)' : 'var(--red)';
  const verdictClass = isApproved ? 'badge-approved' : 'badge-revision';
  let html = `<div class="card">
    <div class="card-header">
      <span class="icon">&#x1f50d;</span>
      <h3>QA Review (Iteration ${iteration})</h3>
      <span class="tag ${verdictClass}">${review.verdict}</span>
    </div>
    <div class="card-body">
      <div class="review-score">
        <span class="score-value" style="color:${scoreColor}">${(review.score*100).toFixed(0)}%</span>
        <div class="score-bar"><div class="score-fill" style="width:${review.score*100}%;background:${scoreColor}"></div></div>
      </div>`;
  if (review.issues && review.issues.length) {
    html += `<div class="spec-field"><label>Issues</label>
      <ul class="review-items">${review.issues.map(i => `<li>&#x26a0; ${i}</li>`).join('')}</ul></div>`;
  }
  if (review.suggestions && review.suggestions.length) {
    html += `<div class="spec-field"><label>Suggestions</label>
      <ul class="review-items">${review.suggestions.map(s => `<li>&#x1f4a1; ${s}</li>`).join('')}</ul></div>`;
  }
  html += `</div></div>`;
  return html;
}

function toggleFeedback() {
  const ta = document.getElementById('hitl-feedback');
  if (ta.style.display === 'block') {
    approveSpec(false);
  } else {
    ta.style.display = 'block';
    ta.focus();
    ta.closest('.hitl-actions').querySelector('.btn-reject').textContent = 'Send & Revise';
  }
}

function approveSpec(approved) {
  const feedback = approved ? '' : (document.getElementById('hitl-feedback')?.value || '');
  const card = document.getElementById('spec-card');
  if (card) {
    const actions = card.querySelector('.hitl-actions');
    if (actions) actions.innerHTML = `<p style="color:${approved ? 'var(--green)' : 'var(--amber)'}; font-weight:600">${approved ? '&#x2713; Approved' : '&#x21bb; Sent for revision'}</p>`;
  }

  setStep('hitl', 'done');
  if (approved) {
    setStep('dev', 'active');
    setStatus('running', 'Developer writing code...');
  } else {
    setStep('ba', 'active');
    setStatus('running', 'BA revising spec...');
  }

  fetch('/api/approve', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({approved, feedback}),
  }).then(r => {
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    function read() {
      reader.read().then(({done, value}) => {
        if (done) return;
        buffer += decoder.decode(value, {stream:true});
        const lines = buffer.split('\\n');
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          handleEvent(JSON.parse(line.slice(6)));
        }
        read();
      });
    }
    read();
  });
}

function handleEvent(ev) {
  if (ev.type === 'stage') {
    // Update pipeline steps
    if (ev.stage === 'ba') {
      setStep('ba', 'active');
      setStatus('running', 'Business Analyst analyzing...');
      if (ev.spec) {
        setStep('ba', 'done');
      }
    }
    if (ev.stage === 'hitl') {
      setStep('ba', 'done');
      // Only set active if not already done (user may have approved already)
      if (!$('step-hitl').classList.contains('done')) {
        setStep('hitl', 'active');
      }
    }
    if (ev.stage === 'dev') {
      setStep('hitl', 'done');
      setStep('dev', 'active');
      setStatus('running', `Developer writing code (iter ${(ev.code?._iter||0)+1})...`);
      if (ev.code) {
        setStep('dev', 'done');
        addCard(makeCodeCard(ev.code));
        Prism.highlightAll();
        loadFiles(); loadOutputs();
      }
    }
    if (ev.stage === 'qa') {
      setStep('qa', 'active');
      setStatus('running', 'QA reviewing code...');
      if (ev.review) {
        const badge = $('qa-badge');
        badge.style.display = 'inline';
        badge.className = 'badge ' + (ev.review.verdict === 'APPROVED' ? 'badge-approved' : 'badge-revision');
        badge.textContent = ev.review.verdict === 'APPROVED' ? 'PASS' : `ITER ${ev.iteration}`;

        addCard(makeReviewCard(ev.review, ev.iteration));

        if (ev.review.verdict === 'APPROVED') {
          setStep('qa', 'done');
        } else {
          setStep('qa', '');
          setStep('dev', 'active');
          setStatus('running', `Developer revising (iteration ${ev.iteration+1})...`);
        }
      }
    }
    if (ev.stage === 'github') {
      setStep('qa', 'done');
      setStep('github', 'done');
      console.log('GitHub event:', JSON.stringify(ev));
      if (ev.pr_url) {
        addCard(`<div class="card">
          <div class="card-header"><span class="icon">&#x1f517;</span><h3>Pull Request Created</h3></div>
          <div class="card-body"><p style="font-size:14px"><a href="${ev.pr_url}" target="_blank" style="color:var(--blue)">${ev.pr_url}</a></p></div>
        </div>`);
      }
    }
  }

  if (ev.type === 'interrupt') {
    setStep('ba', 'done');
    setStep('hitl', 'active');
    setStatus('running', 'Waiting for your approval...');
    addCard(makeSpecCard(ev.data, true));
  }

  if (ev.type === 'error') {
    setStatus('idle', 'Error: ' + ev.message);
    btnRun.disabled = false;
    input.focus();
  }

  if (ev.type === 'done') {
    const msg = ev.output_path ? `Pipeline complete — saved to ${ev.output_path}` : 'Pipeline complete';
    setStatus('done', msg);
    if (ev.output_path) {
      let savedHtml = `<p style="font-size:13px;color:var(--green)">Output saved to: <code>${ev.output_path}</code></p>`;
      if (ev.pr_url) {
        savedHtml += `<p style="font-size:13px;margin-top:8px">PR: <a href="${ev.pr_url}" target="_blank" style="color:var(--blue)">${ev.pr_url}</a></p>`;
      }
      addCard(`<div class="card"><div class="card-header"><span class="icon">&#x1f4be;</span><h3>Results Saved</h3></div>
        <div class="card-body">${savedHtml}</div></div>`);
    }
    btnRun.disabled = false;
    input.focus();
    loadFiles(); loadOutputs();
  }
}

function run() {
  const q = input.value.trim();
  if (!q) return;
  input.value = '';
  btnRun.disabled = true;
  content.querySelectorAll('.card').forEach(c => c.remove());
  if($('empty')) $('empty').style.display = 'none';
  resetSteps();
  setStep('ba', 'active');
  setStatus('running', 'Business Analyst analyzing user story...');

  const es = new EventSource('/api/run?q=' + encodeURIComponent(q));
  activeSource = es;

  // Show user story card
  addCard(`<div class="card">
    <div class="card-header"><span class="icon">&#x1f4dd;</span><h3>User Story</h3></div>
    <div class="card-body"><p style="font-size:14px">${q}</p></div>
  </div>`);

  es.onmessage = e => {
    const ev = JSON.parse(e.data);
    handleEvent(ev);
    if (ev.type === 'done' || ev.type === 'error') { es.close(); activeSource = null; }
  };
  es.onerror = () => { es.close(); activeSource = null; btnRun.disabled = false;
                        setStatus('idle', 'Connection lost'); };
}

function viewFile(path) {
  fetch('/api/files/' + encodeURIComponent(path))
    .then(r => r.text())
    .then(text => {
      const escaped = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const ext = path.split('.').pop();
      const lang = ext === 'py' ? 'python' : 'plaintext';
      addCard(`<div class="card">
        <div class="card-header"><span class="icon">&#x1f4c4;</span><h3>${path}</h3></div>
        <div class="card-body"><div class="code-block"><pre><code class="language-${lang}">${escaped}</code></pre></div></div>
      </div>`);
      Prism.highlightAll();
    });
}

function resetSession() {
  fetch('/api/reset', {method:'POST'}).then(() => {
    content.querySelectorAll('.card').forEach(c => c.remove());
    if($('empty')) $('empty').style.display = 'flex';
    resetSteps();
    setStatus('idle', 'Ready');
    loadFiles(); loadOutputs();
    fetch('/api/info').then(r=>r.json()).then(d => {
      $('meta').innerHTML = `v${d.version}<br>BA: <b>${d.models.ba.split(':')[1]}</b><br>Dev: <b>${d.models.dev.split(':')[1]}</b><br>QA: <b>${d.models.qa.split(':')[1]}</b><br>Session: <code>${d.session_id}</code>`;
    });
    input.focus();
  });
}

loadFiles(); loadOutputs();
</script>
</body>
</html>
"""
