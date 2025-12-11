#!/usr/bin/env python3
"""
Script pour analyser pourquoi le COGS est excessif
Compare les commandes créées vs livrées le 10/12/2025
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product, Recipe, RecipeIngredient, DeliveryDebt
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func

def analyser_cogs_excessif(target_date_str):
    """Analyse pourquoi le COGS est excessif"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 100)
        print("ANALYSE COGS EXCESSIF")
        print("=" * 100)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # 1. Commandes créées le 10/12
        print("=" * 100)
        print("1️⃣  COMMANDES CRÉÉES LE 10/12")
        print("=" * 100)
        print()
        
        orders_created = Order.query.filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
        ).all()
        
        print(f"   Total commandes créées : {len(orders_created)}")
        
        # Calculer COGS pour ces commandes
        cogs_created = Decimal('0.0')
        for order in orders_created:
            for item in order.items:
                product = item.product
                if not product:
                    continue
                
                quantity = Decimal(str(item.quantity))
                
                if product.recipe_definition:
                    recipe = product.recipe_definition
                    yield_qty = Decimal(str(recipe.yield_quantity or 1))
                    
                    cost_per_unit = Decimal('0.0')
                    for ingredient in recipe.ingredients:
                        ingredient_product = ingredient.product
                        if ingredient_product:
                            qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                            ingredient_cost_price = Decimal(str(ingredient_product.cost_price or 0))
                            cost_per_ingredient = (qty_needed / yield_qty) * ingredient_cost_price
                            cost_per_unit += cost_per_ingredient
                    
                    cogs_created += quantity * cost_per_unit
                else:
                    cost_price = Decimal(str(product.cost_price or 0))
                    cogs_created += quantity * cost_price
        
        print(f"   COGS commandes créées : {float(cogs_created):,.2f} DA")
        print()
        
        # 2. Commandes livrées le 10/12 (même logique que CA)
        print("=" * 100)
        print("2️⃣  COMMANDES LIVRÉES LE 10/12 (Logique CA)")
        print("=" * 100)
        print()
        
        # Charger toutes les commandes complétées
        all_orders = Order.query.filter(
            Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
        ).all()
        
        orders_delivered = []
        cogs_delivered = Decimal('0.0')
        
        def get_order_revenue_date(order):
            """Même logique que _get_order_revenue_date"""
            # Chercher une dette pour cette commande
            debt = DeliveryDebt.query.filter_by(order_id=order.id).first()
            if debt and debt.created_at:
                return debt.created_at.date()
            return order.due_date.date() if order.due_date else order.created_at.date()
        
        for order in all_orders:
            delivery_date = get_order_revenue_date(order)
            if delivery_date == target_date:
                orders_delivered.append(order)
                
                # Calculer COGS pour cette commande
                for item in order.items:
                    product = item.product
                    if not product:
                        continue
                    
                    quantity = Decimal(str(item.quantity))
                    
                    if product.recipe_definition:
                        recipe = product.recipe_definition
                        yield_qty = Decimal(str(recipe.yield_quantity or 1))
                        
                        cost_per_unit = Decimal('0.0')
                        for ingredient in recipe.ingredients:
                            ingredient_product = ingredient.product
                            if ingredient_product:
                                qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                                ingredient_cost_price = Decimal(str(ingredient_product.cost_price or 0))
                                cost_per_ingredient = (qty_needed / yield_qty) * ingredient_cost_price
                                cost_per_unit += cost_per_ingredient
                        
                        cogs_delivered += quantity * cost_per_unit
                    else:
                        cost_price = Decimal(str(product.cost_price or 0))
                        cogs_delivered += quantity * cost_price
        
        print(f"   Total commandes livrées : {len(orders_delivered)}")
        print(f"   COGS commandes livrées : {float(cogs_delivered):,.2f} DA")
        print()
        
        # 3. Comparaison
        print("=" * 100)
        print("3️⃣  COMPARAISON")
        print("=" * 100)
        print()
        
        print(f"   COGS créées le 10/12  : {float(cogs_created):,.2f} DA")
        print(f"   COGS livrées le 10/12  : {float(cogs_delivered):,.2f} DA")
        print(f"   Différence             : {float(cogs_created - cogs_delivered):,.2f} DA")
        print()
        
        # 4. Détail des commandes créées mais pas livrées le 10/12
        print("=" * 100)
        print("4️⃣  COMMANDES CRÉÉES MAIS PAS LIVRÉES LE 10/12")
        print("=" * 100)
        print()
        
        orders_created_not_delivered = []
        for order in orders_created:
            delivery_date = get_order_revenue_date(order)
            if delivery_date != target_date:
                orders_created_not_delivered.append((order, delivery_date))
        
        if orders_created_not_delivered:
            print(f"   Total : {len(orders_created_not_delivered)} commandes")
            print()
            print(f"   {'ID':<8} {'Créée':<12} {'Livrée':<12} {'Montant':<12} {'COGS':<12}")
            print("   " + "-" * 60)
            
            total_cogs_problem = Decimal('0.0')
            for order, delivery_date in orders_created_not_delivered[:20]:  # Afficher les 20 premières
                # Calculer montant et COGS
                order_amount = sum(float(item.quantity or 0) * float(item.unit_price or 0) for item in order.items)
                
                order_cogs = Decimal('0.0')
                for item in order.items:
                    product = item.product
                    if not product:
                        continue
                    
                    quantity = Decimal(str(item.quantity))
                    
                    if product.recipe_definition:
                        recipe = product.recipe_definition
                        yield_qty = Decimal(str(recipe.yield_quantity or 1))
                        
                        cost_per_unit = Decimal('0.0')
                        for ingredient in recipe.ingredients:
                            ingredient_product = ingredient.product
                            if ingredient_product:
                                qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                                ingredient_cost_price = Decimal(str(ingredient_product.cost_price or 0))
                                cost_per_ingredient = (qty_needed / yield_qty) * ingredient_cost_price
                                cost_per_unit += cost_per_ingredient
                        
                        order_cogs += quantity * cost_per_unit
                    else:
                        cost_price = Decimal(str(product.cost_price or 0))
                        order_cogs += quantity * cost_price
                
                total_cogs_problem += order_cogs
                
                created_str = order.created_at.strftime('%d/%m') if order.created_at else 'N/A'
                delivered_str = delivery_date.strftime('%d/%m') if delivery_date else 'N/A'
                
                print(f"   {order.id:<8} {created_str:<12} {delivered_str:<12} {order_amount:>10,.0f} {float(order_cogs):>10,.0f}")
            
            if len(orders_created_not_delivered) > 20:
                print(f"   ... et {len(orders_created_not_delivered) - 20} autres")
            
            print()
            print(f"   COGS total de ces commandes : {float(total_cogs_problem):,.2f} DA")
            print()
            print("   ⚠️  Ces commandes sont comptées dans le COGS du 10/12")
            print("       mais leur CA sera compté à la date de livraison")
            print("       C'est la cause de l'incohérence !")
        else:
            print("   ✅ Toutes les commandes créées le 10/12 sont aussi livrées le 10/12")
        
        print()
        print("=" * 100)
        print("5️⃣  RECOMMANDATION")
        print("=" * 100)
        print()
        print("   Le COGS doit utiliser la MÊME logique de date que le CA :")
        print("   - Si commande a une dette : utiliser DeliveryDebt.created_at")
        print("   - Sinon : utiliser Order.due_date")
        print("   - Pas Order.created_at !")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyser_cogs_excessif.py YYYY-MM-DD")
        print("Exemple: python3 scripts/analyser_cogs_excessif.py 2025-12-10")
        sys.exit(1)
    
    analyser_cogs_excessif(sys.argv[1])

