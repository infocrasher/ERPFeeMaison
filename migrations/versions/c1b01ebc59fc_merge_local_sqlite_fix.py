"""merge local sqlite fix

Revision ID: c1b01ebc59fc
Revises: 23adf923c0a3, 2dc96cd598b0, 365191f90e87, add_order_item_reception, f283921abf9b
Create Date: 2025-12-08 02:35:58.913269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1b01ebc59fc'
down_revision = ('23adf923c0a3', '2dc96cd598b0', '365191f90e87', 'add_order_item_reception', 'f283921abf9b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
