#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement de la valorisation
Teste la fonction update_stock_by_location
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def test_valorisation():
    """Teste la valorisation lors de l'ajout de stock"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("TEST DE LA VALORISATION")
        print("=" * 80)
        print()
        
        # Trouver un produit test
        test_product = Product.query.filter(
            Product.name.ilike('%margarine%')
        ).first()
        
        if not test_product:
            print("❌ Produit test non trouvé")
            return
        
        print(f"✅ Produit test: {test_product.name} (ID: {test_product.id})")
        print(f"   PMP actuel: {test_product.cost_price} DA")
        print()
        
        print("ÉTAT INITIAL:")
        print(f"  Stock magasin: {test_product.stock_ingredients_magasin}")
        print(f"  Valeur magasin: {test_product.valeur_stock_ingredients_magasin}")
        print(f"  Stock local: {test_product.stock_ingredients_local}")
        print(f"  Valeur local: {test_product.valeur_stock_ingredients_local}")
        print(f"  Total stock value: {test_product.total_stock_value}")
        print()
        
        # Test 1: Ajouter 1000g au magasin avec un prix de 0.5 DA/g
        print("TEST 1: Ajout de 1000g au magasin à 0.5 DA/g")
        print("-" * 80)
        
        stock_before = test_product.stock_ingredients_magasin
        value_before = test_product.valeur_stock_ingredients_magasin
        total_value_before = test_product.total_stock_value
        
        test_product.update_stock_by_location(
            'stock_ingredients_magasin',
            1000.0,
            unit_cost_override=0.5
        )
        
        print(f"  Stock magasin AVANT: {stock_before}")
        print(f"  Stock magasin APRÈS: {test_product.stock_ingredients_magasin}")
        print(f"  Valeur magasin AVANT: {value_before}")
        print(f"  Valeur magasin APRÈS: {test_product.valeur_stock_ingredients_magasin}")
        print(f"  Total value AVANT: {total_value_before}")
        print(f"  Total value APRÈS: {test_product.total_stock_value}")
        print()
        
        # Vérification
        expected_value_increase = 1000.0 * 0.5
        actual_value_increase = float(test_product.valeur_stock_ingredients_magasin or 0) - float(value_before or 0)
        
        print("VÉRIFICATION:")
        print(f"  Augmentation attendue: {expected_value_increase:.2f} DA")
        print(f"  Augmentation réelle: {actual_value_increase:.2f} DA")
        
        if abs(expected_value_increase - actual_value_increase) < 0.01:
            print("  ✅ La valorisation fonctionne correctement!")
        else:
            print("  ❌ Problème de valorisation détecté!")
        
        print()
        print("⚠️  Note: Les modifications ne seront PAS sauvegardées (rollback)")
        db.session.rollback()
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    test_valorisation()

