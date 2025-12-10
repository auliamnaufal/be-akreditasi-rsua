from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from ...models.incident import AuditLog, Incident, IncidentCategory, IncidentGrading, IncidentStatus, SKPCode, MDPCode
from ...models.user import User
from ...services.ml import predict_incident, predict_skp_mdp
from .state import ensure_transition


def create_audit_log(
    session: Session,
    incident: Incident,
    actor: User,
    from_status: IncidentStatus,
    to_status: IncidentStatus,
    payload_diff: Dict[str, Any] | None = None,
) -> None:
    log = AuditLog(
        incident_id=incident.id,
        actor_id=actor.id,
        from_status=from_status,
        to_status=to_status,
        payload_diff=None if payload_diff is None else str(payload_diff),
    )
    session.add(log)

def _month_range(dt: datetime) -> tuple[datetime, datetime]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month


def _frequency_to_probability(freq: int) -> int | None:
    if freq is None:
        return None
    if freq == 0:
        return 1
    if freq == 1:
        return 3
    if freq in (2, 3):
        return 4
    return 5


def _harm_to_severity(text: str | None) -> int | None:
    if not text:
        return None
    lower = text.strip().lower()
    if "tidak ada cedera" in lower or "tidak ada cidera" in lower:
        return 1
    if "ringan" in lower:
        return 2
    if "reversible" or "berkurangnya" or "robek" in lower:
        return 3
    if "irreversible" or "luas" or "berat" or "cacat" or "lumpuh" or "kehilangan" in lower:
        return 4
    if "kematian" in lower:
        return 5

    return None


def _matrix_grade(prob: int | None, severity: int | None) -> IncidentGrading | None:
    if prob is None or severity is None:
        return None
    matrix = {
        5: {1: IncidentGrading.HIJAU, 2: IncidentGrading.HIJAU, 3: IncidentGrading.KUNING, 4: IncidentGrading.MERAH, 5: IncidentGrading.MERAH},
        4: {1: IncidentGrading.HIJAU, 2: IncidentGrading.HIJAU, 3: IncidentGrading.KUNING, 4: IncidentGrading.MERAH, 5: IncidentGrading.MERAH},
        3: {1: IncidentGrading.BIRU, 2: IncidentGrading.HIJAU, 3: IncidentGrading.KUNING, 4: IncidentGrading.MERAH, 5: IncidentGrading.MERAH},
        2: {1: IncidentGrading.BIRU, 2: IncidentGrading.BIRU, 3: IncidentGrading.HIJAU, 4: IncidentGrading.KUNING, 5: IncidentGrading.MERAH},
        1: {1: IncidentGrading.BIRU, 2: IncidentGrading.BIRU, 3: IncidentGrading.HIJAU, 4: IncidentGrading.KUNING, 5: IncidentGrading.MERAH},
    }
    return matrix.get(prob, {}).get(severity)


def compute_grading(session: Session, incident: Incident) -> IncidentGrading | None:
    if incident.department_id is None or incident.occurred_at is None:
        return None

    month_start, next_month = _month_range(incident.occurred_at)
    freq_query = (
        select(func.count(Incident.id))
        .where(
            Incident.department_id == incident.department_id,
            Incident.occurred_at >= month_start,
            Incident.occurred_at < next_month,
        )
    )
    monthly_count = session.exec(freq_query).one()
    probability = _frequency_to_probability(int(monthly_count))
    severity = _harm_to_severity(incident.harm_indicator)
    return _matrix_grade(probability, severity)


def submit_incident(session: Session, incident: Incident, actor: User) -> Incident:
    ensure_transition(incident, IncidentStatus.SUBMITTED, {role.name for role in actor.roles})
    previous_status = incident.status
    prediction = predict_incident(incident.free_text_description, {"department": incident.department_id})
    incident.predicted_category = prediction["category"]
    incident.predicted_confidence = prediction["confidence"]
    incident.model_version = prediction["model_version"]
    skp_mdp = predict_skp_mdp(incident.free_text_description)
    print(skp_mdp)
    if skp_mdp.get("skp"):
        skp_label = str(skp_mdp["skp"]).strip().lower().replace(" ", "")
        if skp_label.isdigit():
            skp_label = f"skp{skp_label}"
        code_map = {code.value: code for code in SKPCode}
        incident.skp_code = code_map.get(skp_label)
    if skp_mdp.get("mdp"):
        mdp_label = str(skp_mdp["mdp"]).strip().lower().replace(" ", "")
        if mdp_label.isdigit():
            mdp_label = f"mdp{mdp_label}"
        code_map = {code.value: code for code in MDPCode}
        incident.mdp_code = code_map.get(mdp_label)
    # Placeholder: future ML can set SKP/MDP here
    incident.grading = compute_grading(session, incident)
    incident.status = IncidentStatus.SUBMITTED
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        session,
        incident,
        actor,
        previous_status,
        IncidentStatus.SUBMITTED,
        payload_diff={
            "prediction": {
                "category": incident.predicted_category.value if incident.predicted_category else None,
                "confidence": incident.predicted_confidence,
                "model_version": incident.model_version,
            },
            "grading": incident.grading.value if incident.grading else None,
        },
    )
    session.add(incident)
    return incident


def update_category(session: Session, incident: Incident, actor: User, category: IncidentCategory) -> Incident:
    if incident.status == IncidentStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail={"error_code": "invalid_state", "message": "Submit the incident before editing its category"},
        )
    if incident.status == IncidentStatus.CLOSED:
        raise HTTPException(
            status_code=409,
            detail={"error_code": "invalid_state", "message": "Cannot edit category for closed incidents"},
        )

    previous_category = incident.final_category
    incident.final_category = category
    incident.last_category_editor_id = actor.id
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        session,
        incident,
        actor,
        incident.status,
        incident.status,
        payload_diff={
            "previous_category": previous_category.value if previous_category else None,
            "final_category": category.value,
            "last_category_editor_id": actor.id,
        },
    )
    session.add(incident)
    return incident


def close_incident(session: Session, incident: Incident, actor: User) -> Incident:
    ensure_transition(incident, IncidentStatus.CLOSED, {role.name for role in actor.roles})
    if incident.final_category is None:
        raise HTTPException(status_code=409, detail={"error_code": "final_category_missing", "message": "Final category required before closing"})
    previous_status = incident.status
    incident.status = IncidentStatus.CLOSED
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(session, incident, actor, previous_status, IncidentStatus.CLOSED)
    session.add(incident)
    return incident
