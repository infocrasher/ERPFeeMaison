#!/usr/bin/env python3
"""
Script d'injection parfait pour le gabarit correct
Utilise les noms exacts de la base de données
"""

import pandas as pd
from decimal import Decimal
from app import create_app, db
from models import User, Category, Product, Unit, Recipe, RecipeIngredient
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_yield_quantity(yield_str):
    """Parse le rendement et calcule la moyenne si c'est une plage (ex: 53-60 -> 56.5)"""
    if pd.isna(yield_str) or yield_str == '':
        return 1
    
    yield_str = str(yield_str).strip()
    
    # Si c'est une plage (ex: 53-60)
    if '-' in yield_str:
        try:
            parts = yield_str.split('-')
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())
            return (min_val + max_val) / 2
        except:
            return 1
    
    # Si c'est un nombre simple
    try:
        return float(yield_str)
    except:
        return 1

def load_gabarit_data():
    """Charge les données du gabarit correct"""
    try:
        logger.info("📂 Chargement du gabarit correct...")
        
        # Charger toutes les feuilles
        ingredients = pd.read_excel('Gabarit_Vide_Correct.xlsx', sheet_name='Ingrédients')
        products = pd.read_excel('Gabarit_Vide_Correct.xlsx', sheet_name='Produits_Finis')
        recipes = pd.read_excel('Gabarit_Vide_Correct.xlsx', sheet_name='Recettes')
        ingredients_recipe = pd.read_excel('Gabarit_Vide_Correct.xlsx', sheet_name='Ingrédients_Recette')
        
        # Filtrer les lignes vides
        ingredients = ingredients[ingredients['nom_ingredient'].notna() & (ingredients['nom_ingredient'] != '')]
        products = products[products['nom_produit'].notna() & (products['nom_produit'] != '')]
        recipes = recipes[recipes['nom_recette'].notna() & (recipes['nom_recette'] != '')]
        ingredients_recipe = ingredients_recipe[
            (ingredients_recipe['nom_recette'].notna()) & 
            (ingredients_recipe['nom_recette'] != '') &
            (ingredients_recipe['nom_ingredient'].notna()) & 
            (ingredients_recipe['nom_ingredient'] != '')
        ]
        
        logger.info(f"✅ Données chargées:")
        logger.info(f"  - {len(ingredients)} ingrédients avec prix")
        logger.info(f"  - {len(products)} produits finis avec prix")
        logger.info(f"  - {len(recipes)} recettes")
        logger.info(f"  - {len(ingredients_recipe)} ingrédients de recettes")
        
        return {
            'ingredients': ingredients,
            'products': products,
            'recipes': recipes,
            'ingredients_recipe': ingredients_recipe
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement: {e}")
        return None

def update_ingredient_prices(data):
    """Met à jour les prix des ingrédients"""
    logger.info("💰 Mise à jour des prix des ingrédients")
    
    updated_count = 0
    
    for _, row in data['ingredients'].iterrows():
        nom = row['nom_ingredient']
        prix = row['prix_achat']
        
        if pd.isna(prix) or prix == '':
            continue
        
        try:
            ingredient = Product.query.filter_by(name=nom, product_type='ingredient').first()
            if ingredient:
                ingredient.cost_price = Decimal(str(prix))
                updated_count += 1
                logger.info(f"✅ {nom}: {prix} DA")
        except Exception as e:
            logger.error(f"❌ Erreur pour {nom}: {e}")
    
    db.session.commit()
    logger.info(f"📊 {updated_count} prix d'ingrédients mis à jour")

def update_product_prices(data):
    """Met à jour les prix des produits finis"""
    logger.info("💰 Mise à jour des prix des produits finis")
    
    updated_count = 0
    
    for _, row in data['products'].iterrows():
        nom = row['nom_produit']
        prix = row['prix_vente']
        
        if pd.isna(prix) or prix == '':
            continue
        
        try:
            product = Product.query.filter_by(name=nom, product_type='finished').first()
            if product:
                product.price = Decimal(str(prix))
                updated_count += 1
                logger.info(f"✅ {nom}: {prix} DA")
        except Exception as e:
            logger.error(f"❌ Erreur pour {nom}: {e}")
    
    db.session.commit()
    logger.info(f"📊 {updated_count} prix de produits mis à jour")

def update_recipe_yields(data):
    """Met à jour les rendements des recettes"""
    logger.info("📏 Mise à jour des rendements des recettes")
    
    updated_count = 0
    
    for _, row in data['recipes'].iterrows():
        nom = row['nom_recette']
        rendement = row['rendement']
        
        if pd.isna(rendement) or rendement == '':
            continue
        
        try:
            recipe = Recipe.query.filter_by(name=nom).first()
            if recipe:
                recipe.yield_quantity = parse_yield_quantity(rendement)
                recipe.yield_unit = row['unite_rendement'] if pd.notna(row['unite_rendement']) else 'pièce'
                updated_count += 1
                logger.info(f"✅ {nom}: {recipe.yield_quantity} {recipe.yield_unit}")
        except Exception as e:
            logger.error(f"❌ Erreur pour {nom}: {e}")
    
    db.session.commit()
    logger.info(f"📊 {updated_count} rendements de recettes mis à jour")

def update_recipe_ingredients(data):
    """Met à jour les ingrédients des recettes"""
    logger.info("🥘 Mise à jour des ingrédients des recettes")
    
    # Supprimer tous les ingrédients de recettes existants
    RecipeIngredient.query.delete()
    db.session.commit()
    logger.info("🗑️  Anciens ingrédients de recettes supprimés")
    
    # Grouper par recette
    ingredients_by_recipe = data['ingredients_recipe'].groupby('nom_recette')
    
    added_count = 0
    
    for recipe_name, ingredients_group in ingredients_by_recipe:
        try:
            # Trouver la recette
            recipe = Recipe.query.filter_by(name=recipe_name).first()
            if not recipe:
                logger.warning(f"⚠️  Recette non trouvée: {recipe_name}")
                continue
            
            # Ajouter les ingrédients
            for _, ing_row in ingredients_group.iterrows():
                ingredient_name = ing_row['nom_ingredient']
                quantite = ing_row['quantite']
                unite = ing_row['unite'] if pd.notna(ing_row['unite']) else 'g'
                notes = ing_row['notes'] if pd.notna(ing_row['notes']) else None
                
                if pd.isna(quantite) or quantite == '':
                    continue
                
                # Trouver l'ingrédient
                ingredient = Product.query.filter_by(name=ingredient_name, product_type='ingredient').first()
                if not ingredient:
                    logger.warning(f"⚠️  Ingrédient non trouvé: {ingredient_name}")
                    continue
                
                # Créer l'ingrédient de recette
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    product_id=ingredient.id,
                    quantity_needed=Decimal(str(quantite)),
                    unit=unite,
                    notes=notes
                )
                
                db.session.add(recipe_ingredient)
                added_count += 1
                
        except Exception as e:
            logger.error(f"❌ Erreur pour la recette {recipe_name}: {e}")
    
    db.session.commit()
    logger.info(f"📊 {added_count} ingrédients de recettes ajoutés")

def main():
    """Fonction principale"""
    app = create_app()
    
    with app.app_context():
        logger.info("🚀 Début de l'injection du gabarit parfait")
        
        # Charger les données
        data = load_gabarit_data()
        if not data:
            logger.error("❌ Impossible de charger les données")
            return
        
        # Mettre à jour les prix des ingrédients
        update_ingredient_prices(data)
        
        # Mettre à jour les prix des produits
        update_product_prices(data)
        
        # Mettre à jour les rendements des recettes
        update_recipe_yields(data)
        
        # Mettre à jour les ingrédients des recettes
        update_recipe_ingredients(data)
        
        # Vérification finale
        logger.info("\n🔍 Vérification finale:")
        recipes_with_ingredients = [r for r in Recipe.query.all() if RecipeIngredient.query.filter_by(recipe_id=r.id).count() > 0]
        logger.info(f"  - Recettes avec ingrédients: {len(recipes_with_ingredients)}")
        
        total_ingredients = RecipeIngredient.query.count()
        logger.info(f"  - Total ingrédients de recettes: {total_ingredients}")
        
        logger.info("✅ Injection terminée avec succès !")

if __name__ == "__main__":
    main() 