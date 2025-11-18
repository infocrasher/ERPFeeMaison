#!/usr/bin/env python3
"""
Script pour ajouter les colonnes valeur_stock_comptoir et valeur_stock_consommables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_valeur_stock_columns():
    """Ajouter les colonnes valeur_stock_comptoir et valeur_stock_consommables"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Ajout des colonnes valeur_stock")
        print("=" * 50)
        
        # SQL pour ajouter les colonnes si elles n'existent pas
        sql_add_columns = """
        DO $$ 
        BEGIN
            -- Ajouter valeur_stock_comptoir si elle n'existe pas
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='products' AND column_name='valeur_stock_comptoir'
            ) THEN
                ALTER TABLE products ADD COLUMN valeur_stock_comptoir NUMERIC(12, 4) NOT NULL DEFAULT 0.0;
                RAISE NOTICE 'Colonne valeur_stock_comptoir ajoutée';
            END IF;
            
            -- Ajouter valeur_stock_consommables si elle n'existe pas
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='products' AND column_name='valeur_stock_consommables'
            ) THEN
                ALTER TABLE products ADD COLUMN valeur_stock_consommables NUMERIC(12, 4) NOT NULL DEFAULT 0.0;
                RAISE NOTICE 'Colonne valeur_stock_consommables ajoutée';
            END IF;
        END $$;
        """
        
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text(sql_add_columns))
                conn.commit()
                print("✅ Colonnes ajoutées avec succès")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("\n✅ Migration terminée")

if __name__ == "__main__":
    add_valeur_stock_columns()

