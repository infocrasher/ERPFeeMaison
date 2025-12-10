#!/usr/bin/env python3
"""
Script pour vérifier les détails de la commande #578
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order

def verifier_commande_578():
    """Vérifier les détails de la commande #578"""
    app = create_app()
    
    with app.app_context():
        order = Order.query.get(578)
        
        if not order:
            print("❌ Commande #578 introuvable")
            return
        
        print("=" * 80)
        print("DÉTAILS COMMANDE #578")
        print("=" * 80)
        print(f"ID: {order.id}")
        print(f"order_type: '{order.order_type}'")
        print(f"Type affiché: {order.get_order_type_display()}")
        print(f"Status: {order.status}")
        print(f"Customer Name: {order.customer_name}")
        print(f"Customer Phone: {order.customer_phone}")
        print(f"Delivery Option: {order.delivery_option}")
        print(f"Total Amount: {order.total_amount}")
        print(f"Created At: {order.created_at}")
        print(f"Due Date: {order.due_date}")
        print()
        
        # Vérifier les valeurs possibles de order_type
        print("=" * 80)
        print("VALEURS POSSIBLES DE order_type")
        print("=" * 80)
        print("- 'customer_order' → Commande Client")
        print("- 'counter_production_request' → Ordre de Production")
        print("- 'in_store' → Vente au comptoir")
        print("- 'pos_direct' → Vente PDV directe")
        print()
        
        # Vérifier ce qui devrait être affiché
        print("=" * 80)
        print("ANALYSE")
        print("=" * 80)
        if order.order_type == 'customer_order':
            print("✅ order_type est 'customer_order' → Devrait afficher 'Commande Client'")
        elif order.order_type == 'counter_production_request':
            print("❌ order_type est 'counter_production_request' → Affiche 'Ordre de Production' (INCORRECT)")
            print("   PROBLÈME: Cette commande devrait être 'customer_order'")
        else:
            print(f"⚠️  order_type est '{order.order_type}' → Affiche 'Ordre de Production'")
            print("   PROBLÈME: Cette commande devrait probablement être 'customer_order'")
        
        # Vérifier les indices
        if order.customer_name:
            print(f"   → A un client: {order.customer_name}")
        if order.delivery_option == 'delivery':
            print(f"   → Livraison à domicile")
        if order.total_amount and float(order.total_amount) > 0:
            print(f"   → Montant: {order.total_amount} DA")
        
        print()
        print("=" * 80)
        print("CORRECTION SUGGÉRÉE")
        print("=" * 80)
        if order.order_type != 'customer_order':
            print("Pour corriger, exécuter:")
            print(f"  UPDATE orders SET order_type = 'customer_order' WHERE id = 578;")
        else:
            print("La commande a déjà le bon order_type.")

if __name__ == '__main__':
    verifier_commande_578()

