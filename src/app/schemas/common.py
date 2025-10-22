from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None


class Pagination(BaseModel):
    items: list
    page: int
    per_page: int
    total: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict | list | str] = None
