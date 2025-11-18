"""Ajout gestion invendus quotidiens et inventaire hebdomadaire comptoir

Revision ID: add_waste_weekly_simple
Revises: 2dc96cd598b0
Create Date: 2025-10-22 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_waste_weekly_simple'
down_revision = '2dc96cd598b0'
branch_labels = None
depends_on = None


def upgrade():
    # Ajouter les colonnes de péremption à la table products
    op.add_column('products', sa.Column('shelf_life_days', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('requires_expiry_tracking', sa.Boolean(), nullable=True, default=False))
    
    # Créer la table daily_waste en utilisant les ENUMs existants
    op.create_table('daily_waste',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('waste_date', sa.Date(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),  # Utiliser String au lieu d'ENUM
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('declared_by_id', sa.Integer(), nullable=False),
        sa.Column('declared_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['declared_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_waste_waste_date'), 'daily_waste', ['waste_date'], unique=False)
    
    # Créer la table weekly_comptoir_inventories
    op.create_table('weekly_comptoir_inventories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inventory_date', sa.Date(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # Utiliser String au lieu d'ENUM
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weekly_comptoir_inventories_inventory_date'), 'weekly_comptoir_inventories', ['inventory_date'], unique=False)
    
    # Créer la table weekly_comptoir_items
    op.create_table('weekly_comptoir_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inventory_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('theoretical_stock', sa.Float(), nullable=False),
        sa.Column('physical_stock', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('variance_percentage', sa.Float(), nullable=True),
        sa.Column('variance_level', sa.String(50), nullable=True),  # Utiliser String au lieu d'ENUM
        sa.Column('theoretical_value', sa.Numeric(12, 4), nullable=False),
        sa.Column('physical_value', sa.Numeric(12, 4), nullable=False),
        sa.Column('variance_value', sa.Numeric(12, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 4), nullable=True),
        sa.Column('counted_at', sa.DateTime(), nullable=True),
        sa.Column('counted_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['inventory_id'], ['weekly_comptoir_inventories.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['counted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Supprimer les tables
    op.drop_table('weekly_comptoir_items')
    op.drop_table('weekly_comptoir_inventories')
    op.drop_table('daily_waste')
    
    # Supprimer les colonnes de péremption
    op.drop_column('products', 'requires_expiry_tracking')
    op.drop_column('products', 'shelf_life_days')









