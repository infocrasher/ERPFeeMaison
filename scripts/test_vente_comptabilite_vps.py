#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour simuler une vente sur le VPS
et vérifier que l'intégration comptable fonctionne

Usage:
    python3 scripts/test_vente_comptabilite_vps.py
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Product, Order, OrderItem, User
from app.sales.models import CashRegisterSession, CashMovement
from app.accounting.models import JournalEntry, JournalEntryLine, Account, Journal
from app.accounting.services import AccountingIntegrationService
from decimal import Decimal
from datetime import datetime, timezone
from flask_login import login_user

def test_vente_comptabilite():
    """Test d'une vente avec vérification de l'intégration comptable"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("TEST VENTE COMPTABILITÉ - VPS")
        print("=" * 70)
        print()
        
        # Récupérer un utilisateur pour le contexte Flask-Login
        test_user = User.query.filter_by(role='admin').first()
        if not test_user:
            test_user = User.query.first()
        
        if test_user:
            print(f"👤 Utilisateur de test: {test_user.username} (ID: {test_user.id})")
        else:
            print("⚠️  Aucun utilisateur trouvé, utilisation de l'ID 1 par défaut")
        print()
        
        # 1. Vérifier les prérequis
        print("📋 1. VÉRIFICATION DES PRÉREQUIS")
        print("-" * 70)
        
        # Vérifier compte caisse
        compte_caisse = Account.query.filter_by(code='530', is_active=True).first()
        if not compte_caisse:
            print("❌ Compte Caisse (530) non trouvé ou inactif")
            return False
        print(f"✅ Compte Caisse (530) trouvé: {compte_caisse.name}")
        
        # Vérifier compte ventes
        compte_ventes = Account.query.filter_by(code='701', is_active=True).first()
        if not compte_ventes:
            print("❌ Compte Ventes (701) non trouvé ou inactif")
            return False
        print(f"✅ Compte Ventes (701) trouvé: {compte_ventes.name}")
        
        # Vérifier journal ventes
        journal_ventes = Journal.query.filter_by(code='VT', is_active=True).first()
        if not journal_ventes:
            print("❌ Journal Ventes (VT) non trouvé ou inactif")
            return False
        print(f"✅ Journal Ventes (VT) trouvé: {journal_ventes.name}")
        
        # Vérifier session de caisse ouverte
        session = CashRegisterSession.query.filter_by(is_open=True).first()
        if not session:
            print("⚠️  Aucune session de caisse ouverte")
            print("   → Création d'une session de test...")
            from datetime import timezone
            session = CashRegisterSession(
                opened_by_id=1,
                initial_amount=1000.0,
                is_open=True,
                opened_at=datetime.now(timezone.utc)
            )
            db.session.add(session)
            db.session.flush()
            print(f"✅ Session de caisse créée (ID: {session.id})")
        else:
            print(f"✅ Session de caisse ouverte trouvée (ID: {session.id})")
        
        print()
        
        # 2. Compter les écritures avant
        print("📊 2. ÉTAT AVANT LA VENTE")
        print("-" * 70)
        
        nb_ecritures_avant = JournalEntry.query.count()
        nb_lignes_avant = JournalEntryLine.query.count()
        solde_caisse_avant = compte_caisse.balance
        solde_ventes_avant = compte_ventes.balance
        
        print(f"   Écritures comptables: {nb_ecritures_avant}")
        print(f"   Lignes d'écriture: {nb_lignes_avant}")
        print(f"   Solde Caisse (530): {solde_caisse_avant:.2f} DA")
        print(f"   Solde Ventes (701): {solde_ventes_avant:.2f} DA")
        print()
        
        # 3. Trouver un produit fini pour la vente
        print("🛒 3. SÉLECTION D'UN PRODUIT")
        print("-" * 70)
        
        produit = Product.query.filter_by(product_type='finished').first()
        if not produit:
            print("❌ Aucun produit fini trouvé dans la base")
            return False
        
        print(f"✅ Produit sélectionné: {produit.name}")
        print(f"   Prix: {produit.price or 0:.2f} DA")
        print(f"   Stock comptoir: {produit.stock_comptoir or 0}")
        print()
        
        # 4. Simuler la vente
        print("💰 4. SIMULATION DE LA VENTE")
        print("-" * 70)
        
        montant_vente = float(produit.price or 1000.0)
        quantite = 1
        
        print(f"   Montant: {montant_vente:.2f} DA")
        print(f"   Quantité: {quantite}")
        print(f"   Mode de paiement: cash")
        print()
        
        # 5. Créer l'écriture comptable
        print("📝 5. CRÉATION DE L'ÉCRITURE COMPTABLE")
        print("-" * 70)
        
        try:
            # Créer un contexte de requête pour que current_user fonctionne
            with app.test_request_context():
                if test_user:
                    login_user(test_user)
                
                entry = AccountingIntegrationService.create_sale_entry(
                    order_id=999,  # ID de test
                    sale_amount=montant_vente,
                    payment_method='cash',
                    description=f'Test vente comptabilité - Produit: {produit.name}'
                )
            print(f"✅ Écriture comptable créée avec succès!")
            print(f"   ID: {entry.id}")
            print(f"   Référence: {entry.reference}")
            print(f"   Date: {entry.entry_date}")
            print(f"   Description: {entry.description}")
            print(f"   Validée: {entry.is_validated}")
            print()
            
            # Vérifier les lignes
            lignes = JournalEntryLine.query.filter_by(entry_id=entry.id).all()
            print(f"   Lignes d'écriture: {len(lignes)}")
            for ligne in lignes:
                compte = Account.query.get(ligne.account_id)
                if ligne.debit_amount > 0:
                    print(f"      Débit {compte.code} ({compte.name}): {ligne.debit_amount:.2f} DA")
                if ligne.credit_amount > 0:
                    print(f"      Crédit {compte.code} ({compte.name}): {ligne.credit_amount:.2f} DA")
            print()
            
        except Exception as e:
            print(f"❌ ERREUR lors de la création de l'écriture comptable:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Vérifier l'état après
        print("📊 6. ÉTAT APRÈS LA VENTE")
        print("-" * 70)
        
        nb_ecritures_apres = JournalEntry.query.count()
        nb_lignes_apres = JournalEntryLine.query.count()
        solde_caisse_apres = compte_caisse.balance
        solde_ventes_apres = compte_ventes.balance
        
        print(f"   Écritures comptables: {nb_ecritures_apres} (+{nb_ecritures_apres - nb_ecritures_avant})")
        print(f"   Lignes d'écriture: {nb_lignes_apres} (+{nb_lignes_apres - nb_lignes_avant})")
        print(f"   Solde Caisse (530): {solde_caisse_apres:.2f} DA (+{solde_caisse_apres - solde_caisse_avant:.2f} DA)")
        print(f"   Solde Ventes (701): {solde_ventes_apres:.2f} DA (+{solde_ventes_apres - solde_ventes_avant:.2f} DA)")
        print()
        
        # 7. Vérifications finales
        print("✅ 7. VÉRIFICATIONS FINALES")
        print("-" * 70)
        
        success = True
        
        # Vérifier que l'écriture a été créée
        if nb_ecritures_apres <= nb_ecritures_avant:
            print("❌ Aucune nouvelle écriture créée")
            success = False
        else:
            print("✅ Nouvelle écriture créée")
        
        # Vérifier que les lignes ont été créées
        if nb_lignes_apres <= nb_lignes_avant:
            print("❌ Aucune nouvelle ligne d'écriture créée")
            success = False
        else:
            print("✅ Nouvelles lignes d'écriture créées")
        
        # Vérifier le solde caisse
        if abs(solde_caisse_apres - solde_caisse_avant - montant_vente) > 0.01:
            print(f"⚠️  Solde caisse incorrect: attendu +{montant_vente:.2f}, obtenu +{solde_caisse_apres - solde_caisse_avant:.2f}")
            success = False
        else:
            print("✅ Solde caisse correct")
        
        # Vérifier le solde ventes
        if abs(solde_ventes_apres - solde_ventes_avant - montant_vente) > 0.01:
            print(f"⚠️  Solde ventes incorrect: attendu +{montant_vente:.2f}, obtenu +{solde_ventes_apres - solde_ventes_avant:.2f}")
            success = False
        else:
            print("✅ Solde ventes correct")
        
        # Vérifier l'équilibre de l'écriture
        total_debit = sum(l.debit_amount for l in lignes)
        total_credit = sum(l.credit_amount for l in lignes)
        if abs(total_debit - total_credit) > 0.01:
            print(f"⚠️  Écriture non équilibrée: Débit={total_debit:.2f}, Crédit={total_credit:.2f}")
            success = False
        else:
            print("✅ Écriture équilibrée")
        
        print()
        print("=" * 70)
        if success:
            print("✅ TEST RÉUSSI - L'intégration comptable fonctionne correctement!")
        else:
            print("❌ TEST ÉCHOUÉ - Des problèmes ont été détectés")
        print("=" * 70)
        
        return success

if __name__ == '__main__':
    try:
        success = test_vente_comptabilite()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

