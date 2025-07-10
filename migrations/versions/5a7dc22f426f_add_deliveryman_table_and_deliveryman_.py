"""add deliveryman table and deliveryman_id to orders

Revision ID: 5a7dc22f426f
Revises: c0510e5bc989
Create Date: 2025-07-02 04:52:09.911717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a7dc22f426f'
down_revision = 'c0510e5bc989'
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table deliverymen
    op.create_table('deliverymen',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Ajouter le champ deliveryman_id à la table orders
    op.add_column('orders', sa.Column('deliveryman_id', sa.Integer(), nullable=True))
    
    # Créer la clé étrangère
    op.create_foreign_key(None, 'orders', 'deliverymen', ['deliveryman_id'], ['id'])


def downgrade():
    # Supprimer la clé étrangère
    op.drop_constraint(None, 'orders', type_='foreignkey')
    
    # Supprimer le champ deliveryman_id
    op.drop_column('orders', 'deliveryman_id')
    
    # Supprimer la table deliverymen
    op.drop_table('deliverymen')
