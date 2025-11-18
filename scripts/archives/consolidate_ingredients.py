#!/usr/bin/env python3
"""
Script pour consolider les ingrédients similaires avec un prix moyen pondéré
"""

import pandas as pd
from decimal import Decimal
from app import create_app, db
from models import Product, RecipeIngredient
import logging
import re
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_name(name):
    """Normalise un nom pour la comparaison"""
    if not name:
        return ""
    # Supprimer les caractères spéciaux et mettre en minuscules
    normalized = re.sub(r'[^\w\s]', '', str(name).lower().strip())
    # Supprimer les quantités (kg, g, ml, etc.)
    normalized = re.sub(r'\d+\s*(kg|g|ml|l|pieces?|pc)', '', normalized)
    return normalized.strip()

def find_similar_ingredients():
    """Trouve les ingrédients similaires"""
    app = create_app()
    
    with app.app_context():
        ingredients = Product.query.filter_by(product_type='ingredient').all()
        
        # Grouper par nom normalisé
        groups = defaultdict(list)
        for ing in ingredients:
            normalized = normalize_name(ing.name)
            groups[normalized].append(ing)
        
        # Filtrer les groupes avec plus d'un ingrédient
        similar_groups = {k: v for k, v in groups.items() if len(v) > 1}
        
        logger.info(f"🔍 Analyse des ingrédients similaires:")
        logger.info(f"  - Total ingrédients: {len(ingredients)}")
        logger.info(f"  - Groupes similaires trouvés: {len(similar_groups)}")
        
        for normalized_name, group in similar_groups.items():
            logger.info(f"\n📦 Groupe: '{normalized_name}'")
            for ing in group:
                logger.info(f"  - {ing.name}: {ing.cost_price} DA")
        
        return similar_groups

def calculate_weighted_average_price(group):
    """Calcule le prix moyen pondéré d'un groupe d'ingrédients"""
    total_weight = 0
    total_value = Decimal('0')
    
    for ing in group:
        # Extraire le poids/volume du nom
        weight = extract_weight_from_name(ing.name)
        if weight > 0:
            total_weight += weight
            total_value += ing.cost_price * Decimal(str(weight))
    
    if total_weight > 0:
        return total_value / Decimal(str(total_weight))
    else:
        # Si pas de poids, faire une moyenne simple
        prices = [ing.cost_price for ing in group if ing.cost_price > 0]
        return sum(prices) / len(prices) if prices else Decimal('0')

def extract_weight_from_name(name):
    """Extrait le poids/volume du nom d'un ingrédient"""
    # Patterns pour extraire les quantités
    patterns = [
        r'(\d+(?:\.\d+)?)\s*kg',  # 25kg, 1.5kg
        r'(\d+(?:\.\d+)?)\s*g',   # 500g, 1.5g
        r'(\d+(?:\.\d+)?)\s*ml',  # 1000ml
        r'(\d+(?:\.\d+)?)\s*l',   # 1.5l
        r'(\d+(?:\.\d+)?)\s*pieces?',  # 100 pieces
        r'(\d+(?:\.\d+)?)\s*pc',  # 100 pc
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name.lower())
        if match:
            return float(match.group(1))
    
    return 1  # Par défaut, poids de 1

