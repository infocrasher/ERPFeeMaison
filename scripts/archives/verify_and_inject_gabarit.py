#!/usr/bin/env python3
"""
Script de vérification et d'injection sécurisée des données du gabarit Excel
Analyse les données existantes et évite les conflits
"""

import pandas as pd
from decimal import Decimal
from app import create_app, db
from models import User, Category, Product, Unit, Recipe, RecipeIngredient
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_existing_data():
    """Analyse les données existantes dans la base"""
    logger.info("=== ANALYSE DES DONNÉES EXISTANTES ===")
    
    # Compter les données existantes
    products_count = Product.query.count()
    categories_count = Category.query.count()
    recipes_count = Recipe.query.count()
    ingredients_count = RecipeIngredient.query.count()
    
    logger.info(f"📊 Données existantes:")
    logger.info(f"   - Produits: {products_count}")
    logger.info(f"   - Catégories: {categories_count}")
    logger.info(f"   - Recettes: {recipes_count}")
    logger.info(f"   - Ingrédients de recettes: {ingredients_count}")
    
    # Analyser les produits existants
    existing_products = Product.query.all()
    existing_names = {p.name: p for p in existing_products}
    
    logger.info(f"\n📋 Produits existants:")
    for product in existing_products:
        logger.info(f"   - {product.name} ({product.product_type}) - Prix: {product.price or product.cost_price} DA")
    
    return {
        'products_count': products_count,
        'categories_count': categories_count,
        'recipes_count': recipes_count,
        'ingredients_count': ingredients_count,
        'existing_products': existing_names
    }

def load_gabarit_data():
    """Charge les données du fichier gabarit Excel"""
    try:
        logger.info("=== CHARGEMENT DU GABARIT ===")
        
        # Charger les 4 feuilles du gabarit
        produits_finis = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Produits_Finis')
        recettes = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Recettes')
        ingredients = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Ingrédients')
        ingredients_recette = pd.read_excel('Gabarit_Rempli_Complet.xlsx', sheet_name='Ingrédients_Recette')
        
        # Les colonnes sont déjà correctes, pas besoin de traiter les en-têtes
        
        logger.info(f"✅ Gabarit chargé:")
        logger.info(f"   - Produits finis: {len(produits_finis)}")
        logger.info(f"   - Recettes: {len(recettes)}")
        logger.info(f"   - Ingrédients: {len(ingredients)}")
        logger.info(f"   - Lignes de recettes: {len(ingredients_recette)}")
        
        return {
            'produits_finis': produits_finis,
            'recettes': recettes,
            'ingredients': ingredients,
            'ingredients_recette': ingredients_recette
        }
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du gabarit: {e}")
        return None

def analyze_conflicts(existing_data, gabarit_data):
    """Analyse les conflits potentiels entre données existantes et gabarit"""
    logger.info("=== ANALYSE DES CONFLITS ===")
    
    existing_products = existing_data['existing_products']
    conflicts = {
        'ingredients_to_skip': [],
        'products_to_skip': [],
        'recipes_to_skip': [],
        'new_ingredients': [],
        'new_products': [],
        'new_recipes': []
    }
    
    # Analyser les ingrédients
    for _, row in gabarit_data['ingredients'].iterrows():
        nom = row['nom_ingredient']
        if nom in existing_products:
            existing = existing_products[nom]
            if existing.product_type == 'ingredient':
                conflicts['ingredients_to_skip'].append(nom)
                logger.info(f"⚠️  Ingrédient existant ignoré: {nom}")
            else:
                logger.warning(f"⚠️  Conflit de type: {nom} existe comme {existing.product_type}")
        else:
            conflicts['new_ingredients'].append(nom)
    
    # Analyser les produits finis
    for _, row in gabarit_data['produits_finis'].iterrows():
        nom = row['nom_produit']
        if nom in existing_products:
            existing = existing_products[nom]
            if existing.product_type == 'finished':
                conflicts['products_to_skip'].append(nom)
                logger.info(f"⚠️  Produit fini existant ignoré: {nom}")
            else:
                logger.warning(f"⚠️  Conflit de type: {nom} existe comme {existing.product_type}")
        else:
            conflicts['new_products'].append(nom)
    
    # Analyser les recettes
    for _, row in gabarit_data['recettes'].iterrows():
        nom = row['nom_recette']
        existing_recipe = Recipe.query.filter_by(name=nom).first()
        if existing_recipe:
            conflicts['recipes_to_skip'].append(nom)
            logger.info(f"⚠️  Recette existante ignorée: {nom}")
        else:
            conflicts['new_recipes'].append(nom)
    
    logger.info(f"\n📊 Résumé des conflits:")
    logger.info(f"   - Ingrédients à ignorer: {len(conflicts['ingredients_to_skip'])}")
    logger.info(f"   - Produits finis à ignorer: {len(conflicts['products_to_skip'])}")
    logger.info(f"   - Recettes à ignorer: {len(conflicts['recipes_to_skip'])}")
    logger.info(f"   - Nouveaux ingrédients: {len(conflicts['new_ingredients'])}")
    logger.info(f"   - Nouveaux produits finis: {len(conflicts['new_products'])}")
    logger.info(f"   - Nouvelles recettes: {len(conflicts['new_recipes'])}")
    
    return conflicts

