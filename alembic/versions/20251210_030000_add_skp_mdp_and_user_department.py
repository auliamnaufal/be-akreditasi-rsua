"""Add SKP/MDP to incidents and department to users

Revision ID: 20251210_030000
Revises: 20251210_020000
Create Date: 2025-12-10 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251210_030000"
down_revision = "20251210_020000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("skp_code", sa.Enum("skp1", "skp2", "skp3", "skp4", "skp5", "skp6", name="skpcode"), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "mdp_code",
            sa.Enum(
                "mdp1",
                "mdp2",
                "mdp3",
                "mdp4",
                "mdp5",
                "mdp6",
                "mdp7",
                "mdp8",
                "mdp9",
                "mdp10",
                "mdp11",
                "mdp12",
                "mdp13",
                "mdp14",
                "mdp15",
                "mdp16",
                "mdp17",
                name="mdpcode",
            ),
            nullable=True,
        ),
    )

    op.add_column("users", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_department", "users", "departments", ["department_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_users_department", "users", type_="foreignkey")
    op.drop_column("users", "department_id")
    op.drop_column("incidents", "mdp_code")
    op.drop_column("incidents", "skp_code")
    op.execute("DROP TYPE IF EXISTS mdpcode")
    op.execute("DROP TYPE IF EXISTS skpcode")
