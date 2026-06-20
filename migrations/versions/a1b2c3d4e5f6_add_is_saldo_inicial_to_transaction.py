"""add is_saldo_inicial flag to transactions

Revision ID: a1b2c3d4e5f6
Revises: d2f6e9b1c4a0
Create Date: 2026-05-30 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d2f6e9b1c4a0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_saldo_inicial",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade():
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_column("is_saldo_inicial")
