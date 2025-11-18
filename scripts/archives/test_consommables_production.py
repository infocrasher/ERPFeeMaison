#!/usr/bin/env python3
"""
Script de test pour vérifier la décrémentation automatique des consommables
lors de la production des produits finis.

Usage: python test_consommables_production.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Order, OrderItem, Category
from app.consumables.models import ConsumableRecipe
from datetime import datetime, timedelta

def test_consommables_production():
    """Test de la décrémentation des consommables lors de la production"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🧪 TEST : Décrémentation automatique des consommables")
        print("=" * 60)
        
        # 1. Vérifier qu'il y a des produits finis avec recettes
        finished_products = Product.query.filter_by(product_type='finished').all()
        print(f"📦 Produits finis trouvés : {len(finished_products)}")
        
        if not finished_products:
            print("❌ Aucun produit fini trouvé. Créons un exemple...")
            return
        
        # 2. Vérifier qu'il y a des consommables
        consumables = Product.query.filter_by(product_type='consommable').all()
        print(f"📦 Consommables trouvés : {len(consumables)}")
        
        if not consumables:
            print("❌ Aucun consommable trouvé. Créons un exemple...")
            return
        
        # 3. Vérifier les recettes de consommables
        consumable_recipes = ConsumableRecipe.query.all()
        print(f"📋 Recettes de consommables : {len(consumable_recipes)}")
        
        if not consumable_recipes:
            print("❌ Aucune recette de consommable trouvée.")
            print("💡 Créez des recettes via /admin/consumables/recipes/create")
            return
        
        # 4. Tester avec une commande existante ou en créer une
        test_order = Order.query.filter_by(status='in_production').first()
        
        if not test_order:
            print("📝 Création d'une commande de test...")
            test_order = Order(
                customer_name="Test Consommables",
                customer_phone="0123456789",
                status='in_production',
                due_date=datetime.utcnow() + timedelta(hours=2),
                created_at=datetime.utcnow()
            )
            db.session.add(test_order)
            db.session.flush()  # Pour obtenir l'ID
            
            # Ajouter un produit fini à la commande
            if finished_products:
                test_product = finished_products[0]
                order_item = OrderItem(
                    order_id=test_order.id,
                    product_id=test_product.id,
                    quantity=5,  # Produire 5 unités
                    unit_price=test_product.price or 10.0
                )
                db.session.add(order_item)
                db.session.commit()
                print(f"✅ Commande de test créée : {test_order.id} avec {test_product.name}")
        
        # 5. Afficher l'état AVANT la production
        print("\n📊 ÉTAT AVANT PRODUCTION :")
        print("-" * 40)
        
        for item in test_order.items:
            product = item.product
            print(f"Produit fini : {product.name}")
            print(f"  - Quantité à produire : {item.quantity}")
            
            if product.recipe_definition:
                print(f"  - Recette : {product.recipe_definition.name}")
                print(f"  - Rendement : {product.recipe_definition.yield_quantity} {product.recipe_definition.yield_unit}")
                
                # Ingrédients
                for ingredient in product.recipe_definition.ingredients:
                    print(f"    - Ingrédient : {ingredient.product.name} ({ingredient.quantity_needed} {ingredient.unit})")
            
            # Consommables liés
            consumable_recipes_for_product = ConsumableRecipe.query.filter(
                ConsumableRecipe.finished_product_id == product.id
            ).all()
            
            if consumable_recipes_for_product:
                print(f"  - Consommables liés :")
                for recipe in consumable_recipes_for_product:
                    consumable = recipe.consumable_product
                    print(f"    - {consumable.name} : {recipe.quantity_per_unit} {consumable.unit} par unité")
                    print(f"      Stock actuel : {consumable.stock_consommables} {consumable.unit}")
            else:
                print(f"  - Aucun consommable lié")
        
        # 6. Simuler la production (passage à ready_at_shop)
        print(f"\n🏭 SIMULATION DE LA PRODUCTION...")
        print(f"Changement de statut : {test_order.status} → ready_at_shop")
        
        # Sauvegarder l'état avant
        stock_before = {}
        for item in test_order.items:
            product = item.product
            if product.recipe_definition:
                # Ingrédients
                for ingredient in product.recipe_definition.ingredients:
                    stock_before[ingredient.product.name] = {
                        'type': 'ingredient',
                        'stock_magasin': ingredient.product.stock_ingredients_magasin,
                        'stock_local': ingredient.product.stock_ingredients_local
                    }
                
                # Consommables
                for recipe in ConsumableRecipe.query.filter(ConsumableRecipe.finished_product_id == product.id):
                    consumable = recipe.consumable_product
                    stock_before[consumable.name] = {
                        'type': 'consommable',
                        'stock_consommables': consumable.stock_consommables
                    }
        
        # Exécuter la décrémentation
        try:
            test_order.decrement_ingredients_stock_on_production()
            db.session.commit()
            print("✅ Décrémentation exécutée avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la décrémentation : {e}")
            db.session.rollback()
            return
        
        # 7. Afficher l'état APRÈS la production
        print("\n📊 ÉTAT APRÈS PRODUCTION :")
        print("-" * 40)
        
        for item in test_order.items:
            product = item.product
            print(f"Produit fini : {product.name}")
            
            if product.recipe_definition:
                # Ingrédients
                for ingredient in product.recipe_definition.ingredients:
                    if ingredient.product.name in stock_before:
                        before = stock_before[ingredient.product.name]
                        after_magasin = ingredient.product.stock_ingredients_magasin
                        after_local = ingredient.product.stock_ingredients_local
                        
                        print(f"    - Ingrédient : {ingredient.product.name}")
                        print(f"      Stock magasin : {before['stock_magasin']} → {after_magasin}")
                        print(f"      Stock local : {before['stock_local']} → {after_local}")
                
                # Consommables
                for recipe in ConsumableRecipe.query.filter(ConsumableRecipe.finished_product_id == product.id):
                    consumable = recipe.consumable_product
                    if consumable.name in stock_before:
                        before = stock_before[consumable.name]
                        after = consumable.stock_consommables
                        
                        print(f"    - Consommable : {consumable.name}")
                        print(f"      Stock : {before['stock_consommables']} → {after}")
                        
                        # Calculer la quantité décrémentée
                        qty_per_unit = recipe.quantity_per_unit
                        total_qty_used = qty_per_unit * float(item.quantity)
                        print(f"      Quantité utilisée : {qty_per_unit} × {item.quantity} = {total_qty_used} {consumable.unit}")
        
        print("\n✅ TEST TERMINÉ")
        print("=" * 60)

if __name__ == "__main__":
    test_consommables_production()

