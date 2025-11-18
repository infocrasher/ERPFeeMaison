#!/usr/bin/env python3
"""
Script pour créer des données de test pour les consommables
Usage: python setup_test_consommables.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Category
from app.consumables.models import ConsumableRecipe
from datetime import datetime

def setup_test_data():
    """Créer des données de test pour les consommables"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🔧 CONFIGURATION DES DONNÉES DE TEST")
        print("=" * 50)
        
        # 1. Créer une catégorie consommables si elle n'existe pas
        consumable_category = Category.query.filter_by(name='Boite Consomable').first()
        if not consumable_category:
            consumable_category = Category(name='Boite Consomable', description='Consommables et emballages')
            db.session.add(consumable_category)
            db.session.commit()
            print("✅ Catégorie 'Boite Consomable' créée")
        else:
            print("✅ Catégorie 'Boite Consomable' existe déjà")
        
        # 2. Créer des consommables de test
        test_consumables = [
            {
                'name': 'Sacs Papier 15cm',
                'product_type': 'consommable',
                'unit': 'pièces',
                'cost_price': 0.05,
                'stock_consommables': 100,
                'seuil_min_consommables': 20
            },
            {
                'name': 'Étiquettes Prix',
                'product_type': 'consommable', 
                'unit': 'pièces',
                'cost_price': 0.02,
                'stock_consommables': 200,
                'seuil_min_consommables': 50
            },
            {
                'name': 'Boîtes Gâteau',
                'product_type': 'consommable',
                'unit': 'pièces', 
                'cost_price': 0.15,
                'stock_consommables': 50,
                'seuil_min_consommables': 10
            }
        ]
        
        created_consumables = []
        for consumable_data in test_consumables:
            existing = Product.query.filter_by(name=consumable_data['name']).first()
            if not existing:
                consumable = Product(
                    name=consumable_data['name'],
                    product_type=consumable_data['product_type'],
                    unit=consumable_data['unit'],
                    cost_price=consumable_data['cost_price'],
                    stock_consommables=consumable_data['stock_consommables'],
                    seuil_min_consommables=consumable_data['seuil_min_consommables'],
                    category_id=consumable_category.id
                )
                db.session.add(consumable)
                created_consumables.append(consumable)
                print(f"✅ Consommable créé : {consumable_data['name']}")
            else:
                created_consumables.append(existing)
                print(f"✅ Consommable existe déjà : {consumable_data['name']}")
        
        db.session.commit()
        
        # 3. Créer des produits finis de test s'ils n'existent pas
        finished_category = Category.query.filter_by(name='Gateaux ').first()
        if not finished_category:
            finished_category = Category(name='Gateaux ', description='Gâteaux et pâtisseries')
            db.session.add(finished_category)
            db.session.commit()
            print("✅ Catégorie 'Gateaux ' créée")
        
        test_finished_products = [
            {
                'name': 'Gâteau Test 1',
                'product_type': 'finished',
                'unit': 'pièces',
                'price': 15.0,
                'cost_price': 8.0,
                'stock_comptoir': 10
            },
            {
                'name': 'Gâteau Test 2', 
                'product_type': 'finished',
                'unit': 'pièces',
                'price': 20.0,
                'cost_price': 12.0,
                'stock_comptoir': 5
            }
        ]
        
        created_finished = []
        for product_data in test_finished_products:
            existing = Product.query.filter_by(name=product_data['name']).first()
            if not existing:
                product = Product(
                    name=product_data['name'],
                    product_type=product_data['product_type'],
                    unit=product_data['unit'],
                    price=product_data['price'],
                    cost_price=product_data['cost_price'],
                    stock_comptoir=product_data['stock_comptoir'],
                    category_id=finished_category.id
                )
                db.session.add(product)
                created_finished.append(product)
                print(f"✅ Produit fini créé : {product_data['name']}")
            else:
                created_finished.append(existing)
                print(f"✅ Produit fini existe déjà : {product_data['name']}")
        
        db.session.commit()
        
        # 4. Créer des recettes de consommables
        if created_finished and created_consumables:
            # Lier le premier produit fini avec les consommables
            finished_product = created_finished[0]
            
            test_recipes = [
                {
                    'finished_product': finished_product,
                    'consumable': created_consumables[0],  # Sacs Papier
                    'quantity_per_unit': 1.0,  # 1 sac par gâteau
                    'notes': 'Un sac papier par gâteau'
                },
                {
                    'finished_product': finished_product,
                    'consumable': created_consumables[1],  # Étiquettes
                    'quantity_per_unit': 1.0,  # 1 étiquette par gâteau
                    'notes': 'Une étiquette prix par gâteau'
                },
                {
                    'finished_product': finished_product,
                    'consumable': created_consumables[2],  # Boîtes
                    'quantity_per_unit': 0.5,  # 0.5 boîte par gâteau (1 boîte pour 2 gâteaux)
                    'notes': 'Une boîte pour 2 gâteaux'
                }
            ]
            
            for recipe_data in test_recipes:
                existing = ConsumableRecipe.query.filter(
                    ConsumableRecipe.finished_product_id == recipe_data['finished_product'].id,
                    ConsumableRecipe.consumable_product_id == recipe_data['consumable'].id
                ).first()
                
                if not existing:
                    recipe = ConsumableRecipe(
                        finished_product_id=recipe_data['finished_product'].id,
                        consumable_product_id=recipe_data['consumable'].id,
                        quantity_per_unit=recipe_data['quantity_per_unit'],
                        notes=recipe_data['notes']
                    )
                    db.session.add(recipe)
                    print(f"✅ Recette créée : {recipe_data['finished_product'].name} → {recipe_data['consumable'].name} ({recipe_data['quantity_per_unit']} par unité)")
                else:
                    print(f"✅ Recette existe déjà : {recipe_data['finished_product'].name} → {recipe_data['consumable'].name}")
        
        db.session.commit()
        
        print("\n🎉 CONFIGURATION TERMINÉE")
        print("=" * 50)
        print("Vous pouvez maintenant tester avec : python test_consommables_production.py")
        print("\nDonnées créées :")
        print(f"- {len(created_consumables)} consommables")
        print(f"- {len(created_finished)} produits finis") 
        print(f"- {len(test_recipes)} recettes de consommables")

if __name__ == "__main__":
    setup_test_data()

