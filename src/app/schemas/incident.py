from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..models.incident import (
    AgeGroup,
    Gender,
    IncidentCategory,
    IncidentGrading,
    IncidentOutcome,
    IncidentPlace,
    IncidentStatus,
    IncidentSubject,
    MDPCode,
    PatientContext,
    PayerType,
    ReporterType,
    ResponderRole,
    SKPCode,
)


class IncidentBase(BaseModel):
    patient_name: str | None = None
    patient_identifier: str | None = None
    reporter_type: ReporterType | None = None
    age: int | None = None
    age_group: AgeGroup | None = None
    gender: Gender | None = None
    payer_type: PayerType | None = None
    admission_at: datetime | None = None
    occurred_at: datetime | None = None
    incident_place: IncidentPlace | None = None
    incident_subject: IncidentSubject | None = None
    patient_context: PatientContext | None = None
    responder_roles: list[ResponderRole] | None = None
    immediate_action: str | None = None
    has_similar_event: bool | None = None
    department_id: int | None = None
    free_text_description: str = Field(min_length=10)
    harm_indicator: str | None = None


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


class IncidentCategoryUpdate(BaseModel):
    category: IncidentCategory


class IncidentRead(BaseModel):
    id: int
    reporter_id: int
    patient_name: str | None
    patient_identifier: str | None
    reporter_type: ReporterType | None
    age: int | None
    age_group: AgeGroup | None
    gender: Gender | None
    payer_type: PayerType | None
    admission_at: datetime | None
    occurred_at: datetime
    incident_place: IncidentPlace | None
    skp_code: SKPCode | None
    mdp_code: MDPCode | None
    incident_subject: IncidentSubject | None
    patient_context: PatientContext | None
    responder_roles: list[ResponderRole] | None
    immediate_action: str | None
    has_similar_event: bool | None
    department_id: int | None
    free_text_description: str
    harm_indicator: str | None
    status: IncidentStatus
    predicted_category: IncidentCategory | None
    predicted_confidence: float | None
    model_version: str | None
    grading: IncidentGrading | None
    pj_decision: IncidentCategory | None
    pj_notes: str | None
    mutu_decision: IncidentCategory | None
    mutu_notes: str | None
    final_category: IncidentCategory | None
    last_category_editor_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
