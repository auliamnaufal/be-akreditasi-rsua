"""add incident indexes

Revision ID: 0002_audit_indexing
Revises: 0001_init
Create Date: 2024-01-01 00:10:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_audit_indexing"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_incidents_status_occurred", "incidents", ["status", "occurred_at"])
    op.create_index("ix_incidents_department_occurred", "incidents", ["department_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_incidents_department_occurred", table_name="incidents")
    op.drop_index("ix_incidents_status_occurred", table_name="incidents")
