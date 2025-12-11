#!/usr/bin/env python3
"""
Script pour investiguer comment le cost_price d'un produit a été calculé
Usage: python3 scripts/investiguer_produit.py <product_id>
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Order, OrderItem, Recipe, RecipeIngredient
from app.purchases.models import Purchase, PurchaseItem
from app.stock.models import StockMovement, StockTransfer, StockTransferLine
from decimal import Decimal
from sqlalchemy import func

def investiguer_produit(product_id):
    """Investigation complète du cost_price d'un produit"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print(f"INVESTIGATION COST_PRICE - PRODUIT ID: {product_id}")
        print("=" * 120)
        print()
        
        # Trouver le produit
        product = Product.query.get(product_id)
        
        if not product:
            print(f"❌ Produit ID {product_id} non trouvé")
            return
        
        print(f"📦 PRODUIT TROUVÉ")
        print("-" * 120)
        print(f"   ID            : {product.id}")
        print(f"   Nom           : {product.name}")
        print(f"   Prix de vente : {product.price} DA")
        print(f"   Cost Price    : {product.cost_price} DA")
        print()
        
        # ========================================================================
        # 1. VÉRIFIER SI LE PRODUIT A UNE RECETTE
        # ========================================================================
        print("=" * 120)
        print("1️⃣  RECETTE ASSOCIÉE")
        print("=" * 120)
        print()
        
        recipe = product.recipe_definition
        if recipe:
            print(f"   ✅ CE PRODUIT A UNE RECETTE !")
            print(f"   Recette ID      : {recipe.id}")
            print(f"   Nom             : {recipe.name}")
            print(f"   yield_quantity  : {recipe.yield_quantity}")
            print()
            
            # Calculer le coût via la recette
            print("   📋 INGRÉDIENTS DE LA RECETTE :")
            print("-" * 120)
            
            total_recipe_cost = Decimal('0')
            yield_qty = Decimal(str(recipe.yield_quantity or 1))
            
            print(f"   {'Ingrédient':<40} {'Qté Recette':<15} {'Cost/Unité':<15} {'Coût Total':<15}")
            print("   " + "-" * 90)
            
            for ing in recipe.ingredients:
                if ing.product:
                    qty = Decimal(str(ing.quantity_needed or 0))
                    cost = Decimal(str(ing.product.cost_price or 0))
                    ing_cost = qty * cost
                    total_recipe_cost += ing_cost
                    print(f"   {ing.product.name[:38]:<40} {qty:<15.2f} {cost:<15.4f} {ing_cost:<15.2f}")
            
            print()
            print(f"   COÛT TOTAL RECETTE   : {total_recipe_cost:.2f} DA")
            print(f"   yield_quantity       : {yield_qty}")
            print(f"   COÛT PAR UNITÉ       : {total_recipe_cost / yield_qty:.2f} DA")
            print()
            
            # Comparer avec le cost_price actuel
            cost_per_unit = float(total_recipe_cost / yield_qty)
            actual_cost = float(product.cost_price or 0)
            
            print(f"   🔍 COMPARAISON :")
            print(f"      Coût calculé (recette) : {cost_per_unit:.2f} DA")
            print(f"      Cost Price actuel      : {actual_cost:.2f} DA")
            
            if abs(cost_per_unit - actual_cost) < 1:
                print(f"      ✅ Le cost_price correspond au calcul de la recette")
            else:
                diff = abs(cost_per_unit - actual_cost)
                print(f"      ⚠️  Différence : {diff:.2f} DA")
        else:
            print("   ❌ Pas de recette associée")
        print()
        
        # ========================================================================
        # 2. HISTORIQUE DES BONS D'ACHAT
        # ========================================================================
        print("=" * 120)
        print("2️⃣  BONS D'ACHAT")
        print("=" * 120)
        print()
        
        purchase_items = PurchaseItem.query.filter_by(product_id=product_id).join(
            Purchase
        ).order_by(Purchase.created_at.desc()).all()
        
        if purchase_items:
            print(f"   Total bons d'achat : {len(purchase_items)}")
            print()
            print(f"   {'Date':<12} {'Réf':<25} {'Qté':<12} {'Prix/U':<15} {'Total':<15} {'Statut':<12}")
            print("   " + "-" * 95)
            
            total_qty = Decimal('0')
            total_value = Decimal('0')
            
            for item in purchase_items:
                purchase = item.purchase
                qty = Decimal(str(item.original_quantity or item.quantity_ordered or 0))
                unit_price = Decimal(str(item.original_unit_price or item.unit_price or 0))
                
                if qty > 0:
                    total_qty += qty
                    total_value += qty * unit_price
                
                date_str = purchase.created_at.strftime('%d/%m/%Y') if purchase.created_at else 'N/A'
                ref = (purchase.reference or 'N/A')[:23]
                status = str(purchase.status.value if purchase.status else 'N/A')
                
                print(f"   {date_str:<12} {ref:<25} {qty:<12.0f} {unit_price:<15.2f} {qty * unit_price:<15.2f} {status:<12}")
            
            print()
            if total_qty > 0:
                pmp_achats = total_value / total_qty
                print(f"   TOTAL : {total_qty:.0f} unités pour {total_value:.2f} DA")
                print(f"   PMP basé sur achats : {pmp_achats:.2f} DA")
        else:
            print("   ❌ Aucun bon d'achat trouvé")
        print()
        
        # ========================================================================
        # 3. VALEURS DE STOCK
        # ========================================================================
        print("=" * 120)
        print("3️⃣  VALEURS DE STOCK")
        print("=" * 120)
        print()
        
        print(f"   Stock comptoir             : {product.stock_comptoir}")
        print(f"   Stock ingrédients local    : {product.stock_ingredients_local}")
        print(f"   Stock ingrédients magasin  : {product.stock_ingredients_magasin}")
        print()
        print(f"   Valeur stock comptoir      : {product.valeur_stock_comptoir}")
        print(f"   Valeur stock local         : {product.valeur_stock_ingredients_local}")
        print(f"   Valeur stock magasin       : {product.valeur_stock_ingredients_magasin}")
        print()
        print(f"   total_stock_value          : {product.total_stock_value}")
        print()
        
        # Calculer le PMP depuis la valeur du stock
        total_stock = float(product.stock_comptoir or 0) + float(product.stock_ingredients_local or 0) + float(product.stock_ingredients_magasin or 0)
        total_value = float(product.total_stock_value or 0)
        
        if total_stock > 0:
            pmp_from_stock = total_value / total_stock
            print(f"   🔍 PMP calculé depuis stock :")
            print(f"      total_stock_value / total_stock = {total_value:.2f} / {total_stock:.0f} = {pmp_from_stock:.2f} DA")
        print()
        
        # ========================================================================
        # 4. MOUVEMENTS DE STOCK RÉCENTS
        # ========================================================================
        print("=" * 120)
        print("4️⃣  MOUVEMENTS DE STOCK (derniers 30)")
        print("=" * 120)
        print()
        
        movements = StockMovement.query.filter_by(product_id=product_id).order_by(
            StockMovement.created_at.desc()
        ).limit(30).all()
        
        if movements:
            print(f"   {'Date':<20} {'Type':<20} {'Qté':<12} {'Valeur':<15} {'Motif':<30}")
            print("   " + "-" * 100)
            
            for m in movements:
                date_str = m.created_at.strftime('%d/%m/%Y %H:%M') if m.created_at else 'N/A'
                mvt_type = str(m.movement_type) if m.movement_type else 'N/A'
                qty = m.quantity or 0
                value = m.value_change or 0
                reason = (m.reason or 'N/A')[:28]
                
                print(f"   {date_str:<20} {mvt_type:<20} {qty:<12.2f} {value:<15.2f} {reason:<30}")
        else:
            print("   ❌ Aucun mouvement de stock trouvé")
        print()
        
        # ========================================================================
        # 5. TRANSFERTS DE STOCK
        # ========================================================================
        print("=" * 120)
        print("5️⃣  TRANSFERTS DE STOCK")
        print("=" * 120)
        print()
        
        transfer_lines = StockTransferLine.query.filter_by(product_id=product_id).order_by(
            StockTransferLine.id.desc()
        ).limit(20).all()
        
        if transfer_lines:
            print(f"   {'ID':<8} {'Date':<20} {'Qté':<12} {'Source':<25} {'Destination':<25}")
            print("   " + "-" * 95)
            
            for line in transfer_lines:
                transfer = line.transfer
                date_str = transfer.created_at.strftime('%d/%m/%Y %H:%M') if transfer.created_at else 'N/A'
                src = str(transfer.source_location)[:23] if transfer.source_location else 'N/A'
                dst = str(transfer.destination_location)[:23] if transfer.destination_location else 'N/A'
                
                print(f"   {transfer.id:<8} {date_str:<20} {line.quantity:<12.2f} {src:<25} {dst:<25}")
        else:
            print("   ❌ Aucun transfert trouvé")
        print()
        
        # ========================================================================
        # 6. CONCLUSION
        # ========================================================================
        print("=" * 120)
        print("6️⃣  CONCLUSION")
        print("=" * 120)
        print()
        
        if recipe:
            cost_recipe = float(total_recipe_cost / yield_qty)
            actual = float(product.cost_price or 0)
            
            if abs(cost_recipe - actual) < 1:
                print(f"   ✅ Le cost_price de {actual:.2f} DA vient du CALCUL DE LA RECETTE")
                print(f"      → Coût total ingrédients : {total_recipe_cost:.2f} DA")
                print(f"      → Divisé par yield_quantity : {yield_qty}")
                print(f"      → Résultat : {cost_recipe:.2f} DA")
            else:
                print(f"   ⚠️  Le cost_price ne correspond pas au calcul de la recette")
                print(f"      → Recette : {cost_recipe:.2f} DA")
                print(f"      → Actuel  : {actual:.2f} DA")
        
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/investiguer_produit.py <product_id>")
        print("Exemple: python3 scripts/investiguer_produit.py 80")
        sys.exit(1)
    
    try:
        product_id = int(sys.argv[1])
        investiguer_produit(product_id)
    except ValueError:
        print(f"❌ ID produit invalide : {sys.argv[1]}")

