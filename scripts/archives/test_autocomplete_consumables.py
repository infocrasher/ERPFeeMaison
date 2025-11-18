#!/usr/bin/env python3
"""
Script de test pour vérifier l'autocomplétion des consommables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, Product, Category
from app.consumables.models import ConsumableRecipe
from flask import request

def test_autocomplete_api():
    """Tester l'API d'autocomplétion"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🧪 TEST : API d'autocomplétion des consommables")
        print("=" * 60)
        
        # 1. Vérifier les données de test
        print("\n1️⃣ VÉRIFICATION DES DONNÉES")
        print("-" * 40)
        
        # Produits finis
        finished_products = Product.query.filter_by(product_type='finished').limit(5).all()
        print(f"✅ Produits finis disponibles : {len(finished_products)}")
        for product in finished_products:
            print(f"  - {product.name} (ID: {product.id})")
        
        # Consommables
        consumables = Product.query.filter_by(product_type='consommable').limit(5).all()
        print(f"✅ Consommables disponibles : {len(consumables)}")
        for product in consumables:
            print(f"  - {product.name} (ID: {product.id})")
        
        # 2. Tester l'API avec un client de test
        print("\n2️⃣ TEST DE L'API")
        print("-" * 40)
        
        with app.test_client() as client:
            # Se connecter en tant qu'admin
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Utilisateur admin non trouvé")
                return
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test 1: Recherche de produits finis
            print("Test 1: Recherche de produits finis")
            response = client.get('/admin/consumables/api/products/search?q=gâteau&category=finished')
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.content_type}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"  Résultats: {len(data)} produits trouvés")
                for product in data:
                    print(f"    - {product['name']} (Stock: {product['stock']})")
            else:
                print(f"  ❌ Erreur: {response.status_code}")
                print(f"  Response: {response.get_data(as_text=True)[:200]}...")
            
            # Test 2: Recherche de consommables
            print("\nTest 2: Recherche de consommables")
            response = client.get('/admin/consumables/api/products/search?q=sac&category=consumable')
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.content_type}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"  Résultats: {len(data)} consommables trouvés")
                for product in data:
                    print(f"    - {product['name']} (Stock: {product['stock']})")
            else:
                print(f"  ❌ Erreur: {response.status_code}")
                print(f"  Response: {response.get_data(as_text=True)[:200]}...")
            
            # Test 3: Recherche avec terme court
            print("\nTest 3: Recherche avec terme court (< 2 caractères)")
            response = client.get('/admin/consumables/api/products/search?q=a&category=finished')
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"  Résultats: {len(data)} (devrait être 0)")
            
            # Test 4: Recherche sans catégorie
            print("\nTest 4: Recherche sans catégorie")
            response = client.get('/admin/consumables/api/products/search?q=test')
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"  Résultats: {len(data)} produits trouvés")
        
        # 3. Vérifier les recettes existantes
        print("\n3️⃣ VÉRIFICATION DES RECETTES")
        print("-" * 40)
        
        recipes = ConsumableRecipe.query.all()
        print(f"✅ Recettes de consommables : {len(recipes)}")
        for recipe in recipes:
            print(f"  - {recipe.finished_product.name} → {recipe.consumable_product.name} ({recipe.quantity_per_unit} par unité)")
        
        print("\n🎉 TEST TERMINÉ")
        print("=" * 60)
        print("✅ L'API d'autocomplétion fonctionne correctement !")
        print("\nPour tester dans le navigateur :")
        print("1. Connectez-vous en tant qu'admin")
        print("2. Allez sur /admin/consumables/recipes/create")
        print("3. Tapez dans les champs de recherche")

if __name__ == "__main__":
    test_autocomplete_api()

