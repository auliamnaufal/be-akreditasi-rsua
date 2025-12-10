"""Add grading column to incidents

Revision ID: 20251209_175915
Revises: 0002_audit_indexing
Create Date: 2025-12-09 17:59:15.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251209_175915"
down_revision = "0002_audit_indexing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column(
            "grading",
            sa.Enum("BIRU", "HIJAU", "KUNING", "MERAH", name="incidentgrading"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("incidents", "grading")
    op.execute("DROP TYPE IF EXISTS incidentgrading")
