#!/usr/bin/env python3
"""
Script d'injection des données du gabarit Excel dans l'ERP Fée Maison
Utilise les modèles existants pour créer les produits, ingrédients et recettes
"""

import pandas as pd
from decimal import Decimal
from app import create_app, db
from models import User, Category, Product, Unit, Recipe, RecipeIngredient
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_gabarit_data():
    """Charge les données du fichier gabarit Excel"""
    try:
        # Charger les 4 feuilles du gabarit
        produits_finis = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Produits_Finis')
        recettes = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Recettes')
        ingredients = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Ingrédients')
        ingredients_recette = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Ingrédients_Recette')
        
        # Traiter les en-têtes (première ligne = en-têtes)
        produits_finis.columns = produits_finis.iloc[0]
        produits_finis = produits_finis.iloc[1:].reset_index(drop=True)
        
        recettes.columns = recettes.iloc[0]
        recettes = recettes.iloc[1:].reset_index(drop=True)
        
        ingredients.columns = ingredients.iloc[0]
        ingredients = ingredients.iloc[1:].reset_index(drop=True)
        
        ingredients_recette.columns = ingredients_recette.iloc[0]
        ingredients_recette = ingredients_recette.iloc[1:].reset_index(drop=True)
        
        return {
            'produits_finis': produits_finis,
            'recettes': recettes,
            'ingredients': ingredients,
            'ingredients_recette': ingredients_recette
        }
    except Exception as e:
        logger.error(f"Erreur lors du chargement du gabarit: {e}")
        return None

def create_or_get_category(category_name):
    """Crée ou récupère une catégorie"""
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()
        logger.info(f"Catégorie créée: {category_name}")
    return category

def create_or_get_unit(unit_name):
    """Crée ou récupère une unité"""
    unit = Unit.query.filter_by(name=unit_name).first()
    if not unit:
        # Déterminer le type d'unité et le facteur de conversion
        if unit_name.lower() in ['g', 'gramme', 'grammes']:
            base_unit = 'g'
            conversion_factor = 1
            unit_type = 'weight'
        elif unit_name.lower() in ['ml', 'millilitre', 'millilitres']:
            base_unit = 'ml'
            conversion_factor = 1
            unit_type = 'volume'
        elif unit_name.lower() in ['pièce', 'pièces', 'pc']:
            base_unit = 'pièce'
            conversion_factor = 1
            unit_type = 'piece'
        else:
            # Par défaut
            base_unit = unit_name
            conversion_factor = 1
            unit_type = 'other'
        
        unit = Unit(
            name=unit_name,
            base_unit=base_unit,
            conversion_factor=conversion_factor,
            unit_type=unit_type
        )
        db.session.add(unit)
        db.session.commit()
        logger.info(f"Unité créée: {unit_name}")
    return unit

def inject_ingredients(data):
    """Injecte les ingrédients dans la base de données"""
    logger.info("=== INJECTION DES INGRÉDIENTS ===")
    
    ingredients_created = []
    
    for _, row in data['ingredients'].iterrows():
        try:
            nom = row['nom']
            prix = Decimal(str(row['prix'])) if pd.notna(row['prix']) else Decimal('0')
            unite = row['unite'] if pd.notna(row['unite']) else 'g'
            
            # Vérifier si l'ingrédient existe déjà
            existing = Product.query.filter_by(name=nom, product_type='ingredient').first()
            if existing:
                logger.info(f"Ingrédient existant ignoré: {nom}")
                ingredients_created.append(existing)
                continue
            
            # Créer l'unité si nécessaire
            unit_obj = create_or_get_unit(unite)
            
            # Créer l'ingrédient
            ingredient = Product(
                name=nom,
                product_type='ingredient',
                cost_price=prix,
                unit=unite,
                description=f"Ingrédient: {nom}"
            )
            
            db.session.add(ingredient)
            ingredients_created.append(ingredient)
            logger.info(f"Ingrédient créé: {nom} - {prix} DA/{unite}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'ingrédient {row.get('nom', 'N/A')}: {e}")
    
    db.session.commit()
    logger.info(f"Total ingrédients créés: {len(ingredients_created)}")
    return ingredients_created

