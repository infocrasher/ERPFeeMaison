#!/usr/bin/env python3
"""
Script de test pour vérifier le calcul du CA avec les dettes livreurs
"""
import sys
import os
from datetime import date, datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order, DeliveryDebt
from app.reports.services import _compute_revenue, _get_order_revenue_date

def test_ca_dette_livreur():
    """Test le calcul du CA pour une dette livreur"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("TEST CALCUL CA - DETTE LIVREUR")
        print("=" * 80)
        print()
        
        # Date de la dette (05/12/2025)
        date_dette = date(2025, 12, 5)
        date_aujourdhui = date.today()
        
        print(f"📅 Date de la dette : {date_dette}")
        print(f"📅 Date d'aujourd'hui : {date_aujourdhui}")
        print()
        
        # Trouver toutes les dettes créées le 05/12/2025
        dettes = DeliveryDebt.query.filter(
            db.func.date(DeliveryDebt.created_at) == date_dette
        ).all()
        
        if not dettes:
            print("❌ Aucune dette trouvée pour le 05/12/2025")
            return
        
        print(f"📋 Dettes trouvées le 05/12/2025 : {len(dettes)}")
        print()
        
        for debt in dettes:
            order = debt.order
            print(f"🔍 DETTE #{debt.id}")
            print(f"   Commande : #{order.id}")
            print(f"   Montant : {debt.amount} DA")
            print(f"   Statut paiement : {'✅ Payée' if debt.paid else '❌ Non payée'}")
            print(f"   Date création dette : {debt.created_at.date()}")
            
            if order.payment_paid_at:
                print(f"   Date paiement commande : {order.payment_paid_at.date()}")
            else:
                print(f"   Date paiement commande : Non payée")
            
            print(f"   Date création commande : {order.created_at.date()}")
            
            # Calculer la date de revenu
            revenue_date = _get_order_revenue_date(order)
            print(f"   📊 DATE DE REVENU CALCULÉE : {revenue_date}")
            
            if debt.paid:
                print(f"   ✅ Dette payée le : {debt.paid_at.date() if debt.paid_at else 'N/A'}")
            else:
                print(f"   ⚠️  Dette NON payée")
            
            print()
        
        # Calculer le CA pour le 05/12/2025 (date de la dette)
        ca_date_dette = _compute_revenue(report_date=date_dette)
        print(f"💰 CA calculé pour le {date_dette} : {ca_date_dette:,.2f} DA")
        
        # Calculer le CA pour aujourd'hui
        ca_aujourdhui = _compute_revenue(report_date=date_aujourdhui)
        print(f"💰 CA calculé pour aujourd'hui ({date_aujourdhui}) : {ca_aujourdhui:,.2f} DA")
        print()
        
        # DÉTAIL : Vérifier toutes les commandes du 05/12 pour comprendre le CA
        print("=" * 80)
        print("📊 DÉTAIL DU CA DU 05/12/2025")
        print("=" * 80)
        print()
        
        # Récupérer toutes les commandes qui contribuent au CA du 05/12
        all_orders_05_12 = Order.query.filter(
            Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
        ).all()
        
        orders_contributing = []
        for order in all_orders_05_12:
            revenue_date = _get_order_revenue_date(order)
            if revenue_date == date_dette:
                order_amount = sum(
                    float(item.quantity or 0) * float(item.unit_price or 0)
                    for item in order.items
                )
                orders_contributing.append({
                    'order': order,
                    'amount': order_amount,
                    'revenue_date': revenue_date
                })
        
        print(f"📋 Commandes contribuant au CA du {date_dette} : {len(orders_contributing)}")
        print()
        
        total_verif = 0.0
        for item in orders_contributing:
            order = item['order']
            amount = item['amount']
            total_verif += amount
            
            # Vérifier si c'est une commande avec dette
            debt = DeliveryDebt.query.filter_by(order_id=order.id).first()
            debt_info = ""
            if debt:
                debt_info = f" (Dette #{debt.id}: {debt.amount} DA, {'Payée' if debt.paid else 'Non payée'})"
            
            print(f"   Commande #{order.id}: {amount:,.2f} DA{debt_info}")
            print(f"      - Date création: {order.created_at.date()}")
            print(f"      - Date livraison (due_date): {order.due_date.date() if order.due_date else 'N/A'}")
            if debt:
                print(f"      - Date création dette: {debt.created_at.date() if debt.created_at else 'N/A'}")
            print(f"      - Date revenu calculée: {item['revenue_date']}")
            print()
        
        print(f"💰 Total vérifié: {total_verif:,.2f} DA")
        print(f"💰 CA calculé: {ca_date_dette:,.2f} DA")
        print(f"   {'✅ Cohérent' if abs(total_verif - ca_date_dette) < 0.01 else '❌ Incohérent'}")
        print()
        
        # Vérifier les dettes non payées
        dettes_non_payees = [d for d in dettes if not d.paid]
        if dettes_non_payees:
            print("=" * 80)
            print("📝 DETTES NON PAYÉES (devraient être dans le CA du 05/12)")
            print("=" * 80)
            for debt in dettes_non_payees:
                revenue_date = _get_order_revenue_date(debt.order)
                print(f"   Dette #{debt.id} - Commande #{debt.order_id} : {debt.amount} DA")
                print(f"   → Date revenu : {revenue_date} {'✅' if revenue_date == date_dette else '❌'}")
            print()
        
        # Vérifier les dettes payées
        dettes_payees = [d for d in dettes if d.paid]
        if dettes_payees:
            print("=" * 80)
            print("✅ DETTES PAYÉES (devraient être dans le CA de la date de livraison, pas paiement)")
            print("=" * 80)
            for debt in dettes_payees:
                revenue_date = _get_order_revenue_date(debt.order)
                print(f"   Dette #{debt.id} - Commande #{debt.order_id} : {debt.amount} DA")
                print(f"   → Date paiement : {debt.paid_at.date() if debt.paid_at else 'N/A'}")
                # La date de revenu devrait être la date de livraison (création dette), pas la date de paiement
                expected_date = debt.created_at.date() if debt.created_at else None
                print(f"   → Date revenu : {revenue_date} {'✅' if revenue_date == expected_date else '❌'}")
                print(f"   → Attendu (date livraison) : {expected_date}")
            print()
        
        print("=" * 80)
        print("💡 INSTRUCTIONS POUR TESTER")
        print("=" * 80)
        print()
        print("1. Si vous avez une dette NON PAYÉE du 05/12/2025 :")
        print("   → Le CA du 05/12 devrait inclure cette dette")
        print("   → Le CA d'aujourd'hui ne devrait PAS l'inclure")
        print()
        print("2. Après avoir encaissé la dette :")
        print("   → Le CA du 05/12 devrait RESTER IDENTIQUE (date de livraison)")
        print("   → Le CA d'aujourd'hui ne devrait PAS changer (CA à date livraison)")
        print()
        print("3. Relancer ce script après l'encaissement pour vérifier")
        print()

if __name__ == '__main__':
    test_ca_dette_livreur()

