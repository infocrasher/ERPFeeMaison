"""add b2b composition and invoice sections

Revision ID: b2b_schema_updates
Revises: c06166c4cc37
Create Date: 2025-12-20 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2b_schema_updates'
down_revision = 'c06166c4cc37'
branch_labels = None
depends_on = None


def upgrade():
    # Ajouter la colonne composition à b2b_order_items
    op.add_column('b2b_order_items', sa.Column('composition', sa.JSON(), nullable=True))
    
    # Ajouter la colonne section à invoice_items
    op.add_column('invoice_items', sa.Column('section', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('invoice_items', 'section')
    op.drop_column('b2b_order_items', 'composition')
