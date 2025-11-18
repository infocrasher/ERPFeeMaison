#!/usr/bin/env python3
"""
Script pour initialiser les valeurs de stock pour tous les emplacements
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product

def init_valeur_stock():
    """Initialise les valeurs de stock pour tous les produits"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🔧 INITIALISATION DES VALEURS DE STOCK")
        print("=" * 60)
        
        products = Product.query.all()
        updated = 0
        
        for product in products:
            cost_price = float(product.cost_price or 0)
            
            updated_any = False
            
            # Stock magasin
            stock_magasin = float(product.stock_ingredients_magasin or 0)
            if stock_magasin > 0:
                expected_value = stock_magasin * cost_price
                current_value = float(product.valeur_stock_ingredients_magasin or 0)
                if current_value == 0 or abs(current_value - expected_value) > 1:
                    product.valeur_stock_ingredients_magasin = expected_value
                    updated_any = True
                    print(f"✅ {product.name} (Magasin): {stock_magasin:.2f} × {cost_price:.2f} = {expected_value:.2f} DA")
            
            # Stock local
            stock_local = float(product.stock_ingredients_local or 0)
            if stock_local > 0:
                expected_value = stock_local * cost_price
                current_value = float(product.valeur_stock_ingredients_local or 0)
                if current_value == 0 or abs(current_value - expected_value) > 1:
                    product.valeur_stock_ingredients_local = expected_value
                    updated_any = True
                    print(f"✅ {product.name} (Local): {stock_local:.2f} × {cost_price:.2f} = {expected_value:.2f} DA")
            
            # Stock comptoir
            stock_comptoir = float(product.stock_comptoir or 0)
            if stock_comptoir > 0:
                expected_value = stock_comptoir * cost_price
                current_value = float(product.valeur_stock_comptoir or 0)
                if current_value == 0 or abs(current_value - expected_value) > 1:
                    product.valeur_stock_comptoir = expected_value
                    updated_any = True
                    print(f"✅ {product.name} (Comptoir): {stock_comptoir:.2f} × {cost_price:.2f} = {expected_value:.2f} DA")
            
            # Stock consommables
            stock_consommables = float(product.stock_consommables or 0)
            if stock_consommables > 0:
                expected_value = stock_consommables * cost_price
                current_value = float(product.valeur_stock_consommables or 0)
                if current_value == 0 or abs(current_value - expected_value) > 1:
                    product.valeur_stock_consommables = expected_value
                    updated_any = True
                    print(f"✅ {product.name} (Consommables): {stock_consommables:.2f} × {cost_price:.2f} = {expected_value:.2f} DA")
            
            if updated_any:
                updated += 1
        
        if updated > 0:
            db.session.commit()
            print(f"\n✅ {updated} produits mis à jour")
        else:
            print("\n✅ Toutes les valeurs sont déjà à jour")
        
        print("\n✅ Initialisation terminée")

if __name__ == "__main__":
    init_valeur_stock()

