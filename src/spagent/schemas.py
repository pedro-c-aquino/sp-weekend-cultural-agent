from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, List


class Event(BaseModel):
    title: str
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


class EvalScore(BaseModel):
    coverage: float = Field(ge=0, le=1)
    freshness_ok: bool
    hallucination_risk: float = Field(ge=0, le=1)
    notes: Optional[str] = None
