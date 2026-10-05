"""switch to GUID type

Revision ID: c6c37306e7f4
Revises: 2724b4a58b15
Create Date: 2026-09-24 16:58:07.726403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c6c37306e7f4'
down_revision: Union[str, None] = '2724b4a58b15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
