#!/usr/bin/env python3
"""
Script pour analyser les problèmes restants :
1. Flux caisse -2,490 DA
2. Présence 0% (AttendanceSummary manquant)
3. Valeur stock incorrecte
"""

import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Product
from app.sales.models import CashMovement
from app.employees.models import Employee, AttendanceRecord, AttendanceSummary
from sqlalchemy import func

def analyser_problemes_restants(target_date_str):
    """Analyse les problèmes restants"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 80)
        print("ANALYSE PROBLÈMES RESTANTS")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # ========================================================================
        # 1. FLUX CAISSE -2,490 DA
        # ========================================================================
        print("=" * 80)
        print("1️⃣  FLUX CAISSE -2,490 DA")
        print("=" * 80)
        print()
        
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == target_date
        ).order_by(CashMovement.created_at).all()
        
        entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
        exit_types = {'sortie', 'retrait', 'frais', 'paiement'}
        
        cash_in = 0.0
        cash_out = 0.0
        
        print("📋 Détail des mouvements :")
        print()
        
        for movement in movements:
            movement_type = (movement.type or '').lower()
            amount = float(movement.amount or 0)
            
            if movement_type in exit_types:
                cash_out += amount
                print(f"   ❌ SORTIE ({movement_type}) : {amount:,.2f} DA")
                print(f"      Raison: {movement.reason or 'N/A'}")
                if movement.notes:
                    print(f"      Notes: {movement.notes[:100]}")
                print()
            elif movement_type in entry_types or amount >= 0:
                cash_in += amount
                print(f"   ✅ ENTRÉE ({movement_type}) : {amount:,.2f} DA")
                print(f"      Raison: {movement.reason or 'N/A'}")
                if movement.notes:
                    print(f"      Notes: {movement.notes[:100]}")
                print()
        
        net = cash_in - cash_out
        
        print(f"💰 Total entrées : {cash_in:,.2f} DA")
        print(f"💰 Total sorties : {cash_out:,.2f} DA")
        print(f"📊 Net : {net:,.2f} DA")
        print()
        
        if net < 0:
            print("💡 EXPLICATION :")
            print(f"   Le flux caisse est négatif car il y a eu une sortie importante de {cash_out:,.2f} DA")
            print("   (retrait, paiement fournisseur, frais, etc.)")
            print("   C'est NORMAL si une sortie importante a été effectuée ce jour-là.")
        print()
        
        # ========================================================================
        # 2. PRÉSENCE 0% - AttendanceSummary manquant
        # ========================================================================
        print("=" * 80)
        print("2️⃣  PRÉSENCE 0% - AttendanceSummary manquant")
        print("=" * 80)
        print()
        
        # Vérifier AttendanceSummary
        summaries = AttendanceSummary.query.filter(
            AttendanceSummary.work_date == target_date
        ).all()
        
        print(f"📋 AttendanceSummary trouvés : {len(summaries)}")
        print()
        
        # Vérifier AttendanceRecord (pointages bruts)
        records = AttendanceRecord.query.filter(
            func.date(AttendanceRecord.timestamp) == target_date
        ).all()
        
        print(f"📋 AttendanceRecord (pointages bruts) trouvés : {len(records)}")
        
        if records:
            print()
            print("   Détail des pointages :")
            employees_with_records = {}
            for record in records:
                emp_id = record.employee_id
                if emp_id not in employees_with_records:
                    employee = record.employee
                    employees_with_records[emp_id] = {
                        'name': employee.name if employee else f'ID {emp_id}',
                        'records': []
                    }
                employees_with_records[emp_id]['records'].append(record)
            
            for emp_id, data in employees_with_records.items():
                print(f"   - {data['name']} : {len(data['records'])} pointage(s)")
                for record in data['records']:
                    print(f"      {record.timestamp.strftime('%H:%M:%S')} - {record.punch_type}")
        else:
            print("   ⚠️  Aucun pointage trouvé pour cette date")
        print()
        
        if len(records) > 0 and len(summaries) == 0:
            print("❌ PROBLÈME IDENTIFIÉ :")
            print("   Il y a des pointages (AttendanceRecord) mais pas de résumés (AttendanceSummary)")
            print("   Les AttendanceSummary doivent être créés depuis les AttendanceRecord")
            print()
            print("💡 SOLUTION :")
            print("   Il faut créer un script ou une tâche qui génère les AttendanceSummary")
            print("   depuis les AttendanceRecord pour chaque jour.")
        elif len(records) == 0:
            print("⚠️  Aucun pointage trouvé pour cette date")
            print("   Vérifier si les pointages ZKTeco ont été reçus et enregistrés")
        print()
        
        # ========================================================================
        # 3. VALEUR STOCK INCORRECTE
        # ========================================================================
        print("=" * 80)
        print("3️⃣  VALEUR STOCK INCORRECTE")
        print("=" * 80)
        print()
        
        # Valeur dans le dashboard (total_stock_value)
        stock_value_dashboard = float(db.session.query(func.sum(Product.total_stock_value)).scalar() or 0)
        print(f"📦 Valeur stock (dashboard - total_stock_value) : {stock_value_dashboard:,.2f} DA")
        print()
        
        # Calculer manuellement depuis les stocks par emplacement
        products = Product.query.all()
        stock_value_manual = 0.0
        products_with_issues = []
        
        for product in products:
            # Utiliser total_stock_value si disponible
            if product.total_stock_value:
                stock_value_manual += float(product.total_stock_value)
            else:
                # Calculer depuis les stocks
                stock_total = (
                    float(product.stock_comptoir or 0) +
                    float(product.stock_ingredients_magasin or 0) +
                    float(product.stock_ingredients_local or 0) +
                    float(product.stock_consommables or 0)
                )
                cost_price = float(product.cost_price or 0)
                calculated_value = stock_total * cost_price
                stock_value_manual += calculated_value
                
                # Vérifier si total_stock_value est différent
                if product.total_stock_value and abs(float(product.total_stock_value) - calculated_value) > 0.01:
                    products_with_issues.append({
                        'name': product.name,
                        'total_stock_value': float(product.total_stock_value),
                        'calculated': calculated_value,
                        'diff': abs(float(product.total_stock_value) - calculated_value)
                    })
        
        print(f"📦 Valeur stock (calcul manuel) : {stock_value_manual:,.2f} DA")
        print()
        
        if abs(stock_value_dashboard - stock_value_manual) > 1000:
            print(f"⚠️  ÉCART DÉTECTÉ : {abs(stock_value_dashboard - stock_value_manual):,.2f} DA")
            print()
        
        if products_with_issues:
            print(f"📋 Produits avec total_stock_value incorrect : {len(products_with_issues)}")
            print()
            for product in products_with_issues[:10]:  # Limiter à 10
                print(f"   - {product['name']}")
                print(f"     total_stock_value : {product['total_stock_value']:,.2f} DA")
                print(f"     Calculé : {product['calculated']:,.2f} DA")
                print(f"     Écart : {product['diff']:,.2f} DA")
                print()
            if len(products_with_issues) > 10:
                print(f"   ... et {len(products_with_issues) - 10} autres")
            print()
        
        # Vérifier comment total_stock_value est mis à jour
        print("💡 VÉRIFICATION :")
        print("   Le total_stock_value doit être mis à jour lors de :")
        print("   - Ajustements de stock")
        print("   - Achats")
        print("   - Ventes")
        print("   - Transfers")
        print()
        
        # ========================================================================
        # RÉSUMÉ
        # ========================================================================
        print("=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print()
        
        print("1. FLUX CAISSE :")
        print(f"   Net : {net:,.2f} DA")
        if net < 0:
            print("   ✅ Normal si sortie importante effectuée")
        print()
        
        print("2. PRÉSENCE :")
        print(f"   AttendanceRecord : {len(records)}")
        print(f"   AttendanceSummary : {len(summaries)}")
        if len(records) > 0 and len(summaries) == 0:
            print("   ❌ Problème : AttendanceSummary non créé")
        print()
        
        print("3. VALEUR STOCK :")
        print(f"   Dashboard : {stock_value_dashboard:,.2f} DA")
        print(f"   Calcul manuel : {stock_value_manual:,.2f} DA")
        if abs(stock_value_dashboard - stock_value_manual) > 1000:
            print(f"   ⚠️  Écart : {abs(stock_value_dashboard - stock_value_manual):,.2f} DA")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyser_problemes_restants.py YYYY-MM-DD")
        print("Exemple: python3 scripts/analyser_problemes_restants.py 2025-12-08")
        sys.exit(1)
    
    analyser_problemes_restants(sys.argv[1])

