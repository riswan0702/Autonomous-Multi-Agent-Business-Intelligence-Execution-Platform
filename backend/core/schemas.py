from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BusinessInput(BaseModel):
    company: str = Field(..., min_length=3, max_length=500)
    product: str = Field(..., min_length=10, max_length=1000)
    target_audience: str = Field(..., min_length=5, max_length=500)
    goals: str = Field(..., min_length=10, max_length=1000)
    constraints: Optional[str] = Field(default="", max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "company": "FitAI India",
                "product": "AI-powered fitness app for workout tracking, nutrition, and stress management",
                "target_audience": "Working professionals aged 25-40 in Tier 1 Indian cities",
                "goals": "Launch GTM strategy, reach 10,000 users in 6 months",
                "constraints": "Bootstrap budget under ₹50L, team of 5"
            }
        }


class AgentTrace(BaseModel):
    agent_name: str
    status: AgentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    latency_ms: Optional[float] = None
    tokens_input: int = 0
    tokens_output: int = 0
    model_used: str = ""
    output_preview: str = ""
    error: Optional[str] = None
    iteration: int = 0


class WorkflowRun(BaseModel):
    run_id: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    input: BusinessInput
    agent_traces: List[AgentTrace] = []
    total_tokens: int = 0
    final_report: Optional[Dict[str, Any]] = None
    qa_score: Optional[float] = None
    error: Optional[str] = None


class AgentMessage(BaseModel):
    agent: str
    content: str
    timestamp: datetime
    tokens: int = 0


class StreamEvent(BaseModel):
    type: str  # agent_start | agent_complete | agent_error | workflow_complete | log
    run_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
