#!/usr/bin/env python3
"""
Script pour configurer une catégorie exemple avec plusieurs plages
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Category, Product
from app.consumables.models import ConsumableCategory, ConsumableRange

def configure_example():
    """Configure une catégorie exemple complète"""
    app = create_app('development')
    
    with app.app_context():
        print("🔧 Configuration d'une catégorie exemple complète")
        print("=" * 60)
        
        # 1. Trouver ou créer la catégorie
        category = Category.query.filter_by(name='Gateaux ').first()
        if not category:
            print("❌ Catégorie 'Gateaux ' non trouvée")
            return
        
        print(f"✅ Catégorie trouvée : {category.name}")
        
        # 2. Trouver ou créer la catégorie de consommables
        consumable_category = ConsumableCategory.query.filter_by(product_category_id=category.id).first()
        
        if consumable_category:
            print(f"✅ Catégorie de consommables existante : {consumable_category.name}")
            
            # Supprimer les anciennes plages
            old_ranges = ConsumableRange.query.filter_by(category_id=consumable_category.id).all()
            for range_obj in old_ranges:
                db.session.delete(range_obj)
            print(f"🗑️  {len(old_ranges)} anciennes plages supprimées")
        else:
            # Créer la catégorie
            consumable_category = ConsumableCategory(
                name='Gâteaux individuels',
                description='Configuration pour les gâteaux individuels avec différentes tailles de boîtes',
                product_category_id=category.id,
                is_active=True
            )
            db.session.add(consumable_category)
            db.session.flush()
            print("✅ Catégorie de consommables créée")
        
        # 3. Créer les consommables s'ils n'existent pas
        consumables_data = [
            {'name': 'Boite 18', 'min': 1, 'max': 8},
            {'name': 'Boite 36', 'min': 9, 'max': 12},
            {'name': 'Boite 48/10', 'min': 13, 'max': 20},
            {'name': 'Plateau', 'min': 21, 'max': 70}
        ]
        
        consumables_dict = {}
        for data in consumables_data:
            consumable = Product.query.filter_by(name=data['name'], product_type='consommable').first()
            if not consumable:
                # Créer le consommable
                category_cons = Category.query.filter_by(name='Boite Consomable').first()
                consumable = Product(
                    name=data['name'],
                    product_type='consommable',
                    unit='pièces',
                    category_id=category_cons.id if category_cons else None,
                    stock_consommables=100
                )
                db.session.add(consumable)
                print(f"✅ Consommable créé : {data['name']}")
            else:
                print(f"✅ Consommable existant : {data['name']}")
            
            consumables_dict[(data['min'], data['max'])] = consumable
        
        db.session.commit()
        
        # 4. Créer les plages
        print("\n📋 Création des plages...")
        ranges_to_create = [
            (1, 8, consumables_dict.get((1, 8))),
            (9, 12, consumables_dict.get((9, 12))),
            (13, 20, consumables_dict.get((13, 20))),
            (21, 70, consumables_dict.get((21, 70)))
        ]
        
        for min_qty, max_qty, consumable in ranges_to_create:
            if not consumable:
                print(f"⚠️  Consommable manquant pour plage {min_qty}-{max_qty}")
                continue
            
            # Créer la plage
            range_obj = ConsumableRange(
                category_id=consumable_category.id,
                min_quantity=min_qty,
                max_quantity=max_qty,
                consumable_product_id=consumable.id,
                quantity_per_unit=1.0
            )
            db.session.add(range_obj)
            print(f"✅ Plage ajoutée : {min_qty}-{max_qty} → {consumable.name}")
        
        db.session.commit()
        
        # 5. Tester le système
        print("\n🧪 TEST DU SYSTÈME")
        print("-" * 40)
        
        test_quantities = [5, 10, 15, 25, 50, 75, 100]
        
        for qty in test_quantities:
            consumables_needed = consumable_category.calculate_consumables_needed(qty)
            print(f"\n{qty} pièces → ", end='')
            if consumables_needed:
                result = []
                for consumable, quantity in consumables_needed:
                    result.append(f"{quantity}× {consumable.name}")
                print(", ".join(result))
            else:
                print("❌ Aucun consommable trouvé")
        
        print("\n🎉 CONFIGURATION TERMINÉE !")
        print("=" * 60)
        print(f"✅ Catégorie : {consumable_category.name}")
        print(f"✅ Plages configurées : {len(ranges_to_create)}")
        print(f"✅ Testé avec succès !")

if __name__ == "__main__":
    configure_example()

