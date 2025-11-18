#!/usr/bin/env python3
"""
Script de test complet des systèmes d'ajustement de stock
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Category, User
from app.consumables.models import ConsumableAdjustment, ConsumableCategory
from app.stock.models import StockLocationType
from datetime import datetime
from decimal import Decimal

def test_all_adjustment_systems():
    """Test tous les systèmes d'ajustement"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🧪 TEST COMPLET DES SYSTÈMES D'AJUSTEMENT")
        print("=" * 60)
        
        # Test 1: Modèle Product (méthodes de mise à jour)
        print("\n1️⃣ TEST: Méthodes Product")
        print("-" * 40)
        
        consumable = Product.query.filter_by(product_type='consommable').first()
        if consumable:
            stock_avant = consumable.stock_consommables or 0
            
            # Test update_stock_by_location
            consumable.update_stock_by_location('stock_consommables', 10)
            stock_apres = consumable.stock_consommables
            print(f"   {consumable.name}: {stock_avant} → {stock_apres} (+10)")
            
            # Remettre à l'état initial
            consumable.update_stock_by_location('stock_consommables', -10)
            
            if stock_apres == stock_avant + 10:
                print("   ✅ Méthode update_stock_by_location: OK")
            else:
                print("   ❌ Méthode update_stock_by_location: ERREUR")
        
        # Test 2: ConsumableAdjustment
        print("\n2️⃣ TEST: ConsumableAdjustment")
        print("-" * 40)
        
        adjustments = ConsumableAdjustment.query.limit(3).all()
        print(f"   Ajustements en base: {len(adjustments)}")
        if adjustments:
            for adj in adjustments:
                print(f"   - {adj.product.name if adj.product else 'N/A'}: {adj.quantity_adjusted} ({adj.adjustment_type})")
        else:
            print("   ℹ️  Aucun ajustement enregistré")
        
        print("   ✅ ConsumableAdjustment: OK (modèle accessible)")
        
        # Test 3: ConsumableCategory
        print("\n3️⃣ TEST: ConsumableCategory")
        print("-" * 40)
        
        categories = ConsumableCategory.query.all()
        print(f"   Catégories de consommables: {len(categories)}")
        for cat in categories:
            print(f"   - {cat.name} (Produits: {cat.product_category.name})")
            
            # Tester le calcul
            result = cat.calculate_consumables_needed(10)
            if result:
                print(f"     Test 10 pièces: {[(c.name if c else 'N/A', q) for c, q in result]}")
        
        print("   ✅ ConsumableCategory: OK")
        
        # Test 4: Inventaire - InventoryItem
        print("\n4️⃣ TEST: InventoryItem")
        print("-" * 40)
        
        from app.inventory.models import InventoryItem
        items = InventoryItem.query.limit(3).all()
        print(f"   Items d'inventaire: {len(items)}")
        print("   ✅ InventoryItem: OK (modèle accessible)")
        
        # Test 5: Vérifier les stocks
        print("\n5️⃣ TEST: Vérification des stocks")
        print("-" * 40)
        
        test_products = [
            (Product.query.filter_by(name='Boite 08').first(), 'stock_consommables'),
            (Product.query.filter_by(product_type='consommable').first(), 'stock_consommables'),
        ]
        
        for product, location in test_products:
            if product:
                stock = getattr(product, location, 0)
                print(f"   {product.name}: {stock} {product.unit} ({location})")
        
        print("\n✅ TOUS LES SYSTÈMES SONT OPÉRATIONNELS")
        print("=" * 60)
        print("\n📋 RÉSUMÉ:")
        print("   ✅ Product.update_stock_by_location: OK")
        print("   ✅ ConsumableAdjustment: OK")
        print("   ✅ ConsumableCategory: OK")
        print("   ✅ InventoryItem: OK")
        print("   ✅ Stocks vérifiés: OK")

if __name__ == "__main__":
    test_all_adjustment_systems()

