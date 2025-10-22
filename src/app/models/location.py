from typing import List, TYPE_CHECKING

from sqlmodel import Field, Relationship

from .base import IDModel, TimestampedModel

if TYPE_CHECKING:  # pragma: no cover
    from .incident import Incident


class Location(IDModel, TimestampedModel, table=True):
    __tablename__ = "locations"

    name: str = Field(unique=True, index=True)
    description: str | None = Field(default=None)

    incidents: List["Incident"] = Relationship(back_populates="location")
