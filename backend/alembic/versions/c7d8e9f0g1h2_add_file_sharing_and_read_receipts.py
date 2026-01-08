"""Add file sharing and read receipts to messages

Revision ID: c7d8e9f0g1h2
Revises: b2c3d4e5f6a7
Create Date: 2026-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0g1h2'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to messages table
    op.add_column('messages', sa.Column('read_at', sa.DateTime(), nullable=True))
    op.add_column('messages', sa.Column('file_url', sa.String(500), nullable=True))
    op.add_column('messages', sa.Column('file_name', sa.String(255), nullable=True))
    op.add_column('messages', sa.Column('file_type', sa.String(50), nullable=True))
    op.add_column('messages', sa.Column('file_size', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns from messages table
    op.drop_column('messages', 'file_size')
    op.drop_column('messages', 'file_type')
    op.drop_column('messages', 'file_name')
    op.drop_column('messages', 'file_url')
    op.drop_column('messages', 'read_at')
