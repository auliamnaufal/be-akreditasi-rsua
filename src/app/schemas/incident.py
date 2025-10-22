from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..models.incident import IncidentCategory, IncidentStatus


class IncidentBase(BaseModel):
    patient_identifier: str | None = None
    occurred_at: datetime | None = None
    location_id: int | None = None
    department_id: int | None = None
    free_text_description: str = Field(min_length=10)
    harm_indicator: str | None = None
    attachments: List[str] | None = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(IncidentBase):
    status: IncidentStatus | None = None


class IncidentSubmitRequest(BaseModel):
    confirm_submit: bool = True


class IncidentPrediction(BaseModel):
    category: IncidentCategory
    confidence: float
    model_version: str


class IncidentReview(BaseModel):
    category: IncidentCategory
    notes: str | None = None


class IncidentRead(BaseModel):
    id: int
    reporter_id: int
    patient_identifier: str | None
    occurred_at: datetime
    location_id: int | None
    department_id: int | None
    free_text_description: str
    harm_indicator: str | None
    attachments: List[str] | None
    status: IncidentStatus
    predicted_category: IncidentCategory | None
    predicted_confidence: float | None
    model_version: str | None
    pj_decision: IncidentCategory | None
    pj_notes: str | None
    mutu_decision: IncidentCategory | None
    mutu_notes: str | None
    final_category: IncidentCategory | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
