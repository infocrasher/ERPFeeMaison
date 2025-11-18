"""merge heads before payment tracking

Revision ID: 03378fe2e790
Revises: 187fe6b7617a, add_consumables_module, add_show_in_pos_categories, add_waste_weekly_simple, c553daaecfbb, add_payment_fields_to_orders
Create Date: 2025-11-11 23:35:47.298807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03378fe2e790'
down_revision = ('187fe6b7617a', 'add_consumables_module', 'add_show_in_pos_categories', 'add_waste_weekly_simple', 'c553daaecfbb', 'add_payment_fields_to_orders')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
