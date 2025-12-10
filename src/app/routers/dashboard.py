from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ..db import get_session
from ..models.department import Department
from ..models.incident import Incident, IncidentCategory, IncidentGrading, MDPCode, SKPCode
from ..schemas.common import APIResponse
from ..security.dependencies import get_current_user
from ..security.permissions import RequireRole

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"], dependencies=[Depends(RequireRole("mutu", "admin"))])


def _grading_level(grading: IncidentGrading | None) -> str:
    if grading == IncidentGrading.MERAH:
        return "ekstrem"
    if grading == IncidentGrading.KUNING:
        return "tinggi"
    if grading == IncidentGrading.HIJAU:
        return "sedang"
    if grading == IncidentGrading.BIRU:
        return "rendah"
    return "tidak tersedia"


def _label_skp(code: SKPCode) -> str:
    return f"SKP {code.value.replace('skp', '')}"


def _label_mdp(code: MDPCode) -> str:
    return f"MDP {code.value.replace('mdp', '')}"


def _resolve_department(session: Session, unit: str) -> Tuple[str, int | None]:
    if unit.lower() == "all":
        return "All", None
    dept = (
        session.exec(select(Department).where(func.lower(Department.name) == unit.lower())).one_or_none()
        if not unit.isdigit()
        else session.exec(select(Department).where(Department.id == int(unit))).one_or_none()
    )
    if not dept:
        raise HTTPException(status_code=404, detail={"error_code": "department_not_found", "message": "Department not found"})
    return dept.name, dept.id


def _label_category(cat: IncidentCategory) -> str:
    mapping = {
        IncidentCategory.KTD: "Kejadian Tidak Diharapkan",
        IncidentCategory.KTC: "Kejadian Tidak Cedera",
        IncidentCategory.KNC: "Kejadian Nyaris Cedera",
        IncidentCategory.KPCS: "Kejadian Potensial Cedera Serius",
        IncidentCategory.SENTINEL: "Sentinel Event",
    }
    return mapping.get(cat, cat.value)


def _period_key(dt: datetime, view: str) -> str:
    if view == "weekly":
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if view == "monthly":
        return dt.strftime("%Y-%m")
    if view == "quarterly":
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    # yearly
    return dt.strftime("%Y")


@router.get("/mutu", response_model=APIResponse[dict])
def mutu_dashboard(
    unit: str = Query("all", description="Department name or id; 'all' aggregates all departments"),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),  # noqa: B008
) -> APIResponse[dict]:
    unit_name, department_id = _resolve_department(session, unit)

    filters = []
    if department_id is not None:
        filters.append(Incident.department_id == department_id)

    incidents = session.exec(select(Incident).where(*filters)).all()
    all_incidents = session.exec(select(Incident)).all()

    total_insiden = len(incidents)

    jenis_counts: Dict[str, int] = {c.value: 0 for c in IncidentCategory}
    skp_counts: Dict[str, int] = {_label_skp(code): 0 for code in SKPCode}
    mdp_counts: Dict[str, int] = {_label_mdp(code): 0 for code in MDPCode}

    dept_risk_filtered: Dict[int, str] = {}
    dept_risk_all: Dict[int, str] = {}

    def apply_risk(collector: Dict[int, str], inc: Incident) -> None:
        if inc.department_id is None:
            return
        current_level = collector.get(inc.department_id)
        new_level = _grading_level(inc.grading)
        priority = {"ekstrem": 3, "tinggi": 2, "sedang": 1, "rendah": 0, "tidak tersedia": -1}
        if current_level is None or priority[new_level] > priority.get(current_level, -1):
            collector[inc.department_id] = new_level

    for inc in incidents:
        category = inc.final_category or inc.predicted_category
        if category:
            jenis_counts[category.value] = jenis_counts.get(category.value, 0) + 1
        if inc.skp_code:
            skp_counts[_label_skp(inc.skp_code)] = skp_counts.get(_label_skp(inc.skp_code), 0) + 1
        if inc.mdp_code:
            mdp_counts[_label_mdp(inc.mdp_code)] = mdp_counts.get(_label_mdp(inc.mdp_code), 0) + 1
        apply_risk(dept_risk_filtered, inc)

    for inc in all_incidents:
        apply_risk(dept_risk_all, inc)

    hospital_risk = _grading_level(
        max((inc.grading for inc in incidents if inc.grading), default=None, key=lambda g: {"MERAH": 3, "KUNING": 2, "HIJAU": 1, "BIRU": 0}[g.value])
        if incidents
        else None
    )

    # Build unit lists and risk summaries
    unit_list = ["All"] + [dept.name for dept in session.exec(select(Department)).all()]
    units_risk = []
    risk_source = dept_risk_all if dept_risk_all else dept_risk_filtered
    if risk_source:
        departments = session.exec(select(Department).where(Department.id.in_(list(risk_source.keys())))).all()
        for dept in departments:
            units_risk.append({"name": dept.name, "level": risk_source.get(dept.id, "tidak tersedia")})

    payload = {
        "unit": unit_name,
        "total_insiden": total_insiden,
        "jenis_kejadian": jenis_counts,
        "skp": skp_counts,
        "mdp": mdp_counts,
        "hospital_risk": hospital_risk,
        "units_risk": units_risk,
        "unit_list": unit_list,
    }
    return APIResponse(status_code=200, message="Dashboard metrics", data=payload)


