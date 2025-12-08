#!/usr/bin/env python3
"""
Script de diagnostic : Problème banque -2 000 000 DA
Identifie les bons d'achat payés par banque avec incohérence entre écriture comptable et montant actuel
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.purchases.models import Purchase, PurchaseStatus
from app.accounting.models import JournalEntry, JournalEntryLine, Account
from decimal import Decimal
from datetime import datetime, timedelta

def diagnostic_banque_bon_achat():
    """Diagnostic complet des incohérences entre bons d'achat et écritures comptables"""
    
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("DIAGNOSTIC BANQUE - BONS D'ACHAT")
        print("=" * 80)
        print()
        
        # 1. Vérifier le solde actuel de la banque
        print("1️⃣  SOLDE ACTUEL DE LA BANQUE")
        print("-" * 80)
        bank_account = Account.query.filter_by(code='512').first()
        if not bank_account:
            print("❌ Compte banque (512) non trouvé !")
            return
        
        # Calculer le solde
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
        print(f"   Solde banque (512) : {solde_banque:,.2f} DA")
        print(f"   Total débits  : {total_debits:,.2f} DA")
        print(f"   Total crédits : {total_credits:,.2f} DA")
        print()
        
        # 2. Trouver tous les bons d'achat payés par banque
        print("2️⃣  BONS D'ACHAT PAYÉS PAR BANQUE")
        print("-" * 80)
        purchases_paid_bank = Purchase.query.filter(
            Purchase.is_paid == True,
            Purchase.payment_method == 'bank'
        ).order_by(Purchase.payment_date.desc()).all()
        
        print(f"   Total : {len(purchases_paid_bank)} bons d'achat payés par banque")
        print()
        
        # 3. Vérifier les incohérences
        print("3️⃣  VÉRIFICATION DES INCOHÉRENCES")
        print("-" * 80)
        
        incohérences = []
        for purchase in purchases_paid_bank:
            # Trouver l'écriture comptable
            entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase.id}").first()
            
            if not entry:
                print(f"   ⚠️  Bon {purchase.reference} (ID: {purchase.id}) : Aucune écriture comptable trouvée")
                continue
            
            # Trouver la ligne de crédit (banque)
            credit_line = JournalEntryLine.query.filter_by(
                entry_id=entry.id,
                account_id=bank_account.id
            ).first()
            
            if not credit_line:
                print(f"   ⚠️  Bon {purchase.reference} (ID: {purchase.id}) : Aucune ligne banque trouvée")
                continue
            
            montant_ecriture = float(credit_line.credit_amount)
            montant_bon = float(purchase.total_amount)
            ecart = montant_ecriture - montant_bon
            
            # Si écart significatif (> 1000 DA ou > 10%)
            if abs(ecart) > 1000 or (montant_ecriture > 0 and abs(ecart / montant_ecriture) > 0.1):
                incohérences.append({
                    'purchase': purchase,
                    'entry': entry,
                    'credit_line': credit_line,
                    'montant_ecriture': montant_ecriture,
                    'montant_bon': montant_bon,
                    'ecart': ecart
                })
        
        if not incohérences:
            print("   ✅ Aucune incohérence détectée")
        else:
            print(f"   ⚠️  {len(incohérences)} incohérence(s) détectée(s) :")
            print()
            
            for inc in incohérences:
                p = inc['purchase']
                e = inc['entry']
                print(f"   📋 Bon d'achat : {p.reference} (ID: {p.id})")
                print(f"      Date paiement : {p.payment_date}")
                print(f"      Montant bon actuel : {inc['montant_bon']:,.2f} DA")
                print(f"      Montant écriture comptable : {inc['montant_ecriture']:,.2f} DA")
                print(f"      ÉCART : {inc['ecart']:,.2f} DA")
                print(f"      Écriture ID : {e.id} (Réf: {e.reference})")
                print(f"      Date écriture : {e.entry_date}")
                print()
        
        # 4. Détails des bons récents (30 derniers jours)
        print("4️⃣  BONS D'ACHAT PAYÉS PAR BANQUE (30 DERNIERS JOURS)")
        print("-" * 80)
        
        date_limite = datetime.utcnow() - timedelta(days=30)
        recent_purchases = [p for p in purchases_paid_bank 
                           if p.payment_date and p.payment_date >= date_limite]
        
        if not recent_purchases:
            print("   Aucun bon d'achat payé par banque dans les 30 derniers jours")
        else:
            print(f"   {len(recent_purchases)} bon(s) trouvé(s) :")
            print()
            for p in recent_purchases[:10]:  # Limiter à 10
                entry = JournalEntry.query.filter_by(reference=f"ACH-{p.id}").first()
                montant_ecriture = 0
                if entry:
                    credit_line = JournalEntryLine.query.filter_by(
                        entry_id=entry.id,
                        account_id=bank_account.id
                    ).first()
                    if credit_line:
                        montant_ecriture = float(credit_line.credit_amount)
                
                ecart = montant_ecriture - float(p.total_amount)
                status = "⚠️  INCOHÉRENCE" if abs(ecart) > 1000 else "✅"
                
                print(f"   {status} {p.reference} (ID: {p.id})")
                print(f"      Date : {p.payment_date}")
                print(f"      Montant bon : {p.total_amount:,.2f} DA")
                print(f"      Montant écriture : {montant_ecriture:,.2f} DA")
                if abs(ecart) > 1000:
                    print(f"      ⚠️  ÉCART : {ecart:,.2f} DA")
                print()
        
        # 5. Résumé et recommandations
        print("=" * 80)
        print("RÉSUMÉ ET RECOMMANDATIONS")
        print("=" * 80)
        print()
        
        if incohérences:
            print(f"⚠️  {len(incohérences)} incohérence(s) détectée(s)")
            print()
            print("PROBLÈME IDENTIFIÉ :")
            print("   Les bons d'achat ont été modifiés après paiement, mais les")
            print("   écritures comptables n'ont pas été mises à jour.")
            print()
            print("SOLUTION PROPOSÉE :")
            print("   1. Identifier le bon d'achat problématique (celui avec le plus grand écart)")
            print("   2. Vérifier si le bon a bien été modifié après paiement")
            print("   3. Corriger l'écriture comptable pour correspondre au montant actuel du bon")
            print("   4. Vérifier le solde de la banque après correction")
            print()
            print("⚠️  ATTENTION : Ne pas modifier sans validation !")
        else:
            print("✅ Aucune incohérence majeure détectée")
            print()
            print("Si le solde de la banque est toujours incorrect, vérifier :")
            print("   - Les écritures manuelles")
            print("   - Les autres types de transactions (salaires, dépenses, etc.)")
            print("   - Les écritures d'ouverture de compte")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    diagnostic_banque_bon_achat()

