from datetime import datetime
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import JSON
from sqlmodel import Column, Enum as SQLEnum, Field, Relationship

from .base import IDModel, TimestampedModel

if TYPE_CHECKING:  # pragma: no cover
    from .department import Department
    from .location import Location
    from .user import User


class IncidentStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PJ_REVIEWED = "PJ_REVIEWED"
    MUTU_REVIEWED = "MUTU_REVIEWED"
    CLOSED = "CLOSED"


class IncidentCategory(str, Enum):
    """Accreditation standard categories: KTD, KTC, KNC, KPCS, Sentinel."""

    KTD = "KTD"  # Kejadian Tidak Diharapkan
    KTC = "KTC"  # Kejadian Tidak Cedera
    KNC = "KNC"  # Kejadian Nyaris Cedera
    KPCS = "KPCS"  # Kejadian Potensial Cedera Serius
    SENTINEL = "Sentinel"  # Sentinel Event


class Incident(IDModel, TimestampedModel, table=True):
    __tablename__ = "incidents"

    reporter_id: int = Field(foreign_key="users.id", index=True)
    patient_identifier: Optional[str] = Field(default=None, index=True)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    location_id: Optional[int] = Field(default=None, foreign_key="locations.id")
    department_id: Optional[int] = Field(default=None, foreign_key="departments.id")
    free_text_description: str
    harm_indicator: Optional[str] = Field(default=None)
    attachments: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: IncidentStatus = Field(
        default=IncidentStatus.DRAFT,
        sa_column=Column(SQLEnum(IncidentStatus), default=IncidentStatus.DRAFT, nullable=False, index=True),
    )

    predicted_category: Optional[IncidentCategory] = Field(default=None, sa_column=Column(SQLEnum(IncidentCategory), nullable=True))
    predicted_confidence: Optional[float] = Field(default=None)
    model_version: Optional[str] = Field(default=None)
    pj_decision: Optional[IncidentCategory] = Field(default=None, sa_column=Column(SQLEnum(IncidentCategory), nullable=True))
    pj_notes: Optional[str] = Field(default=None)
    mutu_decision: Optional[IncidentCategory] = Field(default=None, sa_column=Column(SQLEnum(IncidentCategory), nullable=True))
    mutu_notes: Optional[str] = Field(default=None)
    final_category: Optional[IncidentCategory] = Field(default=None, sa_column=Column(SQLEnum(IncidentCategory), nullable=True))

    reporter: "User" = Relationship(back_populates="reported_incidents")
    location: Optional["Location"] = Relationship(back_populates="incidents")
    department: Optional["Department"] = Relationship(back_populates="incidents")
    audit_logs: List["AuditLog"] = Relationship(back_populates="incident")


class AuditLog(IDModel, TimestampedModel, table=True):
    __tablename__ = "audit_logs"

    incident_id: int = Field(foreign_key="incidents.id", index=True)
    actor_id: int = Field(foreign_key="users.id")
    from_status: Optional[IncidentStatus] = Field(default=None, sa_column=Column(SQLEnum(IncidentStatus), nullable=True))
    to_status: Optional[IncidentStatus] = Field(default=None, sa_column=Column(SQLEnum(IncidentStatus), nullable=True))
    payload_diff: Optional[str] = Field(default=None)

    incident: Incident = Relationship(back_populates="audit_logs")
