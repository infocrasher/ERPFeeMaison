from app import create_app
from extensions import db
from app.purchases.models import Purchase
from app.accounting.models import JournalEntryLine
from sqlalchemy import desc

app = create_app()

with app.app_context():
    print("--- Searching for large Purchases ---")
    # Look for purchases > 1,000,000
    large_purchases = Purchase.query.filter(Purchase.total_amount > 1000000).order_by(desc(Purchase.total_amount)).all()
    
    if large_purchases:
        for p in large_purchases:
            print(f"Purchase ID: {p.id}, Ref: {p.reference}, Supplier: {p.supplier_name}, Total: {p.total_amount}, Paid: {p.is_paid}")
    else:
        print("No purchases > 1,000,000 found.")

    print("\n--- Searching for large Journal Entries ---")
    # Look for credit/debit > 1,000,000
    large_entries = JournalEntryLine.query.filter(
        (JournalEntryLine.debit_amount > 1000000) | (JournalEntryLine.credit_amount > 1000000)
    ).all()
    
    if large_entries:
        for line in large_entries:
            print(f"Entry ID: {line.entry_id}, Account: {line.account_id}, Debit: {line.debit_amount}, Credit: {line.credit_amount}, Desc: {line.description}")
    else:
        print("No journal entries > 1,000,000 found.")
