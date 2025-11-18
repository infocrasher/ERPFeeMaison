"""Add show_in_pos field to categories table

Revision ID: add_show_in_pos_categories
Revises: add_profiles_table
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_show_in_pos_categories'
down_revision = 'add_profiles_table'  # Révision précédente
branch_labels = None
depends_on = None


def upgrade():
    # Vérifier si la colonne show_in_pos existe déjà
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Vérifier si la table categories existe
    tables = inspector.get_table_names()
    if 'categories' not in tables:
        print("⚠️  Table 'categories' n'existe pas encore. La migration sera ignorée.")
        return
    
    # Vérifier si la colonne existe déjà
    categories_columns = [col['name'] for col in inspector.get_columns('categories')]
    if 'show_in_pos' not in categories_columns:
        # Ajouter la colonne show_in_pos avec valeur par défaut True
        op.add_column('categories', 
            sa.Column('show_in_pos', sa.Boolean(), nullable=False, server_default='true')
        )
        print("✅ Colonne 'show_in_pos' ajoutée à la table 'categories'")
    else:
        print("ℹ️  Colonne 'show_in_pos' existe déjà dans 'categories'")


def downgrade():
    # Vérifier si la colonne existe avant de la supprimer
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    tables = inspector.get_table_names()
    if 'categories' not in tables:
        return
    
    categories_columns = [col['name'] for col in inspector.get_columns('categories')]
    if 'show_in_pos' in categories_columns:
        op.drop_column('categories', 'show_in_pos')
        print("✅ Colonne 'show_in_pos' supprimée de la table 'categories'")


