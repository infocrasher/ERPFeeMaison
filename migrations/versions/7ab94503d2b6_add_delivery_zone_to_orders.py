"""add_delivery_zone_to_orders

Revision ID: 7ab94503d2b6
Revises: c5f701da0053
Create Date: 2025-11-16 02:58:48.717923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ab94503d2b6'
down_revision = 'c5f701da0053'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('delivery_zone', sa.String(length=100), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('delivery_zone')
