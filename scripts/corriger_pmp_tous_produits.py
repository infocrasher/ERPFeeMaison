#!/usr/bin/env python3
"""
Script pour corriger le PMP de tous les produits avec cost_price anormal
Le problème : la valeur_stock_comptoir est incorrecte, ce qui fausse le calcul du PMP
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Recipe
from decimal import Decimal

def corriger_pmp_tous():
    """Corrige le PMP de tous les produits anormaux"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("CORRECTION DU PMP POUR TOUS LES PRODUITS ANORMAUX")
        print("=" * 120)
        print()
        
        # Trouver tous les produits où cost_price > price
        products_anormaux = Product.query.filter(
            Product.cost_price > Product.price,
            Product.price > 0
        ).all()
        
        print(f"   Total produits avec PMP anormal : {len(products_anormaux)}")
        print()
        
        corrections = []
        
        for product in products_anormaux:
            print("=" * 120)
            print(f"📦 {product.name} (ID: {product.id})")
            print("-" * 120)
            
            # Données actuelles
            prix_vente = float(product.price or 0)
            cost_actuel = float(product.cost_price or 0)
            stock_comptoir = float(product.stock_comptoir or 0)
            valeur_comptoir = float(product.valeur_stock_comptoir or 0)
            
            print(f"   Prix de vente         : {prix_vente:.2f} DA")
            print(f"   Cost Price actuel     : {cost_actuel:.2f} DA")
            print(f"   Stock comptoir        : {stock_comptoir:.0f}")
            print(f"   Valeur stock comptoir : {valeur_comptoir:.2f} DA")
            print()
            
            # Déterminer le cost_price correct
            recipe = product.recipe_definition
            cost_correct = None
            source = None
            
            if recipe:
                # Calculer le coût via la recette
                total_recipe_cost = Decimal('0')
                yield_qty = Decimal(str(recipe.yield_quantity or 1))
                
                for ing in recipe.ingredients:
                    if ing.product:
                        qty = Decimal(str(ing.quantity_needed or 0))
                        cost = Decimal(str(ing.product.cost_price or 0))
                        total_recipe_cost += qty * cost
                
                cost_correct = float(total_recipe_cost / yield_qty)
                source = "recette"
                
                print(f"   📋 RECETTE : {recipe.name}")
                print(f"      Coût total ingrédients : {total_recipe_cost:.2f} DA")
                print(f"      yield_quantity : {yield_qty}")
                print(f"      Coût par unité : {cost_correct:.2f} DA")
            else:
                # Pas de recette - on ne peut pas calculer
                print(f"   ❌ Pas de recette - impossible de calculer le coût correct")
                continue
            
            print()
            print(f"   🔍 ANALYSE :")
            print(f"      Cost Price actuel    : {cost_actuel:.2f} DA")
            print(f"      Cost Price correct   : {cost_correct:.2f} DA (via {source})")
            print(f"      Écart                : {cost_actuel - cost_correct:.2f} DA")
            print()
            
            # Calculer la valeur stock correcte
            valeur_correcte = stock_comptoir * cost_correct
            
            print(f"   💰 VALEURS DE STOCK :")
            print(f"      Valeur actuelle   : {valeur_comptoir:.2f} DA")
            print(f"      Valeur correcte   : {valeur_correcte:.2f} DA")
            print(f"      Écart             : {valeur_comptoir - valeur_correcte:.2f} DA")
            print()
            
            if cost_correct > 0:
                corrections.append({
                    'product': product,
                    'cost_actuel': cost_actuel,
                    'cost_correct': cost_correct,
                    'valeur_actuelle': valeur_comptoir,
                    'valeur_correcte': valeur_correcte,
                    'stock_comptoir': stock_comptoir
                })
        
        # Résumé et confirmation
        print()
        print("=" * 120)
        print("📊 RÉSUMÉ DES CORRECTIONS À APPLIQUER")
        print("=" * 120)
        print()
        
        print(f"   {'ID':<6} {'Produit':<35} {'Cost Actuel':<15} {'Cost Correct':<15} {'Valeur Actuelle':<18} {'Valeur Correcte':<18}")
        print("   " + "-" * 110)
        
        for c in corrections:
            p = c['product']
            print(f"   {p.id:<6} {p.name[:33]:<35} {c['cost_actuel']:<15.2f} {c['cost_correct']:<15.2f} {c['valeur_actuelle']:<18.2f} {c['valeur_correcte']:<18.2f}")
        
        print()
        print("=" * 120)
        print("⚠️  ATTENTION : Cette correction va modifier :")
        print("   - Le cost_price de chaque produit")
        print("   - La valeur_stock_comptoir de chaque produit")
        print("   - Le total_stock_value sera recalculé")
        print()
        print("   Tapez 'CORRIGER TOUT' pour appliquer les corrections : ", end='')
        
        response = input().strip()
        
        if response == 'CORRIGER TOUT':
            print()
            print("   🔄 Application des corrections...")
            print()
            
            for c in corrections:
                product = c['product']
                
                old_cost = product.cost_price
                old_valeur = product.valeur_stock_comptoir
                
                # Appliquer les corrections
                product.cost_price = Decimal(str(c['cost_correct']))
                product.valeur_stock_comptoir = Decimal(str(c['valeur_correcte']))
                
                # Recalculer total_stock_value
                product.total_stock_value = (
                    Decimal(str(product.valeur_stock_comptoir or 0)) +
                    Decimal(str(product.valeur_stock_ingredients_local or 0)) +
                    Decimal(str(product.valeur_stock_ingredients_magasin or 0)) +
                    Decimal(str(product.valeur_stock_consommables or 0))
                )
                
                print(f"   ✅ {product.name}")
                print(f"      cost_price : {old_cost} → {product.cost_price}")
                print(f"      valeur_stock_comptoir : {old_valeur} → {product.valeur_stock_comptoir}")
                print()
            
            db.session.commit()
            print("   ✅ TOUTES LES CORRECTIONS ONT ÉTÉ APPLIQUÉES !")
            print()
            print("   Le dashboard devrait maintenant afficher des marges correctes.")
        else:
            print()
            print("   ❌ Corrections annulées")

if __name__ == '__main__':
    corriger_pmp_tous()

