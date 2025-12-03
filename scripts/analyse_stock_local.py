#!/usr/bin/env python3
"""
Script pour analyser en détail le stock local et détecter les anomalies
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def analyze_stock_local():
    """Analyse détaillée du stock local"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("ANALYSE DÉTAILLÉE DU STOCK LOCAL")
        print("=" * 120)
        print()
        
        # Récupérer tous les ingrédients avec stock local > 0
        ingredients = Product.query.filter(
            Product.product_type == 'ingredient',
            Product.stock_ingredients_local > 0
        ).order_by(Product.valeur_stock_ingredients_local.desc()).all()
        
        if not ingredients:
            print("❌ Aucun ingrédient trouvé dans le stock local")
            return
        
        print(f"📦 {len(ingredients)} ingrédients avec stock local\n")
        
        # Afficher tous les produits avec leurs détails
        print(f"{'ID':<6} {'Produit':<40} {'Qté Stock':<15} {'PMP':<15} {'Valeur Stockée':<18} {'Valeur Calculée':<18} {'Diff':<12}")
        print("-" * 120)
        
        total_valeur_stockee = 0.0
        total_valeur_calculee = 0.0
        anomalies = []
        
        for p in ingredients:
            stock = float(p.stock_ingredients_local or 0)
            pmp = float(p.cost_price or 0)
            valeur_stockee = float(p.valeur_stock_ingredients_local or 0)
            valeur_calculee = stock * pmp
            diff = abs(valeur_calculee - valeur_stockee)
            
            total_valeur_stockee += valeur_stockee
            total_valeur_calculee += valeur_calculee
            
            # Détecter les anomalies (différence > 1 DA)
            if diff > 1.0:
                anomalies.append({
                    'product': p,
                    'stock': stock,
                    'pmp': pmp,
                    'valeur_stockee': valeur_stockee,
                    'valeur_calculee': valeur_calculee,
                    'diff': diff
                })
            
            # Afficher avec couleur si anomalie
            marker = "⚠️ " if diff > 1.0 else "   "
            print(f"{marker}{p.id:<6} {p.name[:38]:<40} {stock:<15.2f} {pmp:<15.4f} {valeur_stockee:<18.2f} {valeur_calculee:<18.2f} {diff:<12.2f}")
        
        print("-" * 120)
        print(f"{'TOTAL':<47} {'':<15} {'':<15} {total_valeur_stockee:<18.2f} {total_valeur_calculee:<18.2f} {abs(total_valeur_calculee - total_valeur_stockee):<12.2f}")
        print()
        
        # Résumé
        print("=" * 120)
        print("RÉSUMÉ")
        print("=" * 120)
        print(f"💰 Valeur totale stockée (valeur_stock_ingredients_local) : {total_valeur_stockee:,.2f} DA".replace(",", " "))
        print(f"🧮 Valeur totale calculée (Qté × PMP)                     : {total_valeur_calculee:,.2f} DA".replace(",", " "))
        print(f"📊 Différence                                             : {abs(total_valeur_calculee - total_valeur_stockee):,.2f} DA".replace(",", " "))
        print()
        
        # Anomalies
        if anomalies:
            print("=" * 120)
            print(f"⚠️  ANOMALIES DÉTECTÉES ({len(anomalies)} produits)")
            print("=" * 120)
            print()
            
            for item in anomalies:
                p = item['product']
                print(f"Produit : {p.name} (ID: {p.id})")
                print(f"  Stock       : {item['stock']:.2f} {p.unit}")
                print(f"  PMP         : {item['pmp']:.4f} DA/{p.unit}")
                print(f"  Valeur BDD  : {item['valeur_stockee']:.2f} DA")
                print(f"  Valeur calc : {item['valeur_calculee']:.2f} DA")
                print(f"  Différence  : {item['diff']:.2f} DA")
                print()
        else:
            print("✅ Aucune anomalie détectée (toutes les valeurs sont cohérentes)")
            print()
        
        # Top 10 des produits par valeur
        print("=" * 120)
        print("TOP 10 - PRODUITS PAR VALEUR")
        print("=" * 120)
        print(f"{'Rang':<6} {'Produit':<40} {'Qté':<15} {'PMP':<15} {'Valeur':<18} {'% Total':<10}")
        print("-" * 120)
        
        top_10 = sorted(ingredients, key=lambda p: float(p.valeur_stock_ingredients_local or 0), reverse=True)[:10]
        for i, p in enumerate(top_10, 1):
            stock = float(p.stock_ingredients_local or 0)
            pmp = float(p.cost_price or 0)
            valeur = float(p.valeur_stock_ingredients_local or 0)
            pct = (valeur / total_valeur_stockee * 100) if total_valeur_stockee > 0 else 0
            
            print(f"{i:<6} {p.name[:38]:<40} {stock:<15.2f} {pmp:<15.4f} {valeur:<18.2f} {pct:<10.2f}%")
        
        print()
        
        # Produits avec PMP élevé
        high_pmp = [p for p in ingredients if float(p.cost_price or 0) > 100]
        if high_pmp:
            print("=" * 120)
            print(f"⚠️  PRODUITS AVEC PMP > 100 DA ({len(high_pmp)} produits)")
            print("=" * 120)
            print(f"{'ID':<6} {'Produit':<40} {'Qté':<15} {'PMP':<15} {'Valeur':<18} {'Unité':<10}")
            print("-" * 120)
            
            for p in high_pmp:
                stock = float(p.stock_ingredients_local or 0)
                pmp = float(p.cost_price or 0)
                valeur = float(p.valeur_stock_ingredients_local or 0)
                
                print(f"{p.id:<6} {p.name[:38]:<40} {stock:<15.2f} {pmp:<15.4f} {valeur:<18.2f} {p.unit or 'N/A':<10}")
            print()
        
        # Produits avec valeur élevée
        high_value = [p for p in ingredients if float(p.valeur_stock_ingredients_local or 0) > 50000]
        if high_value:
            print("=" * 120)
            print(f"⚠️  PRODUITS AVEC VALEUR > 50,000 DA ({len(high_value)} produits)")
            print("=" * 120)
            print(f"{'ID':<6} {'Produit':<40} {'Qté':<15} {'PMP':<15} {'Valeur':<18}")
            print("-" * 120)
            
            for p in high_value:
                stock = float(p.stock_ingredients_local or 0)
                pmp = float(p.cost_price or 0)
                valeur = float(p.valeur_stock_ingredients_local or 0)
                
                print(f"{p.id:<6} {p.name[:38]:<40} {stock:<15.2f} {pmp:<15.4f} {valeur:<18.2f}")
            print()
        
        print("=" * 120)
        print("\n💡 Pour corriger les incohérences détectées, exécutez:")
        print("   python3 scripts/correction_valorisation_stock.py --apply")
        print()
        print("=" * 120)

if __name__ == '__main__':
    analyze_stock_local()

