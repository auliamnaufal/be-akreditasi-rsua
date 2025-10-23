from fastapi import APIRouter

from ..models.incident import IncidentCategory
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
