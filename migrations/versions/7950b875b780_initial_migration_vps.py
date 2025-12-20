"""Initial migration VPS

Revision ID: 7950b875b780
Revises: 
Create Date: 2025-11-19 00:46:55.643916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7950b875b780'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Mini upgrade for local sync (only essential tables)
    op.create_table('accounting_accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )

def downgrade():
    op.drop_table('accounting_accounts')
