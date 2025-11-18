#!/usr/bin/env python3
"""
Script d'import des données historiques de comptabilité dans la base de données.

Ce script :
1. Lit le CSV généré par extract_historical_data_from_excel.py
2. Importe les données dans la table historical_accounting_data
3. Peut être exécuté sur le VPS après déploiement

Usage:
    python scripts/import_historical_data.py donnees_historiques_comptabilite.csv
"""

import sys
import os
import csv
from datetime import datetime
from decimal import Decimal

# Ajouter le répertoire parent au path pour importer l'app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from app.accounting.models import HistoricalAccountingData

def import_historical_data(csv_filepath):
    """Importe les données historiques depuis un CSV"""
    app = create_app()
    
    with app.app_context():
        print(f"📂 Lecture du fichier: {csv_filepath}")
        
        if not os.path.exists(csv_filepath):
            print(f"❌ Fichier non trouvé: {csv_filepath}")
            sys.exit(1)
        
        # Compter les lignes
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            total_rows = sum(1 for _ in reader)
        
        print(f"📊 {total_rows} enregistrements à importer\n")
        
        # Réimporter pour traiter
        imported = 0
        updated = 0
        errors = 0
        
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader, 1):
                try:
                    # Parser la date
                    record_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    
                    # Parser les montants
                    revenue = Decimal(str(row.get('revenue', 0) or 0))
                    purchases = Decimal(str(row.get('purchases', 0) or 0))
                    salaries = Decimal(str(row.get('salaries', 0) or 0))
                    rent = Decimal(str(row.get('rent', 0) or 0))
                    other_expenses = Decimal(str(row.get('other_expenses', 0) or 0))
                    
                    # Chercher si l'enregistrement existe déjà
                    existing = HistoricalAccountingData.query.filter_by(record_date=record_date).first()
                    
                    if existing:
                        # Mettre à jour
                        existing.revenue = revenue
                        existing.purchases = purchases
                        existing.salaries = salaries
                        existing.rent = rent
                        existing.other_expenses = other_expenses
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        # Créer nouveau
                        new_record = HistoricalAccountingData(
                            record_date=record_date,
                            revenue=revenue,
                            purchases=purchases,
                            salaries=salaries,
                            rent=rent,
                            other_expenses=other_expenses
                        )
                        db.session.add(new_record)
                        imported += 1
                    
                    # Commit par batch de 100
                    if (row_idx % 100) == 0:
                        db.session.commit()
                        print(f"   ✅ Traité {row_idx}/{total_rows} enregistrements...")
                
                except Exception as e:
                    errors += 1
                    print(f"   ❌ Erreur ligne {row_idx}: {e}")
                    continue
        
        # Commit final
        try:
            db.session.commit()
            print(f"\n✅ Import terminé avec succès!")
            print(f"   📥 Nouveaux enregistrements: {imported}")
            print(f"   🔄 Enregistrements mis à jour: {updated}")
            print(f"   ❌ Erreurs: {errors}")
            print(f"   📊 Total dans la base: {HistoricalAccountingData.query.count()} enregistrements")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors du commit: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_historical_data.py <fichier_csv>")
        print("\nExemple:")
        print("  python scripts/import_historical_data.py donnees_historiques_comptabilite.csv")
        sys.exit(1)
    
    csv_filepath = sys.argv[1]
    import_historical_data(csv_filepath)

if __name__ == '__main__':
    main()
