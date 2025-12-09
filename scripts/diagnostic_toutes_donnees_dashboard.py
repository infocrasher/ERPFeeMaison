#!/usr/bin/env python3
"""
Script de diagnostic complet pour toutes les données du dashboard
Identifie toutes les incohérences
"""

import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Product
from app.purchases.models import Purchase
from app.routes.dashboard import build_dashboard_context
from sqlalchemy import func

def diagnostic_toutes_donnees(target_date_str):
    """Diagnostic complet de toutes les données"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 80)
        print("DIAGNOSTIC COMPLET DASHBOARD")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # Construire le contexte du dashboard
        context = build_dashboard_context(target_date, 'day')
        
        # ========================================================================
        # 1. VALEUR STOCK
        # ========================================================================
        print("=" * 80)
        print("1️⃣  VALEUR STOCK")
        print("=" * 80)
        print()
        
        stock_summary = context.get('stock', {})
        dashboard_value = stock_summary.get('total_value', 0.0)
        print(f"📦 Valeur stock (dashboard) : {dashboard_value:,.2f} DA")
        print()
        
        # Calculer manuellement comme dans stock overview
        products = Product.query.all()
        calculated_value = sum(
            float(p.valeur_stock_ingredients_magasin or 0) +
            float(p.valeur_stock_ingredients_local or 0) +
            float(p.valeur_stock_comptoir or 0) +
            float(p.valeur_stock_consommables or 0)
            for p in products
        )
        print(f"📦 Valeur stock (calcul manuel) : {calculated_value:,.2f} DA")
        print()
        
        # Vérifier total_stock_value
        total_stock_value_sum = float(db.session.query(func.sum(Product.total_stock_value)).scalar() or 0)
        print(f"📦 Valeur stock (total_stock_value) : {total_stock_value_sum:,.2f} DA")
        print()
        
        if abs(dashboard_value - calculated_value) > 100:
            print(f"⚠️  INCOHÉRENCE : {abs(dashboard_value - calculated_value):,.2f} DA")
            print("   Le dashboard n'utilise pas le calcul correct")
        elif abs(dashboard_value - total_stock_value_sum) < 100:
            print(f"⚠️  PROBLÈME : Le dashboard utilise encore total_stock_value")
            print("   Il devrait utiliser le calcul par emplacement")
        else:
            print("✅ Valeur stock correcte")
        print()
        
        # ========================================================================
        # 2. ACHATS DU JOUR
        # ========================================================================
        print("=" * 80)
        print("2️⃣  ACHATS DU JOUR")
        print("=" * 80)
        print()
        
        purchase_cost_today = stock_summary.get('purchase_today', 0.0)
        print(f"💰 Achat du jour (dashboard) : {purchase_cost_today:,.2f} DA")
        print()
        
        # Vérifier les achats avec created_at
        purchases_created = Purchase.query.filter(
            func.date(Purchase.created_at) == target_date
        ).all()
        
        print(f"📋 Achats créés le {target_date.strftime('%d/%m/%Y')} : {len(purchases_created)}")
        if purchases_created:
            total_created = sum(float(p.total_amount or 0) for p in purchases_created)
            print(f"💰 Total achats créés : {total_created:,.2f} DA")
            print()
            print("   Détail des achats créés :")
            for p in purchases_created[:10]:
                print(f"      - {p.reference} : {float(p.total_amount or 0):,.2f} DA")
                print(f"        Créé : {p.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if hasattr(p, 'payment_date') and p.payment_date:
                    print(f"        Payé : {p.payment_date}")
                print()
            if len(purchases_created) > 10:
                print(f"      ... et {len(purchases_created) - 10} autres")
        print()
        
        # Vérifier les achats avec payment_date
        purchases_paid = Purchase.query.filter(
            Purchase.payment_date == target_date
        ).all()
        
        print(f"📋 Achats payés le {target_date.strftime('%d/%m/%Y')} : {len(purchases_paid)}")
        if purchases_paid:
            total_paid = sum(float(p.total_amount or 0) for p in purchases_paid)
            print(f"💰 Total achats payés : {total_paid:,.2f} DA")
            print()
            print("   Détail des achats payés :")
            for p in purchases_paid[:10]:
                print(f"      - {p.reference} : {float(p.total_amount or 0):,.2f} DA")
                print(f"        Créé : {p.created_at.strftime('%Y-%m-%d')}")
                print(f"        Payé : {p.payment_date}")
                print()
            if len(purchases_paid) > 10:
                print(f"      ... et {len(purchases_paid) - 10} autres")
        print()
        
        # Comparaison
        if purchases_created:
            total_created = sum(float(p.total_amount or 0) for p in purchases_created)
            if abs(purchase_cost_today - total_created) > 0.01:
                print(f"⚠️  INCOHÉRENCE :")
                print(f"   Dashboard : {purchase_cost_today:,.2f} DA")
                print(f"   Calculé (created_at) : {total_created:,.2f} DA")
                print(f"   Écart : {abs(purchase_cost_today - total_created):,.2f} DA")
            else:
                print("✅ Achat du jour cohérent")
        print()
        
        # ========================================================================
        # 3. AUTRES DONNÉES À VÉRIFIER
        # ========================================================================
        print("=" * 80)
        print("3️⃣  AUTRES DONNÉES")
        print("=" * 80)
        print()
        
        overview = context.get('overview', {})
        sales_block = context.get('sales', {})
        cash_block = context.get('cash', {})
        
        print("📊 Données du dashboard :")
        print(f"   CA du jour : {sales_block.get('daily_revenue', 0):,.2f} DA")
        print(f"   Commandes : {sales_block.get('daily_orders', 0)}")
        print(f"   Valeur stock : {stock_summary.get('total_value', 0):,.2f} DA")
        print(f"   Achat du jour : {stock_summary.get('purchase_today', 0):,.2f} DA")
        print(f"   Flux caisse : {cash_block.get('net', 0):,.2f} DA")
        print()
        
        # ========================================================================
        # 4. RÉSUMÉ ET RECOMMANDATIONS
        # ========================================================================
        print("=" * 80)
        print("4️⃣  RÉSUMÉ")
        print("=" * 80)
        print()
        
        issues = []
        
        if abs(dashboard_value - calculated_value) > 100:
            issues.append(f"Valeur stock incorrecte : {dashboard_value:,.2f} vs {calculated_value:,.2f} DA")
        
        if purchases_created:
            total_created = sum(float(p.total_amount or 0) for p in purchases_created)
            if abs(purchase_cost_today - total_created) > 0.01:
                issues.append(f"Achat du jour incorrect : {purchase_cost_today:,.2f} vs {total_created:,.2f} DA")
        
        if issues:
            print("❌ PROBLÈMES DÉTECTÉS :")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Toutes les données sont cohérentes")
        print()
        
        print("💡 RECOMMANDATIONS :")
        print("   1. Vérifier que le code a été déployé sur le VPS")
        print("   2. Vider le cache du navigateur (Ctrl+F5)")
        print("   3. Vérifier que les valeurs valeur_stock_* sont à jour")
        print("   4. Vérifier si les achats utilisent created_at ou payment_date")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/diagnostic_toutes_donnees_dashboard.py YYYY-MM-DD")
        print("Exemple: python3 scripts/diagnostic_toutes_donnees_dashboard.py 2025-12-08")
        sys.exit(1)
    
    diagnostic_toutes_donnees(sys.argv[1])

