# 📋 Guide des Gabarits et Scripts d'Injection ERP

## 🎯 Objectif
Ce guide explique comment utiliser les gabarits Excel et scripts d'injection pour gérer les recettes et ingrédients dans l'ERP Fée Maison.

## 📁 Fichiers Créés

### 1. Gabarits Excel

#### `Gabarit_Vide_Correct.xlsx`
- **Usage** : Gabarit vide avec les noms exacts de la base de données
- **Contenu** :
  - 134 ingrédients (noms exacts de la DB)
  - 101 produits finis
  - 7 catégories
  - 32 unités
- **Avantage** : Évite les erreurs de correspondance de noms

#### `Gabarit_Consolide.xlsx`
- **Usage** : Gabarit avec ingrédients similaires fusionnés
- **Contenu** :
  - 134 ingrédients consolidés (avec prix moyens pondérés)
  - 101 produits finis
- **Avantage** : Prix optimisés pour les ingrédients similaires

### 2. Scripts Python

#### `create_gabarit_vide.py`
```bash
python3 create_gabarit_vide.py
```
- Crée le gabarit vide avec les noms exacts de la DB
- Génère `Gabarit_Vide_Correct.xlsx`

#### `consolidate_ingredients.py`
```bash
python3 consolidate_ingredients.py
```
- Analyse et consolide les ingrédients similaires
- Calcule les prix moyens pondérés
- Crée `Gabarit_Consolide.xlsx`

#### `inject_gabarit_parfait.py`
```bash
python3 inject_gabarit_parfait.py
```
- Injection depuis `Gabarit_Vide_Correct.xlsx`
- Utilise les noms exacts de la DB

#### `inject_gabarit_consolide.py`
```bash
python3 inject_gabarit_consolide.py
```
- Injection depuis `Gabarit_Consolide.xlsx`
- Utilise les ingrédients consolidés

#### `cleanup_purchase_items.py`
```bash
python3 cleanup_purchase_items.py
```
- Nettoie les références orphelines après consolidation

## 🔄 Workflow Recommandé

### Option 1 : Gabarit Vide (Recommandé pour nouveaux projets)
1. **Créer le gabarit** :
   ```bash
   python3 create_gabarit_vide.py
   ```

2. **Remplir le gabarit** :
   - Ouvrir `Gabarit_Vide_Correct.xlsx`
   - Remplir les prix dans les feuilles "Ingrédients" et "Produits_Finis"
   - Remplir les recettes dans "Recettes" et "Ingrédients_Recette"

3. **Injecter les données** :
   ```bash
   python3 inject_gabarit_parfait.py
   ```

### Option 2 : Gabarit Consolidé (Recommandé pour optimisation)
1. **Consolider les ingrédients** :
   ```bash
   python3 consolidate_ingredients.py
   ```

2. **Nettoyer les références** (si nécessaire) :
   ```bash
   python3 cleanup_purchase_items.py
   ```

3. **Remplir le gabarit consolidé** :
   - Ouvrir `Gabarit_Consolide.xlsx`
   - Les prix des ingrédients similaires sont déjà optimisés
   - Remplir les recettes

4. **Injecter les données** :
   ```bash
   python3 inject_gabarit_consolide.py
   ```

## 📊 Consolidation des Ingrédients Similaires

Le script de consolidation a identifié et fusionné ces groupes :

| Groupe | Ingrédients | Prix Moyen Pondéré |
|--------|-------------|-------------------|
| **Sel** | Sel + sel 1kg | 0.05 DA |
| **Semoule Moula moyenne** | 10kg + 2kg | 0.07 DA |
| **Tomate conserve** | 1kg + Tomate Conserve | 2.33 DA |
| **Margarine Fleurial** | 500g + 250g | 0.37 DA |

### Calcul du Prix Moyen Pondéré
```
Prix = (Prix1 × Poids1 + Prix2 × Poids2) / (Poids1 + Poids2)
```

## 🎯 Fonctionnalités des Scripts

### Parsing des Rendements
- Gère les plages : `"100-110"` → `105`
- Gère les nombres simples : `"50"` → `50`
- Valeur par défaut : `1` si invalide

### Gestion des Erreurs
- Logging détaillé de toutes les opérations
- Gestion des ingrédients manquants
- Gestion des recettes manquantes
- Validation des données

### Sécurité
- Sauvegarde automatique des modifications
- Vérification des contraintes de base de données
- Nettoyage des références orphelines

## 📋 Structure des Feuilles Excel

### Feuille "Ingrédients"
| Colonne | Description | Exemple |
|---------|-------------|---------|
| `nom_ingredient` | Nom exact de l'ingrédient | "Farine" |
| `prix_achat` | Prix d'achat en DA | "0.85" |
| `unite` | Unité de mesure | "kg" |
| `description` | Description optionnelle | "Farine de blé" |
| `categorie` | Catégorie | "Farines" |

### Feuille "Produits_Finis"
| Colonne | Description | Exemple |
|---------|-------------|---------|
| `nom_produit` | Nom du produit fini | "Pain" |
| `prix_vente` | Prix de vente en DA | "15.00" |
| `unite` | Unité de vente | "pièce" |
| `categorie` | Catégorie | "Pains" |

### Feuille "Recettes"
| Colonne | Description | Exemple |
|---------|-------------|---------|
| `nom_recette` | Nom de la recette | "Pain" |
| `rendement` | Quantité produite | "10" ou "8-12" |
| `unite_rendement` | Unité du rendement | "pièce" |
| `temps_preparation` | Temps en minutes | "30" |
| `temps_cuisson` | Temps en minutes | "45" |

### Feuille "Ingrédients_Recette"
| Colonne | Description | Exemple |
|---------|-------------|---------|
| `nom_recette` | Nom de la recette | "Pain" |
| `nom_ingredient` | Nom de l'ingrédient | "Farine" |
| `quantite` | Quantité nécessaire | "1000" |
| `unite` | Unité de mesure | "g" |
| `notes` | Notes optionnelles | "Tamiser" |

## ⚠️ Points d'Attention

1. **Noms exacts** : Utilisez toujours les noms exacts de la base de données
2. **Prix en DA** : Tous les prix doivent être en Dinars Algériens
3. **Quantités** : Utilisez des nombres décimaux (ex: 1000.5)
4. **Rendements** : Peuvent être des plages (ex: "8-12") ou des nombres simples
5. **Sauvegarde** : Faites une sauvegarde avant injection

## 🔧 Dépannage

### Erreur "Ingrédient non trouvé"
- Vérifiez que le nom correspond exactement à celui de la DB
- Utilisez le gabarit vide pour voir les noms exacts

### Erreur "Recette non trouvée"
- Vérifiez que le nom de la recette correspond au produit fini
- Assurez-vous que le produit fini existe dans la DB

### Erreur de prix
- Vérifiez que les prix sont des nombres valides
- Évitez les caractères spéciaux dans les prix

## 📞 Support

Pour toute question ou problème :
1. Vérifiez les logs du script
2. Consultez ce guide
3. Contactez l'équipe technique 