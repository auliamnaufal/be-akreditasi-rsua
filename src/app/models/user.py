from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import Field, Relationship

from .base import IDModel, TimestampedModel
from .role import Role, UserRole

if TYPE_CHECKING:  # pragma: no cover
    from .incident import Incident
else:
    # Ensure the Incident model is registered with SQLAlchemy before relationship
    # configuration runs so string-based relationships can resolve properly.
    from .incident import Incident  # noqa: F401

class User(IDModel, TimestampedModel, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    full_name: str = Field(index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    token_version: int = Field(default=1, nullable=False)
    last_password_change: Optional[datetime] = Field(default=None)

    # many-to-many to Role, SQLModel style
    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRole)

    # one-to-many to Incident, SQLModel style
    reported_incidents: List["Incident"] = Relationship(back_populates="reporter")
