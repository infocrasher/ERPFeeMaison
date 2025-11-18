#!/usr/bin/env python3
"""
Script de vérification du système de consommables
Usage: python verify_consommables_system.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Order, OrderItem, Category
from app.consumables.models import ConsumableRecipe, ConsumableUsage, ConsumableAdjustment
from datetime import datetime, timedelta

def verify_consommables_system():
    """Vérifier que le système de consommables fonctionne correctement"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🔍 VÉRIFICATION DU SYSTÈME CONSOMMABLES")
        print("=" * 60)
        
        # 1. Vérifier la structure de base
        print("\n1️⃣ VÉRIFICATION DE LA STRUCTURE")
        print("-" * 40)
        
        # Catégories
        consumable_category = Category.query.filter_by(name='Boite Consomable').first()
        if consumable_category:
            print(f"✅ Catégorie consommables : {consumable_category.name}")
        else:
            print("❌ Catégorie 'Boite Consomable' manquante")
            return False
        
        # Produits consommables
        consumables = Product.query.filter_by(product_type='consommable').all()
        print(f"✅ Consommables en base : {len(consumables)}")
        
        if len(consumables) == 0:
            print("❌ Aucun consommable trouvé. Exécutez : python setup_test_consommables.py")
            return False
        
        # Produits finis
        finished_products = Product.query.filter_by(product_type='finished').all()
        print(f"✅ Produits finis en base : {len(finished_products)}")
        
        # 2. Vérifier les recettes de consommables
        print("\n2️⃣ VÉRIFICATION DES RECETTES")
        print("-" * 40)
        
        consumable_recipes = ConsumableRecipe.query.all()
        print(f"✅ Recettes de consommables : {len(consumable_recipes)}")
        
        if len(consumable_recipes) == 0:
            print("❌ Aucune recette de consommable. Créez-en via /admin/consumables/recipes/create")
            return False
        
        # Afficher les recettes
        for recipe in consumable_recipes:
            print(f"  - {recipe.finished_product.name} → {recipe.consumable_product.name} ({recipe.quantity_per_unit} par unité)")
        
        # 3. Vérifier les stocks
        print("\n3️⃣ VÉRIFICATION DES STOCKS")
        print("-" * 40)
        
        for consumable in consumables:
            stock = consumable.stock_consommables or 0
            seuil = consumable.seuil_min_consommables or 0
            status = "🟢 OK" if stock > seuil else "🔴 FAIBLE"
            print(f"  - {consumable.name} : {stock} {consumable.unit} (seuil: {seuil}) {status}")
        
        # 4. Vérifier les commandes en production
        print("\n4️⃣ VÉRIFICATION DES COMMANDES")
        print("-" * 40)
        
        orders_in_production = Order.query.filter_by(status='in_production').all()
        print(f"✅ Commandes en production : {len(orders_in_production)}")
        
        if len(orders_in_production) == 0:
            print("ℹ️  Aucune commande en production. Créez-en une pour tester.")
        else:
            for order in orders_in_production:
                print(f"  - Commande #{order.id} : {order.customer_name} ({len(order.items)} articles)")
                
                for item in order.items:
                    product = item.product
                    print(f"    - {product.name} : {item.quantity} {product.unit}")
                    
                    # Vérifier si le produit a des consommables liés
                    recipes = ConsumableRecipe.query.filter(
                        ConsumableRecipe.finished_product_id == product.id
                    ).all()
                    
                    if recipes:
                        print(f"      Consommables liés :")
                        for recipe in recipes:
                            consumable = recipe.consumable_product
                            qty_needed = recipe.quantity_per_unit * float(item.quantity)
                            print(f"        - {consumable.name} : {qty_needed} {consumable.unit} (stock: {consumable.stock_consommables})")
                    else:
                        print(f"      Aucun consommable lié")
        
        # 5. Test de la méthode de décrémentation
        print("\n5️⃣ TEST DE LA DÉCRÉMENTATION")
        print("-" * 40)
        
        if orders_in_production:
            test_order = orders_in_production[0]
            print(f"Test avec la commande #{test_order.id}")
            
            # Sauvegarder l'état avant
            stock_before = {}
            for item in test_order.items:
                product = item.product
                recipes = ConsumableRecipe.query.filter(
                    ConsumableRecipe.finished_product_id == product.id
                ).all()
                
                for recipe in recipes:
                    consumable = recipe.consumable_product
                    stock_before[consumable.name] = consumable.stock_consommables
            
            # Exécuter la décrémentation
            try:
                test_order.decrement_ingredients_stock_on_production()
                db.session.commit()
                print("✅ Décrémentation exécutée avec succès")
                
                # Vérifier les changements
                print("Changements détectés :")
                for item in test_order.items:
                    product = item.product
                    recipes = ConsumableRecipe.query.filter(
                        ConsumableRecipe.finished_product_id == product.id
                    ).all()
                    
                    for recipe in recipes:
                        consumable = recipe.consumable_product
                        before = stock_before.get(consumable.name, 0)
                        after = consumable.stock_consommables
                        change = after - before
                        
                        if change != 0:
                            print(f"  - {consumable.name} : {before} → {after} (Δ{change})")
                        else:
                            print(f"  - {consumable.name} : Aucun changement")
                
            except Exception as e:
                print(f"❌ Erreur lors de la décrémentation : {e}")
                db.session.rollback()
                return False
        else:
            print("ℹ️  Aucune commande en production pour tester la décrémentation")
        
        # 6. Vérifier les modules
        print("\n6️⃣ VÉRIFICATION DES MODULES")
        print("-" * 40)
        
        # Vérifier que le module consumables est bien enregistré
        # (app est déjà créé au début de la fonction)
        
        with app.app_context():
            # Vérifier les routes
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            consumable_routes = [rule for rule in rules if '/consumables' in rule]
            
            if consumable_routes:
                print(f"✅ Routes consommables enregistrées : {len(consumable_routes)}")
                for route in consumable_routes[:5]:  # Afficher les 5 premières
                    print(f"  - {route}")
            else:
                print("❌ Aucune route consommable trouvée")
                return False
        
        print("\n🎉 VÉRIFICATION TERMINÉE")
        print("=" * 60)
        print("✅ Le système de consommables est opérationnel !")
        print("\nProchaines étapes :")
        print("1. Créez des recettes de consommables via /admin/consumables/recipes/create")
        print("2. Créez des commandes avec des produits finis")
        print("3. Passez les commandes en production")
        print("4. Changez le statut à 'ready_at_shop' pour déclencher la décrémentation")
        
        return True

if __name__ == "__main__":
    success = verify_consommables_system()
    if not success:
        print("\n❌ Des problèmes ont été détectés. Vérifiez la configuration.")
        sys.exit(1)
    else:
        print("\n✅ Tout fonctionne correctement !")
