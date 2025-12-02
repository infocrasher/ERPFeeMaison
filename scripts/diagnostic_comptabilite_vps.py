#!/usr/bin/env python3
"""
Script de diagnostic complet de la comptabilité sur le VPS
Vérifie tous les problèmes identifiés dans l'analyse
"""

import sys
import os
from decimal import Decimal

# Ajouter le chemin de l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from app.accounting.models import Account, Journal, JournalEntry, JournalEntryLine, JournalType
from app.sales.models import CashMovement, CashRegisterSession
from sqlalchemy import func, text
from datetime import date, datetime

def print_section(title):
    """Afficher une section"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_problem(problem_num, description, status="❌"):
    """Afficher un problème"""
    print(f"\n{status} PROBLÈME {problem_num}: {description}")

def print_ok(message):
    """Afficher un OK"""
    print(f"✅ {message}")

def print_warning(message):
    """Afficher un avertissement"""
    print(f"⚠️  {message}")

def check_accounts_and_journals():
    """Vérifier l'existence des comptes et journaux nécessaires"""
    print_section("1. VÉRIFICATION DES COMPTES ET JOURNAUX")
    
    # Comptes nécessaires
    required_accounts = {
        '530': 'Caisse',
        '512': 'Banque',
        '701': 'Ventes de marchandises',
        '601': 'Achats de marchandises',
        '411': 'Clients',
        '401': 'Fournisseurs',
        '758': 'Produits divers',
        '658': 'Charges diverses',
        '641': 'Rémunérations du personnel',
        '421': 'Personnel - Rémunérations dues',
        '300': 'Stocks de marchandises',
        '101': 'Capital'
    }
    
    missing_accounts = []
    inactive_accounts = []
    
    for code, name in required_accounts.items():
        account = Account.query.filter_by(code=code).first()
        if not account:
            missing_accounts.append((code, name))
            print_problem(f"Compte {code}", f"Compte {code} ({name}) n'existe pas")
        elif not account.is_active:
            inactive_accounts.append((code, name))
            print_warning(f"Compte {code} ({name}) existe mais est inactif")
        else:
            print_ok(f"Compte {code} ({name}) existe et est actif")
    
    # Journaux nécessaires
    required_journals = {
        'VT': ('VENTES', JournalType.VENTES),
        'AC': ('ACHATS', JournalType.ACHATS),
        'CA': ('CAISSE', JournalType.CAISSE),
        'BQ': ('BANQUE', JournalType.BANQUE),
        'OD': ('OPERATIONS_DIVERSES', JournalType.OPERATIONS_DIVERSES)
    }
    
    missing_journals = []
    
    for code, (name, journal_type) in required_journals.items():
        journal = Journal.query.filter_by(code=code).first()
        if not journal:
            missing_journals.append((code, name))
            print_problem(f"Journal {code}", f"Journal {code} ({name}) n'existe pas")
        elif journal.journal_type != journal_type:
            print_warning(f"Journal {code} existe mais avec un type différent ({journal.journal_type.value} au lieu de {journal_type.value})")
        else:
            print_ok(f"Journal {code} ({name}) existe et est correct")
    
    return {
        'missing_accounts': missing_accounts,
        'inactive_accounts': inactive_accounts,
        'missing_journals': missing_journals
    }

