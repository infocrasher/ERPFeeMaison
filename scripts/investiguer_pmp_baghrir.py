#!/usr/bin/env python3
"""
Script d'investigation approfondie du PMP erroné du Baghrir
Recherche TOUTES les opérations qui ont pu modifier le cost_price
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Order, OrderItem, Recipe, RecipeIngredient
from app.purchases.models import Purchase, PurchaseItem
from app.stock.models import StockMovement, StockTransfer, StockTransferLine
from app.accounting.models import JournalEntry
from decimal import Decimal
from sqlalchemy import func, or_, text
from datetime import datetime

def investiguer_pmp():
    """Investigation approfondie du PMP erroné"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("INVESTIGATION APPROFONDIE - PMP BAGHRIR PETITE TAILLE SIMPLE")
        print("=" * 120)
        print()
        
        # Trouver le produit
        product = Product.query.filter(Product.name.ilike('%Baghrir Petite Taille Simple%')).first()
        
        if not product:
            print("❌ Produit non trouvé")
            return
        
        product_id = product.id
        print(f"   📦 Produit ID: {product_id} - {product.name}")
        print(f"   💰 Cost Price actuel: {product.cost_price} DA")
        print(f"   📊 Stock comptoir: {product.stock_comptoir}")
        print(f"   📊 Total stock value: {product.total_stock_value}")
        print()
        
        # ========================================================================
        # 1. VÉRIFIER SI LE PRODUIT A UNE RECETTE
        # ========================================================================
        print("=" * 120)
        print("1️⃣  VÉRIFICATION RECETTE")
        print("=" * 120)
        print()
        
        recipe = product.recipe_definition
        if recipe:
            print(f"   ⚠️  CE PRODUIT A UNE RECETTE !")
            print(f"   Recette ID: {recipe.id}")
            print(f"   Nom: {recipe.name}")
            print(f"   yield_quantity: {recipe.yield_quantity}")
            print()
            
            # Calculer le coût via la recette
            print("   Ingrédients :")
            total_recipe_cost = Decimal('0')
            yield_qty = Decimal(str(recipe.yield_quantity or 1))
            
            for ing in recipe.ingredients:
                if ing.product:
                    qty = Decimal(str(ing.quantity_needed or 0))
                    cost = Decimal(str(ing.product.cost_price or 0))
                    ing_cost = qty * cost
                    total_recipe_cost += ing_cost
                    print(f"      - {ing.product.name}: {qty} x {cost} = {ing_cost} DA")
            
            cost_per_unit_recipe = total_recipe_cost / yield_qty if yield_qty > 0 else 0
            print()
            print(f"   Coût total recette: {total_recipe_cost} DA")
            print(f"   Coût par unité (recette): {cost_per_unit_recipe:.2f} DA")
            print()
            print(f"   🔴 LE PMP DE 1374.68 DA VIENT PROBABLEMENT DE CETTE RECETTE !")
            print(f"      Si yield_quantity = 1 mais devrait être ~50, le coût est multiplié par 50")
        else:
            print("   ✅ Pas de recette associée à ce produit")
        print()
        
        # ========================================================================
        # 2. HISTORIQUE DES TRANSFERTS DE STOCK
        # ========================================================================
        print("=" * 120)
        print("2️⃣  TRANSFERTS DE STOCK")
        print("=" * 120)
        print()
        
        # Vérifier les lignes de transfert
        transfer_lines = StockTransferLine.query.filter_by(product_id=product_id).all()
        
        if transfer_lines:
            print(f"   Total transferts: {len(transfer_lines)}")
            print()
            for line in transfer_lines[:20]:
                transfer = line.transfer
                print(f"   - ID:{transfer.id} | {transfer.created_at} | {line.quantity} unités | {transfer.source_location} → {transfer.destination_location}")
        else:
            print("   Aucun transfert trouvé")
        print()
        
        # ========================================================================
        # 3. COMMANDES/VENTES CONTENANT CE PRODUIT
        # ========================================================================
        print("=" * 120)
        print("3️⃣  VENTES DE CE PRODUIT (dernières 20)")
        print("=" * 120)
        print()
        
        order_items = OrderItem.query.filter_by(product_id=product_id).join(
            Order
        ).order_by(Order.created_at.desc()).limit(20).all()
        
        if order_items:
            print(f"   Total ventes trouvées: {len(order_items)}")
            print()
            for item in order_items:
                order = item.order
                print(f"   - Commande #{order.id} | {order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else 'N/A'} | Qté: {item.quantity} | Prix: {item.unit_price} DA")
        else:
            print("   Aucune vente trouvée")
        print()
        
        # ========================================================================
        # 4. VÉRIFIER LES VALEURS DE STOCK
        # ========================================================================
        print("=" * 120)
        print("4️⃣  VALEURS DE STOCK ACTUELLES")
        print("=" * 120)
        print()
        
        print(f"   stock_comptoir: {product.stock_comptoir}")
        print(f"   stock_ingredients_local: {product.stock_ingredients_local}")
        print(f"   stock_ingredients_magasin: {product.stock_ingredients_magasin}")
        print(f"   stock_consommables: {product.stock_consommables}")
        print()
        print(f"   valeur_stock_comptoir: {product.valeur_stock_comptoir}")
        print(f"   valeur_stock_ingredients_local: {product.valeur_stock_ingredients_local}")
        print(f"   valeur_stock_ingredients_magasin: {product.valeur_stock_ingredients_magasin}")
        print(f"   valeur_stock_consommables: {product.valeur_stock_consommables}")
        print()
        print(f"   total_stock_value: {product.total_stock_value}")
        print()
        
        # Calculer le PMP à partir de la valeur stock
        total_stock = float(product.stock_comptoir or 0) + float(product.stock_ingredients_local or 0) + float(product.stock_ingredients_magasin or 0)
        total_value = float(product.total_stock_value or 0)
        
        if total_stock > 0:
            pmp_from_value = total_value / total_stock
            print(f"   💡 PMP calculé depuis total_stock_value / total_stock:")
            print(f"      {total_value:.2f} / {total_stock:.2f} = {pmp_from_value:.2f} DA")
            print()
            if abs(pmp_from_value - float(product.cost_price or 0)) < 1:
                print(f"   🔴 LE COST_PRICE VIENT DU CALCUL total_stock_value / stock !")
        print()
        
        # ========================================================================
        # 5. RECHERCHE DANS LES BONS D'ACHAT - TOUS LES BAGHRIR
        # ========================================================================
        print("=" * 120)
        print("5️⃣  TOUS LES ACHATS DE 'BAGHRIR' (tous types)")
        print("=" * 120)
        print()
        
        # Chercher tous les produits Baghrir
        all_baghrir = Product.query.filter(Product.name.ilike('%Baghrir%')).all()
        print(f"   Produits 'Baghrir' trouvés: {len(all_baghrir)}")
        for b in all_baghrir:
            print(f"      - ID:{b.id} | {b.name} | Price: {b.price} | Cost: {b.cost_price}")
        print()
        
        # ========================================================================
        # 6. HYPOTHÈSE : CONFUSION AVEC BAGHRIR GRANDE TAILLE
        # ========================================================================
        print("=" * 120)
        print("6️⃣  HYPOTHÈSE : CONFUSION AVEC UN AUTRE BAGHRIR")
        print("=" * 120)
        print()
        
        # Chercher Baghrir Grande Taille
        baghrir_grand = Product.query.filter(Product.name.ilike('%Baghrir Grand%')).first()
        if baghrir_grand:
            print(f"   Baghrir Grande Taille trouvé:")
            print(f"      ID: {baghrir_grand.id}")
            print(f"      Nom: {baghrir_grand.name}")
            print(f"      Price: {baghrir_grand.price}")
            print(f"      Cost Price: {baghrir_grand.cost_price}")
            print()
            
            # Vérifier si le cost_price du petit = cost_price du grand
            if baghrir_grand.cost_price:
                print(f"   🔍 Comparaison:")
                print(f"      Cost Baghrir Petite: {product.cost_price}")
                print(f"      Cost Baghrir Grande: {baghrir_grand.cost_price}")
        print()
        
        # ========================================================================
        # 7. CONCLUSION ET CORRECTION
        # ========================================================================
        print("=" * 120)
        print("7️⃣  CONCLUSION")
        print("=" * 120)
        print()
        
        if recipe:
            print("   🔴 CAUSE PROBABLE : Le produit a une RECETTE avec yield_quantity incorrect")
            print("      Le cost_price est calculé via la recette, pas via les achats")
            print()
            print("   SOLUTION :")
            print("      1. Supprimer la recette si ce produit est ACHETÉ (pas fabriqué)")
            print("      2. OU corriger le yield_quantity de la recette")
            print("      3. OU recalculer le cost_price manuellement à ~30 DA")
        else:
            print("   🔴 CAUSE PROBABLE : Erreur dans le calcul du PMP lors d'une opération passée")
            print()
            print("   SOLUTION :")
            print("      Corriger manuellement le cost_price à ~30 DA (basé sur les achats)")
        
        print()
        print("=" * 120)
        print("8️⃣  CORRECTION MANUELLE")
        print("=" * 120)
        print()
        print(f"   PMP actuel: {product.cost_price} DA")
        print(f"   PMP correct (basé sur achats): ~30 DA")
        print()
        print("   Voulez-vous corriger le cost_price à 30 DA ?")
        print("   Tapez 'OUI' pour confirmer : ", end='')
        
        response = input().strip().upper()
        
        if response == 'OUI':
            old_cost = product.cost_price
            product.cost_price = 30.0
            
            # Recalculer les valeurs de stock
            if product.stock_comptoir:
                product.valeur_stock_comptoir = float(product.stock_comptoir) * 30.0
            
            db.session.commit()
            
            print()
            print(f"   ✅ CORRECTION APPLIQUÉE !")
            print(f"      Ancien cost_price: {old_cost} DA")
            print(f"      Nouveau cost_price: 30 DA")
        else:
            print()
            print("   ❌ Correction annulée")

if __name__ == '__main__':
    investiguer_pmp()

