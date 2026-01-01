from app import create_app, db
from app.accounting.models import JournalEntry, JournalEntryLine, Account
from sqlalchemy import or_

app = create_app()

with app.app_context():
    print("🔍 Recherche de la transaction de ~860,245.24 DZD...")
    
    # Le user parle de 860,245 DZD
    target_amount = 860245
    # On cherche large autour de ce montant
    
    lines = JournalEntryLine.query.filter(
         JournalEntryLine.debit_amount > 860000
    ).all()
    
    found = False
    for line in lines:
        entry = line.entry
        account = line.account
        # On ne s'intéresse qu'aux comptes de classe 6 (Charges) car c'est ça qui pollue le dashboard
        if account.code.startswith('6'):
            found = True
            print(f"--- 🚨 COUPABLE TROUVÉ (ID: {entry.id}) ---")
            print(f"Date: {entry.entry_date}")
            print(f"Description: {entry.description}")
            print(f"Compte de Charge: {account.code} - {account.name}")
            print(f"Montant Débit: {line.debit_amount}")
            print(f"Ligne ID: {line.id}")
            print("---------------------------------")

    if not found:
        print("❌ Aucune charge > 860,000 trouvée. Vérifions toutes les transactions...")
        all_lines = JournalEntryLine.query.filter(JournalEntryLine.debit_amount > 860000).all()
        for line in all_lines:
            print(f"Compte: {line.account.code} | Montant: {line.debit_amount} | Desc: {line.entry.description}")