def consolidate_ingredients():
    """Consolide les ingrédients similaires"""
    app = create_app()
    
    with app.app_context():
        similar_groups = find_similar_ingredients()
        
        if not similar_groups:
            logger.info("✅ Aucun groupe d'ingrédients similaires trouvé")
            return
        
        consolidated_count = 0
        
        for normalized_name, group in similar_groups.items():
            logger.info(f"\n🔧 Consolidation du groupe: '{normalized_name}'")
            
            # Calculer le prix moyen pondéré
            avg_price = calculate_weighted_average_price(group)
            logger.info(f"  Prix moyen pondéré: {avg_price:.2f} DA")
            
            # Choisir l'ingrédient principal (le premier du groupe)
            main_ingredient = group[0]
            other_ingredients = group[1:]
            
            logger.info(f"  Ingrédient principal: {main_ingredient.name}")
            
            # Mettre à jour le prix de l'ingrédient principal
            main_ingredient.cost_price = avg_price
            logger.info(f"  ✅ Prix mis à jour: {main_ingredient.name} -> {avg_price:.2f} DA")
            
            # Remplacer les références dans les recettes
            for other_ing in other_ingredients:
                # Trouver toutes les recettes qui utilisent cet ingrédient
                recipe_ingredients = RecipeIngredient.query.filter_by(product_id=other_ing.id).all()
                
                for ri in recipe_ingredients:
                    # Vérifier si la recette utilise déjà l'ingrédient principal
                    existing = RecipeIngredient.query.filter_by(
                        recipe_id=ri.recipe_id,
                        product_id=main_ingredient.id
                    ).first()
                    
                    if existing:
                        # Si l'ingrédient principal est déjà utilisé, supprimer l'autre
                        db.session.delete(ri)
                        logger.info(f"    🗑️  Supprimé doublon dans recette {ri.recipe_id}")
                    else:
                        # Sinon, remplacer par l'ingrédient principal
                        ri.product_id = main_ingredient.id
                        logger.info(f"    🔄 Remplacé par {main_ingredient.name} dans recette {ri.recipe_id}")
                
                # Supprimer l'ingrédient en double
                db.session.delete(other_ing)
                logger.info(f"  🗑️  Supprimé: {other_ing.name}")
            
            consolidated_count += 1
        
        # Sauvegarder les modifications
        db.session.commit()
        
        logger.info(f"\n📊 Résumé de la consolidation:")
        logger.info(f"  - Groupes consolidés: {consolidated_count}")
        
        # Vérification finale
        final_ingredients = Product.query.filter_by(product_type='ingredient').all()
        logger.info(f"  - Ingrédients restants: {len(final_ingredients)}")
        
        # Afficher quelques exemples d'ingrédients consolidés
        logger.info(f"\n📋 Exemples d'ingrédients consolidés:")
        for ing in final_ingredients[:10]:
            logger.info(f"  - {ing.name}: {ing.cost_price} DA")

def create_consolidated_gabarit():
    """Crée un gabarit avec les ingrédients consolidés"""
    app = create_app()
    
    with app.app_context():
        # Récupérer les données consolidées
        ingredients = Product.query.filter_by(product_type='ingredient').all()
        finished_products = Product.query.filter_by(product_type='finished').all()
        
        # Créer les feuilles du gabarit
        
        # 1. Feuille Ingrédients consolidés
        ingredients_data = []
        for ing in ingredients:
            ingredients_data.append({
                'nom_ingredient': ing.name,
                'prix_achat': ing.cost_price,
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
                'prix_vente': prod.price,
                'unite': prod.unit,
                'description': prod.description or ''
            })
        
        df_products = pd.DataFrame(products_data)
        
        # 3. Feuille Recettes (vide pour remplir)
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
        
        # Créer le fichier Excel
        with pd.ExcelWriter('Gabarit_Consolide.xlsx', engine='openpyxl') as writer:
            df_ingredients.to_excel(writer, sheet_name='Ingrédients', index=False)
            df_products.to_excel(writer, sheet_name='Produits_Finis', index=False)
            df_recipes.to_excel(writer, sheet_name='Recettes', index=False)
            df_ingredients_recipe.to_excel(writer, sheet_name='Ingrédients_Recette', index=False)
        
        logger.info("✅ Gabarit consolidé créé: Gabarit_Consolide.xlsx")
        logger.info(f"📊 Contenu:")
        logger.info(f"  - {len(ingredients)} ingrédients consolidés")
        logger.info(f"  - {len(finished_products)} produits finis")

def main():
    """Fonction principale"""
    logger.info("🚀 Début de la consolidation des ingrédients")
    
    # Consolider les ingrédients
    consolidate_ingredients()
    
    # Créer le gabarit consolidé
    create_consolidated_gabarit()
    
    logger.info("✅ Consolidation terminée !")

if __name__ == "__main__":
    main() 