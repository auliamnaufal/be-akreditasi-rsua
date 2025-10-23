from __future__ import annotations

from typing import List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from .base import IDModel, TimestampedModel

if TYPE_CHECKING:  # pragma: no cover
    from .incident import Incident


class Department(IDModel, TimestampedModel, table=True):
    __tablename__ = "departments"
    name: str = Field(unique=True, index=True)
    description: str | None = Field(default=None)
    incidents: list["Incident"] = Relationship(back_populates="department")
