"""add_consumable_categories_and_ranges

Revision ID: c553daaecfbb
Revises: 1a3472678c27
Create Date: 2025-10-27 22:17:06.945025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c553daaecfbb'
down_revision = '1a3472678c27'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'consumable_categories' not in tables:
        op.create_table(
            'consumable_categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('product_category_id', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_category_id'], ['categories.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'consumable_ranges' not in tables:
        op.create_table(
            'consumable_ranges',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('min_quantity', sa.Integer(), nullable=False),
            sa.Column('max_quantity', sa.Integer(), nullable=False),
            sa.Column('consumable_product_id', sa.Integer(), nullable=False),
            sa.Column('quantity_per_unit', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['consumable_categories.id']),
            sa.ForeignKeyConstraint(['consumable_product_id'], ['products.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    # Supprimer les tables dans l'ordre inverse
    op.drop_table('consumable_ranges')
    op.drop_table('consumable_categories')
