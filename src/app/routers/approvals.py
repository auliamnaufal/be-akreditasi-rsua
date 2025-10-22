from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models.incident import Incident
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.incident import IncidentRead, IncidentReview
from ..security.dependencies import get_current_user
from ..security.permissions import RequireRole
from ..services.incidents.service import close_incident, mutu_review, pj_review

router = APIRouter(prefix="/v1/approvals", tags=["Approvals"])


@router.post("/{incident_id}/pj", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("pj"))])
def pj_approve(
    incident_id: int,
    payload: IncidentReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(select(Incident).where(Incident.id == incident_id)).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    pj_review(session, incident, current_user, payload.category, payload.notes)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=200, message="PJ review recorded", data=IncidentRead.model_validate(incident))


@router.post("/{incident_id}/mutu", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("mutu"))])
def mutu_approve(
    incident_id: int,
    payload: IncidentReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(select(Incident).where(Incident.id == incident_id)).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    mutu_review(session, incident, current_user, payload.category, payload.notes)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=200, message="Mutu review recorded", data=IncidentRead.model_validate(incident))


@router.post("/{incident_id}/close", response_model=APIResponse[IncidentRead], dependencies=[Depends(RequireRole("mutu", "admin"))])
def close(
    incident_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> APIResponse[IncidentRead]:
    incident = session.exec(select(Incident).where(Incident.id == incident_id)).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail={"error_code": "incident_not_found", "message": "Incident not found"})
    close_incident(session, incident, current_user)
    session.commit()
    session.refresh(incident)
    return APIResponse(status_code=200, message="Incident closed", data=IncidentRead.model_validate(incident))
