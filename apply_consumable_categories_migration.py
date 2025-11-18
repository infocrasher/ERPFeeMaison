#!/usr/bin/env python3
"""
Script pour appliquer manuellement la migration des catégories de consommables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.consumables.models import ConsumableCategory, ConsumableRange

def apply_migration():
    """Applique la migration manuellement"""
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Application de la migration des catégories de consommables...")
        
        # Créer les tables si elles n'existent pas
        try:
            # Créer les tables
            from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
            from datetime import datetime
            
            # Vérifier si les tables existent déjà
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            from sqlalchemy import text
            
            if 'consumable_categories' not in existing_tables:
                print("📋 Création de la table consumable_categories...")
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        CREATE TABLE consumable_categories (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            description TEXT,
                            product_category_id INTEGER NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP,
                            updated_at TIMESTAMP,
                            FOREIGN KEY (product_category_id) REFERENCES categories(id)
                        )
                    '''))
                    conn.commit()
                print("✅ Table consumable_categories créée")
            
            if 'consumable_ranges' not in existing_tables:
                print("📋 Création de la table consumable_ranges...")
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        CREATE TABLE consumable_ranges (
                            id SERIAL PRIMARY KEY,
                            category_id INTEGER NOT NULL,
                            min_quantity INTEGER NOT NULL,
                            max_quantity INTEGER NOT NULL,
                            consumable_product_id INTEGER NOT NULL,
                            quantity_per_unit DOUBLE PRECISION NOT NULL DEFAULT 1.0,
                            notes TEXT,
                            created_at TIMESTAMP,
                            updated_at TIMESTAMP,
                            FOREIGN KEY (category_id) REFERENCES consumable_categories(id),
                            FOREIGN KEY (consumable_product_id) REFERENCES products(id)
                        )
                    '''))
                    conn.commit()
                print("✅ Table consumable_ranges créée")
            
            print("🎉 Migration appliquée avec succès !")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration : {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("\n✅ Les tables des catégories de consommables sont maintenant disponibles !")
    else:
        print("\n❌ Erreur lors de l'application de la migration.")
        sys.exit(1)
