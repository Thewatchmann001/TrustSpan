"""Add multiple verification paths for credibility scoring

Revision ID: d8e9f0g1h2i3
Revises: c7d8e9f0g1h2
Create Date: 2026-01-08 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8e9f0g1h2i3'
down_revision = 'c7d8e9f0g1h2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add document verification fields
    op.add_column('startups', sa.Column('business_registration_verified', sa.Boolean(), default=False))
    op.add_column('startups', sa.Column('tax_id_verified', sa.Boolean(), default=False))
    op.add_column('startups', sa.Column('documents_url', sa.String(500), nullable=True))
    
    # Add founder profile verification
    op.add_column('startups', sa.Column('founder_profile_verified', sa.Boolean(), default=False))
    op.add_column('startups', sa.Column('founder_experience_years', sa.Integer(), nullable=True))
    op.add_column('startups', sa.Column('founder_background', sa.Text(), nullable=True))
    
    # Add product/traction verification
    op.add_column('startups', sa.Column('has_mvp', sa.Boolean(), default=False))
    op.add_column('startups', sa.Column('user_base_count', sa.Integer(), default=0))
    op.add_column('startups', sa.Column('monthly_revenue', sa.Float(), default=0.0))
    
    # Add milestone tracking
    op.add_column('startups', sa.Column('milestones_completed', sa.Integer(), default=0))
    op.add_column('startups', sa.Column('last_milestone_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove all added columns
    op.drop_column('startups', 'last_milestone_date')
    op.drop_column('startups', 'milestones_completed')
    op.drop_column('startups', 'monthly_revenue')
    op.drop_column('startups', 'user_base_count')
    op.drop_column('startups', 'has_mvp')
    op.drop_column('startups', 'founder_background')
    op.drop_column('startups', 'founder_experience_years')
    op.drop_column('startups', 'founder_profile_verified')
    op.drop_column('startups', 'documents_url')
    op.drop_column('startups', 'tax_id_verified')
    op.drop_column('startups', 'business_registration_verified')
