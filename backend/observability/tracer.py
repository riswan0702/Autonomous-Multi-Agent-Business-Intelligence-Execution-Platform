"""
Observability module:
- Per-agent tracing (start time, end time, latency snapshot)
- Token tracking per agent and per run
- Error tracking
- Structured JSON logs
- In-memory run store (production: replace with Redis/DB)
"""

import json
import time
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from core.schemas import AgentTrace, AgentStatus
from core.security import redact_sensitive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("bi-platform")


class AgentTracer:
    """Traces a single agent's execution."""

    def __init__(self, run_id: str, agent_name: str, model: str = ""):
        self.run_id = run_id
        self.agent_name = agent_name
        self.model = model
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._start_ts: Optional[float] = None
        self._end_ts: Optional[float] = None   # FIX: snapshot latency at completion
        self.tokens_input = 0
        self.tokens_output = 0
        self.status = AgentStatus.PENDING
        self.output_preview = ""
        self.error: Optional[str] = None
        self.iteration = 0
        self.logs: List[Dict] = []

    def start(self):
        self.status = AgentStatus.RUNNING
        self.start_time = datetime.utcnow()
        self._start_ts = time.time()
        self._log("info", f"Agent {self.agent_name} started")

    def complete(self, output: str, tokens_in: int, tokens_out: int, model: str = ""):
        self.status = AgentStatus.COMPLETED
        self.end_time = datetime.utcnow()
        self._end_ts = time.time()   # FIX: snapshot so latency_ms stays accurate
        self.tokens_input += tokens_in
        self.tokens_output += tokens_out
        if model:
            self.model = model
        self.output_preview = redact_sensitive(output[:300])
        self._log("info", f"Agent {self.agent_name} completed", {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model": self.model,
            "latency_ms": self.latency_ms,
        })

    def fail(self, error: str):
        self.status = AgentStatus.FAILED
        self.end_time = datetime.utcnow()
        self._end_ts = time.time()
        self.error = error
        self._log("error", f"Agent {self.agent_name} failed: {error}")

    @property
    def latency_ms(self) -> Optional[float]:
        """Returns snapshotted latency (accurate even after run completes)."""
        if self._start_ts is None:
            return None
        end = self._end_ts if self._end_ts else time.time()
        return round((end - self._start_ts) * 1000, 1)

    def _log(self, level: str, message: str, extra: Dict = None):
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "agent": self.agent_name,
            "level": level,
            "msg": message,
        }
        if extra:
            entry.update(extra)
        self.logs.append(entry)
        getattr(logger, level, logger.info)(json.dumps(entry))

    def to_trace(self) -> AgentTrace:
        return AgentTrace(
            agent_name=self.agent_name,
            status=self.status,
            start_time=self.start_time,
            end_time=self.end_time,
            latency_ms=self.latency_ms,
            tokens_input=self.tokens_input,
            tokens_output=self.tokens_output,
            model_used=self.model,
            output_preview=self.output_preview,
            error=self.error,
            iteration=self.iteration,
        )


class RunTracer:
    """Tracks an entire multi-agent workflow run."""

    def __init__(self, run_id: str, business_input: Dict):
        self.run_id = run_id
        self.business_input = business_input
        self.created_at = datetime.utcnow()
        self.agent_tracers: Dict[str, AgentTracer] = {}
        self.status = AgentStatus.PENDING
        self._start_ts = time.time()
        self._final_report = None

    def start_agent(self, agent_name: str, model: str = "") -> AgentTracer:
        tracer = AgentTracer(self.run_id, agent_name, model)
        tracer.start()
        self.agent_tracers[agent_name] = tracer
        return tracer

    def get_traces(self) -> List[AgentTrace]:
        return [t.to_trace() for t in self.agent_tracers.values()]

    def get_total_tokens(self) -> int:
        return sum(
            t.tokens_input + t.tokens_output
            for t in self.agent_tracers.values()
        )

    def get_all_logs(self) -> List[Dict]:
        logs = []
        for t in self.agent_tracers.values():
            logs.extend(t.logs)
        return sorted(logs, key=lambda x: x.get("ts", ""))

    def get_summary(self) -> Dict[str, Any]:
        total_time = round((time.time() - self._start_ts) * 1000, 1)
        return {
            "run_id": self.run_id,
            "status": self.status,
            "total_latency_ms": total_time,
            "total_tokens": self.get_total_tokens(),
            "agents_completed": sum(
                1 for t in self.agent_tracers.values()
                if t.status == AgentStatus.COMPLETED
            ),
            "agents_failed": sum(
                1 for t in self.agent_tracers.values()
                if t.status == AgentStatus.FAILED
            ),
        }



_run_store: Dict[str, RunTracer] = {}


def create_run_tracer(business_input: Dict) -> tuple[str, RunTracer]:
    run_id = str(uuid.uuid4())[:8]
    tracer = RunTracer(run_id, business_input)
    _run_store[run_id] = tracer
    return run_id, tracer


def get_run_tracer(run_id: str) -> Optional[RunTracer]:
    return _run_store.get(run_id)


def list_runs() -> List[Dict]:
    return [
        {
            "run_id": run_id,
            "created_at": t.created_at.isoformat(),
            "status": t.status,
            "total_tokens": t.get_total_tokens(),
        }
        for run_id, t in sorted(
            _run_store.items(),
            key=lambda x: x[1].created_at,
            reverse=True,
        )
    ]
