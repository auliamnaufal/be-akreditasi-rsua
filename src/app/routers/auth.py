from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..db import get_session
from ..models.role import Role
from ..models.user import User
from ..schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from ..schemas.common import APIResponse
from ..security.dependencies import get_current_user
from ..security.jwt import TokenType, create_access_token, create_refresh_token, decode_token
from ..security.passwords import hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


def _issue_tokens(user: User) -> TokenPair:
    primary_role = user.roles[0].name if user.roles else "perawat"
    roles = [r.name for r in user.roles]
    access_token = create_access_token(str(user.id), primary_role, user.token_version, extra_claims={"roles": roles})
    refresh_token = create_refresh_token(str(user.id), primary_role, user.token_version, extra_claims={"roles": roles})
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=APIResponse[TokenPair], status_code=201)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> APIResponse[TokenPair]:
    existing = session.exec(select(User).where(User.email == payload.email)).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "email_taken", "message": "Email already registered"})
    role = session.exec(select(Role).where(Role.name == payload.role)).one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail={"error_code": "invalid_role", "message": "Role not found"})
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
        token_version=1,
    )
    user.roles.append(role)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=201, message="Registered successfully", data=_issue_tokens(user))


@router.post("/login", response_model=APIResponse[TokenPair])
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> APIResponse[TokenPair]:
    user = session.exec(
        select(User).options(selectinload(User.roles)).where(User.email == payload.email)
    ).one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail={"error_code": "invalid_credentials", "message": "Invalid email or password"})
    if not user.roles:
        raise HTTPException(status_code=403, detail={"error_code": "role_not_assigned", "message": "User has no roles"})
    return APIResponse(status_code=200, message="Login success", data=_issue_tokens(user))


@router.post("/refresh", response_model=APIResponse[TokenPair])
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)) -> APIResponse[TokenPair]:
    try:
        claims = decode_token(payload.refresh_token, refresh=True)
    except Exception as exc:  # pragma: no cover - jwt errors
        raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Invalid refresh token"}) from exc
    if claims.get("typ") != TokenType.REFRESH:
        raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Refresh token required"})

    user = session.exec(
        select(User).options(selectinload(User.roles)).where(User.id == int(claims["sub"]))
    ).one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail={"error_code": "user_not_active", "message": "User inactive"})
    if user.token_version != claims.get("token_version"):
        raise HTTPException(status_code=401, detail={"error_code": "token_revoked", "message": "Token revoked"})

    user.token_version += 1
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return APIResponse(status_code=200, message="Token refreshed", data=_issue_tokens(user))


@router.post("/logout", response_model=APIResponse[dict])
def logout(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> APIResponse[dict]:
    current_user.token_version += 1
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    return APIResponse(status_code=200, message="Logged out", data={"token_version": current_user.token_version})
