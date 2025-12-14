#!/usr/bin/env python3
"""
Script d'audit spécifique pour le 14/12/2025
Compare les données ERP avec les données réelles de la gérante
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product, DeliveryDebt
from sqlalchemy import func, and_, or_
from app.reports.kpi_service import RealKpiService
from app.sales.models import CashMovement, CashRegisterSession

def format_currency(value):
    return f"{float(value):,.2f} DA"

def main():
    target_date = date(2025, 12, 14)
    
    # Données réelles de la gérante
    GERANTE_FOND_CAISSE = 10410
    GERANTE_RECETTE = 64155
    GERANTE_CASHOUT = 56000
    GERANTE_ECART = 8720
    VENTES_NON_ENREGISTREES = 2320
    
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("🔍 AUDIT 14/12/2025 - COMPARAISON ERP vs GÉRANTE")
        print("="*80)
        
        # 1. Données de la gérante
        print("\n📋 DONNÉES DE LA GÉRANTE:")
        print("-" * 50)
        print(f"   Fond de caisse : {format_currency(GERANTE_FOND_CAISSE)}")
        print(f"   Recette réelle : {format_currency(GERANTE_RECETTE)}")
        print(f"   Cashout        : {format_currency(GERANTE_CASHOUT)}")
        print(f"   Écart déclaré  : {format_currency(GERANTE_ECART)}")
        print(f"   Ventes non enregistrées : {format_currency(VENTES_NON_ENREGISTREES)}")
        
        # 2. Données ERP
        print("\n📊 DONNÉES ERP:")
        print("-" * 50)
        
        # KPIs
        kpis = RealKpiService.get_daily_kpis(target_date)
        print(f"   CA Dashboard : {format_currency(kpis['revenue']['total'])}")
        print(f"      - POS : {format_currency(kpis['revenue']['pos'])}")
        print(f"      - Shop : {format_currency(kpis['revenue']['shop'])}")
        
        # CashMovements
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == target_date
        ).all()
        
        entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
        exit_types = {'sortie', 'retrait', 'frais', 'paiement', 'depot', 'dépôt', 'banque'}
        
        cash_in = 0.0
        cash_out = 0.0
        
        for m in movements:
            mtype = (m.type or '').lower()
            amount = float(m.amount or 0)
            if mtype in exit_types or 'depot' in mtype or 'banque' in mtype:
                cash_out += abs(amount)
            else:
                cash_in += amount
        
        print(f"\n   Encaissements ERP : {format_currency(cash_in)}")
        print(f"   Sorties ERP (Cashout) : {format_currency(cash_out)}")
        print(f"   Flux Net ERP : {format_currency(cash_in - cash_out)}")
        
        # 3. Comparaison
        print("\n📊 COMPARAISON:")
        print("-" * 50)
        
        ecart_recette = GERANTE_RECETTE - cash_in
        ecart_cashout = GERANTE_CASHOUT - cash_out
        
        print(f"   Recette gérante vs ERP : {format_currency(GERANTE_RECETTE)} vs {format_currency(cash_in)}")
        print(f"   ➜ Écart : {format_currency(ecart_recette)}")
        
        print(f"\n   Cashout gérante vs ERP : {format_currency(GERANTE_CASHOUT)} vs {format_currency(cash_out)}")
        print(f"   ➜ Écart : {format_currency(ecart_cashout)}")
        
        # 4. Analyse de l'écart recette
        print("\n🔍 ANALYSE DE L'ÉCART RECETTE:")
        print("-" * 50)
        print(f"   Écart total : {format_currency(ecart_recette)}")
        print(f"   - Ventes non enregistrées : {format_currency(VENTES_NON_ENREGISTREES)}")
        ecart_restant = ecart_recette - VENTES_NON_ENREGISTREES
        print(f"   = Écart restant inexpliqué : {format_currency(ecart_restant)}")
        
        # 5. Détail des mouvements
        print("\n📋 DÉTAIL DES MOUVEMENTS DE CAISSE:")
        print("-" * 120)
        print(f"{'ID':<6} {'Heure':<8} {'Type':<15} {'Montant':<15} {'Raison':<50}")
        print("-" * 120)
        
        for m in sorted(movements, key=lambda x: x.created_at):
            time_str = m.created_at.strftime('%H:%M') if m.created_at else 'N/A'
            mtype = (m.type or 'N/A')[:15]
            reason = (m.reason or '')[:50]
            print(f"{m.id:<6} {time_str:<8} {mtype:<15} {format_currency(m.amount):<15} {reason}")
        
        # 6. Résumé par type
        print("\n📊 RÉSUMÉ PAR TYPE:")
        print("-" * 50)
        
        by_type = {}
        for m in movements:
            mtype = (m.type or 'N/A').lower()
            if mtype not in by_type:
                by_type[mtype] = {'count': 0, 'total': 0.0}
            by_type[mtype]['count'] += 1
            by_type[mtype]['total'] += float(m.amount or 0)
        
        for mtype, data in sorted(by_type.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"   {mtype:<20}: {data['count']:>3} mouvement(s) = {format_currency(data['total'])}")
        
        # 7. Commandes créées ce jour
        print("\n📦 COMMANDES CRÉÉES LE 14/12:")
        print("-" * 50)
        
        orders = Order.query.filter(
            func.date(Order.created_at) == target_date
        ).all()
        
        pos_orders = [o for o in orders if o.order_type == 'in_store']
        shop_orders = [o for o in orders if o.order_type == 'customer_order']
        prod_orders = [o for o in orders if o.order_type == 'counter_production_request']
        
        pos_total = sum(float(o.total_amount or 0) for o in pos_orders)
        shop_total = sum(float(o.total_amount or 0) for o in shop_orders)
        
        print(f"   POS (Ventes Comptoir) : {len(pos_orders)} commandes = {format_currency(pos_total)}")
        print(f"   Shop (Commandes Client) : {len(shop_orders)} commandes = {format_currency(shop_total)}")
        print(f"   Production : {len(prod_orders)} ordres")
        
        # 8. Encaissements de commandes anciennes
        print("\n📅 ENCAISSEMENTS DE COMMANDES ANCIENNES (créées avant 14/12):")
        print("-" * 100)
        
        ancient_payments = []
        for m in movements:
            reason = (m.reason or '').lower()
            if 'commande #' in reason:
                # Extraire l'ID de la commande
                import re
                match = re.search(r'commande #(\d+)', reason)
                if match:
                    order_id = int(match.group(1))
                    order = Order.query.get(order_id)
                    if order and order.created_at.date() < target_date:
                        ancient_payments.append({
                            'movement_id': m.id,
                            'order_id': order_id,
                            'order_created': order.created_at.date(),
                            'amount': float(m.amount or 0),
                            'reason': m.reason
                        })
        
        if ancient_payments:
            total_ancient = sum(p['amount'] for p in ancient_payments)
            print(f"   Trouvé {len(ancient_payments)} encaissement(s) de commandes anciennes:")
            for p in ancient_payments:
                print(f"      - Commande #{p['order_id']} (créée {p['order_created']}): {format_currency(p['amount'])}")
            print(f"   Total : {format_currency(total_ancient)}")
        else:
            print("   Aucun encaissement de commande ancienne trouvé")
        
        # 9. Synthèse finale
        print("\n" + "="*80)
        print("📋 SYNTHÈSE FINALE")
        print("="*80)
        
        print(f"""
   📌 Recette gérante : {format_currency(GERANTE_RECETTE)}
   📌 Encaissements ERP : {format_currency(cash_in)}
   📌 Différence : {format_currency(ecart_recette)}
   
   📌 Ventes non enregistrées déclarées : {format_currency(VENTES_NON_ENREGISTREES)}
   📌 Écart restant à expliquer : {format_currency(ecart_restant)}
   
   💡 HYPOTHÈSES:
      - Acomptes ou paiements partiels non tracés ?
      - Ventes en espèces non enregistrées dans l'ERP ?
      - Encaissements manuels hors système ?
        """)
        
        print("="*80)
        print("✅ AUDIT TERMINÉ")
        print("="*80)

if __name__ == '__main__':
    main()
