#!/usr/bin/env python3
"""
Script de vérification des valeurs affichées sur le dashboard
Compare les calculs du dashboard avec les données réelles de la base
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product
from sqlalchemy import func, case, and_, or_
from app.employees.models import Employee, AttendanceRecord
from app.sales.models import CashMovement
from app.purchases.models import Purchase
from app.reports.kpi_service import RealKpiService

def parse_date(date_str):
    """Parse une date depuis différents formats"""
    if not date_str:
        return date.today()
    
    # Format YYYY-MM-DD
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        pass
    
    # Format DD/MM/YYYY
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except ValueError:
        pass
    
    # Format DD-MM-YYYY
    try:
        return datetime.strptime(date_str, '%d-%m-%Y').date()
    except ValueError:
        pass
    
    raise ValueError(f"Format de date non reconnu: {date_str}")

def format_currency(value):
    """Formate une valeur monétaire"""
    return f"{float(value):,.2f} DA"

def format_number(value):
    """Formate un nombre"""
    return f"{int(value):,}"

def verifier_commandes_pos(target_date):
    """Vérifie les commandes POS (in_store) créées ce jour"""
    print("\n" + "="*80)
    print("📊 VÉRIFICATION COMMANDES POS (Ventes au Comptoir)")
    print("="*80)
    
    # Calcul du dashboard (RealKpiService)
    pos_orders = Order.query.filter(
        Order.order_type == 'in_store',
        func.date(Order.created_at) == target_date
    ).all()
    
    pos_count = len(pos_orders)
    pos_revenue = sum(float(o.total_amount or 0) for o in pos_orders)
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"✅ Nombre de commandes POS: {pos_count}")
    print(f"💰 CA POS: {format_currency(pos_revenue)}")
    
    if pos_count > 0:
        print(f"\n📋 Détail des commandes POS:")
        print("-" * 80)
        print(f"{'ID':<6} {'Statut':<20} {'Montant':<15} {'Créée à':<20} {'Client':<30}")
        print("-" * 80)
        
        for order in sorted(pos_orders, key=lambda x: x.created_at):
            created_str = order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else 'N/A'
            client = order.customer_name or 'Sans nom'
            print(f"{order.id:<6} {order.status:<20} {format_currency(order.total_amount):<15} {created_str:<20} {client[:30]:<30}")
        
        # Vérifier les statuts
        status_count = {}
        for order in pos_orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        print(f"\n📊 Répartition par statut:")
        for status, count in sorted(status_count.items()):
            print(f"  - {status}: {count}")
    else:
        print("⚠️  Aucune commande POS trouvée pour cette date")
    
    return {
        'count': pos_count,
        'revenue': pos_revenue,
        'orders': pos_orders
    }

def verifier_commandes_livrees(target_date):
    """Vérifie les commandes livrées (non-POS) avec due_date ce jour"""
    print("\n" + "="*80)
    print("🚚 VÉRIFICATION COMMANDES LIVRÉES (Shop)")
    print("="*80)
    
    # Calcul du dashboard (RealKpiService)
    shop_orders = Order.query.filter(
        Order.order_type != 'in_store',
        Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
        func.date(Order.due_date) == target_date
    ).all()
    
    shop_count = len(shop_orders)
    shop_revenue = sum(float(o.total_amount or 0) for o in shop_orders)
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"✅ Nombre de commandes livrées: {shop_count}")
    print(f"💰 CA Commandes: {format_currency(shop_revenue)}")
    
    if shop_count > 0:
        print(f"\n📋 Détail des commandes livrées:")
        print("-" * 80)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Due Date':<20} {'Client':<30}")
        print("-" * 80)
        
        for order in sorted(shop_orders, key=lambda x: x.due_date):
            due_str = order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            client = order.customer_name or 'Sans nom'
            order_type_display = order.get_order_type_display()
            print(f"{order.id:<6} {order_type_display[:25]:<25} {order.status:<20} {format_currency(order.total_amount):<15} {due_str:<20} {client[:30]:<30}")
        
        # Répartition par type
        type_count = {}
        for order in shop_orders:
            order_type = order.get_order_type_display()
            type_count[order_type] = type_count.get(order_type, 0) + 1
        
        print(f"\n📊 Répartition par type:")
        for order_type, count in sorted(type_count.items()):
            print(f"  - {order_type}: {count}")
    else:
        print("⚠️  Aucune commande livrée trouvée pour cette date")
    
    return {
        'count': shop_count,
        'revenue': shop_revenue,
        'orders': shop_orders
    }

def verifier_dette_livreur(target_date):
    """Vérifie la dette livreur (reste à payer sur commandes livrées)"""
    print("\n" + "="*80)
    print("💳 VÉRIFICATION DETTE LIVREUR")
    print("="*80)
    
    shop_orders = Order.query.filter(
        Order.order_type != 'in_store',
        Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
        func.date(Order.due_date) == target_date
    ).all()
    
    total_debt = 0.0
    orders_with_debt = []
    
    for order in shop_orders:
        debt = float(order.total_amount or 0) - float(order.amount_paid or 0)
        if debt > 0:
            total_debt += debt
            orders_with_debt.append({
                'id': order.id,
                'total': float(order.total_amount or 0),
                'paid': float(order.amount_paid or 0),
                'debt': debt,
                'client': order.customer_name or 'Sans nom'
            })
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"💰 Dette totale: {format_currency(total_debt)}")
    print(f"📊 Nombre de commandes avec dette: {len(orders_with_debt)}")
    
    if orders_with_debt:
        print(f"\n📋 Détail des dettes:")
        print("-" * 80)
        print(f"{'ID':<6} {'Montant Total':<15} {'Payé':<15} {'Dette':<15} {'Client':<30}")
        print("-" * 80)
        for o in sorted(orders_with_debt, key=lambda x: x['debt'], reverse=True):
            print(f"{o['id']:<6} {format_currency(o['total']):<15} {format_currency(o['paid']):<15} {format_currency(o['debt']):<15} {o['client'][:30]:<30}")
    
    return total_debt

def verifier_cogs(target_date):
    """Vérifie le COGS (Coût des marchandises vendues)"""
    print("\n" + "="*80)
    print("🔧 VÉRIFICATION COGS (Coût des Marchandises Vendues)")
    print("="*80)
    
    # Récupérer les IDs des commandes concernées
    pos_order_ids = [o.id for o in Order.query.filter(
        Order.order_type == 'in_store',
        func.date(Order.created_at) == target_date
    ).all()]
    
    shop_order_ids = [o.id for o in Order.query.filter(
        Order.order_type != 'in_store',
        Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
        func.date(Order.due_date) == target_date
    ).all()]
    
    all_order_ids = pos_order_ids + shop_order_ids
    
    if not all_order_ids:
        print("⚠️  Aucune commande trouvée, COGS = 0")
        return {'ingredients': 0.0, 'labor': 0.0, 'total': 0.0}
    
    # Calcul COGS ingrédients
    cogs_query = db.session.query(
        func.sum(OrderItem.quantity * Product.cost_price)
    ).join(Product, OrderItem.product_id == Product.id)\
     .filter(OrderItem.order_id.in_(all_order_ids))
    
    cogs_ingredients = float(cogs_query.scalar() or 0.0)
    
    # Calcul Main d'œuvre
    daily_attendance = AttendanceRecord.get_daily_summary(target_date)
    labor_cost = 0.0
    
    for emp_data in daily_attendance.values():
        emp = emp_data['employee']
        hours = float(emp_data['total_hours'] or 0)
        
        if not emp or hours <= 0:
            continue
        
        if emp.hourly_rate and emp.hourly_rate > 0:
            rate = float(emp.hourly_rate)
        elif emp.salaire_fixe and emp.salaire_fixe > 0:
            rate = float(emp.salaire_fixe) / 208.0
        else:
            rate = 0.0
        
        labor_cost += (hours * rate)
    
    total_cogs = cogs_ingredients + labor_cost
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"💰 COGS Ingrédients: {format_currency(cogs_ingredients)}")
    print(f"👥 COGS Main d'œuvre: {format_currency(labor_cost)}")
    print(f"📊 COGS Total: {format_currency(total_cogs)}")
    
    return {
        'ingredients': cogs_ingredients,
        'labor': labor_cost,
        'total': total_cogs
    }

def verifier_toutes_commandes(target_date):
    """Vérifie TOUTES les commandes créées ce jour (pour comparaison)"""
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION TOUTES LES COMMANDES CRÉÉES CE JOUR")
    print("="*80)
    
    all_orders = Order.query.filter(
        func.date(Order.created_at) == target_date
    ).all()
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"📊 Total commandes créées: {len(all_orders)}")
    
    if all_orders:
        print(f"\n📋 Détail complet:")
        print("-" * 100)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Créée à':<20} {'Due Date':<20}")
        print("-" * 100)
        
        for order in sorted(all_orders, key=lambda x: x.created_at):
            created_str = order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else 'N/A'
            due_str = order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            order_type_display = order.get_order_type_display()
            print(f"{order.id:<6} {order_type_display[:25]:<25} {order.status:<20} {format_currency(order.total_amount):<15} {created_str:<20} {due_str:<20}")
        
        # Répartition par type
        type_count = {}
        for order in all_orders:
            order_type = order.get_order_type_display()
            type_count[order_type] = type_count.get(order_type, 0) + 1
        
        print(f"\n📊 Répartition par type:")
        for order_type, count in sorted(type_count.items()):
            print(f"  - {order_type}: {count}")
        
        # Répartition par statut
        status_count = {}
        for order in all_orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        print(f"\n📊 Répartition par statut:")
        for status, count in sorted(status_count.items()):
            print(f"  - {status}: {count}")
    
    return all_orders

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
    else:
        target_date_str = input("Entrez la date (YYYY-MM-DD ou DD/MM/YYYY) [aujourd'hui]: ").strip()
        if not target_date_str:
            target_date_str = None
    
    try:
        target_date = parse_date(target_date_str) if target_date_str else date.today()
    except ValueError as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("🔍 VÉRIFICATION DES VALEURS DU DASHBOARD")
        print("="*80)
        print(f"📅 Date analysée: {target_date.strftime('%d/%m/%Y')}")
        
        # 1. Vérifier toutes les commandes créées ce jour
        all_orders = verifier_toutes_commandes(target_date)
        
        # 2. Vérifier les commandes POS
        pos_data = verifier_commandes_pos(target_date)
        
        # 3. Vérifier les commandes livrées
        shop_data = verifier_commandes_livrees(target_date)
        
        # 4. Vérifier la dette livreur
        debt = verifier_dette_livreur(target_date)
        
        # 5. Vérifier le COGS
        cogs_data = verifier_cogs(target_date)
        
        # 6. Calculer les KPIs via RealKpiService (comme le dashboard)
        print("\n" + "="*80)
        print("📊 CALCULS DU DASHBOARD (RealKpiService)")
        print("="*80)
        
        real_kpis = RealKpiService.get_daily_kpis(target_date)
        
        print(f"\n💰 CA Total: {format_currency(real_kpis['revenue']['total'])}")
        print(f"   - POS: {format_currency(real_kpis['revenue']['pos'])}")
        print(f"   - Commandes: {format_currency(real_kpis['revenue']['shop'])}")
        
        print(f"\n📊 Nombre de commandes:")
        print(f"   - POS: {real_kpis['counts']['pos']}")
        print(f"   - Commandes: {real_kpis['counts']['shop']}")
        print(f"   - Total: {real_kpis['counts']['total']}")
        
        print(f"\n🔧 COGS:")
        print(f"   - Ingrédients: {format_currency(real_kpis['cogs']['ingredients'])}")
        print(f"   - Main d'œuvre: {format_currency(real_kpis['cogs']['labor'])}")
        print(f"   - Total: {format_currency(real_kpis['cogs']['total'])}")
        
        print(f"\n💵 Marge Nette:")
        print(f"   - Montant: {format_currency(real_kpis['margin']['net'])}")
        print(f"   - Pourcentage: {real_kpis['margin']['percent']:.1f}%")
        
        print(f"\n💳 Dette Livreur: {format_currency(real_kpis['delivery_debt'])}")
        
        # 7. Comparaison et alertes
        print("\n" + "="*80)
        print("⚠️  COMPARAISON ET ALERTES")
        print("="*80)
        
        # Vérifier les écarts
        issues = []
        
        if pos_data['count'] != real_kpis['counts']['pos']:
            issues.append(f"❌ Écart POS: Calcul direct={pos_data['count']}, Dashboard={real_kpis['counts']['pos']}")
        
        if abs(pos_data['revenue'] - real_kpis['revenue']['pos']) > 0.01:
            issues.append(f"❌ Écart CA POS: Calcul direct={format_currency(pos_data['revenue'])}, Dashboard={format_currency(real_kpis['revenue']['pos'])}")
        
        if shop_data['count'] != real_kpis['counts']['shop']:
            issues.append(f"❌ Écart Commandes: Calcul direct={shop_data['count']}, Dashboard={real_kpis['counts']['shop']}")
        
        if abs(shop_data['revenue'] - real_kpis['revenue']['shop']) > 0.01:
            issues.append(f"❌ Écart CA Commandes: Calcul direct={format_currency(shop_data['revenue'])}, Dashboard={format_currency(real_kpis['revenue']['shop'])}")
        
        if abs(debt - real_kpis['delivery_debt']) > 0.01:
            issues.append(f"❌ Écart Dette: Calcul direct={format_currency(debt)}, Dashboard={format_currency(real_kpis['delivery_debt'])}")
        
        if abs(cogs_data['total'] - real_kpis['cogs']['total']) > 0.01:
            issues.append(f"❌ Écart COGS: Calcul direct={format_currency(cogs_data['total'])}, Dashboard={format_currency(real_kpis['cogs']['total'])}")
        
        if issues:
            print("\n⚠️  PROBLÈMES DÉTECTÉS:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ Tous les calculs sont cohérents!")
        
        # Vérifier les commandes créées mais non comptabilisées
        print("\n" + "="*80)
        print("🔍 COMMANDES CRÉÉES MAIS NON COMPTABILISÉES DANS LE CA")
        print("="*80)
        
        # Commandes créées ce jour mais non POS et non livrées ce jour
        non_counted = []
        for order in all_orders:
            if order.order_type == 'in_store':
                # POS: doit être comptabilisé
                continue
            else:
                # Non-POS: doit être livré avec due_date ce jour
                if order.status not in ['delivered', 'completed', 'delivered_unpaid']:
                    non_counted.append({
                        'order': order,
                        'reason': f"Statut: {order.status} (doit être delivered/completed/delivered_unpaid)"
                    })
                elif func.date(order.due_date) != target_date:
                    due_date_str = order.due_date.strftime('%d/%m/%Y') if order.due_date else 'N/A'
                    non_counted.append({
                        'order': order,
                        'reason': f"Due date: {due_date_str} (doit être {target_date.strftime('%d/%m/%Y')})"
                    })
        
        if non_counted:
            print(f"\n⚠️  {len(non_counted)} commande(s) créée(s) ce jour mais non comptabilisée(s):")
            print("-" * 100)
            print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Raison':<40}")
            print("-" * 100)
            for item in non_counted:
                order = item['order']
                print(f"{order.id:<6} {order.get_order_type_display()[:25]:<25} {order.status:<20} {format_currency(order.total_amount):<15} {item['reason'][:40]:<40}")
        else:
            print("\n✅ Toutes les commandes créées ce jour sont correctement comptabilisées ou ont une raison valide de ne pas l'être.")
        
        print("\n" + "="*80)
        print("✅ VÉRIFICATION TERMINÉE")
        print("="*80)

if __name__ == '__main__':
    main()

