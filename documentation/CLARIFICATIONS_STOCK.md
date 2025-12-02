# Clarifications sur la Gestion de Stock

**Date:** 2025-01-XX  
**Basé sur:** Réponses utilisateur aux questions de l'analyse

---

## ✅ Points Clarifiés

### 1. Consommables - Logique de Décrémentation

**Réponse:** Les consommables ont une logique de décrémentation dans `/admin/consumables/` avec des recettes.

**Vérification Code:**
- ✅ Interface existe : `app/consumables/routes.py` → `/admin/consumables/`
- ✅ Deux systèmes de recettes :
  - **Ancien:** `ConsumableRecipe` (par produit fini individuel)
  - **Nouveau:** `ConsumableCategory` (par catégorie de produit avec plages)
- ✅ Routes disponibles :
  - `/admin/consumables/recipes` - Liste des recettes
  - `/admin/consumables/recipes/create` - Créer une recette

**Conclusion:** Le système de consommables est bien configuré. La décrémentation se fait via :
- `ConsumableRecipe` dans `decrement_ingredients_stock_on_production()` (lignes 669-690)
- `ConsumableCategory` dans `complete_sale()` (lignes 255-271) et `decrement_ingredients_stock_on_production()` (lignes 692-712)

**⚠️ PROBLÈME IDENTIFIÉ:** Dans `change_status_to_ready()`, les consommables ne sont **PAS décrémentés**. C'est le seul endroit où c'est manquant.

---

### 2. Décrémentation des Ingrédients - Bouton "Reçu"

**Réponse:** La décrémentation des ingrédients se fait dans le dashboard shop par le bouton "reçu" qui la déclenche.

**Vérification Code:**
- ✅ Route : `app/orders/status_routes.py` → `change_status_to_ready()` (ligne 17)
- ✅ Appelée depuis : Dashboard shop via bouton "reçu"
- ✅ Logique : Décrémente les ingrédients selon la recette (lignes 45-82)

**Conclusion:** Le flux est correct. Le bouton "reçu" dans le dashboard shop appelle `change_status_to_ready()` qui décrémente les ingrédients.

---

### 3. Produits Finis Achetables

**Réponse:** Il y a des produits finis qu'on peut acheter avec le bouton "Peut être acheté". Laisser ignorer pour l'instant avec juste une alerte que ce produit ne contient pas de recette.

**Vérification Code:**
- ✅ Champ existe : `Product.can_be_purchased` (ligne 153 dans `models.py`)
- ⚠️ Problème actuel : `_increment_shop_stock_with_value()` vérifie `if product_fini and product_fini.recipe_definition:` (ligne 591)
  - Si pas de recette → produit ignoré

**Action Requise:**
- Ajouter une alerte si produit fini sans recette lors de l'incrémentation
- Ne pas bloquer, juste alerter

---

### 4. Calcul de la Valeur avec PMP

**Réponse:** La valeur doit être calculée avec le PMP.

**Vérification Code:**
- ✅ Dans `update_stock_by_location()` : Utilise `self.cost_price` (PMP) pour calculer la valeur (ligne 249)
- ✅ Dans `_increment_shop_stock_with_value()` : Calcule valeur avec `cost_per_unit` de la recette (ligne 597)
- ✅ Dans `_decrement_stock_with_value_on_delivery()` : Utilise PMP (`cost_price`) pour décrémenter valeur (ligne 623)

**Conclusion:** Le système utilise bien le PMP pour calculer les valeurs. ✅

---

### 5. Calcul du PMP - Quantité Totale Achetée

**Réponse:** Il ne divise pas par comptoir normalement qui est un type de stock. Le PMP se calcule en divisant la valeur totale du stock acheté d'un produit par la quantité totale achetée, afin d'obtenir un prix moyen pondéré par unité.

**Vérification Code:**
```python
# Ligne 604-606 dans models.py (_increment_shop_stock_with_value)
new_total_stock_qty = Decimal(str(product_fini.total_stock_all_locations))
if new_total_stock_qty > 0:
    product_fini.cost_price = product_fini.total_stock_value / new_total_stock_qty
```

**Analyse:**
- ✅ Divise par `total_stock_all_locations` (tous emplacements confondus)
- ✅ C'est correct selon votre explication : PMP = valeur totale / quantité totale achetée
- ✅ Le PMP est unique pour le produit, pas par emplacement

**Conclusion:** Le calcul du PMP est correct. Il divise bien par la quantité totale (tous emplacements), pas seulement le comptoir. ✅

---

### 6. Logique Stocks Négatifs - Table Temporaire

**Réponse:** Revoir la logique, on y a travaillé l'autre fois en créant une table temporaire si ma mémoire ne me fait pas défaut (à vérifier).