def check_bank_entries():
    """Vérifier les écritures pour le compte banque"""
    print_section("2. VÉRIFICATION DES ÉCRITURES BANQUE (512)")
    
    bank_account = Account.query.filter_by(code='512').first()
    if not bank_account:
        print_problem("Banque", "Compte 512 (Banque) n'existe pas")
        return None
    
    # Compter les écritures
    total_entries = db.session.query(func.count(JournalEntryLine.id))\
        .filter(JournalEntryLine.account_id == bank_account.id)\
        .scalar() or 0
    
    print(f"\n📊 Nombre total d'écritures pour le compte 512: {total_entries}")
    
    if total_entries == 0:
        print_problem("Banque", "Aucune écriture comptable pour le compte 512")
        print("   → Cela explique pourquoi l'état de banque affiche 0")
    else:
        print_ok(f"{total_entries} écriture(s) trouvée(s) pour le compte 512")
    
    # Calculer le solde
    total_debits = db.session.query(func.sum(JournalEntryLine.debit_amount))\
        .join(JournalEntry)\
        .filter(JournalEntryLine.account_id == bank_account.id)\
        .scalar() or Decimal('0')
    
    total_credits = db.session.query(func.sum(JournalEntryLine.credit_amount))\
        .join(JournalEntry)\
        .filter(JournalEntryLine.account_id == bank_account.id)\
        .scalar() or Decimal('0')
    
    balance = float(total_debits) - float(total_credits)
    
    print(f"\n💰 Solde banque calculé: {balance:,.2f} DA")
    print(f"   Débits totaux: {float(total_debits):,.2f} DA")
    print(f"   Crédits totaux: {float(total_credits):,.2f} DA")
    
    # Vérifier les cashouts
    cashout_entries = JournalEntry.query.filter(
        JournalEntry.reference.like('DEPOSIT-%')
    ).all()
    
    print(f"\n💸 Écritures de cashout trouvées: {len(cashout_entries)}")
    
    if len(cashout_entries) == 0:
        print_warning("Aucune écriture de cashout trouvée")
        print("   → Vérifier si des cashouts ont été effectués")
    else:
        print_ok(f"{len(cashout_entries)} écriture(s) de cashout trouvée(s)")
        for entry in cashout_entries[:5]:  # Afficher les 5 premières
            bank_line = JournalEntryLine.query.filter_by(
                entry_id=entry.id,
                account_id=bank_account.id
            ).first()
            if bank_line:
                print(f"   - {entry.entry_date}: {entry.reference} - {float(bank_line.debit_amount):,.2f} DA")
    
    # Vérifier le solde initial
    opening_entries = JournalEntry.query.filter(
        JournalEntry.reference.like('OUVERTURE-%')
    ).all()
    
    print(f"\n🏦 Écritures d'ouverture trouvées: {len(opening_entries)}")
    
    if len(opening_entries) == 0:
        print_warning("Aucune écriture d'ouverture trouvée")
        print("   → Le solde initial de la banque n'a peut-être pas été défini")
    else:
        for entry in opening_entries:
            bank_line = JournalEntryLine.query.filter_by(
                entry_id=entry.id,
                account_id=bank_account.id
            ).first()
            if bank_line:
                print(f"   - {entry.entry_date}: {entry.reference} - Solde initial: {float(bank_line.debit_amount):,.2f} DA")
    
    return {
        'total_entries': total_entries,
        'balance': balance,
        'cashout_entries': len(cashout_entries),
        'opening_entries': len(opening_entries)
    }

def check_cashouts():
    """Vérifier les cashouts et leurs écritures comptables"""
    print_section("3. VÉRIFICATION DES CASHOUTS")
    
    # Compter les cashouts dans cash_movements
    cashouts = CashMovement.query.filter(
        CashMovement.reason.like('%Dépôt en banque%')
    ).all()
    
    print(f"\n💵 Cashouts trouvés dans cash_movements: {len(cashouts)}")
    
    if len(cashouts) == 0:
        print_warning("Aucun cashout trouvé")
        return None
    
    # Vérifier les écritures comptables correspondantes
    cashouts_without_entry = []
    cashouts_with_entry = []
    
    for cashout in cashouts:
        # Chercher l'écriture comptable correspondante
        entry = JournalEntry.query.filter(
            JournalEntry.reference.like(f'DEPOSIT-{cashout.id}%')
        ).first()
        
        if not entry:
            cashouts_without_entry.append(cashout)
            print_problem(f"Cashout #{cashout.id}", 
                         f"Cashout du {cashout.created_at.strftime('%Y-%m-%d')} "
                         f"({cashout.amount:,.2f} DA) n'a pas d'écriture comptable")
        else:
            cashouts_with_entry.append((cashout, entry))
            print_ok(f"Cashout #{cashout.id} a une écriture comptable ({entry.reference})")
    
    print(f"\n📊 Résumé:")
    print(f"   - Cashouts avec écriture: {len(cashouts_with_entry)}")
    print(f"   - Cashouts SANS écriture: {len(cashouts_without_entry)}")
    
    if len(cashouts_without_entry) > 0:
        print_problem("Cashout", 
                     f"{len(cashouts_without_entry)} cashout(s) n'ont pas d'écriture comptable")
        print("   → Cela explique pourquoi la banque n'est pas incrémentée")
    
    return {
        'total_cashouts': len(cashouts),
        'with_entry': len(cashouts_with_entry),
        'without_entry': len(cashouts_without_entry)
    }

