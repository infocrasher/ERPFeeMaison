#!/usr/bin/env python3
"""
Script de correction de la valorisation des stocks
Recalcule les valeurs de stock basées sur le PMP (cost_price)

ATTENTION: Ce script modifie la base de données !
Exécutez d'abord avec --dry-run pour voir les changements proposés
"""

import sys
import os
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def recalculate_stock_values(dry_run=True):
    """Recalcule les valeurs de stock basées sur le PMP"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("CORRECTION DE LA VALORISATION DES STOCKS")
        print(f"Mode: {'SIMULATION (dry-run)' if dry_run else '⚠️ MODIFICATION RÉELLE'}")
        print("=" * 80)
        print()
        
        # Récupérer tous les produits avec stock > 0
        products = Product.query.filter(
            db.or_(
                Product.stock_comptoir > 0,
                Product.stock_ingredients_magasin > 0,
                Product.stock_ingredients_local > 0,
                Product.stock_consommables > 0
            )
        ).all()
        
        corrections_needed = 0
        corrections_made = 0
        
        print(f"{'ID':<6} {'Produit':<30} {'Stock':<12} {'PMP':<10} {'Ancienne Val.':<15} {'Nouvelle Val.':<15}")
        print("-" * 100)
        
        for p in products:
            # Calculer la valeur attendue basée sur le PMP
            cost_price = Decimal(str(p.cost_price or 0))
            
            # Si pas de PMP, on ne peut pas valoriser
            if cost_price <= 0:
                continue
            
            # Calculer les nouvelles valeurs
            stock_comptoir = Decimal(str(p.stock_comptoir or 0))
            stock_magasin = Decimal(str(p.stock_ingredients_magasin or 0))
            stock_local = Decimal(str(p.stock_ingredients_local or 0))
            stock_consommables = Decimal(str(p.stock_consommables or 0))
            
            expected_value_comptoir = stock_comptoir * cost_price
            expected_value_magasin = stock_magasin * cost_price
            expected_value_local = stock_local * cost_price
            expected_value_consommables = stock_consommables * cost_price
            expected_total_value = expected_value_comptoir + expected_value_magasin + expected_value_local + expected_value_consommables
            
            current_total_value = Decimal(str(p.total_stock_value or 0))
            
            # Vérifier si une correction est nécessaire
            tolerance = Decimal('0.01')
            if abs(expected_total_value - current_total_value) > tolerance:
                corrections_needed += 1
                
                print(f"{p.id:<6} {p.name[:28]:<30} {float(p.total_stock_all_locations):<12.2f} {float(cost_price):<10.4f} {float(current_total_value):<15.2f} {float(expected_total_value):<15.2f}")
                
                if not dry_run:
                    # Appliquer les corrections
                    p.valeur_stock_comptoir = expected_value_comptoir
                    p.valeur_stock_ingredients_magasin = expected_value_magasin
                    p.valeur_stock_ingredients_local = expected_value_local
                    p.valeur_stock_consommables = expected_value_consommables
                    p.total_stock_value = expected_total_value
                    corrections_made += 1
        
        if not dry_run:
            db.session.commit()
            print()
            print(f"✅ {corrections_made} corrections appliquées")
        else:
            print()
            print(f"📋 {corrections_needed} corrections nécessaires")
            print()
            print("Pour appliquer les corrections, exécutez:")
            print("  python3 scripts/correction_valorisation_stock.py --apply")
        
        print()
        print("=" * 80)

def set_default_pmp_for_products_without():
    """Définit un PMP par défaut pour les produits sans PMP"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("PRODUITS SANS PMP (cost_price)")
        print("=" * 80)
        print()
        
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
        ).all()
        
        if products_no_pmp:
            print(f"⚠️  {len(products_no_pmp)} produits avec stock mais sans PMP:\n")
            print(f"{'ID':<6} {'Produit':<35} {'Stock':<12} {'Prix Vente':<12}")
            print("-" * 70)
            
            for p in products_no_pmp:
                print(f"{p.id:<6} {p.name[:33]:<35} {float(p.total_stock_all_locations):<12.2f} {float(p.price or 0):<12.2f}")
            
            print()
            print("💡 Pour définir un PMP, vous pouvez:")
            print("   1. Modifier chaque produit via l'interface admin")
            print("   2. Utiliser une requête SQL directe:")
            print()
            print("   -- Exemple: Définir PMP = 80% du prix de vente")
            print("   UPDATE products SET cost_price = price * 0.8 WHERE cost_price IS NULL OR cost_price = 0;")
        else:
            print("✅ Tous les produits avec stock ont un PMP défini")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        print("⚠️  ATTENTION: Ce script va MODIFIER la base de données !")
        confirm = input("Êtes-vous sûr de vouloir continuer ? (oui/non) : ")
        if confirm.lower() == 'oui':
            recalculate_stock_values(dry_run=False)
        else:
            print("❌ Opération annulée")
    else:
        recalculate_stock_values(dry_run=True)
        print()
        set_default_pmp_for_products_without()

