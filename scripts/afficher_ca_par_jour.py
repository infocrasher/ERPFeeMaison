#!/usr/bin/env python3
"""
Script pour afficher le CA jour par jour du 01/12 au 10/12
"""
import sys
import os
from datetime import date, timedelta

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order, DeliveryDebt
from app.reports.services import _compute_revenue, _get_order_revenue_date

def afficher_ca_par_jour():
    """Affiche le CA jour par jour du 01/12 au 10/12"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("CA PAR JOUR - DU 01/12 AU 10/12/2025")
        print("=" * 80)
        print()
        
        # Dates du 01/12 au 10/12
        start_date = date(2025, 12, 1)
        end_date = date(2025, 12, 10)
        
        print(f"📅 Période : {start_date} → {end_date}")
        print()
        
        # Tableau des CA
        print(f"{'Date':<12} {'CA (DA)':<15} {'Détail':<50}")
        print("-" * 80)
        
        total_ca = 0.0
        
        for i in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=i)
            ca = _compute_revenue(report_date=current_date)
            total_ca += ca
            
            # Détail des commandes de ce jour
            all_orders = Order.query.filter(
                Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
            ).all()
            
            orders_today = []
            for order in all_orders:
                revenue_date = _get_order_revenue_date(order)
                if revenue_date == current_date:
                    order_amount = sum(
                        float(item.quantity or 0) * float(item.unit_price or 0)
                        for item in order.items
                    )
                    debt = DeliveryDebt.query.filter_by(order_id=order.id).first()
                    order_type = "Dette livreur" if debt else "Vente directe"
                    orders_today.append({
                        'id': order.id,
                        'amount': order_amount,
                        'type': order_type
                    })
            
            # Format détail
            if orders_today:
                detail = f"{len(orders_today)} commande(s)"
                if len(orders_today) <= 3:
                    detail_parts = [f"#{o['id']}: {o['amount']:.0f}DA" for o in orders_today]
                    detail = ", ".join(detail_parts)
            else:
                detail = "Aucune vente"
            
            # Format CA avec couleur
            ca_str = f"{ca:,.2f}"
            if ca > 0:
                ca_str = f"✅ {ca_str}"
            else:
                ca_str = f"   {ca_str}"
            
            print(f"{current_date.strftime('%d/%m/%Y'):<12} {ca_str:<15} {detail:<50}")
        
        print("-" * 80)
        print(f"{'TOTAL':<12} {total_ca:,.2f} DA")
        print()
        
        # Détail par type de vente
        print("=" * 80)
        print("📊 RÉPARTITION PAR TYPE")
        print("=" * 80)
        print()
        
        ventes_directes = 0.0
        dettes_livreur = 0.0
        
        for i in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=i)
            all_orders = Order.query.filter(
                Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
            ).all()
            
            for order in all_orders:
                revenue_date = _get_order_revenue_date(order)
                if revenue_date == current_date:
                    order_amount = sum(
                        float(item.quantity or 0) * float(item.unit_price or 0)
                        for item in order.items
                    )
                    debt = DeliveryDebt.query.filter_by(order_id=order.id).first()
                    if debt:
                        dettes_livreur += order_amount
                    else:
                        ventes_directes += order_amount
        
        print(f"💰 Ventes directes (payées immédiatement) : {ventes_directes:,.2f} DA")
        print(f"💳 Dettes livreurs (payées plus tard)     : {dettes_livreur:,.2f} DA")
        print(f"📊 TOTAL                                  : {total_ca:,.2f} DA")
        print()

if __name__ == '__main__':
    afficher_ca_par_jour()

