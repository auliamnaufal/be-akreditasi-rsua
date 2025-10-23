from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..db import get_session
from ..models.incident import Incident, IncidentStatus
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.incident import (
    IncidentCreate,
    IncidentRead,
    IncidentSubmitRequest,
    IncidentUpdate,
)
from ..security.dependencies import get_current_user
from ..security.permissions import RequireRole
from ..services.incidents.service import submit_incident

router = APIRouter(prefix="/v1/incidents", tags=["Incidents"])


@router.post("", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("perawat"))], status_code=201)
def create_incident(
    payload: IncidentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = Incident(
        reporter_id=current_user.id,
        patient_identifier=payload.patient_identifier,
        occurred_at=payload.occurred_at or datetime.utcnow(),
        location_id=payload.location_id,
        department_id=payload.department_id,
        free_text_description=payload.free_text_description,
        harm_indicator=payload.harm_indicator,
        attachments=payload.attachments,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=201, message="Incident draft created", data=IncidentRead.model_validate(incident))


@router.put("/{incident_id}", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("perawat"))])
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(select(Incident).where(Incident.id == incident_id)).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    if incident.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error_code": "forbidden", "message": "Cannot modify others' incidents"})
    if incident.status != IncidentStatus.DRAFT:
        raise HTTPException(status_code=409, detail={"error_code": "invalid_state", "message": "Only draft incidents can be edited"})
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(incident, key, value)
    incident.updated_at = datetime.utcnow()
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=200, message="Incident updated", data=IncidentRead.model_validate(incident))


@router.post("/{incident_id}/submit", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("perawat"))])
def submit(
    incident_id: int,
    payload: IncidentSubmitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(select(Incident).where(Incident.id == incident_id)).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    if incident.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error_code": "forbidden", "message": "Cannot submit others' incidents"})
    if incident.status != IncidentStatus.DRAFT:
        raise HTTPException(status_code=409, detail={"error_code": "invalid_state", "message": "Only draft incidents can be submitted"})
    submit_incident(session, incident, current_user)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=200, message="Incident submitted. Prediction generated.", data=IncidentRead.model_validate(incident))


@router.get("", response_model=APIResponse[dict])
def list_incidents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: IncidentStatus | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:
    filters = []
    user_roles = {role.name for role in current_user.roles}
    if "perawat" in user_roles and not user_roles.intersection({"admin", "pj", "mutu"}):
        filters.append(Incident.reporter_id == current_user.id)
    if status:
        filters.append(Incident.status == status)

    statement = select(Incident).where(*filters).order_by(Incident.created_at.desc())
    count_stmt = select(func.count()).select_from(Incident)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int(session.exec(count_stmt).one())
    incidents = session.exec(statement.offset((page - 1) * per_page).limit(per_page)).all()
    items = [IncidentRead.model_validate(incident).model_dump() for incident in incidents]
    response = {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
    }
    return APIResponse(status_code=200, message="Incidents fetched", data=response)


@router.get("/{incident_id}", response_model=APIResponse[IncidentRead])
def get_incident(
    incident_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(
        select(Incident).options(selectinload(Incident.audit_logs)).where(Incident.id == incident_id)
    ).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    user_roles = {role.name for role in current_user.roles}
    if incident.reporter_id != current_user.id and not user_roles.intersection({"admin", "pj", "mutu"}):
        raise HTTPException(status_code=403, detail={"error_code": "forbidden", "message": "Access denied"})
    return APIResponse(status_code=200, message="Incident detail", data=IncidentRead.model_validate(incident))
