"""initial schema

Revision ID: 2724b4a58b15
Revises: 
Create Date: 2026-09-24 16:03:50.165385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2724b4a58b15'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('farmer', 'admin', name='userrole'), nullable=False),
    sa.Column('current_refresh_token_hash', sa.String(), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('password_reset_token_hash', sa.String(), nullable=True),
    sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('cows',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('farmer_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('breed', sa.Enum('holstein_friesian', 'ankole', 'ankole_friesian_cross', 'other', name='breedtype'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cows_farmer_id'), 'cows', ['farmer_id'], unique=False)
    op.create_index(op.f('ix_cows_id'), 'cows', ['id'], unique=False)
    op.create_table('logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('cow_id', sa.UUID(), nullable=False),
    sa.Column('date', sa.String(), nullable=False),
    sa.Column('feed', sa.Float(), nullable=False),
    sa.Column('milking_times', sa.Integer(), nullable=False),
    sa.Column('total_milk', sa.Float(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('color', sa.String(), nullable=False),
    sa.Column('advice', sa.String(), nullable=False),
    sa.Column('predicted_yield', sa.Float(), nullable=True),
    sa.Column('used_ml_model', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['cow_id'], ['cows.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_logs_cow_id'), 'logs', ['cow_id'], unique=False)
    op.create_index(op.f('ix_logs_date'), 'logs', ['date'], unique=False)
    op.create_index(op.f('ix_logs_id'), 'logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_logs_id'), table_name='logs')
    op.drop_index(op.f('ix_logs_date'), table_name='logs')
    op.drop_index(op.f('ix_logs_cow_id'), table_name='logs')
    op.drop_table('logs')
    op.drop_index(op.f('ix_cows_id'), table_name='cows')
    op.drop_index(op.f('ix_cows_farmer_id'), table_name='cows')
    op.drop_table('cows')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
