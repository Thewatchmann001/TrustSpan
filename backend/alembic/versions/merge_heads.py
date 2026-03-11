"""merge heads

Revision ID: merge001
Revises: a0361b251fa3, f1g2h3i4j5k6
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = 'merge001'
down_revision = ('a0361b251fa3', 'f1g2h3i4j5k6')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
