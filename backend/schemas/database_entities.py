from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=160)
    report_type: str = Field(..., min_length=2, max_length=80)
    parameters: dict[str, Any] | None = None


class PlanningRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="normal", max_length=30)
    due_date: datetime | None = None
