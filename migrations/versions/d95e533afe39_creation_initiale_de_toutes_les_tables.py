"""Creation initiale de toutes les tables

Revision ID: d95e533afe39
Revises: 
Create Date: 2025-06-26 02:04:30.593829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd95e533afe39'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('employees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.Column('salaire_fixe', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('prime', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('units',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('base_unit', sa.String(length=10), nullable=False),
    sa.Column('conversion_factor', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('unit_type', sa.String(length=20), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('order_type', sa.String(length=50), nullable=False),
    sa.Column('customer_name', sa.String(length=200), nullable=True),
    sa.Column('customer_phone', sa.String(length=20), nullable=True),
    sa.Column('customer_address', sa.Text(), nullable=True),
    sa.Column('delivery_option', sa.String(length=20), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=False),
    sa.Column('delivery_cost', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_orders_status'), ['status'], unique=False)

    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('product_type', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=False),
    sa.Column('sku', sa.String(length=50), nullable=True),
    sa.Column('quantity_in_stock', sa.Float(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('stock_comptoir', sa.Float(), nullable=False),
    sa.Column('stock_ingredients_local', sa.Float(), nullable=False),
    sa.Column('stock_ingredients_magasin', sa.Float(), nullable=False),
    sa.Column('stock_consommables', sa.Float(), nullable=False),
    sa.Column('total_stock_value', sa.Numeric(precision=12, scale=4), server_default='0.0', nullable=False),
    sa.Column('seuil_min_comptoir', sa.Float(), nullable=True),
    sa.Column('seuil_min_ingredients_local', sa.Float(), nullable=True),
    sa.Column('seuil_min_ingredients_magasin', sa.Float(), nullable=True),
    sa.Column('seuil_min_consommables', sa.Float(), nullable=True),
    sa.Column('last_stock_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sku')
    )
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_products_name'), ['name'], unique=False)

    op.create_table('purchases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=50), nullable=False),
    sa.Column('supplier_name', sa.String(length=200), nullable=False),
    sa.Column('supplier_contact', sa.String(length=100), nullable=True),
    sa.Column('supplier_phone', sa.String(length=20), nullable=True),
    sa.Column('supplier_email', sa.String(length=120), nullable=True),
    sa.Column('supplier_address', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'REQUESTED', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'INVOICED', 'CANCELLED', name='purchasestatus'), nullable=False),
    sa.Column('urgency', sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='purchaseurgency'), nullable=False),
    sa.Column('requested_by_id', sa.Integer(), nullable=False),
    sa.Column('approved_by_id', sa.Integer(), nullable=True),
    sa.Column('received_by_id', sa.Integer(), nullable=True),
    sa.Column('requested_date', sa.DateTime(), nullable=False),
    sa.Column('approved_date', sa.DateTime(), nullable=True),
    sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
    sa.Column('received_date', sa.DateTime(), nullable=True),
    sa.Column('is_paid', sa.Boolean(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('subtotal_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('shipping_cost', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('internal_notes', sa.Text(), nullable=True),
    sa.Column('terms_conditions', sa.Text(), nullable=True),
    sa.Column('payment_terms', sa.String(length=100), nullable=True),
    sa.Column('default_stock_location', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['received_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reference')
    )
    op.create_table('stock_transfers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=50), nullable=False),
    sa.Column('source_location', sa.Enum('COMPTOIR', 'INGREDIENTS_LOCAL', 'INGREDIENTS_MAGASIN', 'CONSOMMABLES', name='stocklocationtype'), nullable=False),
    sa.Column('destination_location', sa.Enum('COMPTOIR', 'INGREDIENTS_LOCAL', 'INGREDIENTS_MAGASIN', 'CONSOMMABLES', name='stocklocationtype'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'REQUESTED', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED', name='transferstatus'), nullable=False),
    sa.Column('requested_by_id', sa.Integer(), nullable=False),
    sa.Column('approved_by_id', sa.Integer(), nullable=True),
    sa.Column('completed_by_id', sa.Integer(), nullable=True),
    sa.Column('requested_date', sa.DateTime(), nullable=False),
    sa.Column('approved_date', sa.DateTime(), nullable=True),
    sa.Column('scheduled_date', sa.DateTime(), nullable=True),
    sa.Column('completed_date', sa.DateTime(), nullable=True),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['completed_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reference')
    )
    op.create_table('order_employees',
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('order_id', 'employee_id')
    )
    op.create_table('order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('purchase_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('purchase_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity_ordered', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('original_quantity', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('original_unit_id', sa.Integer(), nullable=True),
    sa.Column('original_unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('quantity_received', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('stock_location', sa.String(length=50), nullable=False),
    sa.Column('description_override', sa.String(length=255), nullable=True),
    sa.Column('supplier_reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['original_unit_id'], ['units.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recipes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('yield_quantity', sa.Integer(), server_default='1', nullable=False),
    sa.Column('yield_unit', sa.String(length=50), server_default='pièces', nullable=False),
    sa.Column('preparation_time', sa.Integer(), nullable=True),
    sa.Column('cooking_time', sa.Integer(), nullable=True),
    sa.Column('difficulty_level', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('production_location', sa.String(length=50), server_default='ingredients_magasin', nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('product_id')
    )
    op.create_table('stock_movements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=50), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('stock_location', sa.Enum('COMPTOIR', 'INGREDIENTS_LOCAL', 'INGREDIENTS_MAGASIN', 'CONSOMMABLES', name='stocklocationtype'), nullable=False),
    sa.Column('movement_type', sa.Enum('ENTREE', 'SORTIE', 'TRANSFERT_SORTIE', 'TRANSFERT_ENTREE', 'AJUSTEMENT_POSITIF', 'AJUSTEMENT_NEGATIF', 'PRODUCTION', 'VENTE', 'INVENTAIRE', name='stockmovementtype'), nullable=False),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.Column('unit_cost', sa.Float(), nullable=True),
    sa.Column('total_value', sa.Float(), nullable=True),
    sa.Column('stock_before', sa.Float(), nullable=True),
    sa.Column('stock_after', sa.Float(), nullable=True),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('transfer_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('reason', sa.String(length=255), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['transfer_id'], ['stock_transfers.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('reference')
    )
    op.create_table('stock_transfer_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transfer_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity_requested', sa.Float(), nullable=False),
    sa.Column('quantity_approved', sa.Float(), nullable=True),
    sa.Column('quantity_transferred', sa.Float(), nullable=True),
    sa.Column('unit_cost', sa.Float(), nullable=True),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['transfer_id'], ['stock_transfers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('recipe_ingredients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity_needed', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recipe_ingredients')
    op.drop_table('stock_transfer_lines')
    op.drop_table('stock_movements')
    op.drop_table('recipes')
    op.drop_table('purchase_items')
    op.drop_table('order_items')
    op.drop_table('order_employees')
    op.drop_table('stock_transfers')
    op.drop_table('purchases')
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_products_name'))

    op.drop_table('products')
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_orders_status'))

    op.drop_table('orders')
    op.drop_table('users')
    op.drop_table('units')
    op.drop_table('employees')
    op.drop_table('categories')
    # ### end Alembic commands ###
