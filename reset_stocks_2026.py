from app import create_app
from extensions import db
from models import Product
from datetime import datetime

app = create_app()

with app.app_context():
    print("🚀 Démarrage du Reset Stock 2026...")
    
    # Récupérer tous les produits
    products = Product.query.all()
    count = len(products)
    print(f"📦 {count} produits trouvés.")
    
    try:
        updated_count = 0
        for p in products:
            # 1. Reset Quantités
            p.stock_comptoir = 0.0
            p.stock_ingredients_local = 0.0
            p.stock_ingredients_magasin = 0.0
            p.stock_consommables = 0.0
            
            # Reset ancien champ si utilisé
            if hasattr(p, 'quantity_in_stock'):
                p.quantity_in_stock = 0.0

            # 2. Reset Valeurs (Comptabilité)
            p.valeur_stock_comptoir = 0.0
            p.valeur_stock_ingredients_local = 0.0
            p.valeur_stock_ingredients_magasin = 0.0
            p.valeur_stock_consommables = 0.0
            p.total_stock_value = 0.0

            # 3. Reset Déficits (Comptabilité)
            p.deficit_stock_comptoir = 0.0
            p.deficit_stock_ingredients_local = 0.0
            p.deficit_stock_ingredients_magasin = 0.0
            p.deficit_stock_consommables = 0.0
            p.value_deficit_total = 0.0
            
            # 4. Timestamp
            p.last_stock_update = datetime.utcnow()
            updated_count += 1

        db.session.commit()
        print(f"✅ SUCCÈS : {updated_count} produits mis à jour (stocks, valeurs et déficits remis à 0).")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERREUR : {e}")
        print("Aucune modification n'a été appliquée.")
