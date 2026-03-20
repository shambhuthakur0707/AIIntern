from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InternshipOut(BaseModel):
    title: str
    company: str
    location: str
    state: str
    source: str
    url: str
    posted_at: Optional[str] = None
    role_tag: str = Field(default="General")


class RefreshResult(BaseModel):
    fetched: int
    deduped: int
    stored: int
    run_at: datetime
