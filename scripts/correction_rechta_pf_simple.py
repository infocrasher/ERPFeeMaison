#!/usr/bin/env python3
"""
Script simple pour corriger Rechta PF à 2 pièces
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def correct_rechta_pf():
    """Corrige Rechta PF à 2 pièces"""
    app = create_app()
    
    with app.app_context():
        rechta_pf = Product.query.filter(Product.name.ilike('%rechta pf%')).first()
        
        if not rechta_pf:
            print("❌ Produit 'Rechta PF' non trouvé")
            return
        
        print(f"✅ Produit trouvé: {rechta_pf.name} (ID: {rechta_pf.id})")
        print(f"   Stock actuel: {rechta_pf.stock_comptoir} pièces")
        print(f"   PMP: {rechta_pf.cost_price} DA")
        
        # Corriger à 2 pièces
        rechta_pf.stock_comptoir = 2.0
        
        # Recalculer la valeur (convertir Decimal en float)
        from decimal import Decimal
        cost_price = float(rechta_pf.cost_price or 0)
        
        if cost_price > 0:
            rechta_pf.valeur_stock_comptoir = float(rechta_pf.stock_comptoir * cost_price)
        else:
            rechta_pf.valeur_stock_comptoir = 0.0
        
        # Recalculer valeur totale
        total_stock = (
            (rechta_pf.stock_comptoir or 0) +
            (rechta_pf.stock_ingredients_magasin or 0) +
            (rechta_pf.stock_ingredients_local or 0) +
            (rechta_pf.stock_consommables or 0)
        )
        
        if cost_price > 0:
            rechta_pf.total_stock_value = float(total_stock * cost_price)
        else:
            rechta_pf.total_stock_value = rechta_pf.valeur_stock_comptoir
        
        db.session.commit()
        
        print(f"✅ Stock corrigé à {rechta_pf.stock_comptoir} pièces")
        print(f"   Valeur: {rechta_pf.valeur_stock_comptoir:.2f} DA")

if __name__ == '__main__':
    correct_rechta_pf()

