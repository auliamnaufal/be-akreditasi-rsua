from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship  # <- use Relationship from sqlmodel

from .base import IDModel, TimestampedModel

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)


class Role(IDModel, TimestampedModel, table=True):
    __tablename__ = "roles"

    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)

    # SQLModel-style many-to-many via link_model
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)
