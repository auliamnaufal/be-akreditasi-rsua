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
    SENTINEL = "SENTINEL"  # Sentinel Event


class IncidentGrading(str, Enum):
    BIRU = "BIRU"
    HIJAU = "HIJAU"
    KUNING = "KUNING"
    MERAH = "MERAH"


class AgeGroup(str, Enum):
    BAYI = "bayi"
    BALITA = "balita"
    ANAK = "anak"
    REMAJA = "remaja"
    DEWASA = "dewasa"
    LANSIA = "lansia"


class Gender(str, Enum):
    L = "l"
    P = "p"


class PayerType(str, Enum):
    UMUM = "umum"
    BPJS_MANDIRI = "bpjs-mandiri"
    SKTM = "sktm"


class ReporterType(str, Enum):
    DOKTER = "dokter"
    PERAWAT = "perawat"
    PETUGAS = "petugas"
    PASIEN = "pasien"
    KELUARGA = "keluarga"
    PENGUNJUNG = "pengunjung"
    LAIN = "lain"


class IncidentPlace(str, Enum):
    PENYAKIT_DALAM = "penyakit-dalam"
    ANAK = "anak"
    BEDAH = "bedah"
    OBSGYN = "obsgyn"
    THT = "tht"
    MATA = "mata"
    SARAF = "saraf"
    ANESTESI = "anestesi"
    KULIT_KELAMIN = "kulit-kelamin"
    JANTUNG = "jantung"
    PARU = "paru"
    JIWA = "jiwa"
    LAIN = "lain"


class IncidentOutcome(str, Enum):
    KEMATIAN = "kematian"
    BERAT = "berat"
    SEDANG = "sedang"
    RINGAN = "ringan"
    TIDAK_CEDERA = "tidak-cedera"


class IncidentSubject(str, Enum):
    PASIEN = "pasien"
    LAIN = "lain"


class PatientContext(str, Enum):
    RAWAT_INAP = "rawat-inap"
    UGD = "ugd"
    RAWAT_JALAN = "rawat-jalan"
    LAIN = "lain"


class ResponderRole(str, Enum):
    TIM = "tim"
    DOKTER = "dokter"
    PERAWAT = "perawat"
    PETUGAS_LAINNYA = "petugas-lainnya"


class SKPCode(str, Enum):
    SKP1 = "skp1"
    SKP2 = "skp2"
    SKP3 = "skp3"
    SKP4 = "skp4"
    SKP5 = "skp5"
    SKP6 = "skp6"


class MDPCode(str, Enum):
    MDP1 = "mdp1"
    MDP2 = "mdp2"
    MDP3 = "mdp3"
    MDP4 = "mdp4"
    MDP5 = "mdp5"
    MDP6 = "mdp6"
    MDP7 = "mdp7"
    MDP8 = "mdp8"
    MDP9 = "mdp9"
    MDP10 = "mdp10"
    MDP11 = "mdp11"
    MDP12 = "mdp12"
    MDP13 = "mdp13"
    MDP14 = "mdp14"
    MDP15 = "mdp15"
    MDP16 = "mdp16"
    MDP17 = "mdp17"


class Incident(IDModel, TimestampedModel, table=True):
    __tablename__ = "incidents"

    patient_name: Optional[str] = Field(default=None)
    reporter_id: int = Field(foreign_key="users.id", index=True)
    patient_identifier: Optional[str] = Field(default=None, index=True)
    reporter_type: Optional[ReporterType] = Field(
        default=None, sa_column=Column(SQLEnum(ReporterType, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    age: Optional[int] = Field(default=None)
    age_group: Optional[AgeGroup] = Field(
        default=None, sa_column=Column(SQLEnum(AgeGroup, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    gender: Optional[Gender] = Field(
        default=None, sa_column=Column(SQLEnum(Gender, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    payer_type: Optional[PayerType] = Field(
        default=None, sa_column=Column(SQLEnum(PayerType, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    admission_at: Optional[datetime] = Field(default=None)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    incident_place: Optional[IncidentPlace] = Field(
        default=None, sa_column=Column(SQLEnum(IncidentPlace, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    incident_unit: Optional[str] = Field(default=None)
    incident_outcome: Optional[IncidentOutcome] = Field(
        default=None, sa_column=Column(SQLEnum(IncidentOutcome, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    skp_code: Optional[SKPCode] = Field(
        default=None, sa_column=Column(SQLEnum(SKPCode, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    mdp_code: Optional[MDPCode] = Field(
        default=None, sa_column=Column(SQLEnum(MDPCode, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    incident_subject: Optional[IncidentSubject] = Field(
        default=None, sa_column=Column(SQLEnum(IncidentSubject, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    patient_context: Optional[PatientContext] = Field(
        default=None, sa_column=Column(SQLEnum(PatientContext, values_callable=lambda e: [i.value for i in e]), nullable=True)
    )
    responder_roles: Optional[list[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    immediate_action: Optional[str] = Field(default=None)
    has_similar_event: Optional[bool] = Field(default=None)
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
    last_category_editor_id: Optional[int] = Field(default=None, foreign_key="users.id")
    grading: Optional["IncidentGrading"] = Field(default=None, sa_column=Column(SQLEnum(IncidentGrading), nullable=True))

    reporter: "User" = Relationship(
        back_populates="reported_incidents",
        sa_relationship_kwargs={"foreign_keys": "Incident.reporter_id"},
    )
    last_category_editor: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Incident.last_category_editor_id"},
    )
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
