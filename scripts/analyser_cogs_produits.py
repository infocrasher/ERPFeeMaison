#!/usr/bin/env python3
"""
Script pour analyser les produits avec un COGS anormalement élevé
Identifie les produits dont le coût dépasse le prix de vente
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

def analyser_cogs_produits(target_date_str):
    """Analyse les produits avec un COGS anormalement élevé"""
    app = create_app()
    
    with app.app_context():
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ Format de date invalide : {target_date_str}")
            return
        
        print("=" * 100)
        print("ANALYSE COGS PAR PRODUIT")
        print("=" * 100)
        print()
        print(f"📅 Date analysée : {target_date.strftime('%d/%m/%Y')}")
        print()
        
        # Récupérer les commandes du jour
        orders = Order.query.filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
        ).all()
        
        print(f"   Total commandes : {len(orders)}")
        print()
        
        # Analyser chaque produit vendu
        products_data = {}
        
        for order in orders:
            for item in order.items:
                product = item.product
                if not product:
                    continue
                
                product_id = product.id
                quantity = float(item.quantity or 0)
                unit_price = float(item.unit_price or 0)
                revenue = quantity * unit_price
                
                # Calculer le COGS pour ce produit
                if product.recipe_definition:
                    recipe = product.recipe_definition
                    yield_qty = float(recipe.yield_quantity or 1)
                    
                    cost_per_unit = 0.0
                    ingredients_detail = []
                    for ingredient in recipe.ingredients:
                        ingredient_product = ingredient.product
                        if ingredient_product:
                            qty_needed = float(ingredient.quantity_needed or 0)
                            ingredient_cost_price = float(ingredient_product.cost_price or 0)
                            cost_per_ingredient = (qty_needed / yield_qty) * ingredient_cost_price
                            cost_per_unit += cost_per_ingredient
                            ingredients_detail.append({
                                'name': ingredient_product.name,
                                'qty_needed': qty_needed,
                                'cost_price': ingredient_cost_price,
                                'cost_per_unit': cost_per_ingredient
                            })
                    
                    cogs = quantity * cost_per_unit
                    has_recipe = True
                else:
                    cost_per_unit = float(product.cost_price or 0)
                    cogs = quantity * cost_per_unit
                    has_recipe = False
                    ingredients_detail = []
                
                # Stocker les données
                if product_id not in products_data:
                    products_data[product_id] = {
                        'name': product.name,
                        'unit_price': unit_price,
                        'cost_per_unit': cost_per_unit,
                        'has_recipe': has_recipe,
                        'quantity_sold': 0,
                        'revenue': 0,
                        'cogs': 0,
                        'ingredients_detail': ingredients_detail
                    }
                
                products_data[product_id]['quantity_sold'] += quantity
                products_data[product_id]['revenue'] += revenue
                products_data[product_id]['cogs'] += cogs
        
        # Calculer marge pour chaque produit
        for product_id, data in products_data.items():
            data['margin'] = data['revenue'] - data['cogs']
            data['margin_pct'] = (data['margin'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
        
        # Trier par marge (du pire au meilleur)
        sorted_products = sorted(products_data.items(), key=lambda x: x[1]['margin'])
        
        # Afficher les produits avec marge négative
        print("=" * 100)
        print("🔴 PRODUITS AVEC MARGE NÉGATIVE (Coût > Prix de vente)")
        print("=" * 100)
        print()
        
        negative_margin_products = [(pid, data) for pid, data in sorted_products if data['margin'] < 0]
        
        if negative_margin_products:
            print(f"   Total : {len(negative_margin_products)} produits problématiques")
            print()
            print(f"   {'Produit':<35} {'Qté':<6} {'Prix':<10} {'Coût':<10} {'CA':<12} {'COGS':<12} {'Marge':<12} {'%':<8}")
            print("   " + "-" * 105)
            
            total_negative_cogs = 0
            total_negative_revenue = 0
            
            for product_id, data in negative_margin_products[:30]:  # Afficher les 30 pires
                name = data['name'][:33]
                qty = data['quantity_sold']
                price = data['unit_price']
                cost = data['cost_per_unit']
                revenue = data['revenue']
                cogs = data['cogs']
                margin = data['margin']
                margin_pct = data['margin_pct']
                
                total_negative_cogs += cogs
                total_negative_revenue += revenue
                
                print(f"   {name:<35} {qty:<6.0f} {price:<10.0f} {cost:<10.0f} {revenue:<12,.0f} {cogs:<12,.0f} {margin:<12,.0f} {margin_pct:<8.1f}%")
            
            print()
            print(f"   TOTAL marge négative : {total_negative_revenue - total_negative_cogs:,.0f} DA")
            print(f"   COGS excessif dû à ces produits : {total_negative_cogs:,.0f} DA")
            print()
            
            # Détail des recettes problématiques
            print("=" * 100)
            print("📋 DÉTAIL DES RECETTES PROBLÉMATIQUES")
            print("=" * 100)
            print()
            
            for product_id, data in negative_margin_products[:10]:  # Détail des 10 pires
                if data['has_recipe'] and data['ingredients_detail']:
                    print(f"   📦 {data['name']}")
                    print(f"      Prix de vente : {data['unit_price']:.0f} DA")
                    print(f"      Coût calculé  : {data['cost_per_unit']:.0f} DA")
                    print(f"      Ingrédients :")
                    for ing in data['ingredients_detail']:
                        print(f"         - {ing['name']}: {ing['qty_needed']:.2f} x {ing['cost_price']:.0f} DA = {ing['cost_per_unit']:.0f} DA/unité")
                    print()
        else:
            print("   ✅ Aucun produit avec marge négative")
            print()
        
        # Résumé global
        print("=" * 100)
        print("📊 RÉSUMÉ GLOBAL")
        print("=" * 100)
        print()
        
        total_revenue = sum(data['revenue'] for data in products_data.values())
        total_cogs = sum(data['cogs'] for data in products_data.values())
        total_margin = total_revenue - total_cogs
        
        print(f"   CA total       : {total_revenue:,.0f} DA")
        print(f"   COGS total     : {total_cogs:,.0f} DA")
        print(f"   Marge totale   : {total_margin:,.0f} DA ({total_margin/total_revenue*100:.1f}%)")
        print()
        
        if total_margin < 0:
            print("   ⚠️  PROBLÈME : Le COGS total dépasse le CA !")
            print()
            print("   CAUSES POSSIBLES :")
            print("   1. cost_price des ingrédients trop élevés")
            print("   2. yield_quantity des recettes trop bas")
            print("   3. quantity_needed des ingrédients trop élevés")
            print("   4. cost_price des produits sans recette incorrects")
            print()
            print("   RECOMMANDATION : Vérifier les recettes et cost_price des produits ci-dessus")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyser_cogs_produits.py YYYY-MM-DD")
        print("Exemple: python3 scripts/analyser_cogs_produits.py 2025-12-10")
        sys.exit(1)
    
    analyser_cogs_produits(sys.argv[1])

