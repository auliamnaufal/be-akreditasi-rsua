from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TimestampedModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


class IDModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
