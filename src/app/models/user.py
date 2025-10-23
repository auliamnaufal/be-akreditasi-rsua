from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship

from .base import IDModel, TimestampedModel
from .role import Role, UserRole

if TYPE_CHECKING:  # pragma: no cover
    from .incident import Incident

class User(IDModel, TimestampedModel, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    full_name: str = Field(index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    token_version: int = Field(default=1, nullable=False)
    last_password_change: Optional[datetime] = Field(default=None)

    # many-to-many to Role, SQLModel style
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRole)

    # one-to-many to Incident, SQLModel style
    reported_incidents: list["Incident"] = Relationship(back_populates="reporter")