def inject_finished_products(data):
    """Injecte les produits finis dans la base de données"""
    logger.info("=== INJECTION DES PRODUITS FINIS ===")
    
    products_created = []
    
    for _, row in data['produits_finis'].iterrows():
        try:
            nom = row['nom_produit']
            categorie = row['catégorie'] if pd.notna(row['catégorie']) else 'Produits Finis'
            prix = Decimal(str(row['prix'])) if pd.notna(row['prix']) else Decimal('0')
            unite = row['unite'] if pd.notna(row['unite']) else 'pièce'
            description = row['description'] if pd.notna(row['description']) else f"Produit fini: {nom}"
            
            # Vérifier si le produit existe déjà
            existing = Product.query.filter_by(name=nom, product_type='finished').first()
            if existing:
                logger.info(f"Produit fini existant ignoré: {nom}")
                products_created.append(existing)
                continue
            
            # Créer la catégorie si nécessaire
            category_obj = create_or_get_category(categorie)
            
            # Créer l'unité si nécessaire
            unit_obj = create_or_get_unit(unite)
            
            # Créer le produit fini
            product = Product(
                name=nom,
                product_type='finished',
                price=prix,
                unit=unite,
                description=description,
                category=category_obj
            )
            
            db.session.add(product)
            products_created.append(product)
            logger.info(f"Produit fini créé: {nom} - {prix} DA/{unite}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du produit fini {row.get('nom_produit', 'N/A')}: {e}")
    
    db.session.commit()
    logger.info(f"Total produits finis créés: {len(products_created)}")
    return products_created

def inject_recipes(data):
    """Injecte les recettes dans la base de données"""
    logger.info("=== INJECTION DES RECETTES ===")
    
    recipes_created = []
    
    # Grouper les ingrédients par recette
    ingredients_by_recipe = data['ingredients_recette'].groupby('nom_recette')
    
    for recipe_name, ingredients_group in ingredients_by_recipe:
        try:
            # Trouver le produit fini correspondant
            finished_product = Product.query.filter_by(name=recipe_name, product_type='finished').first()
            if not finished_product:
                logger.warning(f"Produit fini non trouvé pour la recette: {recipe_name}")
                continue
            
            # Vérifier si la recette existe déjà
            existing_recipe = Recipe.query.filter_by(name=recipe_name).first()
            if existing_recipe:
                logger.info(f"Recette existante ignorée: {recipe_name}")
                recipes_created.append(existing_recipe)
                continue
            
            # Créer la recette
            recipe = Recipe(
                name=recipe_name,
                product_id=finished_product.id,
                yield_quantity=1,
                yield_unit='pièce',
                production_location='ingredients_magasin',
                description=f"Recette pour {recipe_name}"
            )
            
            db.session.add(recipe)
            db.session.flush()  # Pour obtenir l'ID de la recette
            
            # Ajouter les ingrédients de la recette
            for _, ing_row in ingredients_group.iterrows():
                try:
                    ingredient_name = ing_row['nom_ingredient']
                    quantite = Decimal(str(ing_row['quantite'])) if pd.notna(ing_row['quantite']) else Decimal('0')
                    unite = ing_row['unite'] if pd.notna(ing_row['unite']) else 'g'
                    notes = ing_row['notes'] if pd.notna(ing_row['notes']) else None
                    
                    # Trouver l'ingrédient dans la base
                    ingredient_product = Product.query.filter_by(name=ingredient_name, product_type='ingredient').first()
                    if not ingredient_product:
                        logger.warning(f"Ingrédient non trouvé: {ingredient_name}")
                        continue
                    
                    # Créer l'ingrédient de recette
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=ingredient_product.id,
                        quantity_needed=quantite,
                        unit=unite,
                        notes=notes
                    )
                    
                    db.session.add(recipe_ingredient)
                    logger.info(f"  - Ingrédient ajouté: {ingredient_name} - {quantite} {unite}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'ingrédient {ing_row.get('nom_ingredient', 'N/A')}: {e}")
            
            recipes_created.append(recipe)
            logger.info(f"Recette créée: {recipe_name} avec {len(ingredients_group)} ingrédients")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la recette {recipe_name}: {e}")
    
    db.session.commit()
    logger.info(f"Total recettes créées: {len(recipes_created)}")
    return recipes_created

def main():
    """Fonction principale d'injection"""
    app = create_app()
    
    with app.app_context():
        logger.info("🚀 Début de l'injection des données du gabarit")
        
        # Charger les données du gabarit
        data = load_gabarit_data()
        if not data:
            logger.error("Impossible de charger les données du gabarit")
            return
        
        logger.info("✅ Données du gabarit chargées avec succès")
        
        # Injecter les données dans l'ordre
        try:
            # 1. Ingrédients (doivent être créés en premier)
            ingredients = inject_ingredients(data)
            
            # 2. Produits finis
            products = inject_finished_products(data)
            
            # 3. Recettes (dépendent des produits et ingrédients)
            recipes = inject_recipes(data)
            
            logger.info("🎉 Injection terminée avec succès !")
            logger.info(f"📊 Résumé:")
            logger.info(f"   - Ingrédients: {len(ingredients)}")
            logger.info(f"   - Produits finis: {len(products)}")
            logger.info(f"   - Recettes: {len(recipes)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'injection: {e}")
            db.session.rollback()

if __name__ == '__main__':
    main() 