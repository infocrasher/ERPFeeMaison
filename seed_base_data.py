#!/usr/bin/env python3
"""
Script d'initialisation des données de base pour ERP Fée Maison
À exécuter après le déploiement pour avoir un système fonctionnel
"""

import os
from app import create_app
from extensions import db
from models import Category, Unit
from app.accounting.models import Account, Journal, FiscalYear
from datetime import date

def seed_units():
    """Ajouter les unités de mesure essentielles"""
    units_data = [
        # Poids
        {'name': 'g', 'base_unit': 'g', 'conversion_factor': 1.0, 'unit_type': 'weight', 'display_order': 1},
        {'name': 'kg', 'base_unit': 'g', 'conversion_factor': 1000.0, 'unit_type': 'weight', 'display_order': 2},
        {'name': 'mg', 'base_unit': 'g', 'conversion_factor': 0.001, 'unit_type': 'weight', 'display_order': 3},
        
        # Volume
        {'name': 'ml', 'base_unit': 'ml', 'conversion_factor': 1.0, 'unit_type': 'volume', 'display_order': 4},
        {'name': 'l', 'base_unit': 'ml', 'conversion_factor': 1000.0, 'unit_type': 'volume', 'display_order': 5},
        {'name': 'cl', 'base_unit': 'ml', 'conversion_factor': 10.0, 'unit_type': 'volume', 'display_order': 6},
        
        # Quantité
        {'name': 'pièce', 'base_unit': 'pièce', 'conversion_factor': 1.0, 'unit_type': 'quantity', 'display_order': 7},
        {'name': 'boîte', 'base_unit': 'pièce', 'conversion_factor': 1.0, 'unit_type': 'quantity', 'display_order': 8},
        {'name': 'paquet', 'base_unit': 'pièce', 'conversion_factor': 1.0, 'unit_type': 'quantity', 'display_order': 9},
        {'name': 'sac', 'base_unit': 'pièce', 'conversion_factor': 1.0, 'unit_type': 'quantity', 'display_order': 10},
    ]
    
    for unit_data in units_data:
        existing = Unit.query.filter_by(name=unit_data['name']).first()
        if not existing:
            unit = Unit(**unit_data)
            db.session.add(unit)
            print(f"✅ Unité ajoutée: {unit_data['name']}")
    
    db.session.commit()
    print("📏 Unités de mesure initialisées")

# Catégories retirées - à ajouter manuellement plus tard via l'interface web

def seed_accounting():
    """Initialiser le plan comptable et les journaux"""
    
    # Exercice fiscal
    current_year = date.today().year
    fiscal_year = FiscalYear.query.filter_by(year=current_year).first()
    if not fiscal_year:
        fiscal_year = FiscalYear(
            year=current_year,
            start_date=date(current_year, 1, 1),
            end_date=date(current_year, 12, 31),
            is_active=True
        )
        db.session.add(fiscal_year)
        print(f"✅ Exercice fiscal {current_year} créé")
    
    # Plan comptable de base
    accounts_data = [
        # Classe 1 - Comptes de capitaux
        {'code': '101', 'name': 'Capital', 'account_type': 'equity', 'nature': 'credit'},
        {'code': '120', 'name': 'Résultat de l\'exercice', 'account_type': 'equity', 'nature': 'credit'},
        
        # Classe 4 - Comptes de tiers
        {'code': '401', 'name': 'Fournisseurs', 'account_type': 'liability', 'nature': 'credit'},
        {'code': '411', 'name': 'Clients', 'account_type': 'asset', 'nature': 'debit'},
        {'code': '421', 'name': 'Personnel - Rémunérations dues', 'account_type': 'liability', 'nature': 'credit'},
        {'code': '437', 'name': 'Charges sociales', 'account_type': 'liability', 'nature': 'credit'},
        
        # Classe 5 - Comptes financiers
        {'code': '512', 'name': 'Banque', 'account_type': 'asset', 'nature': 'debit'},
        {'code': '530', 'name': 'Caisse', 'account_type': 'asset', 'nature': 'debit'},
        
        # Classe 6 - Comptes de charges
        {'code': '601', 'name': 'Achats matières premières', 'account_type': 'expense', 'nature': 'debit'},
        {'code': '602', 'name': 'Achats fournitures', 'account_type': 'expense', 'nature': 'debit'},
        {'code': '641', 'name': 'Rémunérations du personnel', 'account_type': 'expense', 'nature': 'debit'},
        {'code': '645', 'name': 'Charges de sécurité sociale', 'account_type': 'expense', 'nature': 'debit'},
        
        # Classe 7 - Comptes de produits
        {'code': '701', 'name': 'Ventes de produits finis', 'account_type': 'income', 'nature': 'credit'},
        {'code': '706', 'name': 'Prestations de services', 'account_type': 'income', 'nature': 'credit'},
    ]
    
    for acc_data in accounts_data:
        existing = Account.query.filter_by(code=acc_data['code']).first()
        if not existing:
            account = Account(**acc_data)
            db.session.add(account)
            print(f"✅ Compte ajouté: {acc_data['code']} - {acc_data['name']}")
    
    # Journaux comptables
    journals_data = [
        {'name': 'Achats', 'journal_type': 'purchase', 'code': 'ACH'},
        {'name': 'Ventes', 'journal_type': 'sale', 'code': 'VTE'},
        {'name': 'Banque', 'journal_type': 'bank', 'code': 'BQ'},
        {'name': 'Caisse', 'journal_type': 'cash', 'code': 'CAI'},
        {'name': 'Opérations Diverses', 'journal_type': 'general', 'code': 'OD'},
        {'name': 'Paie', 'journal_type': 'payroll', 'code': 'PAI'},
    ]
    
    for jour_data in journals_data:
        existing = Journal.query.filter_by(code=jour_data['code']).first()
        if not existing:
            journal = Journal(**jour_data)
            db.session.add(journal)
            print(f"✅ Journal ajouté: {jour_data['code']} - {jour_data['name']}")
    
    db.session.commit()
    print("📊 Plan comptable et journaux initialisés")

def main():
    """Fonction principale d'initialisation"""
    app = create_app(os.getenv('FLASK_ENV') or 'production')
    
    with app.app_context():
        print("🚀 Initialisation des données de base ERP Fée Maison")
        print("=" * 60)
        
        # Vérifier que les tables existent
        try:
            db.create_all()
            print("✅ Tables de base vérifiées")
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            return
        
        # Initialiser les données
        try:
            seed_units()
            seed_accounting()
            
            print("=" * 60)
            print("🎉 Initialisation terminée avec succès !")
            print("\n📋 Données ajoutées:")
            print(f"   📏 Unités: {Unit.query.count()}")
            print(f"   📊 Comptes: {Account.query.count()}")
            print(f"   📝 Journaux: {Journal.query.count()}")
            print("\n💡 Les catégories seront ajoutées via l'interface web")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main() 