-- Script SQL pour créer la table salary_advances directement
-- À exécuter si la migration Alembic ne fonctionne pas

-- Créer la table salary_advances si elle n'existe pas déjà
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

-- Créer l'index pour optimiser les requêtes par période
CREATE INDEX IF NOT EXISTS idx_salary_advance_period 
ON salary_advances(employee_id, period_month, period_year);

-- Vérifier que la table a été créée
SELECT 'Table salary_advances créée avec succès!' as status;

