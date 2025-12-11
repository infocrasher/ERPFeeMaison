from app import create_app
from models import db, Supplier
from app.purchases.models import Purchase

app = create_app()

with app.app_context():
    supplier_id = 12
    supplier = db.session.get(Supplier, supplier_id)
    
    if not supplier:
        print(f"Supplier ID {supplier_id} not found!")
    else:
        print(f"Supplier: {supplier.company_name} (ID: {supplier.id})")
        
        # Check linked purchases
        linked_count = Purchase.query.filter_by(supplier_id=supplier.id).count()
        print(f"Linked purchases (by ID): {linked_count}")
        
        # Check unlinked purchases by name
        unlinked_count = Purchase.query.filter(
            Purchase.supplier_id == None,
            Purchase.supplier_name == supplier.company_name
        ).count()
        print(f"Unlinked purchases (by Name '{supplier.company_name}'): {unlinked_count}")
        
        # Check all by name regardless of ID
        all_by_name_count = Purchase.query.filter(
            Purchase.supplier_name == supplier.company_name
        ).count()
        print(f"All purchases with name '{supplier.company_name}': {all_by_name_count}")
