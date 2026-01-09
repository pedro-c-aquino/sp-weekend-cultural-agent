from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Any, Dict, Literal, Optional, List


class Event(BaseModel):
    title: Optional[str]
    starts_at: Optional[str]
    ends_at: Optional[str] = None
    date_text: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = "São Paulo"
    category: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None


class EventList(BaseModel):
    events: List[Event]


class EvalScore(BaseModel):
    coverage: float = Field(ge=0, le=1)
    freshness_ok: bool
    hallucination_risk: float = Field(ge=0, le=1)
    notes: Optional[str] = None


class Evaluation(BaseModel):
    title: str
    is_event: bool


class Result(BaseModel):
    title: str
    snippet: str
    url: str
    source: Optional[str]
    date: Optional[str]


ToolName = Literal[
    "fetch_sympla",
    "fetch_sesc",
    "fetch_eventim",
    "fetch_sao_paulo_secreto",
    "extract_events",
    "dedupe_events",
    "validate_events",
    "websearch_events",
    "stop",
]


class PlanStep(BaseModel):
    tool: ToolName
    description: str
    params: Dict[str, Any] = Field(default_factory=dict)


class SuccessCriteria(BaseModel):
    min_events: int = 10
    city: Optional[str] = "São Paulo"
    date_range_required: bool = True


class FallbackPlan(BaseModel):
    trigger: str
    steps: List[PlanStep]


class Plan(BaseModel):
    goal: str
    strategy: str
    steps: List[PlanStep]
    success_criteria: SuccessCriteria
    fallback: Optional[FallbackPlan] = None


class StepResult(BaseModel):
    tool: ToolName
    ok: bool = None
    events_found: Optional[int] = None
    errors: Optional[int] = 0
    duration_ms: Optional[int] = None
    notes: Optional[str] = None


class ExecutionSummary(BaseModel):
    total_events: int
    sources_used: List[str]
    errors: int = 0


class FetchResult(BaseModel):
    url: str
    html: str
    source: str
