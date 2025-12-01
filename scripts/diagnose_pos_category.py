#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi les produits d'une catégorie
ne s'affichent pas dans le POS

Usage:
    python scripts/diagnose_pos_category.py "gâteaux"
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Category
from sqlalchemy import or_

def diagnose_category(category_name):
    """Diagnostique pourquoi les produits d'une catégorie ne s'affichent pas dans le POS"""
    app = create_app()
    
    with app.app_context():
        # Trouver la catégorie
        category = Category.query.filter(
            Category.name.ilike(f'%{category_name}%')
        ).first()
        
        if not category:
            print(f"❌ Catégorie '{category_name}' non trouvée")
            print("\n📋 Catégories disponibles :")
            categories = Category.query.all()
            for cat in categories:
                print(f"   - {cat.name} (ID: {cat.id}, show_in_pos: {cat.show_in_pos})")
            return
        
        print(f"✅ Catégorie trouvée : {category.name} (ID: {category.id})")
        print(f"   show_in_pos: {category.show_in_pos}")
        print()
        
        # Compter tous les produits de cette catégorie
        all_products = Product.query.filter_by(category_id=category.id).all()
        print(f"📦 Total produits dans cette catégorie : {len(all_products)}")
        print()
        
        # Analyser chaque produit
        print("=" * 80)
        print("ANALYSE DÉTAILLÉE DES PRODUITS")
        print("=" * 80)
        
        products_shown = []
        products_hidden = []
        
        for product in all_products:
            reasons_hidden = []
            
            # Vérifier show_in_pos de la catégorie
            if not category.show_in_pos:
                reasons_hidden.append("❌ Catégorie show_in_pos = False")
            
            # Vérifier le type de produit
            is_finished = product.product_type == 'finished'
            can_be_sold = product.can_be_sold == True
            
            if not is_finished and not can_be_sold:
                reasons_hidden.append(f"❌ Type: '{product.product_type}', can_be_sold: {can_be_sold}")
            
            # Vérifier le stock comptoir
            stock_comptoir = float(product.stock_comptoir or 0)
            if stock_comptoir <= 0:
                reasons_hidden.append(f"❌ stock_comptoir = {stock_comptoir}")
            
            # Vérifier les réservations (simulation)
            from app.sales.routes import get_reserved_stock_by_product
            reserved_stock = get_reserved_stock_by_product()
            reserved_qty = reserved_stock.get(product.id, 0)
            available_stock = max(0, stock_comptoir - reserved_qty)
            
            if available_stock <= 0 and stock_comptoir > 0:
                reasons_hidden.append(f"⚠️ Stock réservé (disponible: {available_stock}, réservé: {reserved_qty})")
            
            # Résumé du produit
            status = "✅ AFFICHÉ" if not reasons_hidden else "❌ MASQUÉ"
            print(f"\n{status} - {product.name} (ID: {product.id})")
            print(f"   Type: {product.product_type}, can_be_sold: {can_be_sold}")
            print(f"   stock_comptoir: {stock_comptoir}")
            print(f"   Stock réservé: {reserved_qty}, Disponible: {available_stock}")
            if reasons_hidden:
                print(f"   Raisons masquage:")
                for reason in reasons_hidden:
                    print(f"      {reason}")
            
            if not reasons_hidden:
                products_shown.append(product)
            else:
                products_hidden.append((product, reasons_hidden))
        
        # Résumé final
        print("\n" + "=" * 80)
        print("RÉSUMÉ")
        print("=" * 80)
        print(f"✅ Produits affichés dans le POS : {len(products_shown)}")
        print(f"❌ Produits masqués : {len(products_hidden)}")
        print()
        
        if products_hidden:
            print("🔍 PRODUITS MASQUÉS ET RAISONS :")
            for product, reasons in products_hidden:
                print(f"\n   {product.name} (ID: {product.id}):")
                for reason in reasons:
                    print(f"      {reason}")
        
        # Suggestions de correction
        print("\n" + "=" * 80)
        print("SUGGESTIONS DE CORRECTION")
        print("=" * 80)
        
        if not category.show_in_pos:
            print(f"\n1. Activer show_in_pos pour la catégorie '{category.name}':")
            print(f"   UPDATE categories SET show_in_pos = true WHERE id = {category.id};")
        
        products_no_stock = [p for p in all_products if float(p.stock_comptoir or 0) <= 0]
        if products_no_stock:
            print(f"\n2. {len(products_no_stock)} produits sans stock_comptoir:")
            for p in products_no_stock[:10]:
                print(f"   - {p.name} (ID: {p.id}): stock_comptoir = {p.stock_comptoir}")
            if len(products_no_stock) > 10:
                print(f"   ... et {len(products_no_stock) - 10} autres")
        
        products_wrong_type = [p for p in all_products if p.product_type != 'finished' and not p.can_be_sold]
        if products_wrong_type:
            print(f"\n3. {len(products_wrong_type)} produits non vendables (ni finished ni can_be_sold):")
            for p in products_wrong_type[:10]:
                print(f"   - {p.name} (ID: {p.id}): type={p.product_type}, can_be_sold={p.can_be_sold}")
            if len(products_wrong_type) > 10:
                print(f"   ... et {len(products_wrong_type) - 10} autres")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_pos_category.py 'nom_catégorie'")
        print("\nExemple: python scripts/diagnose_pos_category.py 'gâteaux'")
        return 1
    
    category_name = sys.argv[1]
    diagnose_category(category_name)
    return 0

if __name__ == '__main__':
    sys.exit(main())

