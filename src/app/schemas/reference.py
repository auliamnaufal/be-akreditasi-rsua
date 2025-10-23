from datetime import datetime

from pydantic import BaseModel


class DepartmentRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class LocationRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationCreate(BaseModel):
    name: str
    description: str | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
