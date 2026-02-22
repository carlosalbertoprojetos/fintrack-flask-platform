"""rename_saldo_to_saldo_inicial

Revision ID: 95a590c4b401
Revises: 577462efa927
Create Date: 2025-08-30 18:27:13.873964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95a590c4b401'
down_revision = '577462efa927'
branch_labels = None
depends_on = None


def upgrade():
    # Renomear a coluna 'saldo' para 'saldo_inicial' na tabela 'conta'
    op.alter_column('conta', 'saldo', new_column_name='saldo_inicial')


def downgrade():
    # Reverter: renomear a coluna 'saldo_inicial' de volta para 'saldo'
    op.alter_column('conta', 'saldo_inicial', new_column_name='saldo')
