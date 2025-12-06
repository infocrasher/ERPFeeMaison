"""add_order_item_reception

Revision ID: add_order_item_reception
Revises: add_salary_advances
Create Date: 2025-12-06 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_order_item_reception'
down_revision = 'add_salary_advances'
branch_labels = None
depends_on = None

def upgrade():
    # Ajout des colonnes pour le suivi de réception partielle
    op.add_column('order_items', sa.Column('is_received', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('order_items', sa.Column('received_at', sa.DateTime(), nullable=True))
    op.add_column('order_items', sa.Column('received_by_id', sa.Integer(), nullable=True))
    
    # Ajout de la clé étrangère vers employees
    # Note: On utilise un nom explicite pour la contrainte pour faciliter le downgrade
    op.create_foreign_key('fk_order_items_received_by', 'order_items', 'employees', ['received_by_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_order_items_received_by', 'order_items', type_='foreignkey')
    op.drop_column('order_items', 'received_by_id')
    op.drop_column('order_items', 'received_at')
    op.drop_column('order_items', 'is_received')
