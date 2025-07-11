"""ajout caisse et mouvements de caisse (POS)

Revision ID: f895bfcbdbd2
Revises: 6a08ba707d0b
Create Date: 2025-06-29 04:21:16.523192

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f895bfcbdbd2'
down_revision = '6a08ba707d0b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cash_register_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('opened_at', sa.DateTime(), nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('initial_amount', sa.Float(), nullable=False),
    sa.Column('closing_amount', sa.Float(), nullable=True),
    sa.Column('opened_by_id', sa.Integer(), nullable=True),
    sa.Column('closed_by_id', sa.Integer(), nullable=True),
    sa.Column('is_open', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['closed_by_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['opened_by_id'], ['employees.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cash_movement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('type', sa.String(length=32), nullable=True),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('reason', sa.String(length=128), nullable=True),
    sa.Column('employee_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['cash_register_session.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cash_movement')
    op.drop_table('cash_register_session')
    # ### end Alembic commands ###