def check_double_accounting():
    """Vérifier la double comptabilisation des ventes"""
    print_section("4. VÉRIFICATION DOUBLE COMPTABILISATION")
    
    # Compter les ventes (écritures avec compte 701)
    sales_account = Account.query.filter_by(code='701').first()
    if not sales_account:
        print_problem("Ventes", "Compte 701 (Ventes) n'existe pas")
        return None
    
    sales_entries = db.session.query(JournalEntry)\
        .join(JournalEntryLine)\
        .filter(JournalEntryLine.account_id == sales_account.id)\
        .distinct()\
        .all()
    
    print(f"\n💰 Écritures de ventes (compte 701): {len(sales_entries)}")
    
    # Compter les mouvements de caisse liés aux ventes
    sales_cash_movements = CashMovement.query.filter(
        CashMovement.reason.like('%Vente%')
    ).all()
    
    print(f"💵 Mouvements de caisse 'Vente': {len(sales_cash_movements)}")
    
    # Vérifier les écritures sur "Produits divers" (758) pour les ventes
    products_account = Account.query.filter_by(code='758').first()
    if products_account:
        products_entries = db.session.query(JournalEntry)\
            .join(JournalEntryLine)\
            .filter(JournalEntryLine.account_id == products_account.id)\
            .filter(JournalEntry.description.like('%Vente%'))\
            .distinct()\
            .all()
        
        print(f"📦 Écritures 'Produits divers' avec 'Vente' dans description: {len(products_entries)}")
        
        if len(products_entries) > 0:
            print_problem("Double comptabilisation", 
                         f"{len(products_entries)} écriture(s) de ventes sur 'Produits divers' (758)")
            print("   → Ces ventes sont probablement comptabilisées deux fois")
            print("   → Une fois dans create_sale_entry() (compte 701)")
            print("   → Une fois dans create_cash_movement_entry() (compte 758)")
    
    return {
        'sales_entries': len(sales_entries),
        'sales_cash_movements': len(sales_cash_movements),
        'double_entries': len(products_entries) if products_account else 0
    }

def check_payroll_entries():
    """Vérifier les écritures de salaires"""
    print_section("5. VÉRIFICATION DES ÉCRITURES DE SALAIRES")
    
    # Chercher les écritures de salaires
    payroll_entries = JournalEntry.query.filter(
        JournalEntry.description.like('%Calcul salaire%')
    ).all()
    
    print(f"\n👥 Écritures de calcul de salaire: {len(payroll_entries)}")
    
    unbalanced_entries = []
    
    for entry in payroll_entries:
        total_debit = sum(line.debit_amount or 0 for line in entry.lines)
        total_credit = sum(line.credit_amount or 0 for line in entry.lines)
        
        difference = abs(float(total_debit) - float(total_credit))
        
        if difference > 0.01:  # Tolérance de 0.01
            unbalanced_entries.append((entry, difference))
            print_problem(f"Salaire {entry.reference}", 
                         f"Écriture non équilibrée: Débit={total_debit:.2f}, Crédit={total_credit:.2f}, Différence={difference:.2f}")
        else:
            print_ok(f"Écriture {entry.reference} est équilibrée")
    
    if len(unbalanced_entries) > 0:
        print_problem("Salaires", 
                     f"{len(unbalanced_entries)} écriture(s) de salaire non équilibrée(s)")
        print("   → Probablement dû à: Débit = salaire brut, Crédit = salaire net")
    
    return {
        'total_entries': len(payroll_entries),
        'unbalanced': len(unbalanced_entries)
    }

def check_entry_balance():
    """Vérifier l'équilibre de toutes les écritures"""
    print_section("6. VÉRIFICATION ÉQUILIBRE DES ÉCRITURES")
    
    # Requête SQL pour trouver les écritures non équilibrées
    unbalanced = db.session.query(
        JournalEntry.id,
        JournalEntry.entry_number,
        func.sum(JournalEntryLine.debit_amount).label('total_debit'),
        func.sum(JournalEntryLine.credit_amount).label('total_credit')
    ).join(JournalEntryLine)\
     .group_by(JournalEntry.id, JournalEntry.entry_number)\
     .having(func.abs(func.sum(JournalEntryLine.debit_amount) - func.sum(JournalEntryLine.credit_amount)) > 0.01)\
     .all()
    
    print(f"\n⚖️  Écritures non équilibrées: {len(unbalanced)}")
    
    if len(unbalanced) > 0:
        print_problem("Équilibre", f"{len(unbalanced)} écriture(s) non équilibrée(s)")
        for entry_id, entry_number, total_debit, total_credit in unbalanced[:10]:
            diff = abs(float(total_debit or 0) - float(total_credit or 0))
            print(f"   - {entry_number}: Débit={float(total_debit or 0):,.2f}, Crédit={float(total_credit or 0):,.2f}, Différence={diff:,.2f}")
    else:
        print_ok("Toutes les écritures sont équilibrées")
    
    return len(unbalanced)

