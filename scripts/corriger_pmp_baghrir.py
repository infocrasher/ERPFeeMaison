#!/usr/bin/env python3
"""
Script pour corriger le PMP (Prix Moyen Pondéré) du produit Baghrir Petite Taille Simple
Le cost_price est à 1374.68 DA alors qu'il devrait être ~30 DA
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product
from app.purchases.models import Purchase, PurchaseItem
from decimal import Decimal
from sqlalchemy import func

def analyser_pmp_baghrir():
    """Analyse et corrige le PMP du produit Baghrir"""
    app = create_app()
    
    with app.app_context():
        print("=" * 100)
        print("CORRECTION PMP BAGHRIR PETITE TAILLE SIMPLE")
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
        print(f"   Cost Price    : {product.cost_price} DA (PMP actuel - ERRONÉ)")
        print()
        
        # Récupérer tous les bons d'achat pour ce produit
        print(f"📋 BONS D'ACHAT POUR CE PRODUIT")
        print("-" * 100)
        
        purchase_items = PurchaseItem.query.filter_by(product_id=product.id).all()
        
        print(f"   Total bons d'achat : {len(purchase_items)}")
        print()
        
        if not purchase_items:
            print("   ⚠️ Aucun bon d'achat trouvé")
            return
        
        # Calculer le PMP correct
        total_quantity = Decimal('0')
        total_value = Decimal('0')
        
        print(f"   {'Date':<12} {'Réf':<20} {'Qté':<10} {'Prix/U':<12} {'Total':<15}")
        print("   " + "-" * 70)
        
        for item in purchase_items:
            purchase = item.purchase
            qty = Decimal(str(item.quantity or 0))
            unit_price = Decimal(str(item.unit_price or 0))
            
            if qty > 0 and unit_price > 0:
                total_quantity += qty
                total_value += qty * unit_price
                
                date_str = purchase.purchase_date.strftime('%d/%m/%Y') if purchase.purchase_date else 'N/A'
                ref = purchase.reference[:18] if purchase.reference else 'N/A'
                
                print(f"   {date_str:<12} {ref:<20} {qty:<10.0f} {unit_price:<12.2f} {qty * unit_price:<15.2f}")
        
        print()
        
        # Calculer le PMP correct
        if total_quantity > 0:
            pmp_correct = total_value / total_quantity
            print(f"   CALCUL PMP CORRECT :")
            print(f"   Total quantité : {total_quantity:.0f} unités")
            print(f"   Total valeur   : {total_value:.2f} DA")
            print(f"   PMP correct    : {pmp_correct:.2f} DA")
            print()
            
            # Comparaison
            print("=" * 100)
            print("🔍 COMPARAISON")
            print("=" * 100)
            print()
            print(f"   PMP actuel (erroné) : {product.cost_price:.2f} DA")
            print(f"   PMP correct         : {pmp_correct:.2f} DA")
            print(f"   Différence          : {float(product.cost_price or 0) - float(pmp_correct):.2f} DA")
            print()
            
            # Demander confirmation pour corriger
            print("=" * 100)
            print("💡 CORRECTION PROPOSÉE")
            print("=" * 100)
            print()
            print(f"   Mettre à jour cost_price de {product.cost_price} DA à {pmp_correct:.2f} DA")
            print()
            
            # Demander confirmation
            print("   Voulez-vous appliquer cette correction ? (oui/non)")
            response = input("   Réponse : ").strip().lower()
            
            if response in ['oui', 'o', 'yes', 'y']:
                # Appliquer la correction
                old_cost = product.cost_price
                product.cost_price = float(pmp_correct)
                db.session.commit()
                
                print()
                print(f"   ✅ CORRECTION APPLIQUÉE !")
                print(f"      Ancien cost_price : {old_cost} DA")
                print(f"      Nouveau cost_price : {product.cost_price} DA")
                print()
                print("   Le COGS sera maintenant calculé correctement.")
            else:
                print()
                print("   ❌ Correction annulée")
        else:
            print("   ⚠️ Impossible de calculer le PMP (quantité = 0)")

if __name__ == '__main__':
    analyser_pmp_baghrir()

