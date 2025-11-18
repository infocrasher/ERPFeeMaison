#!/usr/bin/env python3
"""
Script pour créer un gabarit Excel vide correct avec les noms exacts de la base de données
"""

import pandas as pd
from app import create_app, db
from models import Product, Category, Unit

def create_correct_template():
    """Crée un gabarit Excel vide avec la structure correcte"""
    app = create_app()
    
    with app.app_context():
        # Récupérer les données de la base
        ingredients = Product.query.filter_by(product_type='ingredient').all()
        finished_products = Product.query.filter_by(product_type='finished').all()
        categories = Category.query.all()
        units = Unit.query.all()
        
        # Créer les feuilles du gabarit
        
        # 1. Feuille Ingrédients
        ingredients_data = []
        for ing in ingredients:
            ingredients_data.append({
                'nom_ingredient': ing.name,
                'prix_achat': '',
                'unite': ing.unit,
                'description': ing.description or '',
                'categorie': ing.category.name if ing.category else ''
            })
        
        df_ingredients = pd.DataFrame(ingredients_data)
        
        # 2. Feuille Produits_Finis
        products_data = []
        for prod in finished_products:
            products_data.append({
                'nom_produit': prod.name,
                'categorie': prod.category.name if prod.category else '',
                'prix_vente': '',
                'unite': prod.unit,
                'description': prod.description or ''
            })
        
        df_products = pd.DataFrame(products_data)
        
        # 3. Feuille Recettes (vide)
        recipes_data = []
        for prod in finished_products:
            recipes_data.append({
                'nom_recette': prod.name,
                'description': f'Recette pour {prod.name}',
                'produit_fini_lie': prod.name,
                'rendement': '',
                'unite_rendement': 'pièce',
                'temps_preparation': '',
                'temps_cuisson': '',
                'niveau_difficulte': 'moyen',
                'lieu_production': 'ingredients_magasin'
            })
        
        df_recipes = pd.DataFrame(recipes_data)
        
        # 4. Feuille Ingrédients_Recette (vide)
        ingredients_recipe_data = []
        for prod in finished_products:
            # Ajouter quelques lignes vides pour chaque recette
            for i in range(10):  # 10 lignes par recette
                ingredients_recipe_data.append({
                    'nom_recette': prod.name,
                    'nom_ingredient': '',
                    'quantite': '',
                    'unite': 'g',
                    'notes': ''
                })
        
        df_ingredients_recipe = pd.DataFrame(ingredients_recipe_data)
        
        # 5. Feuille Catégories
        categories_data = []
        for cat in categories:
            categories_data.append({
                'nom_categorie': cat.name,
                'description': cat.description or ''
            })
        
        df_categories = pd.DataFrame(categories_data)
        
        # 6. Feuille Unités
        units_data = []
        for unit in units:
            units_data.append({
                'nom_unite': unit.name,
                'base_unite': unit.base_unit,
                'facteur_conversion': unit.conversion_factor,
                'type_unite': unit.unit_type
            })
        
        df_units = pd.DataFrame(units_data)
        
        # Créer le fichier Excel
        with pd.ExcelWriter('Gabarit_Vide_Correct.xlsx', engine='openpyxl') as writer:
            df_ingredients.to_excel(writer, sheet_name='Ingrédients', index=False)
            df_products.to_excel(writer, sheet_name='Produits_Finis', index=False)
            df_recipes.to_excel(writer, sheet_name='Recettes', index=False)
            df_ingredients_recipe.to_excel(writer, sheet_name='Ingrédients_Recette', index=False)
            df_categories.to_excel(writer, sheet_name='Catégories', index=False)
            df_units.to_excel(writer, sheet_name='Unités', index=False)
        
        print("✅ Gabarit vide correct créé: Gabarit_Vide_Correct.xlsx")
        print(f"📊 Contenu:")
        print(f"  - {len(ingredients)} ingrédients")
        print(f"  - {len(finished_products)} produits finis")
        print(f"  - {len(categories)} catégories")
        print(f"  - {len(units)} unités")

if __name__ == "__main__":
    create_correct_template() 