def check_balance_performance():
    """Vérifier la performance de la propriété balance"""
    print_section("7. VÉRIFICATION PERFORMANCE PROPRIÉTÉ BALANCE")
    
    # Trouver les comptes avec beaucoup d'écritures
    accounts_with_many_entries = db.session.query(
        Account.id,
        Account.code,
        Account.name,
        func.count(JournalEntryLine.id).label('entry_count')
    ).join(JournalEntryLine)\
     .group_by(Account.id, Account.code, Account.name)\
     .having(func.count(JournalEntryLine.id) > 100)\
     .order_by(func.count(JournalEntryLine.id).desc())\
     .limit(10)\
     .all()
    
    print(f"\n🐌 Comptes avec plus de 100 écritures:")
    
    if len(accounts_with_many_entries) > 0:
        print_warning(f"{len(accounts_with_many_entries)} compte(s) avec beaucoup d'écritures")
        print("   → La propriété balance sera très lente sur ces comptes")
        for account_id, code, name, count in accounts_with_many_entries:
            print(f"   - {code} ({name}): {count} écritures")
    else:
        print_ok("Aucun compte avec plus de 100 écritures")
    
    return len(accounts_with_many_entries)

def check_reference_duplicates():
    """Vérifier les doublons de référence"""
    print_section("8. VÉRIFICATION DOUBLONS DE RÉFÉRENCE")
    
    duplicates = db.session.query(
        JournalEntry.entry_number,
        func.count(JournalEntry.id).label('count')
    ).group_by(JournalEntry.entry_number)\
     .having(func.count(JournalEntry.id) > 1)\
     .all()
    
    print(f"\n🔢 Références dupliquées: {len(duplicates)}")
    
    if len(duplicates) > 0:
        print_problem("Références", f"{len(duplicates)} référence(s) dupliquée(s)")
        for entry_number, count in duplicates:
            print(f"   - {entry_number}: {count} occurrence(s)")
    else:
        print_ok("Aucune référence dupliquée")
    
    return len(duplicates)

def main():
    """Fonction principale"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("  DIAGNOSTIC COMPLET DE LA COMPTABILITÉ - VPS")
        print("="*80)
        print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base de données: {db.engine.url}")
        
        results = {}
        
        # 1. Vérifier comptes et journaux
        results['accounts_journals'] = check_accounts_and_journals()
        
        # 2. Vérifier écritures banque
        results['bank'] = check_bank_entries()
        
        # 3. Vérifier cashouts
        results['cashouts'] = check_cashouts()
        
        # 4. Vérifier double comptabilisation
        results['double_accounting'] = check_double_accounting()
        
        # 5. Vérifier écritures salaires
        results['payroll'] = check_payroll_entries()
        
        # 6. Vérifier équilibre
        results['unbalanced'] = check_entry_balance()
        
        # 7. Vérifier performance
        results['performance'] = check_balance_performance()
        
        # 8. Vérifier doublons
        results['duplicates'] = check_reference_duplicates()
        
        # Résumé final
        print_section("RÉSUMÉ FINAL")
        
        problems_found = []
        
        if results['accounts_journals']['missing_accounts']:
            problems_found.append(f"❌ {len(results['accounts_journals']['missing_accounts'])} compte(s) manquant(s)")
        
        if results['accounts_journals']['missing_journals']:
            problems_found.append(f"❌ {len(results['accounts_journals']['missing_journals'])} journal(aux) manquant(s)")
        
        if results['bank'] and results['bank']['total_entries'] == 0:
            problems_found.append("❌ Aucune écriture pour le compte banque (512)")
        
        if results['cashouts'] and results['cashouts']['without_entry'] > 0:
            problems_found.append(f"❌ {results['cashouts']['without_entry']} cashout(s) sans écriture comptable")
        
        if results['double_accounting'] and results['double_accounting']['double_entries'] > 0:
            problems_found.append(f"❌ {results['double_accounting']['double_entries']} double(s) comptabilisation(s)")
        
        if results['payroll'] and results['payroll']['unbalanced'] > 0:
            problems_found.append(f"❌ {results['payroll']['unbalanced']} écriture(s) de salaire non équilibrée(s)")
        
        if results['unbalanced'] > 0:
            problems_found.append(f"❌ {results['unbalanced']} écriture(s) non équilibrée(s)")
        
        if results['duplicates'] > 0:
            problems_found.append(f"❌ {results['duplicates']} référence(s) dupliquée(s)")
        
        if len(problems_found) == 0:
            print("\n✅ Aucun problème critique détecté !")
        else:
            print(f"\n⚠️  {len(problems_found)} problème(s) détecté(s):")
            for problem in problems_found:
                print(f"   {problem}")
        
        print("\n" + "="*80)
        print("  FIN DU DIAGNOSTIC")
        print("="*80 + "\n")

if __name__ == '__main__':
    main()

