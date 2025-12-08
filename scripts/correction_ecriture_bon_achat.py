#!/usr/bin/env python3
"""
Script de correction : Écriture comptable bon d'achat
Corrige l'écriture comptable pour correspondre au montant actuel du bon d'achat
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.purchases.models import Purchase
from app.accounting.models import JournalEntry, JournalEntryLine, Account
from decimal import Decimal

def correction_ecriture_bon_achat(purchase_id, dry_run=True):
    """
    Corrige l'écriture comptable d'un bon d'achat
    
    Args:
        purchase_id: ID du bon d'achat à corriger
        dry_run: Si True, affiche seulement ce qui sera fait sans modifier
    """
    
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("CORRECTION ÉCRITURE COMPTABLE - BON D'ACHAT")
        print("=" * 80)
        print()
        
        if dry_run:
            print("⚠️  MODE SIMULATION (dry-run) - Aucune modification ne sera effectuée")
            print()
        
        # 1. Récupérer le bon d'achat
        purchase = Purchase.query.get(purchase_id)
        if not purchase:
            print(f"❌ Bon d'achat ID {purchase_id} non trouvé !")
            return False
        
        print(f"📋 Bon d'achat : {purchase.reference} (ID: {purchase.id})")
        print(f"   Date paiement : {purchase.payment_date}")
        print(f"   Mode paiement : {purchase.payment_method}")
        print(f"   Statut payé : {purchase.is_paid}")
        print(f"   Montant actuel : {purchase.total_amount:,.2f} DA")
        print()
        
        if not purchase.is_paid:
            print("⚠️  Ce bon d'achat n'est pas marqué comme payé.")
            print("   Aucune écriture comptable à corriger.")
            return False
        
        # 2. Récupérer l'écriture comptable
        entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase.id}").first()
        if not entry:
            print("❌ Aucune écriture comptable trouvée pour ce bon d'achat.")
            print(f"   Référence attendue : ACH-{purchase.id}")
            return False
        
        print(f"📝 Écriture comptable trouvée :")
        print(f"   ID : {entry.id}")
        print(f"   Référence : {entry.reference}")
        print(f"   Date : {entry.entry_date}")
        print()
        
        # 3. Récupérer les comptes
        bank_account = Account.query.filter_by(code='512').first()
        purchase_account = Account.query.filter_by(code='601').first()
        
        if not bank_account:
            print("❌ Compte banque (512) non trouvé !")
            return False
        if not purchase_account:
            print("❌ Compte achats (601) non trouvé !")
            return False
        
        # 4. Récupérer les lignes d'écriture
        bank_line = JournalEntryLine.query.filter_by(
            entry_id=entry.id,
            account_id=bank_account.id
        ).first()
        
        purchase_line = JournalEntryLine.query.filter_by(
            entry_id=entry.id,
            account_id=purchase_account.id
        ).first()
        
        if not bank_line:
            print("❌ Ligne banque (512) non trouvée dans l'écriture !")
            return False
        if not purchase_line:
            print("❌ Ligne achats (601) non trouvée dans l'écriture !")
            return False
        
        # 5. Afficher les montants actuels
        montant_actuel_bon = float(purchase.total_amount)
        montant_ecriture_banque = float(bank_line.credit_amount)
        montant_ecriture_achat = float(purchase_line.debit_amount)
        
        print("💰 MONTANTS ACTUELS :")
        print(f"   Bon d'achat : {montant_actuel_bon:,.2f} DA")
        print(f"   Écriture banque (crédit) : {montant_ecriture_banque:,.2f} DA")
        print(f"   Écriture achats (débit) : {montant_ecriture_achat:,.2f} DA")
        print()
        
        ecart_banque = montant_ecriture_banque - montant_actuel_bon
        ecart_achat = montant_ecriture_achat - montant_actuel_bon
        
        print("📊 ÉCARTS :")
        print(f"   Banque : {ecart_banque:,.2f} DA")
        print(f"   Achats : {ecart_achat:,.2f} DA")
        print()
        
        # 6. Vérifier si correction nécessaire
        if abs(ecart_banque) < 0.01 and abs(ecart_achat) < 0.01:
            print("✅ Les montants sont déjà corrects ! Aucune correction nécessaire.")
            return True
        
        # 7. Afficher ce qui sera fait
        print("🔧 CORRECTION À EFFECTUER :")
        print(f"   Ligne banque (ID: {bank_line.id}) :")
        print(f"      Ancien crédit : {montant_ecriture_banque:,.2f} DA")
        print(f"      Nouveau crédit : {montant_actuel_bon:,.2f} DA")
        print(f"   Ligne achats (ID: {purchase_line.id}) :")
        print(f"      Ancien débit : {montant_ecriture_achat:,.2f} DA")
        print(f"      Nouveau débit : {montant_actuel_bon:,.2f} DA")
        print()
        
        # 8. Appliquer la correction
        if not dry_run:
            try:
                bank_line.credit_amount = Decimal(str(montant_actuel_bon))
                purchase_line.debit_amount = Decimal(str(montant_actuel_bon))
                
                db.session.commit()
                
                print("✅ Correction appliquée avec succès !")
                print()
                print("📊 VÉRIFICATION APRÈS CORRECTION :")
                print(f"   Ligne banque crédit : {float(bank_line.credit_amount):,.2f} DA")
                print(f"   Ligne achats débit : {float(purchase_line.debit_amount):,.2f} DA")
                print()
                
                # Recalculer le solde de la banque
                from sqlalchemy import func
                total_debits = db.session.query(func.sum(JournalEntryLine.debit_amount))\
                    .join(JournalEntry)\
                    .filter(JournalEntryLine.account_id == bank_account.id)\
                    .scalar() or 0
                
                total_credits = db.session.query(func.sum(JournalEntryLine.credit_amount))\
                    .join(JournalEntry)\
                    .filter(JournalEntryLine.account_id == bank_account.id)\
                    .scalar() or 0
                
                solde_banque = float(total_debits) - float(total_credits)
                print(f"💰 NOUVEAU SOLDE BANQUE : {solde_banque:,.2f} DA")
                print()
                
                return True
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERREUR lors de la correction : {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("⚠️  MODE SIMULATION - Aucune modification effectuée")
            print("   Pour appliquer la correction, relancer avec dry_run=False")
            print()
            return True
        
        print("=" * 80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Corriger une écriture comptable de bon d\'achat')
    parser.add_argument('purchase_id', type=int, help='ID du bon d\'achat à corriger')
    parser.add_argument('--apply', action='store_true', help='Appliquer la correction (par défaut: simulation)')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    if not dry_run:
        print("⚠️  ATTENTION : Vous allez modifier la base de données !")
        print("   Assurez-vous d'avoir fait une sauvegarde.")
        print()
        confirmation = input("Confirmer la correction ? (oui/non) : ")
        if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Correction annulée.")
            sys.exit(0)
        print()
    
    correction_ecriture_bon_achat(args.purchase_id, dry_run=dry_run)

