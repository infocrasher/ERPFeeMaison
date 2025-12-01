#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier les slugs de catégories dans le POS

Usage:
    python scripts/diagnose_pos_category_slug.py "boissons"
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product, Category

def diagnose_category_slug(category_name):
    """Diagnostique les slugs de catégorie pour le POS"""
    app = create_app()
    
    with app.app_context():
        # Trouver la catégorie
        category = Category.query.filter(
            Category.name.ilike(f'%{category_name}%')
        ).first()
        
        if not category:
            print(f"❌ Catégorie '{category_name}' non trouvée")
            return
        
        print(f"✅ Catégorie trouvée : {category.name} (ID: {category.id})")
        print(f"   show_in_pos: {category.show_in_pos}")
        print()
        
        # Générer le slug comme le backend
        backend_slug = category.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')
        print(f"📋 Slug généré côté backend : '{backend_slug}'")
        print()
        
        # Trouver les produits de cette catégorie avec stock_comptoir > 0
        products = Product.query.filter(
            Product.category_id == category.id,
            Product.product_type == 'finished',
            Product.stock_comptoir > 0
        ).all()
        
        print(f"📦 Produits finis avec stock_comptoir > 0 dans cette catégorie : {len(products)}")
        print()
        
        if products:
            print("📋 Exemples de produits (5 premiers) :")
            for product in products[:5]:
                product_slug = product.category.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e') if product.category else 'autres'
                print(f"   - {product.name} (ID: {product.id})")
                print(f"     Slug produit: '{product_slug}'")
                print(f"     Slug catégorie: '{backend_slug}'")
                print(f"     Match: {'✅' if product_slug == backend_slug else '❌'}")
                print()
        
        # Vérifier les catégories POS
        pos_categories = Category.query.filter(Category.show_in_pos == True).order_by(Category.name).all()
        print(f"📋 Catégories visibles dans le POS ({len(pos_categories)}):")
        for cat in pos_categories:
            cat_slug = cat.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')
            is_match = cat_slug == backend_slug
            marker = '✅' if is_match else '  '
            print(f"   {marker} {cat.name} → slug: '{cat_slug}'")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_pos_category_slug.py 'nom_catégorie'")
        print("\nExemple: python scripts/diagnose_pos_category_slug.py 'boissons'")
        return 1
    
    category_name = sys.argv[1]
    diagnose_category_slug(category_name)
    return 0

if __name__ == '__main__':
    sys.exit(main())

