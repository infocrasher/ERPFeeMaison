#!/usr/bin/env python3
"""
Script pour injecter les stocks depuis le fichier Excel Stock V1.xlsx

Usage:
    python scripts/inject_stock_from_excel.py [--dry-run] [--confirm-all]
"""

import sys
import os
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import Product

def analyze_excel_file(file_path):
    """Analyse le fichier Excel et retourne un DataFrame"""
    print(f"📊 Analyse du fichier Excel : {file_path}")
    
    # Lire le fichier Excel avec gestion de l'encodage
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture avec openpyxl: {e}")
        print("   Tentative avec xlrd...")
        try:
            df = pd.read_excel(file_path, engine='xlrd')
        except Exception as e2:
            print(f"❌ Erreur lors de la lecture: {e2}")
            raise
    
    print(f"\n✅ Fichier chargé : {len(df)} lignes")
    print(f"📋 Colonnes : {', '.join(df.columns.tolist())}")
    
    # Vérifier les IDs valides
    valid_ids = df['id'].notna() & (df['id'].astype(str).str.isdigit() | df['id'].apply(lambda x: isinstance(x, (int, float))))
    invalid_ids_count = (~valid_ids).sum()
    if invalid_ids_count > 0:
        print(f"⚠️  {invalid_ids_count} lignes avec ID invalide")
    
    # Afficher les types uniques
    if 'type' in df.columns:
        print(f"\n📦 Types de produits trouvés :")
        for ptype in df['type'].unique():
            count = len(df[df['type'] == ptype])
            print(f"   - {ptype}: {count} produits")
    
    # Afficher quelques exemples de noms (pour vérifier l'encodage)
    if 'nom' in df.columns:
        print(f"\n📝 Exemples de noms (vérification encodage) :")
        for i, name in enumerate(df['nom'].head(5)):
            print(f"   {i+1}. {name}")
    
    return df

def get_stock_field_by_type(product_type, product=None):
    """
    Retourne le nom du champ de stock selon le type de produit
    
    Mapping:
    - consommable -> stock_consommables
    - ingrédient -> stock_ingredients_magasin (par défaut, ou local si recette le demande)
    - produit fini / finished -> stock_comptoir
    
    Si product est fourni, vérifie la recette pour déterminer le stock d'ingrédient
    """
    type_mapping = {
        'consommable': 'stock_consommables',
        'consommables': 'stock_consommables',
        'ingrédient': 'stock_ingredients_magasin',
        'ingredient': 'stock_ingredients_magasin',
        'ingredients': 'stock_ingredients_magasin',
        'produit fini': 'stock_comptoir',
        'finished': 'stock_comptoir',
        'produits finis': 'stock_comptoir',
    }
    
    # Normaliser le type (minuscules, sans accents si possible)
    normalized_type = str(product_type).lower().strip()
    
    # Si c'est un ingrédient et qu'on a le produit, vérifier la recette
    if normalized_type in ['ingrédient', 'ingredient', 'ingredients'] and product:
        # Vérifier si le produit est utilisé dans une recette avec production_location
        from models import Recipe
        recipe_using = Recipe.query.filter(
            Recipe.ingredients.any(product_id=product.id)
        ).first()
        
        if recipe_using and recipe_using.production_location:
            location_map = {
                'ingredients_magasin': 'stock_ingredients_magasin',
                'ingredients_local': 'stock_ingredients_local'
            }
            return location_map.get(recipe_using.production_location, 'stock_ingredients_magasin')
    
    return type_mapping.get(normalized_type, 'stock_ingredients_magasin')  # Par défaut magasin

