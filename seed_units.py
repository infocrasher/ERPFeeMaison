import sys
import os
from decimal import Decimal

# Ajoute le répertoire racine du projet au chemin de recherche de Python
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import Unit
from extensions import db

# Crée une instance de l'application Flask pour avoir le contexte
# Assurez-vous que la configuration par défaut dans config.py pointe vers votre base de données de développement
config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(config_name)

# La liste finale des unités que nous avons validée
units_to_seed = [
    # Poids
    {'name': 'Sac 25kg', 'base_unit': 'g', 'conversion_factor': Decimal('25000'), 'unit_type': 'Poids'},
    {'name': 'Sac 10kg', 'base_unit': 'g', 'conversion_factor': Decimal('10000'), 'unit_type': 'Poids'},
    {'name': 'Sac 5kg', 'base_unit': 'g', 'conversion_factor': Decimal('5000'), 'unit_type': 'Poids'},
    {'name': 'Sac 2kg', 'base_unit': 'g', 'conversion_factor': Decimal('2000'), 'unit_type': 'Poids'},
    {'name': 'Sac 1kg', 'base_unit': 'g', 'conversion_factor': Decimal('1000'), 'unit_type': 'Poids'},
    {'name': 'Barre 1,8kg', 'base_unit': 'g', 'conversion_factor': Decimal('1800'), 'unit_type': 'Poids'},
    {'name': 'Bidon 3,8kg', 'base_unit': 'g', 'conversion_factor': Decimal('3800'), 'unit_type': 'Poids'},
    {'name': 'Boite 500g', 'base_unit': 'g', 'conversion_factor': Decimal('500'), 'unit_type': 'Poids'},
    {'name': 'Sachet 500g', 'base_unit': 'g', 'conversion_factor': Decimal('500'), 'unit_type': 'Poids'},
    {'name': 'Pot 500g', 'base_unit': 'g', 'conversion_factor': Decimal('500'), 'unit_type': 'Poids'},
    {'name': 'Boite 250g', 'base_unit': 'g', 'conversion_factor': Decimal('250'), 'unit_type': 'Poids'},
    {'name': 'Sachet 125g', 'base_unit': 'g', 'conversion_factor': Decimal('125'), 'unit_type': 'Poids'},
    {'name': 'Sachet 10g', 'base_unit': 'g', 'conversion_factor': Decimal('10'), 'unit_type': 'Poids'},
    
    # Volume
    {'name': 'Bidon 5L', 'base_unit': 'ml', 'conversion_factor': Decimal('5000'), 'unit_type': 'Volume'},
    {'name': 'Bouteille 5L', 'base_unit': 'ml', 'conversion_factor': Decimal('5000'), 'unit_type': 'Volume'},
    {'name': 'Bouteille 2L', 'base_unit': 'ml', 'conversion_factor': Decimal('2000'), 'unit_type': 'Volume'},
    {'name': 'Bouteille 1L', 'base_unit': 'ml', 'conversion_factor': Decimal('1000'), 'unit_type': 'Volume'},
    
    # Pièces/Unités
    {'name': 'Lot de 100 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('100'), 'unit_type': 'Unitaire'},
    {'name': 'Lot de 50 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('50'), 'unit_type': 'Unitaire'},
    {'name': 'Plateau de 30 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('30'), 'unit_type': 'Unitaire'},
    {'name': 'Lot de 12 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('12'), 'unit_type': 'Unitaire'},
    {'name': 'Lot de 10 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('10'), 'unit_type': 'Unitaire'},
    {'name': 'Lot de 6 pièces', 'base_unit': 'pièce', 'conversion_factor': Decimal('6'), 'unit_type': 'Unitaire'},
    {'name': 'Fardeau de 6 bouteilles', 'base_unit': 'pièce', 'conversion_factor': Decimal('6'), 'unit_type': 'Unitaire'},

    # Unités de Base (avec des noms clairs)
    {'name': 'Gramme (g)', 'base_unit': 'g', 'conversion_factor': Decimal('1'), 'unit_type': 'Poids'},
    {'name': 'Millilitre (ml)', 'base_unit': 'ml', 'conversion_factor': Decimal('1'), 'unit_type': 'Volume'},
    {'name': 'Pièce', 'base_unit': 'pièce', 'conversion_factor': Decimal('1'), 'unit_type': 'Unitaire'},
]

def seed_db():
    with app.app_context():
        print("Début du seeding des unités...")
        
        for unit_data in units_to_seed:
            existing_unit = Unit.query.filter_by(name=unit_data['name']).first()
            
            if existing_unit:
                print(f"  -> Ignoré : L'unité '{unit_data['name']}' existe déjà.")
            else:
                new_unit = Unit(
                    name=unit_data['name'],
                    base_unit=unit_data['base_unit'],
                    conversion_factor=unit_data['conversion_factor'],
                    unit_type=unit_data['unit_type']
                )
                db.session.add(new_unit)
                print(f"  -> ✅ Créé : L'unité '{unit_data['name']}' a été ajoutée.")
        
        try:
            db.session.commit()
            print("\nSeeding terminé avec succès !")
        except Exception as e:
            db.session.rollback()
            print(f"\nErreur lors du commit : {e}")

if __name__ == '__main__':
    seed_db()