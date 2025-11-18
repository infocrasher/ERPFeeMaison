"""add payment tracking fields to orders

Revision ID: add_payment_fields_to_orders
Revises: ajout_image_filename_a_product
Create Date: 2024-09-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payment_fields_to_orders'
down_revision = 'ajout_image_filename_a_product'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='pending'))
        batch_op.add_column(sa.Column('payment_paid_at', sa.DateTime(), nullable=True))

    op.execute("UPDATE orders SET amount_paid = 0 WHERE amount_paid IS NULL")
    op.execute("UPDATE orders SET payment_status = 'pending' WHERE payment_status IS NULL")

    with op.batch_alter_table('orders') as batch_op:
        batch_op.alter_column('amount_paid', server_default=None)
        batch_op.alter_column('payment_status', server_default=None)


def downgrade():
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('payment_paid_at')
        batch_op.drop_column('payment_status')
        batch_op.drop_column('amount_paid')

