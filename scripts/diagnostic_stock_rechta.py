#!/usr/bin/env python3
"""
Script de diagnostic pour analyser le problème de stock de "Rechta PF"
Recherche quand et pourquoi le stock a atteint 9998 pièces
"""

import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product, Order, OrderItem
from app.stock.models import StockMovement, StockMovementType, StockLocationType
from extensions import db
from sqlalchemy import func, desc

def analyze_rechta_stock():
    """Analyse complète du stock de Rechta PF"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("DIAGNOSTIC STOCK - RECHTA PF")
        print("=" * 80)
        print()
        
        # 1. Trouver le produit
        product = Product.query.filter(
            Product.name.ilike('%rechta%')
        ).first()
        
        if not product:
            print("❌ Produit 'Rechta PF' non trouvé")
            print("\nProduits contenant 'rechta':")
            products = Product.query.filter(Product.name.ilike('%rechta%')).all()
            for p in products:
                print(f"  - {p.name} (ID: {p.id})")
            return
        
        print(f"✅ Produit trouvé: {product.name} (ID: {product.id})")
        print(f"   Stock actuel comptoir: {product.stock_comptoir}")
        print(f"   Stock total: {product.total_stock_all_locations}")
        print(f"   Dernière mise à jour: {product.last_stock_update}")
        print()
        
        # 2. Analyser les mouvements de stock
        print("=" * 80)
        print("HISTORIQUE DES MOUVEMENTS DE STOCK")
        print("=" * 80)
        print()
        
        movements = StockMovement.query.filter(
            StockMovement.product_id == product.id,
            StockMovement.stock_location == StockLocationType.COMPTOIR
        ).order_by(desc(StockMovement.created_at)).limit(50).all()
        
        if not movements:
            print("⚠️  Aucun mouvement de stock trouvé dans stock_movements")
            print("   (Les mouvements peuvent ne pas être tracés si créés avant l'implémentation)")
        else:
            print(f"📊 {len(movements)} derniers mouvements trouvés:\n")
            print(f"{'Date':<20} {'Type':<20} {'Qté':<12} {'Avant':<12} {'Après':<12} {'Raison':<30}")
            print("-" * 120)
            
            for mvt in movements:
                date_str = mvt.created_at.strftime('%Y-%m-%d %H:%M') if mvt.created_at else 'N/A'
                mvt_type = mvt.movement_type.value if mvt.movement_type else 'N/A'
                qty = f"{mvt.quantity:+.2f}"
                before = f"{mvt.stock_before:.2f}" if mvt.stock_before else 'N/A'
                after = f"{mvt.stock_after:.2f}" if mvt.stock_after else 'N/A'
                reason = (mvt.reason or '')[:28]
                
                print(f"{date_str:<20} {mvt_type:<20} {qty:<12} {before:<12} {after:<12} {reason:<30}")
        
        print()
        
        # 3. Analyser les commandes qui ont modifié ce produit
        print("=" * 80)
        print("COMMANDES CONTENANT RECHTA PF")
        print("=" * 80)
        print()
        
        order_items = OrderItem.query.filter(
            OrderItem.product_id == product.id
        ).order_by(desc(OrderItem.order_id)).limit(50).all()
        
        if order_items:
            print(f"📦 {len(order_items)} commandes trouvées:\n")
            print(f"{'Commande':<12} {'Type':<20} {'Statut':<20} {'Qté':<12} {'Date':<20} {'Créée par':<20}")
            print("-" * 120)
            
            for item in order_items:
                order = item.order
                order_type = order.order_type if order else 'N/A'
                status = order.status if order else 'N/A'
                qty = f"{item.quantity:.2f}"
                date_str = order.created_at.strftime('%Y-%m-%d %H:%M') if order and order.created_at else 'N/A'
                user_name = order.user.username if order and order.user else 'N/A'
                
                print(f"#{order.id:<11} {order_type:<20} {status:<20} {qty:<12} {date_str:<20} {user_name:<20}")
        else:
            print("⚠️  Aucune commande trouvée")
        
        print()
        
        # 4. Rechercher les ajustements manuels suspects
        print("=" * 80)
        print("AJUSTEMENTS MANUELS SUSPECTS")
        print("=" * 80)
        print()
        
        suspicious_movements = StockMovement.query.filter(
            StockMovement.product_id == product.id,
            StockMovement.stock_location == StockLocationType.COMPTOIR,
            StockMovement.movement_type.in_([
                StockMovementType.AJUSTEMENT_POSITIF,
                StockMovementType.AJUSTEMENT_NEGATIF,
                StockMovementType.INVENTAIRE
            ])
        ).order_by(desc(StockMovement.created_at)).all()
        
        if suspicious_movements:
            print(f"🔍 {len(suspicious_movements)} ajustements manuels trouvés:\n")
            for mvt in suspicious_movements:
                date_str = mvt.created_at.strftime('%Y-%m-%d %H:%M') if mvt.created_at else 'N/A'
                print(f"  Date: {date_str}")
                print(f"  Type: {mvt.movement_type.value}")
                print(f"  Quantité: {mvt.quantity:+.2f}")
                print(f"  Stock avant: {mvt.stock_before:.2f}")
                print(f"  Stock après: {mvt.stock_after:.2f}")
                print(f"  Raison: {mvt.reason or 'N/A'}")
                print(f"  Utilisateur: {mvt.user.username if mvt.user else 'N/A'}")
                print()
        else:
            print("⚠️  Aucun ajustement manuel trouvé dans stock_movements")
        
        # 5. Rechercher les grandes incrémentations
        print("=" * 80)
        print("GRANDES INCRÉMENTATIONS (>100 pièces)")
        print("=" * 80)
        print()
        
        large_increments = StockMovement.query.filter(
            StockMovement.product_id == product.id,
            StockMovement.stock_location == StockLocationType.COMPTOIR,
            StockMovement.quantity > 100
        ).order_by(desc(StockMovement.quantity)).all()
        
        if large_increments:
            print(f"⚠️  {len(large_increments)} grandes incrémentations trouvées:\n")
            for mvt in large_increments:
                date_str = mvt.created_at.strftime('%Y-%m-%d %H:%M') if mvt.created_at else 'N/A'
                print(f"  Date: {date_str}")
                print(f"  Type: {mvt.movement_type.value}")
                print(f"  Quantité: {mvt.quantity:+.2f}")
                print(f"  Stock avant: {mvt.stock_before:.2f}")
                print(f"  Stock après: {mvt.stock_after:.2f}")
                print(f"  Commande: #{mvt.order_id if mvt.order_id else 'N/A'}")
                print(f"  Raison: {mvt.reason or 'N/A'}")
                print()
        else:
            print("✅ Aucune grande incrémentation trouvée dans stock_movements")
        
        # 6. Analyser les ordres de production
        print("=" * 80)
        print("ORDres DE PRODUCTION (counter_production_request)")
        print("=" * 80)
        print()
        
        production_orders = Order.query.join(OrderItem).filter(
            OrderItem.product_id == product.id,
            Order.order_type == 'counter_production_request'
        ).order_by(desc(Order.created_at)).limit(20).all()
        
        if production_orders:
            print(f"🏭 {len(production_orders)} ordres de production trouvés:\n")
            for order in production_orders:
                item = next((i for i in order.items if i.product_id == product.id), None)
                if item:
                    date_str = order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A'
                    print(f"  Commande #{order.id} - {date_str}")
                    print(f"    Statut: {order.status}")
                    print(f"    Quantité: {item.quantity:.2f}")
                    print(f"    Date due: {order.due_date.strftime('%Y-%m-%d %H:%M') if order.due_date else 'N/A'}")
                    print()
        else:
            print("⚠️  Aucun ordre de production trouvé")
        
        # 7. Vérifier les ventes (décrémentations)
        print("=" * 80)
        print("VENTES (DÉCRÉMENTATIONS)")
        print("=" * 80)
        print()
        
        sales = StockMovement.query.filter(
            StockMovement.product_id == product.id,
            StockMovement.stock_location == StockLocationType.COMPTOIR,
            StockMovement.movement_type == StockMovementType.VENTE,
            StockMovement.quantity < 0
        ).order_by(desc(StockMovement.created_at)).limit(20).all()
        
        if sales:
            print(f"💰 {len(sales)} ventes trouvées:\n")
            total_sold = sum(abs(s.quantity) for s in sales)
            print(f"  Total vendu (sur ces {len(sales)} ventes): {total_sold:.2f} pièces\n")
        else:
            print("⚠️  Aucune vente trouvée dans stock_movements")
        
        # 8. Résumé et recommandations
        print("=" * 80)
        print("RÉSUMÉ ET RECOMMANDATIONS")
        print("=" * 80)
        print()
        print(f"Stock actuel: {product.stock_comptoir:.2f} pièces")
        print()
        
        if product.stock_comptoir > 1000:
            print("⚠️  ATTENTION: Stock anormalement élevé (>1000 pièces)")
            print("   Causes possibles:")
            print("   1. Erreur de saisie lors d'un ajustement manuel")
            print("   2. Bug dans l'incrémentation du stock (boucle, multiplication)")
            print("   3. Ordre de production avec quantité erronée")
            print("   4. Problème de conversion d'unités")
            print()
            print("   Actions recommandées:")
            print("   1. Vérifier les logs de l'application pour cette période")
            print("   2. Vérifier les ajustements manuels récents")
            print("   3. Vérifier les ordres de production récents")
            print("   4. Effectuer un inventaire physique")
            print("   5. Corriger le stock manuellement si nécessaire")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    analyze_rechta_stock()