**Vérification Code:**
- ❌ Pas de table temporaire trouvée dans le code
- ✅ Mais logique de déficit implémentée dans `update_stock_by_location()` :
  - Champs `deficit_stock_ingredients_magasin` (ligne 137)
  - Champs `deficit_stock_ingredients_local` (ligne 138)
  - Champs `deficit_stock_comptoir` (ligne 139)
  - Champs `deficit_stock_consommables` (ligne 140)
  - Champs `value_deficit_total` (ligne 122)

**Logique Actuelle (lignes 264-293):**
- ✅ Autorise stocks négatifs
- ✅ Crée un déficit de valeur lors de consommation à découvert
- ✅ Le déficit est résorbé lors des prochaines entrées

**Conclusion:** La logique de déficit existe dans les colonnes de la table `products`, pas dans une table temporaire. Le système gère bien les stocks négatifs avec déficit de valeur. ✅

---

### 7. Valeur lors des Transferts

**Réponse:** La valeur se transfère quand on fait un transfert.

**Vérification Code:**
```python
# app/stock/routes.py lignes 627-631
# Décrémentation stock source
product.update_stock_by_location(source_stock_key, -quantity)

# Incrémentation stock destination
product.update_stock_by_location(dest_stock_key, quantity)
```

**Analyse:**
- ✅ `update_stock_by_location()` gère automatiquement la valeur (lignes 228-300 dans `models.py`)
- ✅ Lors d'une décrémentation : valeur décrémentée selon PMP
- ✅ Lors d'une incrémentation : valeur incrémentée selon PMP
- ✅ La valeur est donc bien transférée automatiquement

**Conclusion:** La valeur se transfère correctement lors des transferts grâce à `update_stock_by_location()`. ✅

---

### 8. Mapping de Localisation - Explication

**Problème Identifié:** Incohérence dans les clés de localisation utilisées.

**Exemples Trouvés:**

#### A. Dans `change_status_to_ready()` (status_routes.py lignes 53-57)
```python
location_map = {
    "ingredients_magasin": "stock_ingredients_magasin",
    "ingredients_local": "stock_ingredients_local"
}
stock_attr = location_map.get(labo_key, labo_key)
```
- **Input:** `labo_key` = `"ingredients_magasin"` ou `"ingredients_local"` (depuis `recipe.production_location`)
- **Output:** `stock_attr` = `"stock_ingredients_magasin"` ou `"stock_ingredients_local"`

#### B. Dans `decrement_ingredients_stock_on_production()` (models.py lignes 656-660)
```python
location_map = {
    "ingredients_magasin": "stock_ingredients_magasin",
    "ingredients_local": "stock_ingredients_local"
}
stock_attr = location_map.get(labo_key, labo_key)
```
- **Même logique** que A

#### C. Dans `update_stock_by_location()` (models.py lignes 234-238)
```python
location_mappings = {
    'stock_ingredients_magasin': ('stock_ingredients_magasin', 'valeur_stock_ingredients_magasin', 'deficit_stock_ingredients_magasin'),
    'stock_ingredients_local': ('stock_ingredients_local', 'valeur_stock_ingredients_local', 'deficit_stock_ingredients_local'),
    'stock_comptoir': ('stock_comptoir', 'valeur_stock_comptoir', 'deficit_stock_comptoir'),
    'stock_consommables': ('stock_consommables', 'valeur_stock_consommables', 'deficit_stock_consommables')
}
```
- **Input:** Clé complète avec préfixe `stock_` (ex: `"stock_ingredients_magasin"`)
- **Output:** Tuple avec attributs de quantité, valeur, déficit

#### D. Dans `complete_transfer()` (stock/routes.py lignes 611-619)
```python
location_map = {
    'INGREDIENTS_MAGASIN': 'stock_ingredients_magasin',
    'INGREDIENTS_LOCAL': 'stock_ingredients_local',
    'COMPTOIR': 'stock_comptoir',
    'CONSOMMABLES': 'stock_consommables'
}
source_stock_key = location_map.get(transfer.source_location.name, f'stock_{transfer.source_location.value}')
```
- **Input:** Enum `StockLocationType` (ex: `INGREDIENTS_MAGASIN`)
- **Output:** Clé avec préfixe `stock_` (ex: `"stock_ingredients_magasin"`)

#### E. Dans `get_stock_by_location_type()` (models.py lignes 186-193)
```python
location_mapping = {
    'comptoir': self.stock_comptoir,
    'ingredients_local': self.stock_ingredients_local,
    'ingredients_magasin': self.stock_ingredients_magasin,
    'consommables': self.stock_consommables
}
```
- **Input:** Clé SANS préfixe `stock_` (ex: `"ingredients_magasin"`)
- **Output:** Valeur du stock

