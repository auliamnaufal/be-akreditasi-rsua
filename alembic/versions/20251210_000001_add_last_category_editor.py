"""Add last_category_editor_id to incidents

Revision ID: 20251210_000001
Revises: 20251209_175915
Create Date: 2025-12-10 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251210_000001"
down_revision = "20251209_175915"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("last_category_editor_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_incidents_last_category_editor",
        "incidents",
        "users",
        ["last_category_editor_id"],
        ["id"],
    )
    op.create_index("ix_incidents_last_category_editor_id", "incidents", ["last_category_editor_id"])


def downgrade() -> None:
    op.drop_index("ix_incidents_last_category_editor_id", table_name="incidents")
    op.drop_constraint("fk_incidents_last_category_editor", "incidents", type_="foreignkey")
    op.drop_column("incidents", "last_category_editor_id")
