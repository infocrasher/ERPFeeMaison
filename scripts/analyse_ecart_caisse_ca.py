#!/usr/bin/env python3
"""
Script pour analyser l'écart entre les entrées de caisse et le CA
"""

import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from app.sales.models import CashMovement
from sqlalchemy import func

def analyser_ecart_caisse_ca(target_date_str):
    """Analyse l'écart entre entrées de caisse et CA"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 80)
        print("ANALYSE ÉCART CAISSE / CA")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # Tous les mouvements de caisse du jour
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == target_date
        ).order_by(CashMovement.created_at).all()
        
        print(f"💵 Total mouvements de caisse : {len(movements)}")
        print()
        
        # Analyser par type
        entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
        exit_types = {'sortie', 'retrait', 'frais', 'paiement'}
        
        movements_by_type = {}
        cash_in_by_type = {}
        cash_out_by_type = {}
        
        for movement in movements:
            movement_type = (movement.type or '').lower()
            amount = float(movement.amount or 0)
            
            # Classer le mouvement
            if movement_type in exit_types:
                cash_out_by_type[movement_type] = cash_out_by_type.get(movement_type, 0) + amount
            elif movement_type in entry_types or amount >= 0:
                cash_in_by_type[movement_type] = cash_in_by_type.get(movement_type, 0) + amount
            else:
                cash_out_by_type[movement_type] = cash_out_by_type.get(movement_type, 0) + abs(amount)
            
            movements_by_type[movement_type] = movements_by_type.get(movement_type, 0) + 1
        
        print("=" * 80)
        print("ENTRÉES DE CAISSE PAR TYPE")
        print("=" * 80)
        print()
        
        total_cash_in = 0
        for movement_type, total in sorted(cash_in_by_type.items(), key=lambda x: x[1], reverse=True):
            count = movements_by_type.get(movement_type, 0)
            total_cash_in += total
            print(f"   {movement_type:20s} : {total:10,.2f} DA ({count} mouvements)")
        
        print()
        print(f"   TOTAL ENTREES : {total_cash_in:,.2f} DA")
        print()
        
        print("=" * 80)
        print("SORTIES DE CAISSE PAR TYPE")
        print("=" * 80)
        print()
        
        total_cash_out = 0
        for movement_type, total in sorted(cash_out_by_type.items(), key=lambda x: x[1], reverse=True):
            count = movements_by_type.get(movement_type, 0)
            total_cash_out += total
            print(f"   {movement_type:20s} : {total:10,.2f} DA ({count} mouvements)")
        
        print()
        print(f"   TOTAL SORTIES : {total_cash_out:,.2f} DA")
        print()
        print(f"   NET : {total_cash_in - total_cash_out:,.2f} DA")
        print()
        
        # Détail des mouvements "vente"
        print("=" * 80)
        print("DÉTAIL DES MOUVEMENTS TYPE 'VENTE'")
        print("=" * 80)
        print()
        
        sales_movements = [m for m in movements if (m.type or '').lower() == 'vente']
        if sales_movements:
            print(f"📊 Total mouvements 'vente' : {len(sales_movements)}")
            print()
            total_sales_movements = 0
            for movement in sales_movements[:10]:  # Limiter à 10
                amount = float(movement.amount or 0)
                total_sales_movements += amount
                print(f"   - {movement.created_at.strftime('%H:%M:%S')} : {amount:,.2f} DA")
                print(f"     Raison: {movement.reason or 'N/A'}")
                if movement.notes:
                    print(f"     Notes: {movement.notes[:100]}")
                print()
            if len(sales_movements) > 10:
                print(f"   ... et {len(sales_movements) - 10} autres")
            print(f"   Total mouvements 'vente' : {total_sales_movements:,.2f} DA")
        else:
            print("   Aucun mouvement type 'vente' trouvé")
        print()
        
        # Détail des mouvements "entrée"
        print("=" * 80)
        print("DÉTAIL DES MOUVEMENTS TYPE 'ENTRÉE'")
        print("=" * 80)
        print()
        
        entry_movements = [m for m in movements if (m.type or '').lower() == 'entrée']
        if entry_movements:
            print(f"📊 Total mouvements 'entrée' : {len(entry_movements)}")
            print()
            total_entry_movements = 0
            for movement in entry_movements[:10]:  # Limiter à 10
                amount = float(movement.amount or 0)
                total_entry_movements += amount
                print(f"   - {movement.created_at.strftime('%H:%M:%S')} : {amount:,.2f} DA")
                print(f"     Raison: {movement.reason or 'N/A'}")
                if movement.notes:
                    print(f"     Notes: {movement.notes[:100]}")
                print()
            if len(entry_movements) > 10:
                print(f"   ... et {len(entry_movements) - 10} autres")
            print(f"   Total mouvements 'entrée' : {total_entry_movements:,.2f} DA")
        else:
            print("   Aucun mouvement type 'entrée' trouvé")
        print()
        
        # Comparaison avec CA
        from app.reports.services import _compute_revenue
        ca_calcule = _compute_revenue(report_date=target_date)
        
        print("=" * 80)
        print("COMPARAISON CAISSE / CA")
        print("=" * 80)
        print()
        print(f"💰 CA calculé (OrderItem) : {ca_calcule:,.2f} DA")
        print(f"💵 Entrées de caisse totales : {total_cash_in:,.2f} DA")
        print()
        
        ecart = total_cash_in - ca_calcule
        print(f"📊 ÉCART : {ecart:,.2f} DA")
        print()
        
        if ecart > 0:
            print("💡 ANALYSE :")
            print(f"   Les entrées de caisse sont supérieures au CA de {ecart:,.2f} DA")
            print("   Cela signifie qu'il y a des mouvements de caisse qui ne sont pas des ventes :")
            print("   - Acomptes reçus")
            print("   - Dépôts clients")
            print("   - Autres entrées non liées aux ventes")
        elif ecart < 0:
            print("💡 ANALYSE :")
            print(f"   Les entrées de caisse sont inférieures au CA de {abs(ecart):,.2f} DA")
            print("   Cela peut indiquer :")
            print("   - Des ventes non encaissées (crédit)")
            print("   - Des ventes payées par carte/banque")
        else:
            print("✅ Les entrées de caisse correspondent au CA")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyse_ecart_caisse_ca.py YYYY-MM-DD")
        print("Exemple: python3 scripts/analyse_ecart_caisse_ca.py 2025-12-08")
        sys.exit(1)
    
    analyser_ecart_caisse_ca(sys.argv[1])

