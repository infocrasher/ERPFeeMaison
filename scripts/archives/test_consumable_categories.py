#!/usr/bin/env python3
"""
Script de test pour le nouveau système de catégories de consommables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Product, Category
from app.consumables.models import ConsumableCategory, ConsumableRange
from datetime import datetime

def test_consumable_categories():
    """Tester le système de catégories de consommables"""
    
    app = create_app('development')
    
    with app.app_context():
        print("🧪 TEST : Système de catégories de consommables")
        print("=" * 60)
        
        # 1. Vérifier les tables
        print("\n1️⃣ VÉRIFICATION DES TABLES")
        print("-" * 40)
        
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'consumable_categories' in tables and 'consumable_ranges' in tables:
            print("✅ Tables créées : consumable_categories, consumable_ranges")
        else:
            print("❌ Tables manquantes")
            return False
        
        # 2. Créer une catégorie de test
        print("\n2️⃣ CRÉATION D'UNE CATÉGORIE DE TEST")
        print("-" * 40)
        
        # Trouver la catégorie "Gateaux "
        category = Category.query.filter_by(name='Gateaux ').first()
        if not category:
            print("❌ Catégorie 'Gateaux ' non trouvée")
            return False
        
        print(f"✅ Catégorie trouvée : {category.name}")
        
        # Créer une catégorie de consommables
        consumable_category = ConsumableCategory.query.filter_by(product_category_id=category.id).first()
        
        if not consumable_category:
            print("📋 Création d'une catégorie de consommables...")
            consumable_category = ConsumableCategory(
                name='Gâteaux individuels',
                description='Configuration pour les gâteaux individuels',
                product_category_id=category.id,
                is_active=True
            )
            db.session.add(consumable_category)
            db.session.flush()  # Pour obtenir l'ID
            
            print("✅ Catégorie créée : Gâteaux individuels")
        else:
            print(f"✅ Catégorie existante : {consumable_category.name}")
        
        # 3. Ajouter des plages de quantités
        print("\n3️⃣ CONFIGURATION DES PLAGES")
        print("-" * 40)
        
        # Trouver des consommables
        boite_18 = Product.query.filter_by(name='Boite 18').first()
        boite_36 = Product.query.filter_by(name='Boite 36').first()
        boite_48 = Product.query.filter_by(name='Boite 48/10').first()
        plateau = Product.query.filter(Product.name.like('%Plateau%')).first()
        
        consumables_available = {
            '1-8': boite_18 if boite_18 else None,
            '9-12': boite_36 if boite_36 else None,
            '13-20': boite_48 if boite_48 else None,
            '21-70': plateau if plateau else None
        }
        
        # Plages de test
        ranges_to_create = [
            {'min': 1, 'max': 8, 'consumable': consumables_available.get('1-8')},
            {'min': 9, 'max': 12, 'consumable': consumables_available.get('9-12')},
            {'min': 13, 'max': 20, 'consumable': consumables_available.get('13-20')},
            {'min': 21, 'max': 70, 'consumable': consumables_available.get('21-70')}
        ]
        
        for range_data in ranges_to_create:
            if not range_data['consumable']:
                print(f"⚠️  Consommable manquant pour plage {range_data['min']}-{range_data['max']}")
                continue
            
            # Vérifier si la plage existe déjà
            existing_range = ConsumableRange.query.filter(
                ConsumableRange.category_id == consumable_category.id,
                ConsumableRange.min_quantity == range_data['min'],
                ConsumableRange.max_quantity == range_data['max']
            ).first()
            
            if not existing_range:
                consumable_range = ConsumableRange(
                    category_id=consumable_category.id,
                    min_quantity=range_data['min'],
                    max_quantity=range_data['max'],
                    consumable_product_id=range_data['consumable'].id,
                    quantity_per_unit=1.0
                )
                db.session.add(consumable_range)
                print(f"✅ Plage ajoutée : {range_data['min']}-{range_data['max']} = {range_data['consumable'].name}")
            else:
                print(f"✅ Plage existante : {range_data['min']}-{range_data['max']} = {existing_range.consumable_product.name}")
        
        db.session.commit()
        
        # 4. Tester le calcul des consommables
        print("\n4️⃣ TEST DU CALCUL")
        print("-" * 40)
        
        test_quantities = [5, 10, 15, 25, 50, 75, 100]
        
        for qty in test_quantities:
            consumables_needed = consumable_category.calculate_consumables_needed(qty)
            print(f"\nPour {qty} pièces :")
            for consumable, quantity in consumables_needed:
                if consumable:
                    print(f"  - {quantity}× {consumable.name}")
        
        print("\n🎉 TEST TERMINÉ")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    success = test_consumable_categories()
    if not success:
        sys.exit(1)