**Résumé des Formats:**
1. **Format Recette:** `"ingredients_magasin"` ou `"ingredients_local"` (sans préfixe `stock_`)
2. **Format update_stock_by_location:** `"stock_ingredients_magasin"` (avec préfixe `stock_`)
3. **Format Enum:** `INGREDIENTS_MAGASIN` (majuscules, sans préfixe)
4. **Format get_stock_by_location_type:** `"ingredients_magasin"` (sans préfixe)

**Conclusion:** Il y a une conversion nécessaire entre les formats. Le mapping est fait correctement dans chaque fonction, mais il serait mieux d'avoir une fonction utilitaire centralisée.

---

### 9. Incohérences à Citer

Voici les incohérences identifiées dans le code :

#### A. Double Gestion de la Valeur dans `change_status_to_ready()`

**Fichier:** `app/orders/status_routes.py` lignes 73-80

**Problème:**
```python
# Ligne 73 : update_stock_by_location() gère déjà la valeur automatiquement
ingredient_product.update_stock_by_location(stock_attr, -quantity_to_decrement)

# Lignes 74-80 : Mais on fait aussi une gestion manuelle de la valeur
ingredient_product.total_stock_value = float(...) - value_to_decrement
ingredient_product.valeur_stock_ingredients_magasin = float(...) - value_to_decrement
```

**Impact:** Double décrémentation de la valeur → valeurs incorrectes

**Solution:** Supprimer les lignes 74-80, laisser `update_stock_by_location()` gérer la valeur.

---

#### B. Consommables Non Décrémentés dans `change_status_to_ready()`

**Fichier:** `app/orders/status_routes.py` lignes 17-116

**Problème:**
- Les ingrédients sont décrémentés (lignes 45-82)
- Les produits finis sont incrémentés (ligne 85)
- **MAIS** les consommables ne sont **PAS décrémentés**

**Comparaison:**
- ✅ Dans `complete_sale()` : Consommables décrémentés (lignes 255-271)
- ✅ Dans `decrement_ingredients_stock_on_production()` : Consommables décrémentés (lignes 666-712)
- ❌ Dans `change_status_to_ready()` : Consommables **IGNORÉS**

**Solution:** Ajouter la décrémentation des consommables après la ligne 85.

---

#### C. Produits Finis Sans Recette Ignorés

**Fichier:** `models.py` lignes 583-609

**Problème:**
```python
if product_fini and product_fini.recipe_definition:  # Ligne 591
    # Incrémentation...
```

**Impact:** Si un produit fini n'a pas de recette, il n'est jamais incrémenté dans le stock comptoir.

**Solution:** Incrémenter même sans recette, avec alerte si pas de recette.

---

#### D. Incohérence dans le Calcul PMP après Décrémentation

**Fichier:** `app/orders/status_routes.py` lignes 73-80

**Problème:**
- On décrémente manuellement `total_stock_value` et `valeur_stock_ingredients_magasin`
- Mais on ne recalcule **PAS** le PMP après
- Le PMP reste incorrect

**Comparaison:**
- ✅ Dans `app/purchases/routes.py` lignes 226-228 : PMP recalculé après mise à jour
- ❌ Dans `change_status_to_ready()` : PMP non recalculé

**Solution:** Soit laisser `update_stock_by_location()` gérer tout, soit recalculer le PMP après.

---

#### E. Mapping de Localisation Incohérent

**Problème:** Différents formats de clés utilisés selon les fonctions (voir section 8).

**Solution:** Créer une fonction utilitaire centralisée pour le mapping.

---

#### F. Fonction `update_stock_quantity()` vs `update_stock_by_location()`

**Fichier:** `app/stock/models.py` lignes 355-428

**Problème:**
- `update_stock_quantity()` : Empêche stocks négatifs (ligne 394 : `max(0, ...)`)
- `update_stock_by_location()` : Autorise stocks négatifs avec déficit

**Impact:** Comportement différent selon la fonction utilisée.

**Solution:** Harmoniser le comportement.

---

## 📋 Résumé des Actions Requises

### 🔴 Priorité CRITIQUE

1. **Ajouter décrémentation consommables dans `change_status_to_ready()`**
2. **Supprimer double gestion valeur dans `change_status_to_ready()`** (lignes 74-80)

### 🟠 Priorité HAUTE

3. **Gérer produits finis sans recette** (alerte + incrémentation)
4. **Recalculer PMP après décrémentation** ou laisser `update_stock_by_location()` gérer

### 🟡 Priorité MOYENNE

5. **Créer fonction utilitaire pour mapping localisation**
6. **Harmoniser comportement stocks négatifs**

---

**Fin des clarifications**

