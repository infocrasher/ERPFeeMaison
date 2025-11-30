"""add_salary_advances_table

Revision ID: add_salary_advances
Revises: 9419cff9a6d1
Create Date: 2025-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_salary_advances'
down_revision = '9419cff9a6d1'  # Dernière migration connue
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table salary_advances si elle n'existe pas déjà
    op.execute("""
        CREATE TABLE IF NOT EXISTS salary_advances (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            advance_date DATE NOT NULL,
            period_month INTEGER NOT NULL,
            period_year INTEGER NOT NULL,
            reason VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            CONSTRAINT fk_salary_advance_employee FOREIGN KEY (employee_id) REFERENCES employees(id),
            CONSTRAINT fk_salary_advance_user FOREIGN KEY (created_by) REFERENCES users(id)
        );
    """)
    
    # Créer l'index pour optimiser les requêtes par période
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_salary_advance_period 
        ON salary_advances(employee_id, period_month, period_year);
    """)


def downgrade():
    op.drop_table('salary_advances')

