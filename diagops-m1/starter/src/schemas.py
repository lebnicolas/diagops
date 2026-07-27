from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiagOpsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: str | None
    symptom: str
    severity: Literal["low", "medium", "high", "critical"]
    failure_hypothesis: str
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    requires_human_review: bool
