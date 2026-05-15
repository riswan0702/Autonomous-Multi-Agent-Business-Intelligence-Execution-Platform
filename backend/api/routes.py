"""
API Routes:
- POST /api/run — start a new BI workflow
- GET /api/run/{run_id}/stream — SSE streaming of agent events
- GET /api/run/{run_id} — get run status and final report
- GET /api/runs — list all runs
- GET /api/runs/{run_id}/logs — get full agent logs
- GET /api/health — health check
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from core.schemas import BusinessInput, AgentStatus
from core.security import validate_business_input, check_rate_limit, SecurityError
from observability.tracer import create_run_tracer, get_run_tracer, list_runs
from agents.orchestrator import OrchestratorAgent

router = APIRouter()

# In-memory event queues for SSE (run_id → asyncio.Queue)
_event_queues: dict[str, asyncio.Queue] = {}


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "bi-platform",
    }


@router.post("/api/run")
async def start_run(
    body: BusinessInput,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """Start a new multi-agent BI workflow."""
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # Security validation
    try:
        safe_input = validate_business_input(body.model_dump())
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create run
    run_id, run_tracer = create_run_tracer(safe_input)
    _event_queues[run_id] = asyncio.Queue()

    # Run in background
    background_tasks.add_task(_run_pipeline, run_id, safe_input, run_tracer)

    return {
        "run_id": run_id,
        "status": "started",
        "stream_url": f"/api/run/{run_id}/stream",
        "status_url": f"/api/run/{run_id}",
    }


async def _run_pipeline(run_id: str, business_input: dict, run_tracer):
    """Background task that runs the full agent pipeline."""
    queue = _event_queues.get(run_id)
    orchestrator = OrchestratorAgent()

    async def emit(event_type: str, data: dict):
        event = {
            "type": event_type,
            "run_id": run_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if queue:
            await queue.put(event)

    try:
        final_report = await orchestrator.run(
            run_id=run_id,
            business_input=business_input,
            run_tracer=run_tracer,
            event_callback=emit,
        )
        run_tracer._final_report = final_report

    except Exception as e:
        run_tracer.status = AgentStatus.FAILED
        if queue:
            await queue.put({
                "type": "workflow_error",
                "run_id": run_id,
                "data": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
            })
    finally:
        # Signal stream end
        if queue:
            await queue.put(None)


@router.get("/api/run/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    """SSE endpoint for real-time agent event streaming."""
    queue = _event_queues.get(run_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({"run_id": run_id, "message": "Connected to agent stream"}),
        }

        while True:
            if await request.is_disconnected():
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": json.dumps({"ts": datetime.utcnow().isoformat()})}
                continue

            if event is None:
                yield {"event": "done", "data": json.dumps({"run_id": run_id})}
                break

            yield {
                "event": event["type"],
                "data": json.dumps(event),
            }

    return EventSourceResponse(event_generator())


@router.get("/api/run/{run_id}")
async def get_run(run_id: str):
    """Get run status, traces, and final report."""
    run_tracer = get_run_tracer(run_id)
    if not run_tracer:
        raise HTTPException(status_code=404, detail="Run not found")

    final_report = getattr(run_tracer, "_final_report", None)

    return {
        "run_id": run_id,
        "status": run_tracer.status,
        "created_at": run_tracer.created_at.isoformat(),
        "agent_traces": [t.model_dump() for t in run_tracer.get_traces()],
        "summary": run_tracer.get_summary(),
        "final_report": final_report,
    }


@router.get("/api/runs")
async def list_all_runs():
    """List all workflow runs."""
    return {"runs": list_runs()}


@router.get("/api/run/{run_id}/logs")
async def get_logs(run_id: str):
    """Get full agent logs for a run."""
    run_tracer = get_run_tracer(run_id)
    if not run_tracer:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": run_id,
        "logs": run_tracer.get_all_logs(),
        "summary": run_tracer.get_summary(),
    }
