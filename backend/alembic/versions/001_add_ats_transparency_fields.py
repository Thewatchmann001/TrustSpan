"""
Alembic Migration: Update CV Model for Transparent ATS System
Adds columns to support separate storage of original file, analysis, and optimizations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_ats_transparency'
down_revision = '31f43d148703'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to CVs table
    op.add_column('cvs', sa.Column('original_file_url', sa.String(500), nullable=True))
    op.add_column('cvs', sa.Column('original_file_name', sa.String(255), nullable=True))
    op.add_column('cvs', sa.Column('ats_score', sa.Float(), nullable=True))
    op.add_column('cvs', sa.Column('ats_grade', sa.String(5), nullable=True))
    op.add_column('cvs', sa.Column('ats_analysis', postgresql.JSON(), nullable=True))
    op.add_column('cvs', sa.Column('ats_issues', postgresql.JSON(), nullable=True))
    op.add_column('cvs', sa.Column('ats_recommendations', postgresql.JSON(), nullable=True))
    op.add_column('cvs', sa.Column('ats_optimized_content', postgresql.JSON(), nullable=True))
    op.add_column('cvs', sa.Column('ats_changes', postgresql.JSON(), nullable=True))
    op.add_column('cvs', sa.Column('ats_optimized_at', sa.DateTime(), nullable=True))
    
    # Create index on ats_score for filtering
    op.create_index(op.f('ix_cvs_ats_score'), 'cvs', ['ats_score'], unique=False)


def downgrade():
    # Remove columns in reverse order
    op.drop_index(op.f('ix_cvs_ats_score'), table_name='cvs')
    op.drop_column('cvs', 'ats_optimized_at')
    op.drop_column('cvs', 'ats_changes')
    op.drop_column('cvs', 'ats_optimized_content')
    op.drop_column('cvs', 'ats_recommendations')
    op.drop_column('cvs', 'ats_issues')
    op.drop_column('cvs', 'ats_analysis')
    op.drop_column('cvs', 'ats_grade')
    op.drop_column('cvs', 'ats_score')
    op.drop_column('cvs', 'original_file_name')
    op.drop_column('cvs', 'original_file_url')
