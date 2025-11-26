#!/usr/bin/env python3
"""
Script d'importation des ingrédients manquants depuis le fichier Excel
ingredients_manquants_vps.xlsx

Structure attendue:
- Nom: Nom du produit
- Prix/Unité: Prix par unité de base
- Unité: Unité de base (g, ml, pièce)
- Catégorie: Nom de la catégorie
- Type: Ingrédients, consomable/Consomable, Produit Fini
- Seuil: Seuil d'alerte (optionnel)

Règles d'importation:
- Ingrédients → seuil_min_ingredients_local
- Consommables → seuil_min_consommables
- Produits finis → seuil_min_comptoir
- can_be_sold et can_be_purchased → laissés à False (à cocher manuellement)
- Si produit existe → ignorer
"""

import pandas as pd
import sys
import os
from decimal import Decimal, InvalidOperation
from app import create_app, db
from models import Product, Category
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_type(type_value):
    """Normalise le type de produit"""
    if pd.isna(type_value):
        return None
    
    type_str = str(type_value).strip()
    type_lower = type_str.lower()
    
    mapping = {
        'ingrédients': 'ingredient',
        'ingredients': 'ingredient',
        'consomable': 'consommable',
        'consommable': 'consommable',
        'produit fini': 'finished',
        'produits finis': 'finished'
    }
    
    return mapping.get(type_lower, None)

def normalize_unit(unit_value):
    """Normalise l'unité"""
    if pd.isna(unit_value):
        return 'g'  # Par défaut
    
    unit_str = str(unit_value).strip().lower()
    
    # Normaliser pièce/Pièce → pièce
    if unit_str in ['pièce', 'piece', 'unité', 'unite']:
        return 'pièce'
    
    # Vérifier que c'est une unité valide
    valid_units = ['g', 'ml', 'pièce']
    if unit_str in valid_units:
        return unit_str
    
    logger.warning(f"Unité non reconnue: {unit_value}, utilisation de 'g' par défaut")
    return 'g'

def create_or_get_category(category_name):
    """Crée ou récupère une catégorie"""
    if pd.isna(category_name):
        return None
    
    category_name = str(category_name).strip()
    category = Category.query.filter_by(name=category_name).first()
    
    if not category:
        category = Category(name=category_name, show_in_pos=True)
        db.session.add(category)
        db.session.flush()  # Pour obtenir l'ID
        logger.info(f"✅ Catégorie créée: {category_name}")
    else:
        logger.debug(f"ℹ️  Catégorie existante: {category_name}")
    
    return category