def create_or_get_category(category_name):
    """Crée ou récupère une catégorie"""
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()
        logger.info(f"✅ Catégorie créée: {category_name}")
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
        logger.info(f"✅ Unité créée: {unit_name}")
    return unit

def inject_new_ingredients(data, conflicts):
    """Injecte uniquement les nouveaux ingrédients"""
    logger.info("=== INJECTION DES NOUVEAUX INGRÉDIENTS ===")
    
    ingredients_created = []
    
    for _, row in data['ingredients'].iterrows():
        nom = row['nom_ingredient']
        
        # Ignorer les ingrédients existants
        if nom in conflicts['ingredients_to_skip']:
            continue
        
        try:
            prix = Decimal(str(row['prix_achat'])) if pd.notna(row['prix_achat']) else Decimal('0')
            unite = row['unite'] if pd.notna(row['unite']) else 'g'
            
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
            logger.info(f"✅ Ingrédient créé: {nom} - {prix} DA/{unite}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de l'ingrédient {nom}: {e}")
    
    db.session.commit()
    logger.info(f"📊 Total nouveaux ingrédients créés: {len(ingredients_created)}")
    return ingredients_created

def inject_new_finished_products(data, conflicts):
    """Injecte uniquement les nouveaux produits finis"""
    logger.info("=== INJECTION DES NOUVEAUX PRODUITS FINIS ===")
    
    products_created = []
    
    for _, row in data['produits_finis'].iterrows():
        nom = row['nom_produit']
        
        # Ignorer les produits existants
        if nom in conflicts['products_to_skip']:
            continue
        
        try:
            categorie = row['categorie'] if pd.notna(row['categorie']) else 'Produits Finis'
            prix = Decimal(str(row['prix_vente'])) if pd.notna(row['prix_vente']) else Decimal('0')
            unite = row['unite'] if pd.notna(row['unite']) else 'pièce'
            description = row['description'] if pd.notna(row['description']) else f"Produit fini: {nom}"
            
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
            logger.info(f"✅ Produit fini créé: {nom} - {prix} DA/{unite}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du produit fini {nom}: {e}")
    
    db.session.commit()
    logger.info(f"📊 Total nouveaux produits finis créés: {len(products_created)}")
    return products_created

def parse_yield_quantity(yield_str):
    """Parse le rendement et calcule la moyenne si c'est une plage (ex: 53-60 -> 56.5)"""
    if pd.isna(yield_str):
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

