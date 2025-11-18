#!/usr/bin/env python3
"""
Script pour corriger les SKU vides en None
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product

def fix_empty_skus():
    """Convertit tous les SKU vides en None pour éviter les violations UNIQUE"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🔧 CORRECTION DES SKU VIDES")
        print("=" * 50)
        
        # Compter les SKU vides
        count_before = Product.query.filter(Product.sku == '').count()
        print(f"📊 SKU vides trouvés: {count_before}")
        
        if count_before > 0:
            # Mettre à jour tous les SKU vides en None
            Product.query.filter(Product.sku == '').update({'sku': None})
            db.session.commit()
            
            print(f"✅ {count_before} produits corrigés (SKU vide → NULL)")
        else:
            print("✅ Aucun SKU vide à corriger")
        
        # Vérifier
        count_after = Product.query.filter(Product.sku == '').count()
        print(f"\n📊 SKU vides restants: {count_after}")
        
        if count_after == 0:
            print("\n✅ SUCCÈS : Tous les SKU vides ont été convertis en NULL")
        else:
            print(f"\n⚠️  ATTENTION : {count_after} SKU vides restants")

if __name__ == "__main__":
    fix_empty_skus()

