from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..db import get_session
from ..models.department import Department
from ..models.location import Location
from ..models.role import Role
from ..models.user import User
from ..schemas.common import APIResponse
from ..schemas.reference import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    LocationCreate,
    LocationRead,
    LocationUpdate,
)
from ..schemas.user import UserCreate, UserRead, UserUpdate
from ..security.permissions import RequireRole
from ..security.passwords import hash_password

router = APIRouter(prefix="/v1/admin", tags=["Admin"], dependencies=[Depends(RequireRole("admin"))])


@router.get("/users", response_model=APIResponse[list[UserRead]])
def list_users(session: Session = Depends(get_session)) -> APIResponse[list[UserRead]]:
    users = session.exec(select(User).options(selectinload(User.roles))).all()
    data = [UserRead.model_validate(u) for u in users]
    return APIResponse(status_code=200, message="Users fetched", data=data)


@router.post("/users", response_model=APIResponse[UserRead], status_code=201)
def create_user(payload: UserCreate, session: Session = Depends(get_session)) -> APIResponse[UserRead]:
    existing = session.exec(select(User).where(User.email == payload.email)).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "email_taken", "message": "Email already exists"})
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    if payload.role_ids:
        roles = session.exec(select(Role).where(Role.id.in_(payload.role_ids))).all()
        user.roles = list(roles)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=201, message="User created", data=UserRead.model_validate(user))


@router.put("/users/{user_id}", response_model=APIResponse[UserRead])
def update_user(user_id: int, payload: UserUpdate, session: Session = Depends(get_session)) -> APIResponse[UserRead]:
    user = session.exec(select(User).options(selectinload(User.roles)).where(User.id == user_id)).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "user_not_found", "message": "User not found"})
    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        user.hashed_password = hash_password(update_data.pop("password"))
        user.token_version += 1
        user.last_password_change = datetime.now(timezone.utc)
    for key, value in update_data.items():
        if key == "role_ids" and value is not None:
            roles = session.exec(select(Role).where(Role.id.in_(value))).all()
            user.roles = list(roles)
        elif key != "role_ids":
            setattr(user, key, value)
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=200, message="User updated", data=UserRead.model_validate(user))


@router.get("/roles", response_model=APIResponse[list[dict]])
def list_roles(session: Session = Depends(get_session)) -> APIResponse[list[dict]]:
    roles = session.exec(select(Role)).all()
    data = [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ]
    return APIResponse(status_code=200, message="Roles fetched", data=data)


@router.post("/departments", response_model=APIResponse[DepartmentRead], status_code=201)
def create_department(payload: DepartmentCreate, session: Session = Depends(get_session)) -> APIResponse[DepartmentRead]:
    department = Department(name=payload.name, description=payload.description)
    session.add(department)
    session.commit()
    session.refresh(department)
    return APIResponse(status_code=201, message="Department created", data=DepartmentRead.model_validate(department))


@router.put("/departments/{department_id}", response_model=APIResponse[DepartmentRead])
def update_department(department_id: int, payload: DepartmentUpdate, session: Session = Depends(get_session)) -> APIResponse[DepartmentRead]:
    department = session.exec(select(Department).where(Department.id == department_id)).one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail={"error_code": "department_not_found", "message": "Department not found"})
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(department, key, value)
    department.updated_at = datetime.now(timezone.utc)
    session.add(department)
    session.commit()
    session.refresh(department)
    return APIResponse(status_code=200, message="Department updated", data=DepartmentRead.model_validate(department))


@router.post("/locations", response_model=APIResponse[LocationRead], status_code=201)
def create_location(payload: LocationCreate, session: Session = Depends(get_session)) -> APIResponse[LocationRead]:
    location = Location(name=payload.name, description=payload.description)
    session.add(location)
    session.commit()
    session.refresh(location)
    return APIResponse(status_code=201, message="Location created", data=LocationRead.model_validate(location))


@router.put("/locations/{location_id}", response_model=APIResponse[LocationRead])
def update_location(location_id: int, payload: LocationUpdate, session: Session = Depends(get_session)) -> APIResponse[LocationRead]:
    location = session.exec(select(Location).where(Location.id == location_id)).one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail={"error_code": "location_not_found", "message": "Location not found"})
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)
    location.updated_at = datetime.now(timezone.utc)
    session.add(location)
    session.commit()
    session.refresh(location)
    return APIResponse(status_code=200, message="Location updated", data=LocationRead.model_validate(location))
