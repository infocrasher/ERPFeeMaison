"""Add profiles table and profile_id to users

Revision ID: add_profiles_table
Revises: 
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'add_profiles_table'
down_revision = '1a3472678c27'  # Révision commune : ajout_module_inventaire_physique_vs
branch_labels = None
depends_on = None


def upgrade():
    # Vérifier si la table profiles existe déjà
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Créer la table profiles si elle n'existe pas
    if 'profiles' not in tables:
        op.create_table('profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('permissions', JSON, nullable=False, server_default='{}'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Vérifier si la colonne profile_id existe déjà dans users
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'profile_id' not in users_columns:
        op.add_column('users', sa.Column('profile_id', sa.Integer(), nullable=True))
        
        # Vérifier si la clé étrangère existe déjà
        foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('users')]
        if 'fk_users_profile_id' not in foreign_keys:
            op.create_foreign_key('fk_users_profile_id', 'users', 'profiles', ['profile_id'], ['id'])


def downgrade():
    # Supprimer la colonne profile_id
    op.drop_constraint('fk_users_profile_id', 'users', type_='foreignkey')
    op.drop_column('users', 'profile_id')
    
    # Supprimer la table profiles
    op.drop_table('profiles')

