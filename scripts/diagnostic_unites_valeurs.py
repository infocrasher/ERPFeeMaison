#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les problèmes d'unités et de valorisation du stock
Problèmes identifiés :
1. Conversion d'unités (grammes vs pièces)
2. Valeur stock à 0 alors que stock est rempli
3. Mouvements de stock non tracés
"""

import sys
import os
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db
from sqlalchemy import func

def analyze_units_and_values():
    """Analyse les problèmes d'unités et de valorisation"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("DIAGNOSTIC UNITÉS ET VALORISATION DES STOCKS")
        print("=" * 80)
        print()
        
        # 1. Analyser tous les produits avec stock > 0 mais valeur = 0
        print("=" * 80)
        print("1. PRODUITS AVEC STOCK > 0 MAIS VALEUR = 0")
        print("=" * 80)
        print()
        
        products_no_value = Product.query.filter(
            db.or_(
                db.and_(Product.stock_comptoir > 0, Product.valeur_stock_comptoir == 0),
                db.and_(Product.stock_ingredients_magasin > 0, Product.valeur_stock_ingredients_magasin == 0),
                db.and_(Product.stock_ingredients_local > 0, Product.valeur_stock_ingredients_local == 0),
                db.and_(Product.stock_consommables > 0, Product.valeur_stock_consommables == 0),
            )
        ).all()
        
        if products_no_value:
            print(f"⚠️  {len(products_no_value)} produits avec stock mais sans valeur:\n")
            print(f"{'Produit':<30} {'Unité':<10} {'Stock Total':<15} {'Valeur':<12} {'PMP':<12}")
            print("-" * 90)
            
            for p in products_no_value[:30]:  # Limiter à 30
                total_stock = p.total_stock_all_locations
                total_value = float(p.total_stock_value or 0)
                cost_price = float(p.cost_price or 0)
                unit = p.unit or 'N/A'
                
                print(f"{p.name[:28]:<30} {unit:<10} {total_stock:<15.2f} {total_value:<12.2f} {cost_price:<12.4f}")
            
            if len(products_no_value) > 30:
                print(f"\n... et {len(products_no_value) - 30} autres produits")
        else:
            print("✅ Tous les produits avec stock ont une valeur associée")
        
        print()
        
        # 2. Analyser les problèmes d'unités
        print("=" * 80)
        print("2. ANALYSE DES UNITÉS")
        print("=" * 80)
        print()
        
        # Compter les produits par unité
        unit_counts = db.session.query(
            Product.unit,
            func.count(Product.id).label('count')
        ).group_by(Product.unit).all()
        
        print("Distribution des unités :")
        for unit, count in unit_counts:
            print(f"  - {unit or 'NULL'}: {count} produits")
        
        print()
        
        # 3. Identifier les produits suspects (stock très élevé)
        print("=" * 80)
        print("3. STOCKS ANORMALEMENT ÉLEVÉS (>5000)")
        print("=" * 80)
        print()
        
        high_stock_products = Product.query.filter(
            db.or_(
                Product.stock_comptoir > 5000,
                Product.stock_ingredients_magasin > 5000,
                Product.stock_ingredients_local > 5000,
            )
        ).all()
        
        if high_stock_products:
            print(f"⚠️  {len(high_stock_products)} produits avec stock > 5000:\n")
            print(f"{'Produit':<30} {'Unité':<10} {'Comptoir':<12} {'Magasin':<12} {'Local':<12}")
            print("-" * 80)
            
            for p in high_stock_products:
                print(f"{p.name[:28]:<30} {(p.unit or 'N/A'):<10} {p.stock_comptoir:<12.2f} {p.stock_ingredients_magasin:<12.2f} {p.stock_ingredients_local:<12.2f}")
        else:
            print("✅ Aucun stock anormalement élevé")
        
        print()
        
        # 4. Analyser Rechta spécifiquement
        print("=" * 80)
        print("4. ANALYSE DÉTAILLÉE - RECHTA")
        print("=" * 80)
        print()
        
        rechta = Product.query.filter(Product.name.ilike('%rechta%')).first()
        
        if rechta:
            print(f"Produit: {rechta.name} (ID: {rechta.id})")
            print(f"  Unité configurée: {rechta.unit}")
            print(f"  Prix de vente: {rechta.price} DA")
            print(f"  PMP (cost_price): {rechta.cost_price} DA")
            print()
            print("  Stocks par emplacement:")
            print(f"    - Comptoir: {rechta.stock_comptoir} {rechta.unit}")
            print(f"    - Magasin: {rechta.stock_ingredients_magasin} {rechta.unit}")
            print(f"    - Local: {rechta.stock_ingredients_local} {rechta.unit}")
            print(f"    - Consommables: {rechta.stock_consommables} {rechta.unit}")
            print(f"    - TOTAL: {rechta.total_stock_all_locations} {rechta.unit}")
            print()
            print("  Valeurs par emplacement:")
            print(f"    - Valeur comptoir: {rechta.valeur_stock_comptoir} DA")
            print(f"    - Valeur magasin: {rechta.valeur_stock_ingredients_magasin} DA")
            print(f"    - Valeur local: {rechta.valeur_stock_ingredients_local} DA")
            print(f"    - TOTAL: {rechta.total_stock_value} DA")
            print()
            
            # Vérifier si l'unité est cohérente
            if rechta.unit in ['pièce', 'pièces', 'piece', 'pieces', 'unité', 'unités']:
                print("  ⚠️  ATTENTION: Unité configurée en pièces")
                print("     Si vous avez ajouté 10kg, le système a peut-être interprété 10000 comme 10000 pièces")
                print("     Solution: Changer l'unité en 'g' ou 'kg'")
            elif rechta.unit in ['g', 'gramme', 'grammes']:
                print("  ✅ Unité configurée en grammes")
                if rechta.total_stock_all_locations == 10000:
                    print("     Stock de 10000g = 10kg - semble correct")
            elif rechta.unit in ['kg', 'kilogramme', 'kilogrammes']:
                print("  ✅ Unité configurée en kilogrammes")
                if rechta.total_stock_all_locations == 10000:
                    print("  ⚠️  ATTENTION: 10000kg semble très élevé")
                    print("     Avez-vous ajouté 10kg qui ont été interprétés en grammes?")
        else:
            print("❌ Produit Rechta non trouvé")
        
        print()
        
        # 5. Analyser Margarine spécifiquement
        print("=" * 80)
        print("5. ANALYSE DÉTAILLÉE - MARGARINE")
        print("=" * 80)
        print()
        
        margarine = Product.query.filter(Product.name.ilike('%margarine%')).first()
        
        if margarine:
            print(f"Produit: {margarine.name} (ID: {margarine.id})")
            print(f"  Unité configurée: {margarine.unit}")
            print(f"  Prix de vente: {margarine.price} DA")
            print(f"  PMP (cost_price): {margarine.cost_price} DA")
            print()
            print("  Stocks:")
            print(f"    - Total: {margarine.total_stock_all_locations} {margarine.unit}")
            print(f"    - Valeur total: {margarine.total_stock_value} DA")
            print()
            
            if float(margarine.total_stock_value or 0) == 0 and margarine.total_stock_all_locations > 0:
                print("  ⚠️  PROBLÈME: Stock > 0 mais valeur = 0 DA")
                print("     Causes possibles:")
                print("     1. PMP (cost_price) non défini ou = 0")
                print("     2. Stock ajouté sans prix d'achat")
                print("     3. Bug dans la fonction de valorisation")
                
                if float(margarine.cost_price or 0) == 0:
                    print()
                    print("  💡 SOLUTION: Définir un prix d'achat (PMP) pour ce produit")
        else:
            print("❌ Produit Margarine non trouvé")
        
        print()
        
        # 6. Résumé et recommandations
        print("=" * 80)
        print("6. RÉSUMÉ ET RECOMMANDATIONS")
        print("=" * 80)
        print()
        
        # Compter les produits sans PMP
        products_no_pmp = Product.query.filter(
            db.or_(
                Product.cost_price == None,
                Product.cost_price == 0
            ),
            db.or_(
                Product.stock_comptoir > 0,
                Product.stock_ingredients_magasin > 0,
                Product.stock_ingredients_local > 0,
                Product.stock_consommables > 0
            )
        ).count()
        
        print(f"📊 Statistiques:")
        print(f"   - Produits avec stock mais sans valeur: {len(products_no_value)}")
        print(f"   - Produits avec stock mais sans PMP: {products_no_pmp}")
        print(f"   - Produits avec stock > 5000: {len(high_stock_products)}")
        print()
        
        print("📋 RECOMMANDATIONS:")
        print()
        print("1. PROBLÈME D'UNITÉS (Rechta):")
        print("   - Vérifier l'unité configurée pour chaque produit")
        print("   - Si un produit est en grammes, s'assurer que les entrées sont aussi en grammes")
        print("   - La différence de 2 unités (10000 vs 9998) peut être due à des arrondis ou des ventes")
        print()
        print("2. PROBLÈME DE VALORISATION:")
        print("   - Définir le PMP (cost_price) pour tous les produits")
        print("   - Recalculer les valeurs de stock avec le script de correction")
        print("   - Lors de l'ajout de stock, toujours spécifier le prix d'achat")
        print()
        print("3. TRAÇABILITÉ:")
        print("   - Les mouvements de stock ne sont pas tracés")
        print("   - Vérifier que les entrées de stock utilisent la fonction de traçabilité")
        print()
        
        print("=" * 80)

