#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les problèmes de KPI identifiés
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product, Recipe, RecipeIngredient
from app.employees.models import Employee, AttendanceSummary
from sqlalchemy import func

def diagnostic_problemes_kpi(target_date_str):
    """Diagnostic des problèmes de KPI"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 80)
        print("DIAGNOSTIC PROBLÈMES KPI")
        print("=" * 80)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # ========================================================================
        # 1. PROBLÈME COGS : Calcul incorrect
        # ========================================================================
        print("=" * 80)
        print("1️⃣  PROBLÈME COGS (Coût des marchandises vendues)")
        print("=" * 80)
        print()
        
        # Méthode actuelle (INCORRECTE) : utilise Product.cost_price
        cogs_actuel = db.session.query(
            func.sum(OrderItem.quantity * Product.cost_price)
        ).select_from(OrderItem).join(
            Product, Product.id == OrderItem.product_id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered'])
        ).scalar() or 0
        
        print(f"❌ COGS actuel (Product.cost_price) : {float(cogs_actuel):,.2f} DA")
        print("   PROBLÈME : Utilise le cost_price du produit fini, pas les ingrédients consommés")
        print()
        
        # Analyser les produits vendus
        orders = Order.query.filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered'])
        ).all()
        
        print(f"📋 Commandes analysées : {len(orders)}")
        print()
        
        # Calculer le COGS correct basé sur les recettes
        cogs_correct = Decimal('0.0')
        produits_avec_recette = 0
        produits_sans_recette = 0
        
        for order in orders:
            for item in order.items:
                product = item.product
                if not product:
                    continue
                
                quantity = Decimal(str(item.quantity))
                
                # Si le produit a une recette, calculer le coût via les ingrédients
                if product.recipe_definition:
                    produits_avec_recette += 1
                    recipe = product.recipe_definition
                    yield_qty = Decimal(str(recipe.yield_quantity or 1))
                    
                    # Coût par unité de produit = somme des coûts des ingrédients / yield
                    cost_per_unit = Decimal('0.0')
                    for ingredient in recipe.ingredients:
                        ingredient_product = ingredient.product
                        if ingredient_product:
                            qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                            cost_per_ingredient = (qty_needed / yield_qty) * Decimal(str(ingredient_product.cost_price or 0))
                            cost_per_unit += cost_per_ingredient
                    
                    cogs_correct += quantity * cost_per_unit
                else:
                    # Produit sans recette : utiliser cost_price
                    produits_sans_recette += 1
                    cost_price = Decimal(str(product.cost_price or 0))
                    cogs_correct += quantity * cost_price
        
        print(f"✅ COGS correct (basé sur recettes) : {float(cogs_correct):,.2f} DA")
        print(f"   Produits avec recette : {produits_avec_recette}")
        print(f"   Produits sans recette : {produits_sans_recette}")
        print()
        
        ecart_cogs = float(cogs_actuel) - float(cogs_correct)
        print(f"📊 ÉCART : {ecart_cogs:,.2f} DA")
        if abs(ecart_cogs) > 100:
            print(f"   ⚠️  Le COGS actuel est incorrect de {ecart_cogs:,.2f} DA")
        print()
        
        # ========================================================================
        # 2. PROBLÈME COÛT MAIN D'ŒUVRE : 0 alors qu'il y a des présences
        # ========================================================================
        print("=" * 80)
        print("2️⃣  PROBLÈME COÛT MAIN D'ŒUVRE")
        print("=" * 80)
        print()
        
        # Vérifier les AttendanceSummary
        summaries = AttendanceSummary.query.filter(
            AttendanceSummary.work_date == target_date
        ).all()
        
        print(f"📋 AttendanceSummary trouvés : {len(summaries)}")
        
        if summaries:
            print("   Détail des présences :")
            total_hours = 0.0
            total_cost = 0.0
            for summary in summaries:
                employee = summary.employee
                if employee:
                    worked = float(summary.worked_hours or 0)
                    overtime = float(summary.overtime_hours or 0)
                    hourly_rate = float(employee.hourly_rate or 0)
                    cost = (worked + overtime) * hourly_rate
                    total_hours += worked + overtime
                    total_cost += cost
                    print(f"      - {employee.name}: {worked + overtime:.2f}h @ {hourly_rate:.2f} DA/h = {cost:,.2f} DA")
            print()
            print(f"   Total heures : {total_hours:.2f}h")
            print(f"   Total coût : {total_cost:,.2f} DA")
        else:
            print("   ⚠️  Aucun AttendanceSummary trouvé pour cette date")
            print("   Vérifier si les pointages ont été traités")
        print()
        
        # Vérifier la requête actuelle
        labor_cost_actuel = db.session.query(
            func.sum((AttendanceSummary.worked_hours + AttendanceSummary.overtime_hours) * Employee.hourly_rate)
        ).select_from(AttendanceSummary).join(
            Employee, Employee.id == AttendanceSummary.employee_id
        ).filter(
            AttendanceSummary.work_date == target_date
        ).scalar() or 0
        
        print(f"💰 Coût main d'œuvre calculé : {float(labor_cost_actuel):,.2f} DA")
        print()
        
        # ========================================================================
        # 3. PROBLÈME PRÉSENCE : 0% alors qu'il y a des présences
        # ========================================================================
        print("=" * 80)
        print("3️⃣  PROBLÈME PRÉSENCE (0%)")
        print("=" * 80)
        print()
        
        total_employees = Employee.query.filter(Employee.is_active.is_(True)).count()
        print(f"👥 Total employés actifs : {total_employees}")
        
        if summaries:
            present = len([
                summary for summary in summaries
                if not summary.is_absent and summary.is_present
            ])
            print(f"✅ Présents : {present}")
            presence_rate = round((present / total_employees) * 100, 1) if total_employees else 0.0
            print(f"📊 Taux de présence : {presence_rate}%")
        else:
            print("   ⚠️  Aucune présence trouvée")
        print()
        
        # ========================================================================
        # 4. PROBLÈME VALEUR STOCK : Incohérence
        # ========================================================================
        print("=" * 80)
        print("4️⃣  PROBLÈME VALEUR STOCK")
        print("=" * 80)
        print()
        
        # Valeur calculée dans le dashboard
        stock_value_dashboard = float(db.session.query(func.sum(Product.total_stock_value)).scalar() or 0)
        print(f"📦 Valeur stock (dashboard) : {stock_value_dashboard:,.2f} DA")
        print()
        
        # Calculer manuellement
        products = Product.query.all()
        stock_value_manual = 0.0
        for product in products:
            # Utiliser total_stock_value si disponible, sinon calculer
            if product.total_stock_value:
                stock_value_manual += float(product.total_stock_value)
            else:
                # Calculer depuis les stocks par emplacement
                stock_total = (
                    float(product.stock_comptoir or 0) +
                    float(product.stock_ingredients_magasin or 0) +
                    float(product.stock_ingredients_local or 0) +
                    float(product.stock_consommables or 0)
                )
                cost_price = float(product.cost_price or 0)
                stock_value_manual += stock_total * cost_price
        
        print(f"📦 Valeur stock (calcul manuel) : {stock_value_manual:,.2f} DA")
        print()
        
        # ========================================================================
        # 5. RÉSUMÉ
        # ========================================================================
        print("=" * 80)
        print("5️⃣  RÉSUMÉ DES PROBLÈMES")
        print("=" * 80)
        print()
        
        print("❌ PROBLÈMES IDENTIFIÉS :")
        print()
        print("1. COGS incorrect :")
        print(f"   - Actuel : {float(cogs_actuel):,.2f} DA")
        print(f"   - Correct : {float(cogs_correct):,.2f} DA")
        print(f"   - Écart : {ecart_cogs:,.2f} DA")
        print("   - Solution : Calculer via recettes et ingrédients consommés")
        print()
        
        print("2. Coût main d'œuvre :")
        print(f"   - Calculé : {float(labor_cost_actuel):,.2f} DA")
        if summaries:
            print(f"   - Présences trouvées : {len(summaries)}")
            print("   - Solution : Vérifier la requête ou le traitement des pointages")
        else:
            print("   - Aucune présence trouvée")
            print("   - Solution : Vérifier le traitement des pointages ZKTeco")
        print()
        
        print("3. Présence 0% :")
        if summaries:
            present = len([s for s in summaries if not s.is_absent and s.is_present])
            print(f"   - Présences trouvées : {present}/{total_employees}")
            print("   - Solution : Vérifier le calcul du taux de présence")
        else:
            print("   - Aucune présence trouvée")
            print("   - Solution : Vérifier le traitement des pointages")
        print()
        
        print("4. Valeur stock :")
        print(f"   - Dashboard : {stock_value_dashboard:,.2f} DA")
        print(f"   - Calcul manuel : {stock_value_manual:,.2f} DA")
        if abs(stock_value_dashboard - stock_value_manual) > 1000:
            print(f"   - Écart : {abs(stock_value_dashboard - stock_value_manual):,.2f} DA")
            print("   - Solution : Vérifier le calcul de total_stock_value")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/diagnostic_problemes_kpi.py YYYY-MM-DD")
        print("Exemple: python3 scripts/diagnostic_problemes_kpi.py 2025-12-08")
        sys.exit(1)
    
    diagnostic_problemes_kpi(sys.argv[1])

