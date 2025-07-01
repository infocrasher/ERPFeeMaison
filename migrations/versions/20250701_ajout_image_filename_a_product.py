"""Ajout du champ image_filename à Product

Revision ID: ajout_image_filename_a_product
Revises: 05d18bd637d0
Create Date: 2025-07-01 02:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ajout_image_filename_a_product'
down_revision = '05d18bd637d0'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_filename', sa.String(length=255), nullable=True))

def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('image_filename')
