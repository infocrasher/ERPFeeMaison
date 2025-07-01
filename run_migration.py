#!/usr/bin/env python3
"""
Script pour exécuter les migrations Alembic avec le contexte Flask
"""
import os
import sys
from app import create_app
from flask_migrate import upgrade, migrate

def main():
    app = create_app()
    
    with app.app_context():
        print("Création de la migration...")
        try:
            # Générer la migration
            os.system('alembic -c migrations/alembic.ini revision --autogenerate -m "Ajout valeur_stock_ingredients_magasin et valeur_stock_ingredients_local à Product"')
            print("Migration générée avec succès!")
            
            print("Application de la migration...")
            # Appliquer la migration
            upgrade()
            print("Migration appliquée avec succès!")
            
        except Exception as e:
            print(f"Erreur lors de la migration: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main() 