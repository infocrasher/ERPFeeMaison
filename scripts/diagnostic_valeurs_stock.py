#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les incohérences de valeur de stock
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product
from decimal import Decimal

def diagnostic_valeurs():
    """Diagnostic des incohérences de valeur de stock"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("DIAGNOSTIC DES INCOHÉRENCES DE VALEUR DE STOCK")
        print("=" * 120)
        print()
        
        # Récupérer tous les produits
        products = Product.query.all()
        
        incoherents = []
        
        for p in products:
            # Calculer la somme des valeurs par emplacement
            valeur_comptoir = float(p.valeur_stock_comptoir or 0)
            valeur_local = float(p.valeur_stock_ingredients_local or 0)
            valeur_magasin = float(p.valeur_stock_ingredients_magasin or 0)
            valeur_conso = float(p.valeur_stock_consommables or 0)
            
            somme_valeurs = valeur_comptoir + valeur_local + valeur_magasin + valeur_conso
            total_stock_value = float(p.total_stock_value or 0)
            
            # Vérifier l'incohérence
            diff = abs(somme_valeurs - total_stock_value)
            
            if diff > 1:  # Plus de 1 DA de différence
                # Calculer le stock total
                stock_comptoir = float(p.stock_comptoir or 0)
                stock_local = float(p.stock_ingredients_local or 0)
                stock_magasin = float(p.stock_ingredients_magasin or 0)
                stock_conso = float(p.stock_consommables or 0)
                stock_total = stock_comptoir + stock_local + stock_magasin + stock_conso
                
                cost_price = float(p.cost_price or 0)
                prix_vente = float(p.price or 0)
                
                incoherents.append({
                    'product': p,
                    'somme_valeurs': somme_valeurs,
                    'total_stock_value': total_stock_value,
                    'diff': diff,
                    'stock_total': stock_total,
                    'cost_price': cost_price,
                    'prix_vente': prix_vente,
                    'valeur_comptoir': valeur_comptoir
                })
        
        print(f"   Total produits incohérents : {len(incoherents)}")
        print()
        
        if incoherents:
            # Trier par différence décroissante
            incoherents.sort(key=lambda x: x['diff'], reverse=True)
            
            print(f"   {'ID':<6} {'Produit':<35} {'Σ Valeurs':<15} {'total_stock_value':<18} {'Diff':<12} {'Stock':<10} {'Cost Price':<12}")
            print("   " + "-" * 120)
            
            for i in incoherents[:30]:  # Afficher les 30 premiers
                p = i['product']
                print(f"   {p.id:<6} {p.name[:33]:<35} {i['somme_valeurs']:<15.2f} {i['total_stock_value']:<18.2f} {i['diff']:<12.2f} {i['stock_total']:<10.1f} {i['cost_price']:<12.2f}")
        
        print()
        print("=" * 120)
        print("ANALYSE DÉTAILLÉE DES CAS LES PLUS GRAVES")
        print("=" * 120)
        print()
        
        for i in incoherents[:5]:  # Analyser les 5 premiers
            p = i['product']
            print(f"📦 {p.name} (ID: {p.id})")
            print("-" * 80)
            print()
            
            print(f"   VALEURS DE STOCK PAR EMPLACEMENT :")
            print(f"   ├── valeur_stock_comptoir          : {float(p.valeur_stock_comptoir or 0):.4f} DA")
            print(f"   ├── valeur_stock_ingredients_local : {float(p.valeur_stock_ingredients_local or 0):.4f} DA")
            print(f"   ├── valeur_stock_ingredients_magasin : {float(p.valeur_stock_ingredients_magasin or 0):.4f} DA")
            print(f"   ├── valeur_stock_consommables      : {float(p.valeur_stock_consommables or 0):.4f} DA")
            print(f"   └── SOMME                          : {i['somme_valeurs']:.4f} DA")
            print()
            print(f"   total_stock_value (stocké)         : {i['total_stock_value']:.4f} DA")
            print(f"   DIFFÉRENCE                         : {i['diff']:.4f} DA")
            print()
            
            print(f"   QUANTITÉS DE STOCK PAR EMPLACEMENT :")
            print(f"   ├── stock_comptoir                 : {float(p.stock_comptoir or 0):.1f}")
            print(f"   ├── stock_ingredients_local        : {float(p.stock_ingredients_local or 0):.1f}")
            print(f"   ├── stock_ingredients_magasin      : {float(p.stock_ingredients_magasin or 0):.1f}")
            print(f"   ├── stock_consommables             : {float(p.stock_consommables or 0):.1f}")
            print(f"   └── TOTAL                          : {i['stock_total']:.1f}")
            print()
            
            print(f"   PRIX :")
            print(f"   ├── cost_price (PMP)               : {i['cost_price']:.4f} DA")
            print(f"   └── prix de vente                  : {i['prix_vente']:.2f} DA")
            print()
            
            # Analyse du bug
            print(f"   🔍 ANALYSE DU BUG :")
            
            if abs(i['cost_price'] - i['total_stock_value']) < 0.01:
                print(f"      ⚠️  cost_price = total_stock_value !")
                print(f"         Cela suggère que total_stock_value a été copié dans cost_price")
                print(f"         au lieu d'être divisé par le stock total.")
            
            if i['stock_total'] > 0:
                pmp_correct_via_somme = i['somme_valeurs'] / i['stock_total']
                pmp_correct_via_total = i['total_stock_value'] / i['stock_total']
                print(f"      PMP si on utilise Σ valeurs     : {pmp_correct_via_somme:.4f} DA")
                print(f"      PMP si on utilise total_stock_value : {pmp_correct_via_total:.4f} DA")
            
            # Vérifier si le produit a une recette
            if p.recipe_definition:
                recipe = p.recipe_definition
                total_recipe_cost = Decimal('0')
                yield_qty = Decimal(str(recipe.yield_quantity or 1))
                
                for ing in recipe.ingredients:
                    if ing.product:
                        qty = Decimal(str(ing.quantity_needed or 0))
                        cost = Decimal(str(ing.product.cost_price or 0))
                        total_recipe_cost += qty * cost
                
                cost_recette = float(total_recipe_cost / yield_qty)
                print(f"      PMP correct selon recette       : {cost_recette:.4f} DA")
            
            print()
            
        # Proposer la correction
        print("=" * 120)
        print("💡 SOLUTION : SYNCHRONISER total_stock_value AVEC LA SOMME DES VALEURS")
        print("=" * 120)
        print()
        print("   Le bug est que total_stock_value n'est pas égal à la somme des valeurs par emplacement.")
        print("   Cela cause un calcul de PMP erroné.")
        print()
        print("   Pour corriger :")
        print("   1. Recalculer total_stock_value = Σ valeurs par emplacement")
        print("   2. Recalculer cost_price = total_stock_value / stock_total")
        print()
        print("   Tapez 'CORRIGER' pour appliquer la correction : ", end='')
        
        response = input().strip()
        
        if response == 'CORRIGER':
            print()
            print("   🔄 Application des corrections...")
            print()
            
            for i in incoherents:
                p = i['product']
                
                old_total = p.total_stock_value
                old_cost = p.cost_price
                
                # 1. Synchroniser total_stock_value
                new_total = (
                    Decimal(str(p.valeur_stock_comptoir or 0)) +
                    Decimal(str(p.valeur_stock_ingredients_local or 0)) +
                    Decimal(str(p.valeur_stock_ingredients_magasin or 0)) +
                    Decimal(str(p.valeur_stock_consommables or 0))
                )
                p.total_stock_value = new_total
                
                # 2. Recalculer cost_price
                stock_total = (
                    float(p.stock_comptoir or 0) +
                    float(p.stock_ingredients_local or 0) +
                    float(p.stock_ingredients_magasin or 0) +
                    float(p.stock_consommables or 0)
                )
                
                if stock_total > 0:
                    p.cost_price = new_total / Decimal(str(stock_total))
                
                print(f"   ✅ {p.name} (ID: {p.id})")
                print(f"      total_stock_value : {old_total} → {p.total_stock_value}")
                print(f"      cost_price        : {old_cost} → {p.cost_price}")
                print()
            
            db.session.commit()
            print("   ✅ CORRECTIONS APPLIQUÉES !")
        else:
            print()
            print("   ❌ Corrections annulées")

if __name__ == '__main__':
    diagnostic_valeurs()

