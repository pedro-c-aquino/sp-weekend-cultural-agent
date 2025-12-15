from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, List


class Source(BaseModel):
    name: str
    url: HttpUrl | str


class Event(BaseModel):
    title: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    venue: Optional[str] = None
    city: Optional[str] = "São Paulo"
    category: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None
    source: Optional[Source] = None


class EvalScore(BaseModel):
    coverage: float = Field(ge=0, le=1)
    freshness_ok: bool
    hallucination_risk: float = Field(ge=0, le=1)
    notes: Optional[str] = None
