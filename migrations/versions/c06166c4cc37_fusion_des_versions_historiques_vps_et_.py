"""Fusion des versions historiques VPS et Local

Revision ID: c06166c4cc37
Revises: 7950b875b780, c1b01ebc59fc
Create Date: 2025-12-20 00:50:56.976787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c06166c4cc37'
down_revision = ('7950b875b780', 'c1b01ebc59fc')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
