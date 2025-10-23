from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

import jwt

from ..config import get_settings

settings = get_settings()


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(subject: str, role: str, expires_delta: timedelta, secret: str, token_type: str, extra_claims: Dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid4().hex,
        "typ": token_type,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str, token_version: int, expires_minutes: int | None = None, extra_claims: Dict[str, Any] | None = None) -> str:
    expires = timedelta(minutes=expires_minutes or settings.access_token_expires_minutes)
    claims = {"token_version": token_version}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(subject, role, expires, settings.jwt_secret_key, TokenType.ACCESS, claims)


def create_refresh_token(subject: str, role: str, token_version: int, expires_minutes: int | None = None, extra_claims: Dict[str, Any] | None = None) -> str:
    expires = timedelta(minutes=expires_minutes or settings.refresh_token_expires_minutes)
    claims = {"token_version": token_version}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(subject, role, expires, settings.jwt_refresh_secret_key, TokenType.REFRESH, claims)


def decode_token(token: str, refresh: bool = False) -> Dict[str, Any]:
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    return payload
