#!/usr/bin/env python3
"""
Script d'audit complet du PMP (Prix Moyen Pondéré)
1. Trouve tous les produits avec PMP anormal (cost_price > price)
2. Analyse l'historique des achats du Baghrir
3. Identifie quand et pourquoi le PMP a changé
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product
from app.purchases.models import Purchase, PurchaseItem
from app.stock.models import StockMovement
from decimal import Decimal
from sqlalchemy import func
from datetime import datetime

def audit_pmp_complet():
    """Audit complet du PMP"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("AUDIT COMPLET DU PMP (Prix Moyen Pondéré)")
        print("=" * 120)
        print()
        
        # ========================================================================
        # 1. TOUS LES PRODUITS AVEC PMP ANORMAL
        # ========================================================================
        print("=" * 120)
        print("1️⃣  PRODUITS AVEC PMP ANORMAL (cost_price > prix de vente)")
        print("=" * 120)
        print()
        
        # Trouver tous les produits où cost_price > price
        products_anormaux = Product.query.filter(
            Product.cost_price > Product.price,
            Product.price > 0
        ).all()
        
        print(f"   Total produits avec PMP anormal : {len(products_anormaux)}")
        print()
        
        if products_anormaux:
            print(f"   {'ID':<6} {'Produit':<40} {'Prix Vente':<12} {'Cost Price':<12} {'Écart':<12} {'%':<10}")
            print("   " + "-" * 100)
            
            for p in products_anormaux:
                price = float(p.price or 0)
                cost = float(p.cost_price or 0)
                ecart = cost - price
                pct = (ecart / price * 100) if price > 0 else 0
                
                print(f"   {p.id:<6} {p.name[:38]:<40} {price:<12.2f} {cost:<12.2f} {ecart:<12.2f} {pct:<10.1f}%")
            print()
        else:
            print("   ✅ Aucun produit avec PMP anormal")
            print()
        
        # ========================================================================
        # 2. ANALYSE DÉTAILLÉE DU BAGHRIR
        # ========================================================================
        print("=" * 120)
        print("2️⃣  ANALYSE DÉTAILLÉE : BAGHRIR PETITE TAILLE SIMPLE")
        print("=" * 120)
        print()
        
        # Trouver le produit
        product = Product.query.filter(Product.name.ilike('%Baghrir Petite Taille Simple%')).first()
        
        if not product:
            print("❌ Produit 'Baghrir Petite Taille Simple' non trouvé")
            return
        
        print(f"   📦 INFORMATIONS PRODUIT")
        print(f"   ID            : {product.id}")
        print(f"   Nom           : {product.name}")
        print(f"   Prix de vente : {product.price} DA")
        print(f"   Cost Price    : {product.cost_price} DA (PMP actuel)")
        print(f"   Stock comptoir: {product.stock_comptoir}")
        print()
        
        # ========================================================================
        # 3. HISTORIQUE DES BONS D'ACHAT
        # ========================================================================
        print("=" * 120)
        print("3️⃣  HISTORIQUE DES BONS D'ACHAT")
        print("=" * 120)
        print()
        
        purchase_items = PurchaseItem.query.filter_by(product_id=product.id).join(
            Purchase, Purchase.id == PurchaseItem.purchase_id
        ).order_by(Purchase.created_at.asc()).all()
        
        print(f"   Total bons d'achat : {len(purchase_items)}")
        print()
        
        if purchase_items:
            total_quantity = Decimal('0')
            total_value = Decimal('0')
            
            print(f"   {'Date':<12} {'Réf':<25} {'Qté':<10} {'Prix/U':<12} {'Total':<15} {'Statut':<12}")
            print("   " + "-" * 90)
            
            for item in purchase_items:
                purchase = item.purchase
                qty = Decimal(str(item.quantity or 0))
                unit_price = Decimal(str(item.unit_price or 0))
                
                if qty > 0 and unit_price > 0:
                    total_quantity += qty
                    total_value += qty * unit_price
                
                date_str = purchase.created_at.strftime('%d/%m/%Y') if purchase.created_at else 'N/A'
                ref = (purchase.reference or 'N/A')[:23]
                status = purchase.status or 'N/A'
                
                print(f"   {date_str:<12} {ref:<25} {qty:<10.0f} {unit_price:<12.2f} {qty * unit_price:<15.2f} {status:<12}")
            
            print()
            print(f"   TOTAUX :")
            print(f"   - Quantité totale : {total_quantity:.0f} unités")
            print(f"   - Valeur totale   : {total_value:.2f} DA")
            
            if total_quantity > 0:
                pmp_correct = total_value / total_quantity
                print(f"   - PMP correct     : {pmp_correct:.2f} DA")
                print()
                print(f"   ⚠️  PMP actuel ({product.cost_price} DA) vs PMP correct ({pmp_correct:.2f} DA)")
        
        print()
        
        # ========================================================================
        # 4. HISTORIQUE DES MOUVEMENTS DE STOCK
        # ========================================================================
        print("=" * 120)
        print("4️⃣  HISTORIQUE DES MOUVEMENTS DE STOCK")
        print("=" * 120)
        print()
        
        movements = StockMovement.query.filter_by(product_id=product.id).order_by(
            StockMovement.created_at.desc()
        ).limit(50).all()
        
        print(f"   Derniers 50 mouvements de stock :")
        print()
        
        if movements:
            print(f"   {'Date':<20} {'Type':<15} {'Qté':<10} {'Valeur':<15} {'Motif':<30}")
            print("   " + "-" * 100)
            
            for m in movements:
                date_str = m.created_at.strftime('%d/%m/%Y %H:%M') if m.created_at else 'N/A'
                mvt_type = m.movement_type or 'N/A'
                qty = m.quantity or 0
                value = m.value_change or 0
                reason = (m.reason or 'N/A')[:28]
                
                print(f"   {date_str:<20} {mvt_type:<15} {qty:<10.2f} {value:<15.2f} {reason:<30}")
        else:
            print("   Aucun mouvement trouvé")
        
        print()
        
        # ========================================================================
        # 5. CORRECTION PROPOSÉE
        # ========================================================================
        print("=" * 120)
        print("5️⃣  CORRECTION PROPOSÉE")
        print("=" * 120)
        print()
        
        if purchase_items and total_quantity > 0:
            pmp_correct = total_value / total_quantity
            
            print(f"   PMP actuel (erroné) : {product.cost_price} DA")
            print(f"   PMP correct         : {pmp_correct:.2f} DA")
            print()
            print(f"   Voulez-vous corriger le cost_price de ce produit ?")
            print(f"   Tapez 'CORRIGER' pour confirmer : ", end='')
            
            response = input().strip()
            
            if response == 'CORRIGER':
                old_cost = product.cost_price
                product.cost_price = float(pmp_correct)
                db.session.commit()
                
                print()
                print(f"   ✅ CORRECTION APPLIQUÉE !")
                print(f"      Ancien cost_price : {old_cost} DA")
                print(f"      Nouveau cost_price : {product.cost_price} DA")
            else:
                print()
                print("   ❌ Correction annulée")
        
        # ========================================================================
        # 6. AUTRES PRODUITS À CORRIGER
        # ========================================================================
        print()
        print("=" * 120)
        print("6️⃣  AUTRES PRODUITS À VÉRIFIER (PMP suspect)")
        print("=" * 120)
        print()
        
        # Produits avec cost_price très différent des achats récents
        all_products = Product.query.filter(Product.cost_price > 0).all()
        
        suspects = []
        for p in all_products:
            # Récupérer le dernier achat
            last_purchase = PurchaseItem.query.filter_by(product_id=p.id).join(
                Purchase
            ).order_by(Purchase.created_at.desc()).first()
            
            if last_purchase:
                last_price = float(last_purchase.unit_price or 0)
                cost_price = float(p.cost_price or 0)
                
                # Si le cost_price est très différent du dernier achat (> 50%)
                if cost_price > 0 and last_price > 0:
                    diff_pct = abs(cost_price - last_price) / last_price * 100
                    if diff_pct > 50:
                        suspects.append({
                            'product': p,
                            'cost_price': cost_price,
                            'last_purchase_price': last_price,
                            'diff_pct': diff_pct
                        })
        
        if suspects:
            print(f"   {len(suspects)} produits avec écart PMP/dernier achat > 50%")
            print()
            print(f"   {'ID':<6} {'Produit':<35} {'Cost Price':<12} {'Dernier Achat':<15} {'Écart %':<10}")
            print("   " + "-" * 80)
            
            for s in sorted(suspects, key=lambda x: x['diff_pct'], reverse=True)[:20]:
                p = s['product']
                print(f"   {p.id:<6} {p.name[:33]:<35} {s['cost_price']:<12.2f} {s['last_purchase_price']:<15.2f} {s['diff_pct']:<10.1f}%")
        else:
            print("   ✅ Aucun autre produit suspect")

if __name__ == '__main__':
    audit_pmp_complet()

