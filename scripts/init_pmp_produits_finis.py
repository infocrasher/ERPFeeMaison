#!/usr/bin/env python3
"""
Script pour initialiser le PMP des produits finis sans cost_price
Deux méthodes :
1. Basé sur le coût de la recette (si disponible)
2. Basé sur un pourcentage du prix de vente (par défaut 70%)
"""

import sys
import os
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import Product
from extensions import db

def init_pmp_products(dry_run=True, percentage=70):
    """Initialise le PMP des produits finis sans cost_price"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("INITIALISATION PMP PRODUITS FINIS")
        print(f"Mode: {'SIMULATION (dry-run)' if dry_run else '⚠️ MODIFICATION RÉELLE'}")
        print(f"Pourcentage du prix de vente: {percentage}%")
        print("=" * 80)
        print()
        
        # Récupérer les produits sans PMP avec stock > 0
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
        
        if not products_no_pmp:
            print("✅ Tous les produits avec stock ont un PMP défini")
            return
        
        print(f"📋 {len(products_no_pmp)} produits trouvés\n")
        print(f"{'ID':<6} {'Produit':<35} {'Prix Vente':<12} {'PMP Calculé':<15} {'Méthode':<20}")
        print("-" * 95)
        
        updates_made = 0
        
        for p in products_no_pmp:
            # Méthode 1 : Si le produit a une recette, utiliser le coût de la recette
            if hasattr(p, 'recipe_definition') and p.recipe_definition:
                recipe = p.recipe_definition
                cost_per_unit = recipe.cost_per_unit
                if cost_per_unit and cost_per_unit > 0:
                    new_pmp = Decimal(str(cost_per_unit)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                    method = "Recette"
                else:
                    # Fallback : pourcentage du prix de vente
                    new_pmp = (Decimal(str(p.price or 0)) * Decimal(str(percentage)) / Decimal('100')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                    method = f"{percentage}% prix vente"
            else:
                # Méthode 2 : Pourcentage du prix de vente
                new_pmp = (Decimal(str(p.price or 0)) * Decimal(str(percentage)) / Decimal('100')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                method = f"{percentage}% prix vente"
            
            print(f"{p.id:<6} {p.name[:33]:<35} {float(p.price or 0):<12.2f} {float(new_pmp):<15.4f} {method:<20}")
            
            if not dry_run:
                p.cost_price = new_pmp
                updates_made += 1
        
        if not dry_run:
            db.session.commit()
            print()
            print(f"✅ {updates_made} PMP initialisés")
            print()
            print("⚠️  IMPORTANT: Exécutez maintenant le script de correction de valorisation:")
            print("   python3 scripts/correction_valorisation_stock.py --apply")
        else:
            print()
            print(f"📋 {len(products_no_pmp)} PMP à initialiser")
            print()
            print("Pour appliquer ces changements, exécutez:")
            print("  python3 scripts/init_pmp_produits_finis.py --apply")
            print()
            print("Puis recalculez les valeurs de stock:")
            print("  python3 scripts/correction_valorisation_stock.py --apply")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        print("⚠️  ATTENTION: Ce script va définir le PMP pour les produits sans cost_price !")
        confirm = input("Êtes-vous sûr de vouloir continuer ? (oui/non) : ")
        if confirm.lower() == 'oui':
            # Vérifier si un pourcentage personnalisé est fourni
            percentage = 70  # Par défaut 70%
            if len(sys.argv) > 2:
                try:
                    percentage = int(sys.argv[2])
                    if percentage < 0 or percentage > 100:
                        print("❌ Le pourcentage doit être entre 0 et 100")
                        sys.exit(1)
                except ValueError:
                    print("❌ Le pourcentage doit être un nombre entier")
                    sys.exit(1)
            
            init_pmp_products(dry_run=False, percentage=percentage)
        else:
            print("❌ Opération annulée")
    else:
        # Mode simulation
        percentage = 70  # Par défaut 70%
        if len(sys.argv) > 1:
            try:
                percentage = int(sys.argv[1])
                if percentage < 0 or percentage > 100:
                    print("❌ Le pourcentage doit être entre 0 et 100")
                    sys.exit(1)
            except ValueError:
                print("❌ Usage: python3 scripts/init_pmp_produits_finis.py [pourcentage] [--apply]")
                sys.exit(1)
        
        init_pmp_products(dry_run=True, percentage=percentage)

