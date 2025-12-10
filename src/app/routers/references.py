from fastapi import APIRouter, Depends

from sqlmodel import Session, select

from ..db import get_session
from ..models.incident import IncidentCategory
from ..models.department import Department
from ..schemas.common import APIResponse

router = APIRouter(prefix="/v1/references", tags=["References"])


CATEGORY_DESCRIPTIONS = {
    IncidentCategory.KTD: "Kejadian Tidak Diharapkan - patient harm occurred.",
    IncidentCategory.KTC: "Kejadian Tidak Cedera - no injury occurred.",
    IncidentCategory.KNC: "Kejadian Nyaris Cedera - near miss.",
    IncidentCategory.KPCS: "Kejadian Potensial Cedera Serius - potential serious injury.",
    IncidentCategory.SENTINEL: "Sentinel Event - severe unexpected occurrence.",
}


@router.get("/incident-categories", response_model=APIResponse[list[dict]])
def list_categories() -> APIResponse[list[dict]]:
    data = [
        {
            "code": category.value,
            "name": category.value,
            "description": CATEGORY_DESCRIPTIONS[category],
        }
        for category in IncidentCategory
    ]
    return APIResponse(status_code=200, message="Incident categories", data=data)


@router.get("/departments", response_model=APIResponse[list[dict]])
def list_departments(session: Session = Depends(get_session)) -> APIResponse[list[dict]]:
    departments = session.exec(select(Department)).all()
    data = [{"id": dept.id, "name": dept.name, "description": dept.description} for dept in departments]
    return APIResponse(status_code=200, message="Departments", data=data)