def inject_new_recipes(data, conflicts):
    """Injecte uniquement les nouvelles recettes"""
    logger.info("=== INJECTION DES NOUVELLES RECETTES ===")
    
    recipes_created = []
    
    # Créer un dictionnaire des données de recettes pour accéder facilement aux rendements
    recipes_data = {}
    for _, row in data['recettes'].iterrows():
        recipes_data[row['nom_recette']] = {
            'rendement': parse_yield_quantity(row['rendement']),
            'unite_rendement': row['unite_rendement'] if pd.notna(row['unite_rendement']) else 'pièce',
            'description': row['description'] if pd.notna(row['description']) else '',
            'temps_preparation': row['temps_preparation'] if pd.notna(row['temps_preparation']) else 0,
            'temps_cuisson': row['temps_cuisson'] if pd.notna(row['temps_cuisson']) else 0,
            'niveau_difficulte': row['niveau_difficulte'] if pd.notna(row['niveau_difficulte']) else 'moyen',
            'lieu_production': row['lieu_production'] if pd.notna(row['lieu_production']) else 'ingredients_magasin'
        }
    
    # Grouper les ingrédients par recette
    ingredients_by_recipe = data['ingredients_recette'].groupby('nom_recette')
    
    for recipe_name, ingredients_group in ingredients_by_recipe:
        # Ignorer les recettes existantes
        if recipe_name in conflicts['recipes_to_skip']:
            continue
        
        try:
            # Trouver le produit fini correspondant
            finished_product = Product.query.filter_by(name=recipe_name, product_type='finished').first()
            if not finished_product:
                logger.warning(f"⚠️  Produit fini non trouvé pour la recette: {recipe_name}")
                continue
            
            # Récupérer les données de rendement
            recipe_info = recipes_data.get(recipe_name, {})
            yield_quantity = recipe_info.get('rendement', 1)
            yield_unit = recipe_info.get('unite_rendement', 'pièce')
            description = recipe_info.get('description', f"Recette pour {recipe_name}")
            production_location = recipe_info.get('lieu_production', 'ingredients_magasin')
            
            # Créer la recette avec le vrai rendement
            recipe = Recipe(
                name=recipe_name,
                product_id=finished_product.id,
                yield_quantity=yield_quantity,
                yield_unit=yield_unit,
                production_location=production_location,
                description=description
            )
            
            db.session.add(recipe)
            db.session.flush()  # Pour obtenir l'ID de la recette
            
            # Ajouter les ingrédients de la recette
            ingredients_added = 0
            for _, ing_row in ingredients_group.iterrows():
                try:
                    ingredient_name = ing_row['nom_ingredient']
                    quantite = Decimal(str(ing_row['quantite'])) if pd.notna(ing_row['quantite']) else Decimal('0')
                    unite = ing_row['unite'] if pd.notna(ing_row['unite']) else 'g'
                    notes = ing_row['notes'] if pd.notna(ing_row['notes']) else None
                    
                    # Trouver l'ingrédient dans la base
                    ingredient_product = Product.query.filter_by(name=ingredient_name, product_type='ingredient').first()
                    if not ingredient_product:
                        logger.warning(f"⚠️  Ingrédient non trouvé: {ingredient_name}")
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
                    ingredients_added += 1
                    
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'ajout de l'ingrédient {ing_row.get('nom_ingredient', 'N/A')}: {e}")
            
            recipes_created.append(recipe)
            logger.info(f"✅ Recette créée: {recipe_name} - Rendement: {yield_quantity} {yield_unit} avec {ingredients_added} ingrédients")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la recette {recipe_name}: {e}")
    
    db.session.commit()
    logger.info(f"📊 Total nouvelles recettes créées: {len(recipes_created)}")
    return recipes_created

def main():
    """Fonction principale de vérification et d'injection"""
    app = create_app()
    
    with app.app_context():
        logger.info("🚀 Début de la vérification et injection sécurisée")
        
        # 1. Analyser les données existantes
        existing_data = analyze_existing_data()
        
        # 2. Charger les données du gabarit
        gabarit_data = load_gabarit_data()
        if not gabarit_data:
            logger.error("❌ Impossible de charger les données du gabarit")
            return
        
        # 3. Analyser les conflits
        conflicts = analyze_conflicts(existing_data, gabarit_data)
        
        # 4. Demander confirmation
        total_new = (len(conflicts['new_ingredients']) + 
                    len(conflicts['new_products']) + 
                    len(conflicts['new_recipes']))
        
        if total_new == 0:
            logger.info("ℹ️  Aucune nouvelle donnée à injecter")
            return
        
        logger.info(f"\n⚠️  ATTENTION: {total_new} nouvelles entrées seront créées")
        logger.info("Continuing automatically...")
        
        # 5. Injecter les nouvelles données dans l'ordre
        try:
            # Ingrédients en premier
            new_ingredients = inject_new_ingredients(gabarit_data, conflicts)
            
            # Produits finis ensuite
            new_products = inject_new_finished_products(gabarit_data, conflicts)
            
            # Recettes en dernier
            new_recipes = inject_new_recipes(gabarit_data, conflicts)
            
            logger.info("\n🎉 Injection sécurisée terminée avec succès !")
            logger.info(f"📊 Résumé final:")
            logger.info(f"   - Nouveaux ingrédients: {len(new_ingredients)}")
            logger.info(f"   - Nouveaux produits finis: {len(new_products)}")
            logger.info(f"   - Nouvelles recettes: {len(new_recipes)}")
            logger.info(f"   - Total créé: {len(new_ingredients) + len(new_products) + len(new_recipes)}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'injection: {e}")
            db.session.rollback()
            logger.info("🔄 Rollback effectué")

if __name__ == '__main__':
    main() 