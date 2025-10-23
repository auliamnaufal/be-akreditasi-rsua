from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserRead(UserBase):
    id: int
    is_active: bool
    roles: List[RoleRead]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str
    role_ids: List[int] | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    role_ids: List[int] | None = None