def inject_stocks(df, dry_run=True, confirm_all=False):
    """
    Injecte les stocks dans la base de données
    
    Args:
        df: DataFrame avec les données Excel
        dry_run: Si True, n'applique pas les modifications (simulation)
        confirm_all: Si True, applique toutes les modifications sans demander confirmation
    """
    app = create_app()
    
    with app.app_context():
        stats = {
            'total': len(df),
            'found': 0,
            'not_found': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        changes_summary = []
        
        print(f"\n{'🔍 MODE SIMULATION' if dry_run else '💾 MODE INJECTION'}")
        print("=" * 60)
        
        for idx, row in df.iterrows():
            try:
                product_id = int(row['id']) if pd.notna(row['id']) else None
            except (ValueError, TypeError) as e:
                stats['errors'].append(f"Ligne {idx + 2}: ID invalide '{row.get('id', 'N/A')}' - {str(e)}")
                continue
                
            # Récupérer le nom (gérer l'encodage UTF-8)
            product_name = None
            if 'nom' in row and pd.notna(row['nom']):
                try:
                    # Essayer de décoder si c'est une chaîne encodée incorrectement
                    name_str = str(row['nom'])
                    # Si ça ressemble à de l'UTF-8 mal décodé (PÃ¢te), essayer de le corriger
                    if 'Ã' in name_str or 'Â' in name_str:
                        try:
                            # Essayer de réencoder en latin-1 puis décoder en UTF-8
                            product_name = name_str.encode('latin-1').decode('utf-8')
                        except:
                            product_name = name_str
                    else:
                        product_name = name_str
                except:
                    product_name = str(row['nom']) if pd.notna(row['nom']) else None
                    
            product_type = row['type'] if 'type' in row and pd.notna(row['type']) else None
            
            # Gérer les valeurs NaN pour nouveau_stock
            if pd.isna(row['nouveau_stock']) or row['nouveau_stock'] == '':
                nouveau_stock = 0.0
            else:
                try:
                    nouveau_stock = float(row['nouveau_stock'])
                except (ValueError, TypeError):
                    nouveau_stock = 0.0
                    print(f"⚠️  ID {product_id}: Valeur de stock invalide '{row['nouveau_stock']}', utilisation de 0.0")
            
            if not product_id:
                stats['errors'].append(f"Ligne {idx + 2}: ID manquant")
                continue
            
            # Trouver le produit par ID (méthode principale - fonctionne même avec encodage incorrect dans le nom)
            product = db.session.get(Product, product_id)
            
            if not product:
                stats['not_found'] += 1
                # Essayer de trouver par nom pour debug (mais l'ID devrait toujours fonctionner)
                if product_name:
                    # Essayer recherche exacte puis recherche partielle
                    product_by_name = Product.query.filter(Product.name == product_name).first()
                    if not product_by_name:
                        product_by_name = Product.query.filter(Product.name.ilike(f'%{product_name[:20]}%')).first()
                    if product_by_name:
                        print(f"⚠️  ID {product_id} ({product_name}): Produit non trouvé par ID, mais trouvé par nom (ID réel: {product_by_name.id})")
                        stats['errors'].append(f"ID {product_id}: Produit non trouvé par ID (ID réel: {product_by_name.id})")
                    else:
                        print(f"❌ ID {product_id} ({product_name}): Produit non trouvé")
                        stats['errors'].append(f"ID {product_id} ({product_name}): Produit non trouvé")
                else:
                    print(f"❌ ID {product_id}: Produit non trouvé (nom manquant)")
                    stats['errors'].append(f"ID {product_id}: Produit non trouvé")
                continue
            
            stats['found'] += 1
            
            # Déterminer le champ de stock à mettre à jour
            stock_field = get_stock_field_by_type(product_type, product)
            current_stock = getattr(product, stock_field, 0.0) or 0.0
            
            # Vérifier que le type Excel correspond au type en base
            if product_type and product.product_type:
                excel_type = str(product_type).lower().strip()
                db_type = str(product.product_type).lower().strip()
                
                # Mapping des types pour comparaison
                type_equivalence = {
                    'consommable': 'consumable',
                    'consommables': 'consumable',
                    'ingrédient': 'ingredient',
                    'ingredient': 'ingredient',
                    'ingredients': 'ingredient',
                    'finished': 'finished',
                    'produit fini': 'finished',
                    'produits finis': 'finished',
                }
                
                excel_type_normalized = type_equivalence.get(excel_type, excel_type)
                
                if excel_type_normalized != db_type:
                    print(f"⚠️  ID {product_id} ({product.name}): Type Excel '{product_type}' ≠ Type DB '{product.product_type}'")
            
            # Vérifier si le stock change vraiment
            if abs(float(current_stock) - nouveau_stock) < 0.001:
                stats['skipped'] += 1
                continue
            
            # Préparer le changement
            change_info = {
                'id': product_id,
                'name': product.name,
                'type': product_type,
                'stock_field': stock_field,
                'current': float(current_stock),
                'new': nouveau_stock,
                'diff': nouveau_stock - float(current_stock)
            }
            changes_summary.append(change_info)
            
            if not dry_run:
                # Appliquer le changement
                try:
                    setattr(product, stock_field, nouveau_stock)
                    product.last_stock_update = datetime.now(timezone.utc)
                    stats['updated'] += 1
                    print(f"✅ ID {product_id} ({product.name}): {stock_field} {current_stock:.2f} → {nouveau_stock:.2f}")
                except Exception as e:
                    stats['errors'].append(f"ID {product_id}: Erreur - {str(e)}")
                    print(f"❌ ID {product_id}: Erreur - {str(e)}")
            else:
                print(f"🔍 ID {product_id} ({product.name}): {stock_field} {current_stock:.2f} → {nouveau_stock:.2f} (simulation)")
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        print(f"Total lignes Excel      : {stats['total']}")
        print(f"Produits trouvés        : {stats['found']}")
        print(f"Produits non trouvés    : {stats['not_found']}")
        print(f"Produits à modifier     : {len(changes_summary)}")
        print(f"Produits ignorés (identique): {stats['skipped']}")
        print(f"Erreurs                 : {len(stats['errors'])}")
        
        if changes_summary:
            print("\n📋 DÉTAIL DES MODIFICATIONS")
            print("=" * 60)
            
            # Grouper par type de stock
            by_stock_field = {}
            for change in changes_summary:
                field = change['stock_field']
                if field not in by_stock_field:
                    by_stock_field[field] = []
                by_stock_field[field].append(change)
            
            for field, changes in by_stock_field.items():
                print(f"\n📍 {field.upper()}: {len(changes)} modifications")
                total_diff = sum(c['diff'] for c in changes)
                print(f"   Variation totale: {total_diff:+.2f}")
                if len(changes) <= 10:
                    for c in changes:
                        print(f"   - {c['name']}: {c['current']:.2f} → {c['new']:.2f} ({c['diff']:+.2f})")
                else:
                    print(f"   (Afficher les 10 premiers sur {len(changes)})")
                    for c in changes[:10]:
                        print(f"   - {c['name']}: {c['current']:.2f} → {c['new']:.2f} ({c['diff']:+.2f})")
        
        if stats['errors']:
            print("\n❌ ERREURS")
            print("=" * 60)
            for error in stats['errors'][:20]:  # Limiter à 20 erreurs
                print(f"   {error}")
            if len(stats['errors']) > 20:
                print(f"   ... et {len(stats['errors']) - 20} autres erreurs")
        
        # Commit si pas en mode dry-run
        if not dry_run:
            if confirm_all or input("\n💾 Confirmer l'injection dans la base de données ? (oui/non): ").lower() == 'oui':
                try:
                    db.session.commit()
                    print("\n✅ Stocks injectés avec succès dans la base de données !")
                except Exception as e:
                    db.session.rollback()
                    print(f"\n❌ Erreur lors du commit : {str(e)}")
                    return False
            else:
                db.session.rollback()
                print("\n⚠️  Injection annulée")
                return False
        
        return True

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Injecter les stocks depuis Excel')
    parser.add_argument('--file', '-f', default='excel_files/Stock V1.xlsx',
                       help='Chemin vers le fichier Excel')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mode simulation (ne modifie pas la base)')
    parser.add_argument('--confirm-all', action='store_true',
                       help='Confirmer toutes les modifications sans demander')
    
    args = parser.parse_args()
    
    # Vérifier que le fichier existe
    if not os.path.exists(args.file):
        print(f"❌ Fichier non trouvé : {args.file}")
        return 1
    
    # Analyser le fichier
    df = analyze_excel_file(args.file)
    
    # Injecter les stocks
    success = inject_stocks(df, dry_run=args.dry_run, confirm_all=args.confirm_all)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

