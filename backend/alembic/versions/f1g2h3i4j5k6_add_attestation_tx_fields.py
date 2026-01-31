"""add_attestation_tx_fields

Revision ID: f1g2h3i4j5k6
Revises: e9f0g1h2i3j4
Create Date: 2026-01-22 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1g2h3i4j5k6'
down_revision = 'e9f0g1h2i3j4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add transaction signature field
    op.add_column('attestations', sa.Column('transaction_signature', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_attestations_transaction_signature'), 'attestations', ['transaction_signature'], unique=False)
    
    # Add cluster field (devnet/mainnet)
    op.add_column('attestations', sa.Column('cluster', sa.String(length=20), nullable=True, server_default='devnet'))
    
    # Add account address field
    op.add_column('attestations', sa.Column('account_address', sa.String(length=44), nullable=True))


def downgrade() -> None:
    # Drop columns
    op.drop_index(op.f('ix_attestations_transaction_signature'), table_name='attestations')
    op.drop_column('attestations', 'account_address')
    op.drop_column('attestations', 'cluster')
    op.drop_column('attestations', 'transaction_signature')
