"""sfp_v3_ledger_and_ai_models

Revision ID: d2f6e9b1c4a0
Revises: 7e8bede739e8, 6c8a700142ca
Create Date: 2026-03-01 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f6e9b1c4a0"
down_revision = ("7e8bede739e8", "6c8a700142ca")
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ledger_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("current_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["conta.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("current_hash"),
    )
    op.create_index(op.f("ix_ledger_entry_user_id"), "ledger_entry", ["user_id"], unique=False)
    op.create_index(op.f("ix_ledger_entry_account_id"), "ledger_entry", ["account_id"], unique=False)
    op.create_index(op.f("ix_ledger_entry_reference_type"), "ledger_entry", ["reference_type"], unique=False)
    op.create_index(op.f("ix_ledger_entry_reference_id"), "ledger_entry", ["reference_id"], unique=False)
    op.create_index(op.f("ix_ledger_entry_created_at"), "ledger_entry", ["created_at"], unique=False)
    op.create_index(op.f("ix_ledger_entry_current_hash"), "ledger_entry", ["current_hash"], unique=True)

    op.create_table(
        "monthly_closure",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("closing_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_receitas", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_despesas", sa.Numeric(14, 2), nullable=False),
        sa.Column("ledger_hash_snapshot", sa.String(length=64), nullable=True),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["conta.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "account_id", "year", "month", name="uq_monthly_closure_scope"),
    )
    op.create_index(op.f("ix_monthly_closure_user_id"), "monthly_closure", ["user_id"], unique=False)
    op.create_index(op.f("ix_monthly_closure_account_id"), "monthly_closure", ["account_id"], unique=False)
    op.create_index(op.f("ix_monthly_closure_year"), "monthly_closure", ["year"], unique=False)
    op.create_index(op.f("ix_monthly_closure_month"), "monthly_closure", ["month"], unique=False)

    op.create_table(
        "simulation_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["conta.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_simulation_session_user_id"), "simulation_session", ["user_id"], unique=False)
    op.create_index(op.f("ix_simulation_session_account_id"), "simulation_session", ["account_id"], unique=False)
    op.create_index(op.f("ix_simulation_session_created_at"), "simulation_session", ["created_at"], unique=False)

    op.create_table(
        "simulation_ledger_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("simulation_session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("current_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["conta.id"]),
        sa.ForeignKeyConstraint(["simulation_session_id"], ["simulation_session.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_simulation_ledger_entry_simulation_session_id"),
        "simulation_ledger_entry",
        ["simulation_session_id"],
        unique=False,
    )
    op.create_index(op.f("ix_simulation_ledger_entry_user_id"), "simulation_ledger_entry", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_simulation_ledger_entry_account_id"),
        "simulation_ledger_entry",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_simulation_ledger_entry_reference_type"),
        "simulation_ledger_entry",
        ["reference_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_simulation_ledger_entry_reference_id"),
        "simulation_ledger_entry",
        ["reference_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_simulation_ledger_entry_created_at"),
        "simulation_ledger_entry",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_simulation_ledger_entry_current_hash"),
        "simulation_ledger_entry",
        ["current_hash"],
        unique=False,
    )

    op.create_table(
        "ai_model_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=30), nullable=False),
        sa.Column("model_path", sa.String(length=500), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("trained_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_model_metadata_user_id"), "ai_model_metadata", ["user_id"], unique=False)
    op.create_index(op.f("ix_ai_model_metadata_model_type"), "ai_model_metadata", ["model_type"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_ai_model_metadata_model_type"), table_name="ai_model_metadata")
    op.drop_index(op.f("ix_ai_model_metadata_user_id"), table_name="ai_model_metadata")
    op.drop_table("ai_model_metadata")

    op.drop_index(op.f("ix_simulation_ledger_entry_current_hash"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_created_at"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_reference_id"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_reference_type"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_account_id"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_user_id"), table_name="simulation_ledger_entry")
    op.drop_index(op.f("ix_simulation_ledger_entry_simulation_session_id"), table_name="simulation_ledger_entry")
    op.drop_table("simulation_ledger_entry")

    op.drop_index(op.f("ix_simulation_session_created_at"), table_name="simulation_session")
    op.drop_index(op.f("ix_simulation_session_account_id"), table_name="simulation_session")
    op.drop_index(op.f("ix_simulation_session_user_id"), table_name="simulation_session")
    op.drop_table("simulation_session")

    op.drop_index(op.f("ix_monthly_closure_month"), table_name="monthly_closure")
    op.drop_index(op.f("ix_monthly_closure_year"), table_name="monthly_closure")
    op.drop_index(op.f("ix_monthly_closure_account_id"), table_name="monthly_closure")
    op.drop_index(op.f("ix_monthly_closure_user_id"), table_name="monthly_closure")
    op.drop_table("monthly_closure")

    op.drop_index(op.f("ix_ledger_entry_current_hash"), table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_created_at"), table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_reference_id"), table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_reference_type"), table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_account_id"), table_name="ledger_entry")
    op.drop_index(op.f("ix_ledger_entry_user_id"), table_name="ledger_entry")
    op.drop_table("ledger_entry")
