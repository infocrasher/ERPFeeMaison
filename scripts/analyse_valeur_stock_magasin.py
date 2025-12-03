#!/usr/bin/env python3
"""
Script pour analyser la valeur du stock magasin et détecter les anomalies
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def analyze_stock_value():
    """Analyse détaillée de la valeur du stock magasin"""
    app = create_app()
    
    with app.app_context():
        print("=" * 100)
        print("ANALYSE DE LA VALEUR DU STOCK MAGASIN")
        print("=" * 100)
        print()
        
        # Récupérer tous les produits avec stock magasin > 0
        products = Product.query.filter(
            Product.stock_ingredients_magasin > 0
        ).order_by(Product.valeur_stock_ingredients_magasin.desc()).all()
        
        if not products:
            print("❌ Aucun produit trouvé dans le stock magasin")
            return
        
        print(f"📦 {len(products)} produits avec stock magasin\n")
        
        # Calculer le total
        total_value = sum(float(p.valeur_stock_ingredients_magasin or 0) for p in products)
        total_qty = sum(float(p.stock_ingredients_magasin or 0) for p in products)
        
        print(f"💰 VALEUR TOTALE : {total_value:,.2f} DA")
        print(f"📊 QUANTITÉ TOTALE : {total_qty:,.2f} unités")
        print()
        
        # Top 20 des produits par valeur
        print("=" * 100)
        print("TOP 20 - PRODUITS PAR VALEUR (les plus chers)")
        print("=" * 100)
        print(f"{'ID':<6} {'Produit':<35} {'Qté':<12} {'PMP':<12} {'Valeur':<15} {'% Total':<10}")
        print("-" * 100)
        
        for i, p in enumerate(products[:20], 1):
            stock = float(p.stock_ingredients_magasin or 0)
            pmp = float(p.cost_price or 0)
            value = float(p.valeur_stock_ingredients_magasin or 0)
            pct = (value / total_value * 100) if total_value > 0 else 0
            
            print(f"{p.id:<6} {p.name[:33]:<35} {stock:<12.2f} {pmp:<12.4f} {value:<15.2f} {pct:<10.2f}%")
        
        print()
        
        # Produits avec valeur > 50,000 DA
        high_value = [p for p in products if float(p.valeur_stock_ingredients_magasin or 0) > 50000]
        if high_value:
            print("=" * 100)
            print(f"⚠️  PRODUITS AVEC VALEUR > 50,000 DA ({len(high_value)} produits)")
            print("=" * 100)
            print(f"{'ID':<6} {'Produit':<35} {'Qté':<12} {'PMP':<12} {'Valeur':<15} {'Unité':<10}")
            print("-" * 100)
            
            for p in high_value:
                stock = float(p.stock_ingredients_magasin or 0)
                pmp = float(p.cost_price or 0)
                value = float(p.valeur_stock_ingredients_magasin or 0)
                
                print(f"{p.id:<6} {p.name[:33]:<35} {stock:<12.2f} {pmp:<12.4f} {value:<15.2f} {p.unit or 'N/A':<10}")
            print()
        
        # Produits avec PMP anormalement élevé (> 1000 DA)
        high_pmp = [p for p in products if float(p.cost_price or 0) > 1000]
        if high_pmp:
            print("=" * 100)
            print(f"⚠️  PRODUITS AVEC PMP > 1000 DA ({len(high_pmp)} produits)")
            print("=" * 100)
            print(f"{'ID':<6} {'Produit':<35} {'Qté':<12} {'PMP':<12} {'Valeur':<15} {'Type':<15}")
            print("-" * 100)
            
            for p in high_pmp:
                stock = float(p.stock_ingredients_magasin or 0)
                pmp = float(p.cost_price or 0)
                value = float(p.valeur_stock_ingredients_magasin or 0)
                
                print(f"{p.id:<6} {p.name[:33]:<35} {stock:<12.2f} {pmp:<12.4f} {value:<15.2f} {p.product_type or 'N/A':<15}")
            print()
        
        # Vérifier la cohérence : valeur calculée vs valeur stockée
        print("=" * 100)
        print("VÉRIFICATION DE COHÉRENCE")
        print("=" * 100)
        
        incoherent = []
        for p in products:
            stock = float(p.stock_ingredients_magasin or 0)
            pmp = float(p.cost_price or 0)
            value_stored = float(p.valeur_stock_ingredients_magasin or 0)
            value_calculated = stock * pmp
            
            diff = abs(value_calculated - value_stored)
            
            # Tolérance de 1 DA
            if diff > 1.0:
                incoherent.append({
                    'product': p,
                    'stock': stock,
                    'pmp': pmp,
                    'value_stored': value_stored,
                    'value_calculated': value_calculated,
                    'diff': diff
                })
        
        if incoherent:
            print(f"⚠️  {len(incoherent)} produits avec incohérence valeur calculée ≠ valeur stockée\n")
            print(f"{'ID':<6} {'Produit':<30} {'Qté':<10} {'PMP':<12} {'Val. Stockée':<15} {'Val. Calculée':<15} {'Diff':<12}")
            print("-" * 100)
            
            for item in incoherent[:20]:  # Top 20 incohérences
                p = item['product']
                print(f"{p.id:<6} {p.name[:28]:<30} {item['stock']:<10.2f} {item['pmp']:<12.4f} "
                      f"{item['value_stored']:<15.2f} {item['value_calculated']:<15.2f} {item['diff']:<12.2f}")
        else:
            print("✅ Toutes les valeurs sont cohérentes (Qté × PMP = Valeur)")
        
        print()
        
        # Statistiques par type de produit
        print("=" * 100)
        print("RÉPARTITION PAR TYPE DE PRODUIT")
        print("=" * 100)
        
        stats_by_type = {}
        for p in products:
            ptype = p.product_type or 'unknown'
            value = float(p.valeur_stock_ingredients_magasin or 0)
            
            if ptype not in stats_by_type:
                stats_by_type[ptype] = {'count': 0, 'value': 0.0}
            
            stats_by_type[ptype]['count'] += 1
            stats_by_type[ptype]['value'] += value
        
        print(f"{'Type':<20} {'Nb Produits':<15} {'Valeur Totale':<20} {'% Total':<10}")
        print("-" * 70)
        
        for ptype, data in sorted(stats_by_type.items(), key=lambda x: x[1]['value'], reverse=True):
            count = data['count']
            value = data['value']
            pct = (value / total_value * 100) if total_value > 0 else 0
            
            print(f"{ptype:<20} {count:<15} {value:<20,.2f} {pct:<10.2f}%")
        
        print()
        print("=" * 100)
        
        # Recommandations
        print("\n📋 RECOMMANDATIONS\n")
        
        if high_value:
            print(f"⚠️  {len(high_value)} produits ont une valeur > 50,000 DA")
            print("   → Vérifier si ces valeurs sont réalistes")
            print()
        
        if high_pmp:
            print(f"⚠️  {len(high_pmp)} produits ont un PMP > 1000 DA/unité")
            print("   → Vérifier l'unité de base et le dernier prix d'achat")
            print()
        
        if incoherent:
            print(f"⚠️  {len(incoherent)} incohérences détectées")
            print("   → Exécuter: python3 scripts/correction_valorisation_stock.py --apply")
            print()
        
        print(f"💡 Pour plus de détails sur un produit spécifique:")
        print(f"   SELECT * FROM products WHERE id = XXX;")
        print()
        print("=" * 100)

if __name__ == '__main__':
    analyze_stock_value()

