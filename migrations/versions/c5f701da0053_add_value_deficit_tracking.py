"""add value deficit tracking

Revision ID: c5f701da0053
Revises: 03378fe2e790
Create Date: 2025-11-15 00:40:25.581287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5f701da0053'
down_revision = '03378fe2e790'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('value_deficit_total', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('deficit_stock_ingredients_magasin', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('deficit_stock_ingredients_local', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('deficit_stock_comptoir', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('deficit_stock_consommables', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False))

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('deficit_stock_consommables')
        batch_op.drop_column('deficit_stock_comptoir')
        batch_op.drop_column('deficit_stock_ingredients_local')
        batch_op.drop_column('deficit_stock_ingredients_magasin')
        batch_op.drop_column('value_deficit_total')