@router.get("/mutu/trend", response_model=APIResponse[dict])
def mutu_trend(
    view: str = Query("weekly", pattern="^(weekly|monthly|quarterly|yearly)$"),
    group: str = Query("jenis", pattern="^(jenis|total|mdp|skp)$"),
    unit: str = Query("all", description="Department name or id; 'all' aggregates all departments"),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),  # noqa: B008
) -> APIResponse[dict]:
    unit_name, department_id = _resolve_department(session, unit)
    filters = []
    if department_id is not None:
        filters.append(Incident.department_id == department_id)

    incidents = session.exec(select(Incident).where(*filters)).all()
    if not incidents:
        return APIResponse(
            status_code=200,
            message="Trend metrics",
            data={"unit": unit_name, "view": view, "group": group, "periods": [], "series": []},
        )

    buckets: Dict[str, List[Incident]] = {}
    for inc in incidents:
        key = _period_key(inc.occurred_at, view) if inc.occurred_at else _period_key(inc.created_at, view)
        buckets.setdefault(key, []).append(inc)

    periods = sorted(buckets.keys())

    series: List[dict] = []

    if group == "jenis":
        categories = list(IncidentCategory)
        for cat in categories:
            data = []
            for p in periods:
                count = 0
                for inc in buckets[p]:
                    val = inc.final_category or inc.predicted_category
                    if val == cat:
                        count += 1
                data.append(count)
            series.append({"key": cat.value, "label": _label_category(cat), "data": data})
    elif group == "total":
        data = [len(buckets[p]) for p in periods]
        series.append({"key": "total", "label": "Total Insiden", "data": data})
    elif group == "skp":
        codes = list(SKPCode)
        for code in codes:
            data = []
            for p in periods:
                count = sum(1 for inc in buckets[p] if inc.skp_code == code)
                data.append(count)
            series.append({"key": code.value.upper(), "label": _label_skp(code), "data": data})
    elif group == "mdp":
        codes = list(MDPCode)
        for code in codes:
            data = []
            for p in periods:
                count = sum(1 for inc in buckets[p] if inc.mdp_code == code)
                data.append(count)
            series.append({"key": code.value.upper(), "label": _label_mdp(code), "data": data})

    payload = {
        "unit": unit_name,
        "view": view,
        "group": group,
        "periods": periods,
        "series": series,
    }
    return APIResponse(status_code=200, message="Trend metrics", data=payload)
