"""add_attestations_table

Revision ID: e9f0g1h2i3j4
Revises: d8e9f0g1h2i3
Create Date: 2026-01-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9f0g1h2i3j4'
down_revision = 'd8e9f0g1h2i3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create attestations table
    op.create_table('attestations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=44), nullable=False),
        sa.Column('attestation_id', sa.String(length=255), nullable=False),
        sa.Column('issuer', sa.String(length=50), nullable=False),
        sa.Column('schema', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('on_chain', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('sas_attestation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_attestations_user_id'), 'attestations', ['user_id'], unique=False)
    op.create_index(op.f('ix_attestations_wallet_address'), 'attestations', ['wallet_address'], unique=False)
    op.create_index(op.f('ix_attestations_attestation_id'), 'attestations', ['attestation_id'], unique=True)
    op.create_index(op.f('ix_attestations_issuer'), 'attestations', ['issuer'], unique=False)
    op.create_index(op.f('ix_attestations_schema'), 'attestations', ['schema'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_attestations_schema'), table_name='attestations')
    op.drop_index(op.f('ix_attestations_issuer'), table_name='attestations')
    op.drop_index(op.f('ix_attestations_attestation_id'), table_name='attestations')
    op.drop_index(op.f('ix_attestations_wallet_address'), table_name='attestations')
    op.drop_index(op.f('ix_attestations_user_id'), table_name='attestations')
    
    # Drop table
    op.drop_table('attestations')
