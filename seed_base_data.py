#!/usr/bin/env python3
"""
Script de synchronisation des données de base ERP Fée Maison
Utilise les données exactes de la base locale pour synchroniser le VPS
"""

import os
from app import create_app
from extensions import db
from models import Unit, Category
from app.accounting.models import Account, Journal, FiscalYear, AccountType, AccountNature, JournalType
from datetime import date

def seed_units():
    """Synchroniser les unités de mesure exactes de la base locale"""
    units_data = [
        # Unités Poids - Sacs
        {'name': 'Sac 25kg', 'base_unit': 'g', 'conversion_factor': 25000.0, 'unit_type': 'Poids'},
        {'name': 'Sac 10kg', 'base_unit': 'g', 'conversion_factor': 10000.0, 'unit_type': 'Poids'},
        {'name': 'Sac 5kg', 'base_unit': 'g', 'conversion_factor': 5000.0, 'unit_type': 'Poids'},
        {'name': 'Sac 2kg', 'base_unit': 'g', 'conversion_factor': 2000.0, 'unit_type': 'Poids'},
        {'name': 'Sac 1kg', 'base_unit': 'g', 'conversion_factor': 1000.0, 'unit_type': 'Poids'},
        {'name': 'Barre 1,8kg', 'base_unit': 'g', 'conversion_factor': 1800.0, 'unit_type': 'Poids'},
        {'name': 'Bidon 3,8kg', 'base_unit': 'g', 'conversion_factor': 3800.0, 'unit_type': 'Poids'},
        
        # Unités Poids - Boites/Sachets
        {'name': 'Boite 500g', 'base_unit': 'g', 'conversion_factor': 500.0, 'unit_type': 'Poids'},
        {'name': 'Sachet 500g', 'base_unit': 'g', 'conversion_factor': 500.0, 'unit_type': 'Poids'},
        {'name': 'Pot 500g', 'base_unit': 'g', 'conversion_factor': 500.0, 'unit_type': 'Poids'},
        {'name': 'Boite 250g', 'base_unit': 'g', 'conversion_factor': 250.0, 'unit_type': 'Poids'},
        {'name': 'Sachet 125g', 'base_unit': 'g', 'conversion_factor': 125.0, 'unit_type': 'Poids'},
        {'name': 'Sachet 10g', 'base_unit': 'g', 'conversion_factor': 10.0, 'unit_type': 'Poids'},
        {'name': 'Gramme (g)', 'base_unit': 'g', 'conversion_factor': 1.0, 'unit_type': 'Poids'},
        
        # Unités Volume
        {'name': 'Bidon 5L', 'base_unit': 'ml', 'conversion_factor': 5000.0, 'unit_type': 'Volume'},
        {'name': 'Bouteille 5L', 'base_unit': 'ml', 'conversion_factor': 5000.0, 'unit_type': 'Volume'},
        {'name': 'Bouteille 2L', 'base_unit': 'ml', 'conversion_factor': 2000.0, 'unit_type': 'Volume'},
        {'name': 'Bouteille 1L', 'base_unit': 'ml', 'conversion_factor': 1000.0, 'unit_type': 'Volume'},
        {'name': 'Millilitre (ml)', 'base_unit': 'ml', 'conversion_factor': 1.0, 'unit_type': 'Volume'},
        
        # Unités Unitaires - Lots
        {'name': 'Lot de 100 pièces', 'base_unit': 'pièce', 'conversion_factor': 100.0, 'unit_type': 'Unitaire'},
        {'name': 'Lot de 50 pièces', 'base_unit': 'pièce', 'conversion_factor': 50.0, 'unit_type': 'Unitaire'},
        {'name': 'Plateau de 30 pièces', 'base_unit': 'pièce', 'conversion_factor': 30.0, 'unit_type': 'Unitaire'},
        {'name': 'Lot de 12 pièces', 'base_unit': 'pièce', 'conversion_factor': 12.0, 'unit_type': 'Unitaire'},
        {'name': 'Lot de 10 pièces', 'base_unit': 'pièce', 'conversion_factor': 10.0, 'unit_type': 'Unitaire'},
        {'name': 'Lot de 6 pièces', 'base_unit': 'pièce', 'conversion_factor': 6.0, 'unit_type': 'Unitaire'},
        {'name': 'Fardeau de 6 bouteilles', 'base_unit': 'pièce', 'conversion_factor': 6.0, 'unit_type': 'Unitaire'},
        {'name': 'Pièce', 'base_unit': 'pièce', 'conversion_factor': 1.0, 'unit_type': 'Unitaire'},
    ]
    
    for unit_data in units_data:
        existing = Unit.query.filter_by(name=unit_data['name']).first()
        if not existing:
            unit = Unit(**unit_data)
            db.session.add(unit)
            print(f"✅ Unité ajoutée: {unit_data['name']}")
        else:
            print(f"ℹ️  Unité existe déjà: {unit_data['name']}")
    
    db.session.commit()
    print("📏 Unités de mesure synchronisées")

