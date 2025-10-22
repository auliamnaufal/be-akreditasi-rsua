from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from ..db import get_session
from ..models.user import User
from .jwt import TokenType, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail={"error_code": "auth_required", "message": "Authorization header missing"})
    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - jwt errors
        raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Invalid access token"}) from exc

    if payload.get("typ") != TokenType.ACCESS:
        raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Access token required"})

    token_version = payload.get("token_version")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Missing subject"})

    user = session.exec(
        select(User).options(selectinload(User.roles)).where(User.id == int(user_id))
    ).one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail={"error_code": "user_not_active", "message": "Inactive or missing user"})

    if user.token_version != token_version:
        raise HTTPException(status_code=401, detail={"error_code": "token_revoked", "message": "Token revoked"})
    return user
