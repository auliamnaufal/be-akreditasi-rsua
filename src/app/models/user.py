from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

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

    roles: List[Role] = Relationship(back_populates="users", link_model=UserRole)
    reported_incidents: List["Incident"] = Relationship(back_populates="reporter")


class UserRead(SQLModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    roles: List[str]
