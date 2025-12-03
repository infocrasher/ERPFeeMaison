#!/usr/bin/env python3
"""
Script pour corriger le stock de Rechta PF
Remet le stock à 2 pièces (valeur réelle) au lieu de 9998
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db
from decimal import Decimal

def correct_rechta_pf_stock():
    """Corrige le stock de Rechta PF à 2 pièces"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("CORRECTION STOCK RECHTA PF")
        print("=" * 80)
        print()
        
        # Trouver Rechta PF
        rechta_pf = Product.query.filter(
            Product.name.ilike('%rechta pf%')
        ).first()
        
        if not rechta_pf:
            print("❌ Produit 'Rechta PF' non trouvé")
            print("\nProduits contenant 'rechta':")
            products = Product.query.filter(Product.name.ilike('%rechta%')).all()
            for p in products:
                print(f"  - {p.name} (ID: {p.id})")
            return
        
        print(f"✅ Produit trouvé: {rechta_pf.name} (ID: {rechta_pf.id})")
        print(f"   Unité: {rechta_pf.unit}")
        print(f"   Stock actuel comptoir: {rechta_pf.stock_comptoir} {rechta_pf.unit}")
        print(f"   Valeur actuelle comptoir: {rechta_pf.valeur_stock_comptoir} DA")
        print(f"   PMP (cost_price): {rechta_pf.cost_price} DA")
        print()
        
        # Nouveau stock
        new_stock = 2.0  # 2 pièces
        cost_price = Decimal(str(rechta_pf.cost_price or 0))
        
        if cost_price <= 0:
            print("⚠️  ATTENTION: Le produit n'a pas de PMP (cost_price) défini")
            print("   La valeur du stock sera mise à 0")
            new_value = Decimal('0')
        else:
            new_value = Decimal(str(new_stock)) * cost_price
        
        print(f"📋 Correction proposée:")
        print(f"   Stock comptoir: {rechta_pf.stock_comptoir} → {new_stock} {rechta_pf.unit}")
        print(f"   Valeur comptoir: {rechta_pf.valeur_stock_comptoir} → {new_value:.2f} DA")
        print()
        
        # Demander confirmation
        confirm = input("Appliquer cette correction ? (oui/non) : ")
        
        if confirm.lower() == 'oui':
            # Sauvegarder l'ancien stock pour référence
            old_stock = rechta_pf.stock_comptoir
            old_value = rechta_pf.valeur_stock_comptoir
            
            # Appliquer la correction
            rechta_pf.stock_comptoir = new_stock
            rechta_pf.valeur_stock_comptoir = float(new_value)
            
            # Recalculer la valeur totale du stock
            total_stock = (
                Decimal(str(rechta_pf.stock_comptoir or 0)) +
                Decimal(str(rechta_pf.stock_ingredients_magasin or 0)) +
                Decimal(str(rechta_pf.stock_ingredients_local or 0)) +
                Decimal(str(rechta_pf.stock_consommables or 0))
            )
            
            if cost_price > 0:
                rechta_pf.total_stock_value = float(total_stock * cost_price)
            else:
                rechta_pf.total_stock_value = float(new_value)
            
            db.session.commit()
            
            print()
            print("✅ Correction appliquée avec succès !")
            print(f"   Stock comptoir: {old_stock} → {rechta_pf.stock_comptoir} {rechta_pf.unit}")
            print(f"   Valeur comptoir: {old_value} → {rechta_pf.valeur_stock_comptoir:.2f} DA")
            print(f"   Valeur totale: {rechta_pf.total_stock_value:.2f} DA")
        else:
            print("❌ Correction annulée")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    correct_rechta_pf_stock()

