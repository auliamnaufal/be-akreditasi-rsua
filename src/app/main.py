from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import admin, approvals, auth, incidents, references
from .security.jwt import decode_token

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Hospital incident reporting service with accreditation-aligned categories.",
    openapi_tags=[
        {"name": "Auth", "description": "Authentication and token management"},
        {"name": "Incidents", "description": "Incident drafting and submission"},
        {"name": "Approvals", "description": "PJ and Mutu approval workflows"},
        {"name": "Admin", "description": "Administrative endpoints"},
        {"name": "References", "description": "Reference data"},
    ],
)


@app.middleware("http")
async def attach_jwt_claims(request: Request, call_next):
    request.state.claims = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            claims = decode_token(token)
            request.state.claims = claims
        except Exception:  # pragma: no cover - best effort
            logger.debug("Failed to decode token in middleware")
    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "validation_error",
            "message": "Validation failed",
            "details": exc.errors(),
        },
    )


@app.get("/health", tags=["References"])
def health_check() -> Dict[str, Any]:
    return {"status": "ok", "app": settings.app_name, "holla": "Hollaa"}


app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(approvals.router)
app.include_router(admin.router)
app.include_router(references.router)
