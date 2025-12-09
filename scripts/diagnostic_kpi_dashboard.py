#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les KPI du dashboard pour une date spécifique
Identifie les incohérences dans les calculs
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product
from app.sales.models import CashMovement
from sqlalchemy import func, and_, or_

def diagnostic_kpi_dashboard(target_date_str):
    """
    Analyse les KPI du dashboard pour une date spécifique
    """
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            print("   Format attendu : YYYY-MM-DD")
            return
        
        print("=" * 80)
        print("DIAGNOSTIC KPI DASHBOARD")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # ========================================================================
        # 1. ANALYSE DES COMMANDES (Order)
        # ========================================================================
        print("=" * 80)
        print("1️⃣  COMMANDES (Order)")
        print("=" * 80)
        print()
        
        # Toutes les commandes du jour
        all_orders = Order.query.filter(
            func.date(Order.created_at) == target_date
        ).all()
        
        print(f"📋 Total commandes créées : {len(all_orders)}")
        
        # Commandes par statut
        orders_by_status = {}
        for order in all_orders:
            status = order.status or 'unknown'
            orders_by_status[status] = orders_by_status.get(status, 0) + 1
        
        print("   Répartition par statut :")
        for status, count in sorted(orders_by_status.items()):
            print(f"      - {status}: {count}")
        print()
        
        # Commandes complétées/livrées (utilisées pour le CA)
        completed_orders = Order.query.filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered'])
        ).all()
        
        print(f"✅ Commandes complétées/livrées : {len(completed_orders)}")
        
        # CA depuis OrderItem
        revenue_from_orders = db.session.query(
            func.sum(func.coalesce(OrderItem.quantity, 0) * func.coalesce(OrderItem.unit_price, 0))
        ).select_from(OrderItem).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered'])
        ).scalar() or 0
        
        print(f"💰 CA calculé depuis OrderItem : {float(revenue_from_orders):,.2f} DA")
        print()
        
        # Détail des commandes complétées
        if completed_orders:
            print("   Détail des commandes complétées :")
            total_manual = 0
            for order in completed_orders[:10]:  # Limiter à 10
                order_items = order.items.all() if hasattr(order.items, 'all') else []
                order_total = sum(float(item.quantity or 0) * float(item.unit_price or 0) for item in order_items)
                total_manual += order_total
                print(f"      - Order #{order.id}: {order_total:,.2f} DA ({order.status})")
            if len(completed_orders) > 10:
                print(f"      ... et {len(completed_orders) - 10} autres")
            print(f"   Total manuel (10 premières) : {total_manual:,.2f} DA")
            print()
        
        # ========================================================================
        # 2. ANALYSE DES VENTES PDV (Sale)
        # ========================================================================
        print("=" * 80)
        print("2️⃣  VENTES PDV (Sale)")
        print("=" * 80)
        print()
        
        # Vérifier si le modèle Sale existe
        try:
            sales = Sale.query.filter(
                func.date(Sale.created_at) == target_date
            ).all()
            
            print(f"🛒 Total ventes PDV : {len(sales)}")
            
            if sales:
                # CA depuis Sale
                revenue_from_sales = db.session.query(
                    func.sum(func.coalesce(SaleItem.quantity, 0) * func.coalesce(SaleItem.unit_price, 0))
                ).select_from(SaleItem).join(
                    Sale, Sale.id == SaleItem.sale_id
                ).filter(
                    func.date(Sale.created_at) == target_date
                ).scalar() or 0
                
                print(f"💰 CA calculé depuis SaleItem : {float(revenue_from_sales):,.2f} DA")
                print()
                
                # Détail des ventes
                print("   Détail des ventes PDV :")
                total_manual_sales = 0
                for sale in sales[:10]:  # Limiter à 10
                    sale_items = sale.items.all() if hasattr(sale.items, 'all') else []
                    sale_total = sum(float(item.quantity or 0) * float(item.unit_price or 0) for item in sale_items)
                    total_manual_sales += sale_total
                    print(f"      - Sale #{sale.id}: {sale_total:,.2f} DA")
                if len(sales) > 10:
                    print(f"      ... et {len(sales) - 10} autres")
                print(f"   Total manuel (10 premières) : {total_manual_sales:,.2f} DA")
                print()
            else:
                print("   Aucune vente PDV trouvée")
                print()
        except Exception as e:
            print(f"⚠️  Erreur lors de l'analyse des ventes PDV : {e}")
            print("   (Le modèle Sale n'existe peut-être pas)")
            print()
        
        # ========================================================================
        # 3. ANALYSE DES MOUVEMENTS DE CAISSE
        # ========================================================================
        print("=" * 80)
        print("3️⃣  MOUVEMENTS DE CAISSE (CashMovement)")
        print("=" * 80)
        print()
        
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == target_date
        ).all()
        
        print(f"💵 Total mouvements de caisse : {len(movements)}")
        
        if movements:
            entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
            exit_types = {'sortie', 'retrait', 'frais', 'paiement'}
            
            cash_in = 0.0
            cash_out = 0.0
            
            for movement in movements:
                movement_type = (movement.type or '').lower()
                amount = float(movement.amount or 0)
                if movement_type in exit_types:
                    cash_out += amount
                elif movement_type in entry_types or amount >= 0:
                    cash_in += amount
                else:
                    cash_out += abs(amount)
            
            print(f"   Entrées : {cash_in:,.2f} DA")
            print(f"   Sorties : {cash_out:,.2f} DA")
            print(f"   Net : {cash_in - cash_out:,.2f} DA")
            print()
            
            # Ventes dans les mouvements
            sales_movements = [m for m in movements if (m.type or '').lower() == 'vente']
            if sales_movements:
                sales_total = sum(float(m.amount or 0) for m in sales_movements)
                print(f"   💰 Ventes (type='vente') : {sales_total:,.2f} DA ({len(sales_movements)} mouvements)")
                print()
        
        # ========================================================================
        # 4. COMPARAISON AVEC LE SERVICE DASHBOARD
        # ========================================================================
        print("=" * 80)
        print("4️⃣  COMPARAISON AVEC SERVICE DASHBOARD")
        print("=" * 80)
        print()
        
        try:
            from app.reports.services import DailySalesReportService, _compute_revenue
            
            # CA calculé par le service
            service_revenue = _compute_revenue(report_date=target_date)
            print(f"📊 CA calculé par _compute_revenue() : {service_revenue:,.2f} DA")
            
            # Rapport complet
            report = DailySalesReportService.generate(target_date)
            report_revenue = report.get('total_revenue', 0.0)
            print(f"📊 CA depuis DailySalesReportService : {report_revenue:,.2f} DA")
            print(f"📊 Nombre de transactions : {report.get('total_transactions', 0)}")
            print(f"📊 Panier moyen : {report.get('average_basket', 0.0):,.2f} DA")
            print()
            
            # Vérifier les incohérences
            if abs(service_revenue - report_revenue) > 0.01:
                print(f"⚠️  INCOHÉRENCE DÉTECTÉE !")
                print(f"   Différence : {abs(service_revenue - report_revenue):,.2f} DA")
                print()
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul par le service : {e}")
            import traceback
            traceback.print_exc()
            print()
        
        # ========================================================================
        # 5. RÉSUMÉ ET RECOMMANDATIONS
        # ========================================================================
        print("=" * 80)
        print("5️⃣  RÉSUMÉ")
        print("=" * 80)
        print()
        
        print(f"📅 Date : {target_date.strftime('%d/%m/%Y')}")
        print(f"📋 Commandes (Order) : {len(all_orders)} total, {len(completed_orders)} complétées")
        print(f"💰 CA depuis OrderItem (completed/delivered) : {float(revenue_from_orders):,.2f} DA")
        
        if pdv_orders:
            pdv_completed = [o for o in pdv_orders if o.status in ['completed', 'delivered']]
            print(f"🛒 Ventes PDV : {len(pdv_orders)} total, {len(pdv_completed)} complétées")
            if len(pdv_completed) != len(pdv_orders):
                print(f"   ⚠️  {len(pdv_orders) - len(pdv_completed)} ventes PDV non complétées (exclues du CA)")
        
        print()
        print("💡 VÉRIFICATIONS À FAIRE :")
        print("   1. Les ventes PDV sont-elles incluses dans le CA ?")
        print("   2. Les commandes avec d'autres statuts sont-elles exclues ?")
        print("   3. Y a-t-il des doublons dans les calculs ?")
        print("   4. Les remises sont-elles correctement appliquées ?")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/diagnostic_kpi_dashboard.py YYYY-MM-DD")
        print("Exemple: python3 scripts/diagnostic_kpi_dashboard.py 2025-12-08")
        sys.exit(1)
    
    diagnostic_kpi_dashboard(sys.argv[1])

