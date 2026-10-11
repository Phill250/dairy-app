"""add totp columns

Revision ID: a1f3c9d2b7e4
Revises: c6c37306e7f4
Create Date: 2026-10-11
"""
from alembic import op
import sqlalchemy as sa

revision = "a1f3c9d2b7e4"
down_revision = "c6c37306e7f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.String(), nullable=True))
    op.add_column(
        "users",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("users", sa.Column("totp_last_step", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("recovery_code_hashes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "recovery_code_hashes")
    op.drop_column("users", "totp_last_step")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret_encrypted")