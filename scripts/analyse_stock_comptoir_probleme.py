#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse approfondie du problème de décrémentation du stock_comptoir
lors de la réception d'une commande client.

Ce script analyse tous les endroits où le stock_comptoir pourrait être modifié
et identifie la source exacte du problème.
"""

import sys
import os
import traceback
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def analyse_code():
    """Analyse statique du code pour identifier les problèmes potentiels"""
    
    print("=" * 80)
    print("ANALYSE STATIQUE DU CODE")
    print("=" * 80)
    print()
    
    print("1. Vérification de _increment_stock_value_only_for_customer_order()")
    print("-" * 80)
    
    # Lire le fichier models.py
    models_path = os.path.join(os.path.dirname(__file__), '..', 'models.py')
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher la méthode
    if '_increment_stock_value_only_for_customer_order' in content:
        print("✅ Méthode trouvée")
        
        # Extraire la méthode
        start = content.find('def _increment_stock_value_only_for_customer_order')
        if start != -1:
            # Trouver la fin de la méthode (prochaine méthode ou fin de classe)
            end_method = content.find('\n    def ', start + 1)
            end_class = content.find('\nclass ', start + 1)
            end = min(end_method, end_class) if end_method != -1 and end_class != -1 else max(end_method, end_class) if end_method != -1 or end_class != -1 else len(content)
            
            method_code = content[start:end]
            
            # Vérifier les appels à update_stock_by_location
            if 'update_stock_by_location' in method_code:
                print("⚠️  PROBLÈME POTENTIEL: update_stock_by_location est appelé")
                # Chercher les appels
                import re
                matches = re.findall(r'update_stock_by_location\([^)]+\)', method_code)
                for match in matches:
                    print(f"   - {match}")
                    if 'stock_comptoir' in match:
                        print("   ❌ ERREUR: stock_comptoir est modifié!")
            else:
                print("✅ Aucun appel à update_stock_by_location")
            
            # Vérifier les modifications directes de stock_comptoir
            if 'stock_comptoir' in method_code:
                print("⚠️  PROBLÈME POTENTIEL: stock_comptoir est référencé")
                # Chercher les lignes contenant stock_comptoir
                lines = method_code.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'stock_comptoir' in line and ('=' in line or '+=' in line or '-=' in line):
                        print(f"   Ligne {i}: {line.strip()}")
                        if '=' in line and 'stock_comptoir_avant' not in line and 'stock_comptoir_apres' not in line:
                            print("   ❌ ERREUR: Modification directe de stock_comptoir détectée!")
            
            # Vérifier le calcul du PMP
            if 'total_stock_all_locations' in method_code:
                print("⚠️  PROBLÈME POTENTIEL: total_stock_all_locations est utilisé")
                print("   Note: Cette propriété inclut stock_comptoir, ce qui peut causer des problèmes")
            
            # Vérifier le calcul de cost_price
            if 'cost_price =' in method_code or 'cost_price/' in method_code:
                print("⚠️  PROBLÈME POTENTIEL: cost_price est modifié")
                print("   Note: La modification de cost_price pourrait déclencher des side effects")
    
    print()
    print("2. Vérification de update_stock_by_location()")
    print("-" * 80)
    
    if 'def update_stock_by_location' in content:
        print("✅ Méthode trouvée")
        
        # Extraire la méthode
        start = content.find('def update_stock_by_location')
        if start != -1:
            end_method = content.find('\n    def ', start + 1)
            end_class = content.find('\nclass ', start + 1)
            end = min(end_method, end_class) if end_method != -1 and end_class != -1 else max(end_method, end_class) if end_method != -1 or end_class != -1 else len(content)
            
            method_code = content[start:end]
            
            # Vérifier si setattr est utilisé
            if 'setattr(self, qty_attr' in method_code:
                print("⚠️  PROBLÈME POTENTIEL: setattr est utilisé pour modifier le stock")
                print("   Note: Si qty_attr est 'stock_comptoir' et quantity_change est négatif, le stock sera décrémenté")
            
            # Vérifier les conditions
            if 'if location_key ==' in method_code or 'if qty_attr ==' in method_code:
                print("✅ Des vérifications de localisation sont présentes")
            else:
                print("⚠️  Aucune vérification spécifique pour stock_comptoir")
    
    print()
    print("3. Vérification de change_status_to_ready()")
    print("-" * 80)
    
    status_routes_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'orders', 'status_routes.py')
    if os.path.exists(status_routes_path):
        with open(status_routes_path, 'r', encoding='utf-8') as f:
            status_content = f.read()
        
        if 'def change_status_to_ready' in status_content:
            print("✅ Route trouvée")
            
            # Extraire la fonction
            start = status_content.find('def change_status_to_ready')
            if start != -1:
                end = status_content.find('\n@', start + 1)
                if end == -1:
                    end = len(status_content)
                
                function_code = status_content[start:end]
                
                # Vérifier les appels à update_stock_by_location
                if 'update_stock_by_location' in function_code:
                    print("⚠️  PROBLÈME POTENTIEL: update_stock_by_location est appelé")
                    import re
                    matches = re.findall(r'update_stock_by_location\([^)]+\)', function_code)
                    for match in matches:
                        print(f"   - {match}")
                        if 'stock_comptoir' in match and '-' in match:
                            print("   ❌ ERREUR: stock_comptoir est décrémenté!")
                
                # Vérifier les appels aux méthodes d'incrémentation
                if '_increment_stock_value_only_for_customer_order' in function_code:
                    print("✅ _increment_stock_value_only_for_customer_order est appelé pour les commandes client")
                if '_increment_shop_stock_with_value' in function_code:
                    print("✅ _increment_shop_stock_with_value est appelé pour les ordres de production")
    
    print()
    print("=" * 80)
    print("HYPOTHÈSES SUR LA CAUSE DU PROBLÈME")
    print("=" * 80)
    print()
    
    print("Hypothèse 1: Le calcul du PMP modifie indirectement stock_comptoir")
    print("   - Lors du calcul: cost_price = total_stock_value / stock_pour_pmp")
    print("   - Si stock_pour_pmp inclut stock_comptoir, cela pourrait causer des problèmes")
    print("   - SOLUTION: Vérifier que stock_pour_pmp n'inclut PAS stock_comptoir")
    print()
    
    print("Hypothèse 2: Un ingrédient est aussi un produit fini")
    print("   - Si un ingrédient dans la recette est le même produit que le produit fini")
    print("   - Lors de la décrémentation des ingrédients, le stock_comptoir du produit fini pourrait être modifié")
    print("   - SOLUTION: Vérifier que les ingrédients ne sont pas des produits finis")
    print()
    
    print("Hypothèse 3: SQLAlchemy flush/commit déclenche des side effects")
    print("   - Lors de db.session.add(product_fini), SQLAlchemy pourrait déclencher des événements")
    print("   - Ces événements pourraient modifier le stock_comptoir")
    print("   - SOLUTION: Vérifier les événements SQLAlchemy sur le modèle Product")
    print()
    
    print("Hypothèse 4: Une autre méthode est appelée en parallèle")
    print("   - Peut-être que mark_as_received_at_shop() ou une autre méthode est appelée")
    print("   - Cette méthode pourrait modifier le stock_comptoir")
    print("   - SOLUTION: Vérifier tous les appels de méthodes lors de la réception")
    print()

def analyse_produit_specifique(product_id, order_id=None):
    """Analyse un produit spécifique pour identifier le problème"""
    
    print("=" * 80)
    print(f"ANALYSE DU PRODUIT #{product_id}")
    print("=" * 80)
    print()
    
    try:
        from app import create_app
        from models import Product, Order, OrderItem
        from extensions import db
        
        app = create_app()
        
        with app.app_context():
            product = Product.query.get(product_id)
            if not product:
                print(f"❌ Produit #{product_id} non trouvé")
                return
            
            print(f"📦 Produit: {product.name} (ID: {product.id})")
            print(f"   Type: {product.product_type}")
            print(f"   Stock comptoir: {product.stock_comptoir}")
            print(f"   Stock total (toutes locations): {product.total_stock_all_locations}")
            print()
            
            # Vérifier si le produit a une recette
            if product.recipe_definition:
                print(f"📋 Recette: {product.recipe_definition.name}")
                print(f"   Ingrédients:")
                for ingredient in product.recipe_definition.ingredients:
                    ing_product = ingredient.product
                    print(f"      - {ing_product.name} (ID: {ing_product.id})")
                    if ing_product.id == product.id:
                        print(f"        ⚠️  ATTENTION: L'ingrédient est le même que le produit fini!")
                print()
            
            # Vérifier les commandes client qui utilisent ce produit
            if order_id:
                order = Order.query.get(order_id)
                if order:
                    print(f"📋 Commande #{order_id}")
                    print(f"   Type: {order.order_type}")
                    print(f"   Statut: {order.status}")
                    print()
                    
                    # Vérifier les items
                    for item in order.items:
                        if item.product_id == product_id:
                            print(f"   Item: {item.quantity} x {product.name}")
                            print(f"   Prix unitaire: {item.unit_price}")
                            print()
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    print()
    print("🔍 ANALYSE APPROFONDIE DU PROBLÈME STOCK_COMPTOIR")
    print()
    
    # Analyse statique
    analyse_code()
    
    # Analyse d'un produit spécifique si fourni
    if len(sys.argv) > 1:
        product_id = int(sys.argv[1])
        order_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        analyse_produit_specifique(product_id, order_id)
    
    print()
    print("=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    print()
    print("1. Ajouter des logs détaillés dans _increment_stock_value_only_for_customer_order()")
    print("2. Vérifier que aucun ingrédient n'est le même produit que le produit fini")
    print("3. Vérifier les événements SQLAlchemy sur le modèle Product")
    print("4. Utiliser le script trace_stock_comptoir.py pour tracer en temps réel")
    print()