def seed_categories():
    """Synchroniser les catégories existantes de la base locale"""
    categories_data = [
        {'name': 'Ingrédients', 'description': 'Matières premières et ingrédients'},
        {'name': 'Pâtes', 'description': 'Produits à base de pâtes'},
    ]
    
    for cat_data in categories_data:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
            print(f"✅ Catégorie ajoutée: {cat_data['name']}")
        else:
            print(f"ℹ️  Catégorie existe déjà: {cat_data['name']}")
    
    db.session.commit()
    print("🏷️ Catégories synchronisées")

def seed_accounting():
    """Synchroniser le plan comptable complet de la base locale"""
    
    # Exercice fiscal 2025
    fiscal_year = FiscalYear.query.filter_by(name="Exercice 2025").first()
    if not fiscal_year:
        fiscal_year = FiscalYear(
            name="Exercice 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            is_current=True
        )
        db.session.add(fiscal_year)
        print("✅ Exercice fiscal 2025 créé")
    
    # Plan comptable complet
    accounts_data = [
        # Classe 1 - Capitaux
        {'code': '10', 'name': 'Capital et réserves', 'account_type': 'CLASSE_1', 'account_nature': 'CREDIT'},
        {'code': '101', 'name': 'Capital social', 'account_type': 'CLASSE_1', 'account_nature': 'CREDIT'},
        
        # Classe 2 - Immobilisations
        {'code': '20', 'name': 'Immobilisations', 'account_type': 'CLASSE_2', 'account_nature': 'DEBIT'},
        {'code': '215', 'name': 'Installations techniques', 'account_type': 'CLASSE_2', 'account_nature': 'DEBIT'},
        {'code': '2154', 'name': 'Matériel de boulangerie', 'account_type': 'CLASSE_2', 'account_nature': 'DEBIT'},
        {'code': '218', 'name': 'Autres immobilisations', 'account_type': 'CLASSE_2', 'account_nature': 'DEBIT'},
        
        # Classe 3 - Stocks
        {'code': '30', 'name': 'Stocks', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '300', 'name': 'Stocks de marchandises', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '301', 'name': 'Matières premières', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '3011', 'name': 'Farines', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '3012', 'name': 'Semoules', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '3013', 'name': 'Levures et améliorants', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '302', 'name': 'Emballages', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '355', 'name': 'Produits finis', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        {'code': '3551', 'name': 'Pain et viennoiseries', 'account_type': 'CLASSE_3', 'account_nature': 'DEBIT'},
        
        # Classe 4 - Tiers
        {'code': '40', 'name': 'Fournisseurs et comptes rattachés', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '401', 'name': 'Fournisseurs', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '41', 'name': 'Clients et comptes rattachés', 'account_type': 'CLASSE_4', 'account_nature': 'DEBIT'},
        {'code': '411', 'name': 'Clients', 'account_type': 'CLASSE_4', 'account_nature': 'DEBIT'},
        {'code': '42', 'name': 'Personnel et comptes rattachés', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '421', 'name': 'Personnel - Rémunérations dues', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '43', 'name': 'Sécurité sociale et autres organismes', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '431', 'name': 'Sécurité sociale', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '44', 'name': 'État et collectivités publiques', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        {'code': '445', 'name': 'TVA à décaisser', 'account_type': 'CLASSE_4', 'account_nature': 'CREDIT'},
        
        # Classe 5 - Financiers
        {'code': '50', 'name': 'Valeurs mobilières de placement', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        {'code': '51', 'name': 'Banques', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        {'code': '512', 'name': 'Banques', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        {'code': '53', 'name': 'Caisse', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        {'code': '530', 'name': 'Caisse', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        {'code': '531', 'name': 'Caisse', 'account_type': 'CLASSE_5', 'account_nature': 'DEBIT'},
        
        # Classe 6 - Charges
        {'code': '60', 'name': 'Achats', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '601', 'name': 'Achats de matières premières', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '602', 'name': 'Achats d\'emballages', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '606', 'name': 'Achats de fournitures', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '607', 'name': 'Achats de marchandises', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '61', 'name': 'Services extérieurs', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '613', 'name': 'Locations', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '615', 'name': 'Entretien et réparations', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '616', 'name': 'Primes d\'assurance', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '62', 'name': 'Autres services extérieurs', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '621', 'name': 'Personnel extérieur', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '625', 'name': 'Déplacements', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '626', 'name': 'Frais postaux', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '627', 'name': 'Services bancaires', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '628', 'name': 'Divers', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '64', 'name': 'Charges de personnel', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '641', 'name': 'Rémunérations du personnel', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '645', 'name': 'Charges de sécurité sociale', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '658', 'name': 'Charges diverses de gestion courante', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '66', 'name': 'Charges financières', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '661', 'name': 'Charges d\'intérêts', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '68', 'name': 'Dotations aux amortissements', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        {'code': '681', 'name': 'Dotations aux amortissements', 'account_type': 'CLASSE_6', 'account_nature': 'DEBIT'},
        
        # Classe 7 - Produits
        {'code': '70', 'name': 'Ventes', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '701', 'name': 'Ventes de produits finis', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '7011', 'name': 'Ventes pain', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '7012', 'name': 'Ventes viennoiseries', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '707', 'name': 'Ventes de marchandises', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '758', 'name': 'Produits divers de gestion courante', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '76', 'name': 'Produits financiers', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
        {'code': '761', 'name': 'Produits de participations', 'account_type': 'CLASSE_7', 'account_nature': 'CREDIT'},
    ]
    
    for acc_data in accounts_data:
        existing = Account.query.filter_by(code=acc_data['code']).first()
        if not existing:
            account = Account(
                code=acc_data['code'],
                name=acc_data['name'],
                account_type=AccountType[acc_data['account_type']],
                account_nature=AccountNature[acc_data['account_nature']]
            )
            db.session.add(account)
            print(f"✅ Compte ajouté: {acc_data['code']} - {acc_data['name']}")
        else:
            print(f"ℹ️  Compte existe déjà: {acc_data['code']}")
    
    # Journaux comptables
    journals_data = [
        {'name': 'Journal des ventes', 'journal_type': 'VENTES', 'code': 'VT'},
        {'name': 'Journal des achats', 'journal_type': 'ACHATS', 'code': 'AC'},
        {'name': 'Journal de caisse', 'journal_type': 'CAISSE', 'code': 'CA'},
        {'name': 'Banque', 'journal_type': 'BANQUE', 'code': 'BQ'},
        {'name': 'Opérations diverses', 'journal_type': 'OPERATIONS_DIVERSES', 'code': 'OD'},
    ]
    
    for jour_data in journals_data:
        existing = Journal.query.filter_by(code=jour_data['code']).first()
        if not existing:
            journal = Journal(
                name=jour_data['name'],
                code=jour_data['code'],
                journal_type=JournalType[jour_data['journal_type']]
            )
            db.session.add(journal)
            print(f"✅ Journal ajouté: {jour_data['code']} - {jour_data['name']}")
        else:
            print(f"ℹ️  Journal existe déjà: {jour_data['code']}")
    
    db.session.commit()
    print("📊 Plan comptable et journaux synchronisés")

def main():
    """Fonction principale de synchronisation"""
    app = create_app(os.getenv('FLASK_ENV') or 'production')
    
    with app.app_context():
        print("🔄 Synchronisation des données de base ERP Fée Maison")
        print("=" * 60)
        
        # Vérifier que les tables existent
        try:
            db.create_all()
            print("✅ Tables de base vérifiées")
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des tables: {e}")
            return
        
        # Synchroniser les données
        try:
            seed_units()
            seed_categories()
            seed_accounting()
            
            print("=" * 60)
            print("🎉 Synchronisation terminée avec succès !")
            print("\n📋 Données synchronisées:")
            print(f"   📏 Unités: {Unit.query.count()}")
            print(f"   🏷️ Catégories: {Category.query.count()}")
            print(f"   📊 Comptes: {Account.query.count()}")
            print(f"   📝 Journaux: {Journal.query.count()}")
            print(f"   📅 Exercices: {FiscalYear.query.count()}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la synchronisation: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main() 