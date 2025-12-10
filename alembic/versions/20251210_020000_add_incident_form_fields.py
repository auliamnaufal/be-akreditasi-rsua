"""Add patient and classification fields to incidents

Revision ID: 20251210_020000
Revises: 20251210_010000
Create Date: 2025-12-10 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251210_020000"
down_revision = "20251210_010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("patient_name", sa.String(length=255), nullable=True))
    op.add_column("incidents", sa.Column("reporter_type", sa.Enum("dokter", "perawat", "petugas", "pasien", "keluarga", "pengunjung", "lain", name="reportertype"), nullable=True))
    op.add_column("incidents", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("age_group", sa.Enum("bayi", "balita", "anak", "remaja", "dewasa", "lansia", name="agegroup"), nullable=True))
    op.add_column("incidents", sa.Column("gender", sa.Enum("l", "p", name="gender"), nullable=True))
    op.add_column("incidents", sa.Column("payer_type", sa.Enum("umum", "bpjs-mandiri", "sktm", name="payertype"), nullable=True))
    op.add_column("incidents", sa.Column("admission_at", sa.DateTime(), nullable=True))
    op.add_column("incidents", sa.Column("incident_place", sa.Enum("penyakit-dalam", "anak", "bedah", "obsgyn", "tht", "mata", "saraf", "anestesi", "kulit-kelamin", "jantung", "paru", "jiwa", "lain", name="incidentplace"), nullable=True))
    op.add_column("incidents", sa.Column("incident_unit", sa.String(length=255), nullable=True))
    op.add_column("incidents", sa.Column("incident_outcome", sa.Enum("kematian", "berat", "sedang", "ringan", "tidak-cedera", name="incidentoutcome"), nullable=True))
    op.add_column("incidents", sa.Column("immediate_action", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("has_similar_event", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("incidents", "has_similar_event")
    op.drop_column("incidents", "immediate_action")
    op.drop_column("incidents", "incident_outcome")
    op.drop_column("incidents", "incident_unit")
    op.drop_column("incidents", "incident_place")
    op.drop_column("incidents", "admission_at")
    op.drop_column("incidents", "payer_type")
    op.drop_column("incidents", "gender")
    op.drop_column("incidents", "age_group")
    op.drop_column("incidents", "age")
    op.drop_column("incidents", "reporter_type")
    op.drop_column("incidents", "patient_name")
    op.execute("DROP TYPE IF EXISTS incidentoutcome")
    op.execute("DROP TYPE IF EXISTS incidentplace")
    op.execute("DROP TYPE IF EXISTS payertype")
    op.execute("DROP TYPE IF EXISTS gender")
    op.execute("DROP TYPE IF EXISTS agegroup")
    op.execute("DROP TYPE IF EXISTS reportertype")
