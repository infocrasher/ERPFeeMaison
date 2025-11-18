#!/usr/bin/env python3
"""
Test spécifique avec le produit "Gâteau Test 1" qui a des consommables liés
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Order, OrderItem
from app.consumables.models import ConsumableRecipe
from datetime import datetime, timedelta

def test_consommables_specific():
    """Test avec le produit Gâteau Test 1 qui a des consommables"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🧪 TEST SPÉCIFIQUE : Gâteau Test 1 avec consommables")
        print("=" * 60)
        
        # 1. Trouver le produit "Gâteau Test 1"
        test_product = Product.query.filter_by(name='Gâteau Test 1').first()
        if not test_product:
            print("❌ Produit 'Gâteau Test 1' non trouvé")
            return
        
        print(f"✅ Produit trouvé : {test_product.name}")
        
        # 2. Vérifier les consommables liés
        recipes = ConsumableRecipe.query.filter(
            ConsumableRecipe.finished_product_id == test_product.id
        ).all()
        
        print(f"✅ Consommables liés : {len(recipes)}")
        for recipe in recipes:
            consumable = recipe.consumable_product
            print(f"  - {consumable.name} : {recipe.quantity_per_unit} {consumable.unit} par unité")
            print(f"    Stock actuel : {consumable.stock_consommables} {consumable.unit}")
        
        # 3. Créer une commande de test
        print(f"\n📝 Création d'une commande de test...")
        test_order = Order(
            customer_name="Test Consommables Spécifique",
            customer_phone="0123456789",
            status='in_production',
            due_date=datetime.utcnow() + timedelta(hours=2),
            created_at=datetime.utcnow()
        )
        db.session.add(test_order)
        db.session.flush()
        
        # Ajouter le produit à la commande
        order_item = OrderItem(
            order_id=test_order.id,
            product_id=test_product.id,
            quantity=10,  # Produire 10 gâteaux
            unit_price=test_product.price or 15.0
        )
        db.session.add(order_item)
        db.session.commit()
        
        print(f"✅ Commande créée : #{test_order.id} avec {test_product.name} (quantité: 10)")
        
        # 4. Afficher l'état AVANT
        print(f"\n📊 ÉTAT AVANT PRODUCTION :")
        print("-" * 40)
        
        for recipe in recipes:
            consumable = recipe.consumable_product
            qty_needed = recipe.quantity_per_unit * 10  # 10 gâteaux
            print(f"  - {consumable.name}")
            print(f"    Stock actuel : {consumable.stock_consommables} {consumable.unit}")
            print(f"    Quantité nécessaire : {qty_needed} {consumable.unit}")
        
        # 5. Exécuter la décrémentation
        print(f"\n🏭 EXÉCUTION DE LA PRODUCTION...")
        
        try:
            test_order.decrement_ingredients_stock_on_production()
            db.session.commit()
            print("✅ Décrémentation exécutée avec succès")
        except Exception as e:
            print(f"❌ Erreur : {e}")
            db.session.rollback()
            return
        
        # 6. Afficher l'état APRÈS
        print(f"\n📊 ÉTAT APRÈS PRODUCTION :")
        print("-" * 40)
        
        for recipe in recipes:
            consumable = recipe.consumable_product
            qty_needed = recipe.quantity_per_unit * 10
            print(f"  - {consumable.name}")
            print(f"    Stock final : {consumable.stock_consommables} {consumable.unit}")
            print(f"    Quantité utilisée : {qty_needed} {consumable.unit}")
            
            # Vérifier la cohérence
            expected_stock = 100 - qty_needed  # Stock initial était 100
            if abs(consumable.stock_consommables - expected_stock) < 0.01:
                print(f"    ✅ Cohérent (attendu: {expected_stock})")
            else:
                print(f"    ❌ Incohérent (attendu: {expected_stock})")
        
        print(f"\n🎉 TEST TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)

if __name__ == "__main__":
    test_consommables_specific()