def list_all_products_with_issues():
    """Liste tous les produits avec des problèmes de valorisation"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 80)
        print("LISTE COMPLÈTE DES PRODUITS AVEC PROBLÈMES DE VALORISATION")
        print("=" * 80 + "\n")
        
        products = Product.query.filter(
            Product.total_stock_all_locations > 0
        ).order_by(Product.name).all()
        
        print(f"{'ID':<6} {'Produit':<35} {'Unité':<8} {'Stock':<12} {'Valeur':<12} {'PMP':<10} {'Statut':<15}")
        print("-" * 100)
        
        for p in products:
            total_stock = float(p.total_stock_all_locations or 0)
            total_value = float(p.total_stock_value or 0)
            cost_price = float(p.cost_price or 0)
            
            if total_stock > 0 and total_value == 0:
                status = "⚠️ SANS VALEUR"
            elif cost_price == 0:
                status = "⚠️ SANS PMP"
            else:
                status = "✅ OK"
            
            print(f"{p.id:<6} {p.name[:33]:<35} {(p.unit or 'N/A'):<8} {total_stock:<12.2f} {total_value:<12.2f} {cost_price:<10.4f} {status:<15}")

if __name__ == '__main__':
    analyze_units_and_values()
    
    # Demander si l'utilisateur veut voir la liste complète
    print("\n" + "=" * 80)
    response = input("Voulez-vous voir la liste complète des produits avec problèmes ? (o/n) : ")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        list_all_products_with_issues()

