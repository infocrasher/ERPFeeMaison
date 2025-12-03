#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de traçage pour identifier les modifications du stock_comptoir
lors de la réception d'une commande client.

Ce script intercepte toutes les modifications du stock_comptoir et trace
l'origine exacte de chaque modification.
"""

import sys
import os
import traceback
from functools import wraps

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Monkey patching pour tracer les modifications
original_setattr = setattr
original_update_stock_by_location = None

# Stocker les traces
traces = []

def trace_setattr(obj, name, value):
    """Intercepte setattr pour tracer les modifications de stock_comptoir"""
    if name == 'stock_comptoir' and hasattr(obj, '__class__'):
        class_name = obj.__class__.__name__
        if class_name == 'Product':
            # Récupérer la valeur avant modification
            old_value = getattr(obj, 'stock_comptoir', None)
            
            # Obtenir la stack trace
            stack = traceback.extract_stack()
            caller_info = stack[-2] if len(stack) >= 2 else stack[-1]
            
            trace_info = {
                'action': 'setattr',
                'product_id': getattr(obj, 'id', None),
                'product_name': getattr(obj, 'name', None),
                'old_value': old_value,
                'new_value': value,
                'file': caller_info.filename,
                'line': caller_info.lineno,
                'function': caller_info.name,
                'code': caller_info.line
            }
            traces.append(trace_info)
            
            print(f"🔍 TRACE setattr stock_comptoir:")
            print(f"   Produit: {trace_info['product_name']} (ID: {trace_info['product_id']})")
            print(f"   Ancienne valeur: {old_value}")
            print(f"   Nouvelle valeur: {value}")
            print(f"   Fichier: {trace_info['file']}:{trace_info['line']}")
            print(f"   Fonction: {trace_info['function']}")
            print(f"   Code: {trace_info['code']}")
            print()
    
    return original_setattr(obj, name, value)

def patch_update_stock_by_location():
    """Patch la méthode update_stock_by_location pour tracer les modifications"""
    from models import Product
    
    original_method = Product.update_stock_by_location
    
    def traced_update_stock_by_location(self, location_key, quantity_change, unit_cost_override=None):
        if location_key == 'stock_comptoir':
            old_value = float(self.stock_comptoir or 0.0)
            
            # Obtenir la stack trace
            stack = traceback.extract_stack()
            caller_info = stack[-2] if len(stack) >= 2 else stack[-1]
            
            # Appeler la méthode originale
            result = original_method(self, location_key, quantity_change, unit_cost_override)
            
            new_value = float(self.stock_comptoir or 0.0)
            
            if old_value != new_value:
                trace_info = {
                    'action': 'update_stock_by_location',
                    'product_id': self.id,
                    'product_name': self.name,
                    'old_value': old_value,
                    'new_value': new_value,
                    'quantity_change': quantity_change,
                    'file': caller_info.filename,
                    'line': caller_info.lineno,
                    'function': caller_info.name,
                    'code': caller_info.line
                }
                traces.append(trace_info)
                
                print(f"🔍 TRACE update_stock_by_location stock_comptoir:")
                print(f"   Produit: {trace_info['product_name']} (ID: {trace_info['product_id']})")
                print(f"   Ancienne valeur: {old_value}")
                print(f"   Nouvelle valeur: {new_value}")
                print(f"   Changement: {quantity_change}")
                print(f"   Fichier: {trace_info['file']}:{trace_info['line']}")
                print(f"   Fonction: {trace_info['function']}")
                print(f"   Code: {trace_info['code']}")
                print()
            
            return result
    
    Product.update_stock_by_location = traced_update_stock_by_location
    return original_method

def trace_order_reception(order_id):
    """Trace la réception d'une commande"""
    print("=" * 80)
    print(f"🔍 DÉBUT DU TRACAGE - Commande #{order_id}")
    print("=" * 80)
    print()
    
    # Réinitialiser les traces
    global traces
    traces = []
    
    # Patcher setattr
    import builtins
    builtins.setattr = trace_setattr
    
    # Patcher update_stock_by_location
    original_update_stock_by_location = patch_update_stock_by_location()
    
    try:
        from app import create_app
        from models import Order, Product
        from extensions import db
        
        app = create_app()
        
        with app.app_context():
            order = Order.query.get(order_id)
            if not order:
                print(f"❌ Commande #{order_id} non trouvée")
                return
            
            print(f"📋 Commande #{order_id}")
            print(f"   Type: {order.order_type}")
            print(f"   Statut actuel: {order.status}")
            print()
            
            # Sauvegarder les stocks avant
            stocks_before = {}
            for item in order.items:
                if item.product:
                    product = item.product
                    stocks_before[product.id] = {
                        'name': product.name,
                        'stock_comptoir': float(product.stock_comptoir or 0.0)
                    }
                    print(f"📦 Produit: {product.name} (ID: {product.id})")
                    print(f"   Stock comptoir AVANT: {stocks_before[product.id]['stock_comptoir']}")
            
            print()
            print("🔄 Simulation de la réception...")
            print()
            
            # Simuler le changement de statut
            from app.orders.status_routes import change_status_to_ready
            from flask_login import current_user
            from flask import request
            
            # Créer un contexte de requête
            with app.test_request_context():
                # Simuler l'appel
                # Note: On ne peut pas vraiment appeler la route directement,
                # donc on va appeler les méthodes directement
                
                if order.order_type == 'customer_order':
                    # Appeler la méthode directement
                    order._increment_stock_value_only_for_customer_order()
                else:
                    order._increment_shop_stock_with_value()
            
            print()
            print("📊 Stocks APRÈS:")
            for item in order.items:
                if item.product:
                    product = item.product
                    stock_after = float(product.stock_comptoir or 0.0)
                    stock_before = stocks_before[product.id]['stock_comptoir']
                    print(f"📦 Produit: {product.name} (ID: {product.id})")
                    print(f"   Stock comptoir AVANT: {stock_before}")
                    print(f"   Stock comptoir APRÈS: {stock_after}")
                    if stock_before != stock_after:
                        print(f"   ⚠️  MODIFICATION DÉTECTÉE: {stock_after - stock_before}")
                    print()
            
            print()
            print("=" * 80)
            print("📋 RÉSUMÉ DES TRACES")
            print("=" * 80)
            print()
            
            if traces:
                for i, trace in enumerate(traces, 1):
                    print(f"Trace #{i}:")
                    print(f"   Action: {trace['action']}")
                    print(f"   Produit: {trace['product_name']} (ID: {trace['product_id']})")
                    print(f"   Ancienne valeur: {trace['old_value']}")
                    print(f"   Nouvelle valeur: {trace['new_value']}")
                    if 'quantity_change' in trace:
                        print(f"   Changement: {trace['quantity_change']}")
                    print(f"   Fichier: {trace['file']}:{trace['line']}")
                    print(f"   Fonction: {trace['function']}")
                    print(f"   Code: {trace['code']}")
                    print()
            else:
                print("✅ Aucune modification du stock_comptoir détectée")
                print()
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        traceback.print_exc()
    finally:
        # Restaurer setattr
        import builtins
        builtins.setattr = original_setattr
        
        # Restaurer update_stock_by_location
        if original_update_stock_by_location:
            from models import Product
            Product.update_stock_by_location = original_update_stock_by_location

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python trace_stock_comptoir.py <order_id>")
        sys.exit(1)
    
    order_id = int(sys.argv[1])
    trace_order_reception(order_id)

