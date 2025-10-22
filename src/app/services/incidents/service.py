from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException
from sqlmodel import Session

from ...models.incident import AuditLog, Incident, IncidentCategory, IncidentStatus
from ...models.user import User
from ...services.ml import predict_incident
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


def submit_incident(session: Session, incident: Incident, actor: User) -> Incident:
    ensure_transition(incident, IncidentStatus.SUBMITTED, {role.name for role in actor.roles})
    previous_status = incident.status
    prediction = predict_incident(incident.free_text_description, {"department": incident.department_id})
    incident.predicted_category = prediction["category"]
    incident.predicted_confidence = prediction["confidence"]
    incident.model_version = prediction["model_version"]
    incident.status = IncidentStatus.SUBMITTED
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(session, incident, actor, previous_status, IncidentStatus.SUBMITTED, payload_diff={"prediction": prediction})
    session.add(incident)
    return incident


def pj_review(session: Session, incident: Incident, actor: User, category: IncidentCategory, notes: str | None) -> Incident:
    ensure_transition(incident, IncidentStatus.PJ_REVIEWED, {role.name for role in actor.roles})
    previous_status = incident.status
    incident.pj_decision = category
    incident.pj_notes = notes
    incident.status = IncidentStatus.PJ_REVIEWED
    incident.final_category = category
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        session,
        incident,
        actor,
        previous_status,
        IncidentStatus.PJ_REVIEWED,
        payload_diff={"pj_decision": category.value, "notes": notes},
    )
    session.add(incident)
    return incident


def mutu_review(session: Session, incident: Incident, actor: User, category: IncidentCategory, notes: str | None) -> Incident:
    ensure_transition(incident, IncidentStatus.MUTU_REVIEWED, {role.name for role in actor.roles})
    previous_status = incident.status
    incident.mutu_decision = category
    incident.mutu_notes = notes
    incident.status = IncidentStatus.MUTU_REVIEWED
    incident.final_category = category
    incident.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        session,
        incident,
        actor,
        previous_status,
        IncidentStatus.MUTU_REVIEWED,
        payload_diff={"mutu_decision": category.value, "notes": notes},
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
