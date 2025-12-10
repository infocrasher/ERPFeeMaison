#!/usr/bin/env python3
"""
Script pour corriger le order_type de la commande #578
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order

def corriger_commande_578():
    """Corriger le order_type de la commande #578"""
    app = create_app()
    
    with app.app_context():
        order = Order.query.get(578)
        
        if not order:
            print("❌ Commande #578 introuvable")
            return
        
        print("=" * 80)
        print("AVANT CORRECTION")
        print("=" * 80)
        print(f"ID: {order.id}")
        print(f"order_type: '{order.order_type}'")
        print(f"Type affiché: {order.get_order_type_display()}")
        print(f"Customer Name: {order.customer_name}")
        print(f"Delivery Option: {order.delivery_option}")
        print(f"Total Amount: {order.total_amount}")
        print()
        
        # Vérifier si la correction est nécessaire
        if order.order_type == 'customer_order':
            print("✅ La commande a déjà le bon order_type ('customer_order')")
            return
        
        # Demander confirmation
        print("=" * 80)
        print("CORRECTION")
        print("=" * 80)
        print(f"Changement: '{order.order_type}' → 'customer_order'")
        print()
        
        # Appliquer la correction
        try:
            order.order_type = 'customer_order'
            db.session.commit()
            
            print("✅ Correction appliquée avec succès !")
            print()
            print("=" * 80)
            print("APRÈS CORRECTION")
            print("=" * 80)
            print(f"ID: {order.id}")
            print(f"order_type: '{order.order_type}'")
            print(f"Type affiché: {order.get_order_type_display()}")
            print()
            print("✅ La commande #578 devrait maintenant s'afficher comme 'Commande Client'")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la correction: {e}")
            raise

if __name__ == '__main__':
    corriger_commande_578()

