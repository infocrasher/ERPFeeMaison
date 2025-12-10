#!/usr/bin/env python3
"""
Script pour vérifier si les commandes de livraison créées depuis le PDV
s'affichent correctement sur le dashboard shop avec adresse et prix de livraison
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order
from datetime import datetime

def verifier_affichage_dashboard_shop():
    """Vérifier l'affichage des commandes de livraison sur le dashboard shop"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("VÉRIFICATION AFFICHAGE DASHBOARD SHOP")
        print("=" * 80)
        print()
        
        # 1. Vérifier les commandes prêtes à livrer (section "Prêt à Livrer")
        print("1️⃣  COMMANDES PRÊTES À LIVRER (ready_at_shop)")
        print("-" * 80)
        
        orders_ready_delivery = Order.query.filter(
            Order.status == 'ready_at_shop',
            Order.delivery_option == 'delivery',
            Order.order_type.in_(['customer_order', 'in_store'])
        ).order_by(Order.due_date.asc()).all()
        
        print(f"   Total trouvé: {len(orders_ready_delivery)}")
        print()
        
        if orders_ready_delivery:
            for order in orders_ready_delivery[:5]:  # Afficher les 5 premières
                print(f"   📦 Commande #{order.id}")
                print(f"      Type: {order.order_type} ({order.get_order_type_display()})")
                print(f"      Client: {order.customer_name or 'N/A'}")
                print(f"      Téléphone: {order.customer_phone or 'N/A'}")
                print(f"      Adresse: {order.customer_address or 'N/A'}")
                print(f"      get_delivery_address(): {order.get_delivery_address() or 'N/A'}")
                print(f"      Prix livraison: {order.delivery_cost or 0} DA")
                print(f"      Total: {order.total_amount or 0} DA")
                print(f"      Statut: {order.status}")
                print()
        else:
            print("   ⚠️  Aucune commande prête à livrer trouvée")
            print()
        
        # 2. Vérifier les commandes créées depuis le PDV récemment
        print("2️⃣  COMMANDES CRÉÉES DEPUIS LE PDV (dernières 24h)")
        print("-" * 80)
        
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_pdv_orders = Order.query.filter(
            Order.created_at >= yesterday,
            Order.delivery_option == 'delivery',
            Order.customer_address.isnot(None)
        ).order_by(Order.created_at.desc()).all()
        
        print(f"   Total trouvé: {len(recent_pdv_orders)}")
        print()
        
        if recent_pdv_orders:
            for order in recent_pdv_orders[:5]:  # Afficher les 5 premières
                print(f"   📦 Commande #{order.id}")
                print(f"      Type: {order.order_type} ({order.get_order_type_display()})")
                print(f"      Client: {order.customer_name or 'N/A'}")
                print(f"      Adresse: {order.customer_address or 'N/A'}")
                print(f"      get_delivery_address(): {order.get_delivery_address() or 'N/A'}")
                print(f"      Prix livraison: {order.delivery_cost or 0} DA")
                print(f"      Statut: {order.status}")
                print(f"      Créée le: {order.created_at}")
                print()
                
                # Vérifier si elle apparaît dans la section "Prêt à Livrer"
                if order.status == 'ready_at_shop':
                    print(f"      ✅ Apparaît dans 'Prêt à Livrer'")
                else:
                    print(f"      ⚠️  N'apparaît PAS dans 'Prêt à Livrer' (statut: {order.status})")
                print()
        else:
            print("   ⚠️  Aucune commande de livraison créée récemment")
            print()
        
        # 3. Résumé et recommandations
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print()
        print("✅ Le dashboard shop devrait afficher:")
        print("   - L'adresse via order.get_delivery_address()")
        print("   - Le prix de livraison via order.delivery_cost")
        print()
        print("✅ Les commandes créées depuis le PDV avec le bouton 'Livraison':")
        print("   - Sont maintenant order_type='customer_order' (après correction)")
        print("   - Ont status='ready_at_shop'")
        print("   - Ont delivery_option='delivery'")
        print("   - Sont incluses dans la requête orders_ready_delivery")
        print()
        print("💡 Pour tester:")
        print("   1. Créer une commande de livraison depuis le PDV")
        print("   2. Vérifier qu'elle apparaît dans la section 'Prêt à Livrer'")
        print("   3. Vérifier que l'adresse et le prix de livraison s'affichent")

if __name__ == '__main__':
    verifier_affichage_dashboard_shop()

