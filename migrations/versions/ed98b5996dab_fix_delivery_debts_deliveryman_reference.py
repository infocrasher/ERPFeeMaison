"""fix_delivery_debts_deliveryman_reference

Revision ID: ed98b5996dab
Revises: 5a7dc22f426f
Create Date: 2025-07-03 01:57:02.392407

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed98b5996dab'
down_revision = '5a7dc22f426f'
branch_labels = None
depends_on = None


def upgrade():
    # Supprimer l'ancienne contrainte de clé étrangère
    op.drop_constraint('delivery_debts_deliveryman_id_fkey', 'delivery_debts', type_='foreignkey')
    
    # Créer la nouvelle contrainte vers deliverymen
    op.create_foreign_key('delivery_debts_deliveryman_id_fkey', 'delivery_debts', 'deliverymen', ['deliveryman_id'], ['id'])


def downgrade():
    # Supprimer la nouvelle contrainte
    op.drop_constraint('delivery_debts_deliveryman_id_fkey', 'delivery_debts', type_='foreignkey')
    
    # Rétablir l'ancienne contrainte vers employees
    op.create_foreign_key('delivery_debts_deliveryman_id_fkey', 'delivery_debts', 'employees', ['deliveryman_id'], ['id'])
