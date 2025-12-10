"""Add subject/context/responder roles to incidents

Revision ID: 20251210_040000
Revises: 20251210_030000
Create Date: 2025-12-10 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251210_040000"
down_revision = "20251210_030000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("incident_subject", sa.Enum("pasien", "lain", name="incidentsubject"), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column("patient_context", sa.Enum("rawat-inap", "ugd", "rawat-jalan", "lain", name="patientcontext"), nullable=True),
    )
    op.add_column("incidents", sa.Column("responder_roles", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "responder_roles")
    op.drop_column("incidents", "patient_context")
    op.drop_column("incidents", "incident_subject")
    op.execute("DROP TYPE IF EXISTS patientcontext")
    op.execute("DROP TYPE IF EXISTS incidentsubject")