def import_products_from_excel(excel_file):
    """Importe les produits depuis le fichier Excel"""
    
    logger.info("=" * 60)
    logger.info("IMPORTATION DES INGRÉDIENTS MANQUANTS")
    logger.info("=" * 60)
    
    # Vérifier que le fichier existe
    if not os.path.exists(excel_file):
        logger.error(f"❌ Fichier non trouvé: {excel_file}")
        return False
    
    # Charger le fichier Excel
    try:
        df = pd.read_excel(excel_file)
        logger.info(f"📂 Fichier chargé: {excel_file}")
        logger.info(f"📊 Nombre de lignes: {len(df)}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du fichier: {e}")
        return False
    
    # Vérifier les colonnes requises
    required_columns = ['Nom', 'Prix/Unité', 'Unité', 'Catégorie', 'Type']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"❌ Colonnes manquantes: {missing_columns}")
        return False
    
    # Statistiques
    stats = {
        'total': len(df),
        'created': 0,
        'skipped_existing': 0,
        'errors': 0,
        'by_type': {
            'ingredient': 0,
            'consommable': 0,
            'finished': 0
        }
    }
    
    errors_list = []
    
    # Traiter chaque ligne
    for idx, row in df.iterrows():
        try:
            # Récupérer les données
            nom = str(row['Nom']).strip() if pd.notna(row['Nom']) else None
            if not nom:
                logger.warning(f"Ligne {idx + 2}: Nom vide, ignorée")
                stats['errors'] += 1
                continue
            
            # Normaliser le type
            product_type = normalize_type(row['Type'])
            if not product_type:
                logger.warning(f"Ligne {idx + 2} ({nom}): Type non reconnu '{row['Type']}', ignorée")
                stats['errors'] += 1
                errors_list.append(f"{nom}: Type non reconnu '{row['Type']}'")
                continue
            
            # Vérifier si le produit existe déjà
            existing = Product.query.filter_by(name=nom).first()
            if existing:
                logger.info(f"⏭️  Produit existant ignoré: {nom} ({existing.product_type})")
                stats['skipped_existing'] += 1
                continue
            
            # Normaliser l'unité
            unit = normalize_unit(row['Unité'])
            
            # Récupérer le prix
            try:
                prix = Decimal(str(row['Prix/Unité'])) if pd.notna(row['Prix/Unité']) else Decimal('0')
            except (ValueError, InvalidOperation):
                logger.warning(f"Ligne {idx + 2} ({nom}): Prix invalide '{row['Prix/Unité']}', utilisation de 0")
                prix = Decimal('0')
            
            # Récupérer ou créer la catégorie
            category = create_or_get_category(row['Catégorie'])
            if not category:
                logger.warning(f"Ligne {idx + 2} ({nom}): Catégorie vide, création sans catégorie")
            
            # Récupérer le seuil
            seuil_value = None
            if 'Seuil' in df.columns and pd.notna(row['Seuil']):
                try:
                    seuil_value = float(row['Seuil'])
                    if seuil_value < 0:
                        seuil_value = 0
                except (ValueError, TypeError):
                    seuil_value = None
            
            # Créer le produit
            product = Product(
                name=nom,
                product_type=product_type,
                unit=unit,
                cost_price=prix if product_type in ['ingredient', 'consommable'] else None,
                price=prix if product_type == 'finished' else None,
                category=category,
                can_be_sold=False,  # À cocher manuellement
                can_be_purchased=False,  # À cocher manuellement
                # Seuils selon le type
                seuil_min_ingredients_local=seuil_value if product_type == 'ingredient' else 0,
                seuil_min_consommables=seuil_value if product_type == 'consommable' else 0,
                seuil_min_comptoir=seuil_value if product_type == 'finished' else 0,
                stock_ingredients_local=0.0,
                stock_ingredients_magasin=0.0,
                stock_consommables=0.0,
                stock_comptoir=0.0
            )
            
            db.session.add(product)
            stats['created'] += 1
            stats['by_type'][product_type] += 1
            
            logger.info(f"✅ Produit créé: {nom} ({product_type}) - {prix} DA/{unit}" + 
                       (f" - Seuil: {seuil_value}" if seuil_value else ""))
            
        except Exception as e:
            logger.error(f"❌ Erreur ligne {idx + 2} ({row.get('Nom', 'N/A')}): {e}")
            stats['errors'] += 1
            errors_list.append(f"{row.get('Nom', 'N/A')}: {str(e)}")
            continue
    
    # Commit des changements
    try:
        db.session.commit()
        logger.info("💾 Changements sauvegardés dans la base de données")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erreur lors du commit: {e}")
        return False
    
    # Rapport final
    logger.info("=" * 60)
    logger.info("RAPPORT D'IMPORTATION")
    logger.info("=" * 60)
    logger.info(f"📊 Total lignes traitées: {stats['total']}")
    logger.info(f"✅ Produits créés: {stats['created']}")
    logger.info(f"⏭️  Produits existants ignorés: {stats['skipped_existing']}")
    logger.info(f"❌ Erreurs: {stats['errors']}")
    logger.info("")
    logger.info("Répartition par type:")
    logger.info(f"  - Ingrédients: {stats['by_type']['ingredient']}")
    logger.info(f"  - Consommables: {stats['by_type']['consommable']}")
    logger.info(f"  - Produits finis: {stats['by_type']['finished']}")
    
    if errors_list:
        logger.info("")
        logger.warning("Erreurs détaillées:")
        for error in errors_list[:10]:  # Limiter à 10 erreurs
            logger.warning(f"  - {error}")
        if len(errors_list) > 10:
            logger.warning(f"  ... et {len(errors_list) - 10} autres erreurs")
    
    logger.info("=" * 60)
    
    return True

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("Usage: python import_ingredients_manquants.py <fichier_excel>")
        print("Exemple: python import_ingredients_manquants.py ingredients_manquants_vps.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    # Créer l'application Flask
    app = create_app()
    
    with app.app_context():
        success = import_products_from_excel(excel_file)
        
        if success:
            print("\n✅ Importation terminée avec succès!")
            sys.exit(0)
        else:
            print("\n❌ Importation échouée. Vérifiez les logs ci-dessus.")
            sys.exit(1)

if __name__ == '__main__':
    main()

