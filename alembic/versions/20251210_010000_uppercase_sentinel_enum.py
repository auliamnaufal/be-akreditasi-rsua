"""Uppercase SENTINEL in incidentcategory enum

Revision ID: 20251210_010000
Revises: 20251210_000001
Create Date: 2025-12-10 01:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251210_010000"
down_revision = "20251210_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Align all incidentcategory enums to use uppercase SENTINEL
    op.execute(
        "ALTER TABLE incidents MODIFY predicted_category "
        "ENUM('KTD','KTC','KNC','KPCS','SENTINEL') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY pj_decision "
        "ENUM('KTD','KTC','KNC','KPCS','SENTINEL') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY mutu_decision "
        "ENUM('KTD','KTC','KNC','KPCS','SENTINEL') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY final_category "
        "ENUM('KTD','KTC','KNC','KPCS','SENTINEL') NULL"
    )


def downgrade() -> None:
    # Restore original casing
    op.execute(
        "ALTER TABLE incidents MODIFY predicted_category "
        "ENUM('KTD','KTC','KNC','KPCS','Sentinel') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY pj_decision "
        "ENUM('KTD','KTC','KNC','KPCS','Sentinel') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY mutu_decision "
        "ENUM('KTD','KTC','KNC','KPCS','Sentinel') NULL"
    )
    op.execute(
        "ALTER TABLE incidents MODIFY final_category "
        "ENUM('KTD','KTC','KNC','KPCS','Sentinel') NULL"
    )
