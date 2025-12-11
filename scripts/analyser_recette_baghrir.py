#!/usr/bin/env python3
"""
Script pour analyser la recette Baghrir Petite Taille Simple
et identifier pourquoi le coût est de 1375 DA au lieu d'un coût raisonnable
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Recipe, RecipeIngredient
from decimal import Decimal

def analyser_recette_baghrir():
    """Analyse la recette Baghrir Petite Taille Simple"""
    app = create_app()
    
    with app.app_context():
        print("=" * 100)
        print("ANALYSE RECETTE BAGHRIR PETITE TAILLE SIMPLE")
        print("=" * 100)
        print()
        
        # Trouver le produit
        product = Product.query.filter(Product.name.ilike('%Baghrir Petite Taille Simple%')).first()
        
        if not product:
            print("❌ Produit 'Baghrir Petite Taille Simple' non trouvé")
            return
        
        print(f"📦 PRODUIT TROUVÉ")
        print("-" * 100)
        print(f"   ID            : {product.id}")
        print(f"   Nom           : {product.name}")
        print(f"   Prix de vente : {product.selling_price} DA")
        print(f"   Cost Price    : {product.cost_price} DA")
        print()
        
        # Trouver la recette
        recipe = product.recipe_definition
        
        if not recipe:
            print("❌ Aucune recette trouvée pour ce produit")
            return
        
        print(f"📋 RECETTE")
        print("-" * 100)
        print(f"   ID             : {recipe.id}")
        print(f"   Nom            : {recipe.name}")
        print(f"   yield_quantity : {recipe.yield_quantity}")
        print()
        
        # Analyser les ingrédients
        print(f"🧂 INGRÉDIENTS")
        print("-" * 100)
        
        total_cost = Decimal('0.0')
        yield_qty = Decimal(str(recipe.yield_quantity or 1))
        
        print(f"   {'Ingrédient':<30} {'Qté Recette':<12} {'Cost/Unité':<12} {'Coût Total':<12} {'Coût/Produit':<12}")
        print("   " + "-" * 90)
        
        for ingredient in recipe.ingredients:
            ing_product = ingredient.product
            if ing_product:
                qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                cost_price = Decimal(str(ing_product.cost_price or 0))
                total_ingredient_cost = qty_needed * cost_price
                cost_per_product = total_ingredient_cost / yield_qty
                total_cost += cost_per_product
                
                print(f"   {ing_product.name[:28]:<30} {qty_needed:<12.2f} {cost_price:<12.2f} {total_ingredient_cost:<12.2f} {cost_per_product:<12.2f}")
        
        print()
        print(f"   TOTAL COÛT PAR UNITÉ : {total_cost:.2f} DA")
        print()
        
        # Analyse du problème
        print("=" * 100)
        print("🔍 ANALYSE DU PROBLÈME")
        print("=" * 100)
        print()
        
        selling_price = Decimal(str(product.selling_price or 0))
        
        print(f"   yield_quantity actuel : {yield_qty}")
        print(f"   Coût par unité calculé : {total_cost:.2f} DA")
        print(f"   Prix de vente : {selling_price:.2f} DA")
        print()
        
        if total_cost > selling_price:
            print(f"   ⚠️  PROBLÈME : Le coût ({total_cost:.2f} DA) dépasse le prix de vente ({selling_price:.2f} DA)")
            print()
            
            # Calculer le yield_quantity correct pour avoir une marge de 30%
            target_margin = 0.30
            target_cost = selling_price * Decimal(str(1 - target_margin))
            
            # Coût total de la recette (sans diviser par yield)
            total_recipe_cost = Decimal('0.0')
            for ingredient in recipe.ingredients:
                ing_product = ingredient.product
                if ing_product:
                    qty_needed = Decimal(str(ingredient.quantity_needed or 0))
                    cost_price = Decimal(str(ing_product.cost_price or 0))
                    total_recipe_cost += qty_needed * cost_price
            
            print(f"   Coût TOTAL de la recette : {total_recipe_cost:.2f} DA")
            print()
            
            # Calculer le yield_quantity correct
            if target_cost > 0:
                correct_yield = total_recipe_cost / target_cost
                print(f"   📊 CALCUL DU YIELD_QUANTITY CORRECT :")
                print(f"      Pour avoir une marge de 30% (coût = {target_cost:.2f} DA) :")
                print(f"      yield_quantity devrait être : {correct_yield:.0f}")
                print()
                print(f"   💡 SOLUTION :")
                print(f"      Mettre à jour yield_quantity de {yield_qty} à {correct_yield:.0f}")
                print(f"      (La recette produit probablement {correct_yield:.0f} unités, pas {yield_qty})")
        else:
            print(f"   ✅ Le coût ({total_cost:.2f} DA) est inférieur au prix de vente ({selling_price:.2f} DA)")
        
        print()
        
        # Lister toutes les recettes avec yield_quantity = 1 ou suspect
        print("=" * 100)
        print("📋 AUTRES RECETTES AVEC YIELD_QUANTITY = 1 (Potentiellement incorrectes)")
        print("=" * 100)
        print()
        
        suspicious_recipes = Recipe.query.filter(Recipe.yield_quantity <= 1).all()
        
        if suspicious_recipes:
            print(f"   Total : {len(suspicious_recipes)} recettes avec yield_quantity <= 1")
            print()
            print(f"   {'Recette':<40} {'yield_qty':<10} {'Produit associé':<30}")
            print("   " + "-" * 80)
            
            for rec in suspicious_recipes[:20]:
                product_name = rec.finished_product.name if rec.finished_product else 'N/A'
                print(f"   {rec.name[:38]:<40} {rec.yield_quantity:<10} {product_name[:28]:<30}")
        else:
            print("   ✅ Aucune recette suspecte")

if __name__ == '__main__':
    analyser_recette_baghrir()

