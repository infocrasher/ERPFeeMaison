#!/usr/bin/env python3
"""
Script pour vérifier tous les KPI du dashboard pour une date spécifique
Compare les valeurs calculées avec ce qui devrait être affiché
"""

import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from app.routes.dashboard import build_dashboard_context
from app.reports.services import DailySalesReportService, PrimeCostReportService

def verifier_kpi_dashboard(target_date_str):
    """Vérifie tous les KPI du dashboard"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 80)
        print("VÉRIFICATION KPI DASHBOARD")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # Construire le contexte du dashboard
        context = build_dashboard_context(target_date, 'day')
        
        # ========================================================================
        # 1. KPI VENTES
        # ========================================================================
        print("=" * 80)
        print("1️⃣  KPI VENTES")
        print("=" * 80)
        print()
        
        sales_block = context.get('sales', {})
        overview = context.get('overview', {})
        
        daily_revenue = sales_block.get('daily_revenue', 0.0)
        daily_orders = sales_block.get('daily_orders', 0)
        average_basket = sales_block.get('average_basket', 0.0)
        
        print(f"💰 CA du jour : {daily_revenue:,.2f} DA")
        print(f"📋 Commandes du jour : {daily_orders}")
        print(f"🛒 Panier moyen : {average_basket:,.2f} DA")
        print()
        
        # Vérifier avec le service
        report = DailySalesReportService.generate(target_date)
        service_revenue = report.get('total_revenue', 0.0)
        service_transactions = report.get('total_transactions', 0)
        service_avg_basket = report.get('average_basket', 0.0)
        
        print("   Vérification avec DailySalesReportService :")
        print(f"      CA : {service_revenue:,.2f} DA")
        print(f"      Transactions : {service_transactions}")
        print(f"      Panier moyen : {service_avg_basket:,.2f} DA")
        print()
        
        if abs(daily_revenue - service_revenue) > 0.01:
            print(f"   ⚠️  INCOHÉRENCE CA : {abs(daily_revenue - service_revenue):,.2f} DA")
        else:
            print("   ✅ CA cohérent")
        
        if daily_orders != service_transactions:
            print(f"   ⚠️  INCOHÉRENCE TRANSACTIONS : {abs(daily_orders - service_transactions)}")
        else:
            print("   ✅ Transactions cohérentes")
        print()
        
        # ========================================================================
        # 2. KPI MARGES
        # ========================================================================
        print("=" * 80)
        print("2️⃣  KPI MARGES")
        print("=" * 80)
        print()
        
        prime_cost_report = PrimeCostReportService.generate(target_date)
        
        revenue = prime_cost_report.get('revenue', 0.0)
        cogs = prime_cost_report.get('cogs', 0.0)
        labor_cost = prime_cost_report.get('labor_cost', 0.0)
        prime_cost = prime_cost_report.get('prime_cost', 0.0)
        gross_margin = prime_cost_report.get('gross_margin', 0.0)
        gross_margin_pct = prime_cost_report.get('gross_margin_percentage', 0.0)
        
        print(f"💰 CA : {revenue:,.2f} DA")
        print(f"📦 COGS (Coût des marchandises) : {cogs:,.2f} DA")
        print(f"👷 Coût main d'œuvre : {labor_cost:,.2f} DA")
        print(f"💼 Prime Cost (COGS + Main d'œuvre) : {prime_cost:,.2f} DA")
        print(f"📈 Marge brute : {gross_margin:,.2f} DA ({gross_margin_pct:.2f}%)")
        print()
        
        # Vérifier les calculs
        calculated_prime_cost = cogs + labor_cost
        calculated_gross_margin = revenue - cogs
        calculated_gross_margin_pct = (calculated_gross_margin / revenue * 100) if revenue > 0 else 0
        
        if abs(prime_cost - calculated_prime_cost) > 0.01:
            print(f"   ⚠️  INCOHÉRENCE Prime Cost : {abs(prime_cost - calculated_prime_cost):,.2f} DA")
        else:
            print("   ✅ Prime Cost cohérent")
        
        if abs(gross_margin - calculated_gross_margin) > 0.01:
            print(f"   ⚠️  INCOHÉRENCE Marge brute : {abs(gross_margin - calculated_gross_margin):,.2f} DA")
        else:
            print("   ✅ Marge brute cohérente")
        print()
        
        # ========================================================================
        # 3. KPI METRIC CARDS
        # ========================================================================
        print("=" * 80)
        print("3️⃣  METRIC CARDS (Affichées dans le dashboard)")
        print("=" * 80)
        print()
        
        metric_cards = context.get('metric_cards', [])
        
        for card in metric_cards:
            label = card.get('label', 'N/A')
            value = card.get('value', 0)
            unit = card.get('unit', '')
            delta = card.get('delta', 0)
            trend_label = card.get('trend_label', '')
            
            print(f"   {label:20s} : {value:12,.2f} {unit:5s} (Δ: {delta:+.2f} {trend_label})")
        
        print()
        
        # ========================================================================
        # 4. RÉSUMÉ ET PROBLÈMES
        # ========================================================================
        print("=" * 80)
        print("4️⃣  RÉSUMÉ")
        print("=" * 80)
        print()
        
        print(f"📅 Date : {target_date.strftime('%d/%m/%Y')}")
        print(f"💰 CA du jour : {daily_revenue:,.2f} DA")
        print(f"📋 Commandes : {daily_orders}")
        print(f"🛒 Panier moyen : {average_basket:,.2f} DA")
        print(f"📈 Marge brute : {gross_margin:,.2f} DA ({gross_margin_pct:.2f}%)")
        print()
        
        # Vérifier les incohérences potentielles
        issues = []
        
        if abs(daily_revenue - service_revenue) > 0.01:
            issues.append(f"CA incohérent : {daily_revenue:,.2f} vs {service_revenue:,.2f}")
        
        if abs(revenue - daily_revenue) > 0.01:
            issues.append(f"CA PrimeCost vs Sales : {revenue:,.2f} vs {daily_revenue:,.2f}")
        
        if issues:
            print("⚠️  PROBLÈMES DÉTECTÉS :")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Tous les KPI sont cohérents")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/verifier_kpi_dashboard.py YYYY-MM-DD")
        print("Exemple: python3 scripts/verifier_kpi_dashboard.py 2025-12-08")
        sys.exit(1)
    
    verifier_kpi_dashboard(sys.argv[1])

