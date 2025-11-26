"""Ajout module gestion consommables avec calcul automatique

Revision ID: add_consumables_module
Revises: f283921abf9b
Create Date: 2025-10-22 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_consumables_module'
down_revision = 'f283921abf9b'
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table consumable_usage
    op.create_table('consumable_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('estimated_quantity_used', sa.Float(), nullable=False),
        sa.Column('actual_quantity_used', sa.Float(), nullable=True),
        sa.Column('estimated_value', sa.Numeric(12, 4), nullable=False),
        sa.Column('actual_value', sa.Numeric(12, 4), nullable=True),
        sa.Column('calculation_method', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consumable_usage_usage_date'), 'consumable_usage', ['usage_date'], unique=False)
    
    # Créer la table consumable_adjustments
    op.create_table('consumable_adjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('adjustment_date', sa.Date(), nullable=False),
        sa.Column('adjustment_type', sa.String(50), nullable=False),
        sa.Column('quantity_adjusted', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('adjusted_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['adjusted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consumable_adjustments_adjustment_date'), 'consumable_adjustments', ['adjustment_date'], unique=False)
    
    # Créer la table consumable_recipes
    op.create_table('consumable_recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('finished_product_id', sa.Integer(), nullable=False),
        sa.Column('consumable_product_id', sa.Integer(), nullable=False),
        sa.Column('quantity_per_unit', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['finished_product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['consumable_product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Supprimer les tables
    op.drop_table('consumable_recipes')
    op.drop_table('consumable_adjustments')
    op.drop_table('consumable_usage')











