#!/usr/bin/env python3
"""
Script d'audit pour investiguer les écarts entre le dashboard et la réalité
Analyse le CA et la dette livreur pour une date donnée
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product, DeliveryDebt
from sqlalchemy import func, and_, or_
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

def audit_ca_pos(target_date):
    """Audit du CA POS (ventes au comptoir)"""
    print("\n" + "="*80)
    print("📊 AUDIT CA POS (Ventes au Comptoir)")
    print("="*80)
    
    # Selon RealKpiService : order_type == 'in_store' ET created_at == date
    pos_orders = Order.query.filter(
        Order.order_type == 'in_store',
        func.date(Order.created_at) == target_date
    ).all()
    
    pos_revenue = sum(float(o.total_amount or 0) for o in pos_orders)
    pos_count = len(pos_orders)
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"✅ Nombre de commandes POS: {pos_count}")
    print(f"💰 CA POS calculé: {format_currency(pos_revenue)}")
    
    if pos_orders:
        print(f"\n📋 Détail des commandes POS:")
        print("-" * 100)
        print(f"{'ID':<6} {'Statut':<20} {'Montant':<15} {'Créée à':<20} {'Client':<30} {'Type':<20}")
        print("-" * 100)
        
        for order in sorted(pos_orders, key=lambda x: x.created_at):
            created_str = order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else 'N/A'
            client = order.customer_name or 'Sans nom'
            order_type_display = order.get_order_type_display()
            print(f"{order.id:<6} {order.status:<20} {format_currency(order.total_amount):<15} {created_str:<20} {client[:30]:<30} {order_type_display[:20]:<20}")
        
        # Vérifier les statuts
        status_count = {}
        for order in pos_orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        print(f"\n📊 Répartition par statut:")
        for status, count in sorted(status_count.items()):
            print(f"  - {status}: {count}")
    else:
        print("⚠️  Aucune commande POS trouvée")
    
    return {
        'count': pos_count,
        'revenue': pos_revenue,
        'orders': pos_orders
    }

def audit_ca_shop(target_date):
    """Audit du CA Shop (commandes livrées)"""
    print("\n" + "="*80)
    print("🚚 AUDIT CA SHOP (Commandes Livrées)")
    print("="*80)
    
    # Selon RealKpiService : order_type != 'in_store' ET status livré ET due_date == date
    shop_orders = Order.query.filter(
        Order.order_type != 'in_store',
        Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
        func.date(Order.due_date) == target_date
    ).all()
    
    shop_revenue = sum(float(o.total_amount or 0) for o in shop_orders)
    shop_count = len(shop_orders)
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"✅ Nombre de commandes livrées: {shop_count}")
    print(f"💰 CA Shop calculé: {format_currency(shop_revenue)}")
    
    if shop_orders:
        print(f"\n📋 Détail des commandes livrées:")
        print("-" * 120)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Créée le':<12} {'Due Date':<20} {'Client':<30}")
        print("-" * 120)
        
        # Séparer les ordres de production (montant 0) des vraies commandes
        production_orders = []
        real_orders = []
        
        for order in sorted(shop_orders, key=lambda x: x.due_date):
            due_str = order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            created_str = order.created_at.strftime('%d/%m/%Y') if order.created_at else 'N/A'
            client = order.customer_name or 'Sans nom'
            order_type_display = order.get_order_type_display()
            amount = float(order.total_amount or 0)
            
            print(f"{order.id:<6} {order_type_display[:25]:<25} {order.status:<20} {format_currency(amount):<15} {created_str:<12} {due_str:<20} {client[:30]:<30}")
            
            if order.order_type == 'counter_production_request' or amount == 0:
                production_orders.append(order)
            else:
                real_orders.append(order)
        
        # Analyser les ordres de production
        if production_orders:
            print(f"\n⚠️  ORDRES DE PRODUCTION INCLUS (ne devraient pas être dans le CA):")
            print(f"   Nombre: {len(production_orders)}")
            print(f"   Montant total: {format_currency(sum(float(o.total_amount or 0) for o in production_orders))}")
            print(f"   ⚠️  Ces ordres ont montant=0, ils ne devraient pas être comptabilisés dans le CA")
        
        # Analyser les vraies commandes
        if real_orders:
            print(f"\n✅ VRAIES COMMANDES CLIENT:")
            print(f"   Nombre: {len(real_orders)}")
            print(f"   Montant total: {format_currency(sum(float(o.total_amount or 0) for o in real_orders))}")
            
            # Vérifier les dates de création
            created_today = [o for o in real_orders if func.date(o.created_at) == target_date]
            created_before = [o for o in real_orders if func.date(o.created_at) != target_date]
            
            if created_before:
                print(f"\n   ⚠️  {len(created_before)} commande(s) créée(s) AVANT le {target_date.strftime('%d/%m/%Y')} mais livrée(s) ce jour:")
                for order in created_before:
                    created_str = order.created_at.strftime('%d/%m/%Y') if order.created_at else 'N/A'
                    print(f"      - Commande #{order.id}: créée le {created_str}, livrée le {target_date.strftime('%d/%m/%Y')}, montant: {format_currency(order.total_amount)}")
            
            if created_today:
                print(f"\n   ✅ {len(created_today)} commande(s) créée(s) ET livrée(s) le {target_date.strftime('%d/%m/%Y')}")
        
        # Répartition par type
        type_count = {}
        type_revenue = {}
        for order in shop_orders:
            order_type = order.get_order_type_display()
            type_count[order_type] = type_count.get(order_type, 0) + 1
            type_revenue[order_type] = type_revenue.get(order_type, 0) + float(order.total_amount or 0)
        
        print(f"\n📊 Répartition par type:")
        for order_type in sorted(type_count.keys()):
            print(f"  - {order_type}: {type_count[order_type]} commandes, {format_currency(type_revenue[order_type])}")
    else:
        print("⚠️  Aucune commande livrée trouvée")
    
    return {
        'count': shop_count,
        'revenue': shop_revenue,
        'orders': shop_orders,
        'production_orders': [o for o in shop_orders if o.order_type == 'counter_production_request' or float(o.total_amount or 0) == 0],
        'real_orders': [o for o in shop_orders if o.order_type != 'counter_production_request' and float(o.total_amount or 0) > 0]
    }

def audit_dette_livreur(target_date):
    """Audit de la dette livreur"""
    print("\n" + "="*80)
    print("💳 AUDIT DETTE LIVREUR")
    print("="*80)
    
    # Selon RealKpiService : commandes Shop livrées ce jour avec reste à payer
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
                'client': order.customer_name or 'Sans nom',
                'status': order.status,
                'due_date': order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            })
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"💰 Dette totale calculée: {format_currency(total_debt)}")
    print(f"📊 Nombre de commandes avec dette: {len(orders_with_debt)}")
    
    if orders_with_debt:
        print(f"\n📋 Détail des dettes:")
        print("-" * 100)
        print(f"{'ID':<6} {'Statut':<20} {'Montant Total':<15} {'Payé':<15} {'Dette':<15} {'Due Date':<20} {'Client':<30}")
        print("-" * 100)
        for o in sorted(orders_with_debt, key=lambda x: x['debt'], reverse=True):
            print(f"{o['id']:<6} {o['status']:<20} {format_currency(o['total']):<15} {format_currency(o['paid']):<15} {format_currency(o['debt']):<15} {o['due_date']:<20} {o['client'][:30]:<30}")
    else:
        print("✅ Aucune dette trouvée (toutes les commandes sont payées)")
    
    # Vérifier aussi les DeliveryDebt (si le modèle existe)
    try:
        delivery_debts = DeliveryDebt.query.filter(
            func.date(DeliveryDebt.created_at) == target_date
        ).all()
        
        if delivery_debts:
            print(f"\n📋 Dettes enregistrées dans DeliveryDebt:")
            print("-" * 100)
            print(f"{'ID':<6} {'Order ID':<10} {'Montant':<15} {'Payé':<15} {'Créée à':<20}")
            print("-" * 100)
            for debt in delivery_debts:
                created_str = debt.created_at.strftime('%d/%m/%Y %H:%M') if debt.created_at else 'N/A'
                print(f"{debt.id:<6} {debt.order_id:<10} {format_currency(debt.amount):<15} {format_currency(debt.amount_paid or 0):<15} {created_str:<20}")
    except Exception as e:
        print(f"\n⚠️  Impossible de vérifier DeliveryDebt: {e}")
    
    return total_debt

def audit_toutes_commandes(target_date):
    """Audit de TOUTES les commandes créées ce jour"""
    print("\n" + "="*80)
    print("🔍 AUDIT TOUTES LES COMMANDES CRÉÉES CE JOUR")
    print("="*80)
    
    all_orders = Order.query.filter(
        func.date(Order.created_at) == target_date
    ).all()
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"📊 Total commandes créées: {len(all_orders)}")
    
    if all_orders:
        print(f"\n📋 Détail complet:")
        print("-" * 120)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Créée à':<20} {'Due Date':<20} {'Payé':<15} {'Client':<30}")
        print("-" * 120)
        
        for order in sorted(all_orders, key=lambda x: x.created_at):
            created_str = order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else 'N/A'
            due_str = order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            client = order.customer_name or 'Sans nom'
            order_type_display = order.get_order_type_display()
            paid = format_currency(order.amount_paid or 0)
            print(f"{order.id:<6} {order_type_display[:25]:<25} {order.status:<20} {format_currency(order.total_amount):<15} {created_str:<20} {due_str:<20} {paid:<15} {client[:30]:<30}")
        
        # Répartition par type
        type_count = {}
        type_revenue = {}
        for order in all_orders:
            order_type = order.get_order_type_display()
            type_count[order_type] = type_count.get(order_type, 0) + 1
            type_revenue[order_type] = type_revenue.get(order_type, 0) + float(order.total_amount or 0)
        
        print(f"\n📊 Répartition par type:")
        for order_type in sorted(type_count.keys()):
            print(f"  - {order_type}: {type_count[order_type]} commandes, {format_currency(type_revenue[order_type])}")
        
        # Répartition par statut
        status_count = {}
        status_revenue = {}
        for order in all_orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1
            status_revenue[order.status] = status_revenue.get(order.status, 0) + float(order.total_amount or 0)
        
        print(f"\n📊 Répartition par statut:")
        for status in sorted(status_count.keys()):
            print(f"  - {status}: {status_count[status]} commandes, {format_currency(status_revenue[status])}")
    
    return all_orders

def comparer_avec_dashboard(target_date):
    """Compare les calculs avec ce que le dashboard affiche"""
    print("\n" + "="*80)
    print("📊 COMPARAISON AVEC LE DASHBOARD (RealKpiService)")
    print("="*80)
    
    real_kpis = RealKpiService.get_daily_kpis(target_date)
    
    print(f"\n📅 Date: {target_date.strftime('%d/%m/%Y')}")
    print(f"\n💰 CA selon RealKpiService:")
    print(f"   - Total: {format_currency(real_kpis['revenue']['total'])}")
    print(f"   - POS: {format_currency(real_kpis['revenue']['pos'])}")
    print(f"   - Shop: {format_currency(real_kpis['revenue']['shop'])}")
    
    print(f"\n📊 Commandes selon RealKpiService:")
    print(f"   - Total: {real_kpis['counts']['total']}")
    print(f"   - POS: {real_kpis['counts']['pos']}")
    print(f"   - Shop: {real_kpis['counts']['shop']}")
    
    print(f"\n💳 Dette Livreur selon RealKpiService: {format_currency(real_kpis['delivery_debt'])}")
    
    return real_kpis

def identifier_commandes_problematiques(target_date, pos_data, shop_data, real_kpis):
    """Identifie les commandes qui causent des écarts"""
    print("\n" + "="*80)
    print("🔍 IDENTIFICATION DES COMMANDES PROBLÉMATIQUES")
    print("="*80)
    
    issues = []
    
    # Vérifier les commandes POS
    if pos_data['count'] != real_kpis['counts']['pos']:
        issues.append({
            'type': 'POS_COUNT_MISMATCH',
            'message': f"Nombre POS: Calcul direct={pos_data['count']}, Dashboard={real_kpis['counts']['pos']}"
        })
    
    if abs(pos_data['revenue'] - real_kpis['revenue']['pos']) > 0.01:
        issues.append({
            'type': 'POS_REVENUE_MISMATCH',
            'message': f"CA POS: Calcul direct={format_currency(pos_data['revenue'])}, Dashboard={format_currency(real_kpis['revenue']['pos'])}"
        })
    
    # Vérifier les commandes Shop
    if shop_data['count'] != real_kpis['counts']['shop']:
        issues.append({
            'type': 'SHOP_COUNT_MISMATCH',
            'message': f"Nombre Shop: Calcul direct={shop_data['count']}, Dashboard={real_kpis['counts']['shop']}"
        })
    
    if abs(shop_data['revenue'] - real_kpis['revenue']['shop']) > 0.01:
        issues.append({
            'type': 'SHOP_REVENUE_MISMATCH',
            'message': f"CA Shop: Calcul direct={format_currency(shop_data['revenue'])}, Dashboard={format_currency(real_kpis['revenue']['shop'])}"
        })
    
    # Identifier les commandes POS qui ne devraient pas être comptabilisées
    print(f"\n🔍 Vérification des commandes POS:")
    pos_problematiques = []
    for order in pos_data['orders']:
        # Vérifier si la commande a un statut qui ne devrait pas être comptabilisé
        if order.status not in ['completed', 'delivered', 'delivered_unpaid']:
            pos_problematiques.append({
                'order': order,
                'reason': f"Statut '{order.status}' ne devrait peut-être pas être comptabilisé"
            })
        # Vérifier si order_type est vraiment 'in_store'
        if order.order_type != 'in_store':
            pos_problematiques.append({
                'order': order,
                'reason': f"order_type='{order.order_type}' au lieu de 'in_store'"
            })
    
    if pos_problematiques:
        print(f"⚠️  {len(pos_problematiques)} commande(s) POS problématique(s):")
        print("-" * 100)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Montant':<15} {'Raison':<40}")
        print("-" * 100)
        for item in pos_problematiques:
            order = item['order']
            print(f"{order.id:<6} {order.get_order_type_display()[:25]:<25} {order.status:<20} {format_currency(order.total_amount):<15} {item['reason'][:40]:<40}")
    
    # Identifier les commandes Shop qui ne devraient pas être comptabilisées
    print(f"\n🔍 Vérification des commandes Shop:")
    shop_problematiques = []
    for order in shop_data['orders']:
        # Vérifier si due_date correspond bien à la date cible
        if func.date(order.due_date) != target_date:
            due_date_str = order.due_date.strftime('%d/%m/%Y') if order.due_date else 'N/A'
            shop_problematiques.append({
                'order': order,
                'reason': f"due_date={due_date_str} au lieu de {target_date.strftime('%d/%m/%Y')}"
            })
        # Vérifier si le statut est correct
        if order.status not in ['delivered', 'completed', 'delivered_unpaid']:
            shop_problematiques.append({
                'order': order,
                'reason': f"Statut '{order.status}' ne devrait pas être comptabilisé"
            })
        # Vérifier si order_type est correct
        if order.order_type == 'in_store':
            shop_problematiques.append({
                'order': order,
                'reason': f"order_type='in_store' mais devrait être Shop"
            })
    
    if shop_problematiques:
        print(f"⚠️  {len(shop_problematiques)} commande(s) Shop problématique(s):")
        print("-" * 100)
        print(f"{'ID':<6} {'Type':<25} {'Statut':<20} {'Due Date':<20} {'Montant':<15} {'Raison':<40}")
        print("-" * 100)
        for item in shop_problematiques:
            order = item['order']
            due_str = order.due_date.strftime('%d/%m/%Y %H:%M') if order.due_date else 'N/A'
            print(f"{order.id:<6} {order.get_order_type_display()[:25]:<25} {order.status:<20} {due_str:<20} {format_currency(order.total_amount):<15} {item['reason'][:40]:<40}")
    
    if issues:
        print(f"\n❌ PROBLÈMES DÉTECTÉS:")
        for issue in issues:
            print(f"  - {issue['message']}")
    else:
        print("\n✅ Aucun écart détecté entre calcul direct et RealKpiService")
    
    return issues, pos_problematiques, shop_problematiques

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
    else:
        target_date_str = input("Entrez la date à auditer (YYYY-MM-DD ou DD/MM/YYYY) [aujourd'hui]: ").strip()
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
        print("🔍 AUDIT CA ET DETTE LIVREUR - INVESTIGATION")
        print("="*80)
        print(f"📅 Date analysée: {target_date.strftime('%d/%m/%Y')}")
        
        # 1. Audit toutes les commandes créées ce jour
        all_orders = audit_toutes_commandes(target_date)
        
        # 2. Audit CA POS
        pos_data = audit_ca_pos(target_date)
        
        # 3. Audit CA Shop
        shop_data = audit_ca_shop(target_date)
        
        # 4. Audit dette livreur
        debt = audit_dette_livreur(target_date)
        
        # 5. Comparer avec le dashboard
        real_kpis = comparer_avec_dashboard(target_date)
        
        # 6. Identifier les problèmes
        issues, pos_problematiques, shop_problematiques = identifier_commandes_problematiques(
            target_date, pos_data, shop_data, real_kpis
        )
        
        # 7. Résumé final avec analyse détaillée
        print("\n" + "="*80)
        print("📋 RÉSUMÉ DE L'AUDIT")
        print("="*80)
        
        total_ca_calcule = pos_data['revenue'] + shop_data['revenue']
        total_ca_dashboard = real_kpis['revenue']['total']
        
        # Calculer le CA "réel" (sans ordres de production)
        ca_shop_sans_production = sum(float(o.total_amount or 0) for o in shop_data.get('real_orders', shop_data['orders']))
        ca_reel = pos_data['revenue'] + ca_shop_sans_production
        
        print(f"\n💰 CA:")
        print(f"   - Calcul direct (avec ordres prod): {format_currency(total_ca_calcule)}")
        print(f"   - Dashboard (RealKpiService): {format_currency(total_ca_dashboard)}")
        print(f"   - CA RÉEL (sans ordres prod): {format_currency(ca_reel)}")
        
        if abs(total_ca_calcule - total_ca_dashboard) > 0.01:
            print(f"   ❌ ÉCART: {format_currency(abs(total_ca_calcule - total_ca_dashboard))}")
        else:
            print(f"   ✅ Cohérent avec RealKpiService")
        
        # Analyser les ordres de production
        production_orders = shop_data.get('production_orders', [])
        if production_orders:
            print(f"\n⚠️  PROBLÈME IDENTIFIÉ:")
            print(f"   - {len(production_orders)} Ordre(s) de Production inclus dans le CA Shop")
            print(f"   - Ces ordres ont montant=0 et ne devraient PAS être comptabilisés")
            print(f"   - CA sans ordres prod: {format_currency(ca_reel)}")
            print(f"   - Différence: {format_currency(total_ca_calcule - ca_reel)}")
        
        # Analyser les commandes créées avant mais livrées aujourd'hui
        real_orders = shop_data.get('real_orders', [])
        if real_orders:
            created_before = [o for o in real_orders if func.date(o.created_at) != target_date]
            if created_before:
                revenue_before = sum(float(o.total_amount or 0) for o in created_before)
                print(f"\n📅 COMMANDES CRÉÉES AVANT MAIS LIVRÉES AUJOURD'HUI:")
                print(f"   - Nombre: {len(created_before)}")
                print(f"   - Montant: {format_currency(revenue_before)}")
                print(f"   - Selon la logique actuelle, ces commandes sont comptabilisées aujourd'hui (date de livraison)")
        
        print(f"\n💳 DETTE LIVREUR:")
        print(f"   - Calcul direct: {format_currency(debt)}")
        print(f"   - Dashboard (RealKpiService): {format_currency(real_kpis['delivery_debt'])}")
        if abs(debt - real_kpis['delivery_debt']) > 0.01:
            print(f"   ❌ ÉCART: {format_currency(abs(debt - real_kpis['delivery_debt']))}")
        else:
            print(f"   ✅ Cohérent")
        
        # Détail des dettes
        if debt > 0:
            print(f"\n   📋 Détail des dettes:")
            shop_orders_debt = Order.query.filter(
                Order.order_type != 'in_store',
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.due_date) == target_date
            ).all()
            
            for order in shop_orders_debt:
                order_debt = float(order.total_amount or 0) - float(order.amount_paid or 0)
                if order_debt > 0:
                    print(f"      - Commande #{order.id} ({order.customer_name or 'Sans nom'}): {format_currency(order_debt)}")
                    print(f"        Montant: {format_currency(order.total_amount)}, Payé: {format_currency(order.amount_paid)}")
        
        print(f"\n📊 COMMANDES:")
        print(f"   - POS: {pos_data['count']} (Dashboard: {real_kpis['counts']['pos']})")
        print(f"   - Shop: {shop_data['count']} (Dashboard: {real_kpis['counts']['shop']})")
        print(f"     - Dont Ordres de Production: {len(production_orders)}")
        print(f"     - Dont Vraies commandes: {len(real_orders)}")
        print(f"   - Total créées ce jour: {len(all_orders)}")
        
        if issues or pos_problematiques or shop_problematiques:
            print(f"\n⚠️  {len(issues) + len(pos_problematiques) + len(shop_problematiques)} problème(s) détecté(s)")
            print("   Voir les détails ci-dessus pour identifier les commandes problématiques")
        else:
            print(f"\n✅ Aucun problème détecté - tout est cohérent")
        
        print("\n" + "="*80)
        print("✅ AUDIT TERMINÉ")
        print("="*80)

if __name__ == '__main__':
    main()

