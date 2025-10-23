from dataclasses import dataclass
from typing import Dict

from fastapi import HTTPException

from ...models.incident import Incident, IncidentStatus


@dataclass(frozen=True)
class Transition:
    source: IncidentStatus
    target: IncidentStatus
    allowed_roles: set[str]


TRANSITIONS: Dict[IncidentStatus, Transition] = {
    IncidentStatus.DRAFT: Transition(IncidentStatus.DRAFT, IncidentStatus.SUBMITTED, {"perawat"}),
    IncidentStatus.SUBMITTED: Transition(IncidentStatus.SUBMITTED, IncidentStatus.PJ_REVIEWED, {"pj"}),
    IncidentStatus.PJ_REVIEWED: Transition(IncidentStatus.PJ_REVIEWED, IncidentStatus.MUTU_REVIEWED, {"mutu"}),
    IncidentStatus.MUTU_REVIEWED: Transition(IncidentStatus.MUTU_REVIEWED, IncidentStatus.CLOSED, {"mutu", "admin"}),
}


def ensure_transition(incident: Incident, target_status: IncidentStatus, actor_roles: set[str]) -> None:
    if incident.status == target_status:
        return
    if incident.status not in TRANSITIONS:
        raise HTTPException(status_code=409, detail={"error_code": "invalid_state_transition", "message": f"Transition from {incident.status} not allowed"})
    transition = TRANSITIONS[incident.status]
    if transition.target != target_status:
        raise HTTPException(status_code=409, detail={"error_code": "invalid_state_transition", "message": f"Must transition to {transition.target}"})
    if not actor_roles.intersection(transition.allowed_roles):
        raise HTTPException(status_code=403, detail={"error_code": "role_not_allowed", "message": "Role not permitted for transition"})
