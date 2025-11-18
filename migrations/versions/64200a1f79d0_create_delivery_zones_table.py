"""create_delivery_zones_table

Revision ID: 64200a1f79d0
Revises: 7ab94503d2b6
Create Date: 2025-11-16 03:02:07.836283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64200a1f79d0'
down_revision = '7ab94503d2b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'delivery_zones',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
    )


def downgrade():
    op.drop_table('delivery_zones')
