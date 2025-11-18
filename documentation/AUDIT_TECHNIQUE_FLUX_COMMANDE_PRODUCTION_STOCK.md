# 🔍 AUDIT TECHNIQUE — FLUX COMMANDE → PRODUCTION → STOCK
## ERP Fée Maison - Rapport Exhaustif

**Date de l'audit :** 2025-01-XX  
**Version du système :** Production  
**Périmètre :** Analyse complète sans modification de code

---

## 📋 TABLE DES MATIÈRES

1. [Résumé Exécutif](#1-résumé-exécutif)
2. [Fonctions et Méthodes de Gestion du Stock](#2-fonctions-et-méthodes-de-gestion-du-stock)
3. [Séquence Logique Complète](#3-séquence-logique-complète)
4. [Relations entre Modèles](#4-relations-entre-modèles)
5. [Routes et Endpoints](#5-routes-et-endpoints)
6. [Gestion des Stocks Insuffisants](#6-gestion-des-stocks-insuffisants)
7. [Carte Fonctionnelle du Flux](#7-carte-fonctionnelle-du-flux)
8. [Points Faibles et Incohérences](#8-points-faibles-et-incohérences)
9. [Opportunités d'Amélioration](#9-opportunités-damélioration)

---

## 1. RÉSUMÉ EXÉCUTIF

### 1.1 Vue d'Ensemble

Le système ERP Fée Maison gère un flux complexe entre **commandes clients**, **ordres de production**, **recettes** et **stocks** répartis sur **4 emplacements** :
- **Stock Comptoir** : Produits finis prêts à la vente
- **Stock Ingredients Local** : Ingrédients pour production locale (Labo B)
- **Stock Ingredients Magasin** : Ingrédients pour production magasin (Labo A)
- **Stock Consommables** : Consommables (emballages, etc.)

### 1.2 Types de Commandes

Le système distingue **3 types de commandes** :

1. **`customer_order`** : Commande client (production nécessaire)
2. **`counter_production_request`** : Ordre de production pour stock comptoir
3. **`in_store`** : Vente directe au comptoir (stock existant)

### 1.3 Flux Principal

```
Création Commande
    ↓
Vérification Stock Ingrédients (si customer_order)
    ↓
Statut: pending → in_production (si stock suffisant)
    ↓
Production (changement statut → ready_at_shop)
    ↓
[DÉCRÉMENTATION] Ingrédients + Consommables
    ↓
[INCRÉMENTATION] Produits Finis (stock_comptoir)
    ↓
Livraison/Vente (statut → delivered/completed)
    ↓
[DÉCRÉMENTATION] Produits Finis (stock_comptoir)
```

---

## 2. FONCTIONS ET MÉTHODES DE GESTION DU STOCK

### 2.1 Méthodes du Modèle `Product`

#### `update_stock_by_location(location_key: str, quantity_change: float) -> bool`
- **Fichier :** `models.py` (lignes 206-242)
- **Description :** Met à jour le stock d'un produit à un emplacement spécifique ET sa valeur
- **Emplacements supportés :**
  - `stock_ingredients_magasin`
  - `stock_ingredients_local`
  - `stock_comptoir`
  - `stock_consommables`
- **Logique :**
  - Calcule `value_change = unit_cost * abs(quantity_change)`
  - Met à jour la quantité : `stock = max(0, current + quantity_change)`
  - Met à jour la valeur : `valeur_stock = max(0, current_valeur + value_change)`
- **Appels :** Partout dans le système (routes, méthodes Order, etc.)

#### `get_stock_by_location(location_key: str) -> float`
- **Fichier :** `models.py` (lignes 203-204)
- **Description :** Récupère le stock d'un produit à un emplacement
- **Appels :** Vérifications de disponibilité

#### `get_stock_by_location_type(location_type: str) -> float`
- **Fichier :** `models.py` (lignes 164-171)
- **Description :** Récupère le stock par type d'emplacement (comptoir, ingredients_local, etc.)

### 2.2 Méthodes du Modèle `Order`

#### `_increment_shop_stock_with_value()`
- **Fichier :** `models.py` (lignes 524-551)
- **Description :** Incrémente le stock comptoir ET sa valeur pour les produits finis
- **Quand appelée :**
  - `mark_as_received_at_shop()` (ligne 506)
  - `change_status_to_ready()` dans `app/orders/status_routes.py` (ligne 85)
- **Logique :**
  1. Pour chaque `OrderItem` :
     - Si produit fini avec recette :
       - Incrémente `stock_comptoir` via `update_stock_by_location()`
       - Calcule valeur : `cost_per_unit * quantity` (depuis `recipe_definition.cost_per_unit`)
       - Incrémente `total_stock_value`
       - Recalcule PMP : `cost_price = total_stock_value / total_stock_all_locations`
- **Impact :** ✅ Stock comptoir + ✅ Valeur stock

#### `_decrement_stock_with_value_on_delivery()`
- **Fichier :** `models.py` (lignes 552-571)
- **Description :** Décrémente le stock comptoir ET sa valeur lors d'une vente
- **Quand appelée :**
  - `mark_as_delivered()` (ligne 513)
- **Logique :**
  1. Pour chaque `OrderItem` :
     - Décrémente `stock_comptoir` via `update_stock_by_location()`
     - Calcule valeur : `PMP_produit_fini * quantity`
     - Décrémente `total_stock_value`
     - **PMP ne change pas** lors d'une sortie
- **Impact :** ✅ Stock comptoir - ✅ Valeur stock -

#### `decrement_ingredients_stock_on_production()`
- **Fichier :** `models.py` (lignes 572-654)
- **Description :** Décrémente le stock des ingrédients ET consommables lors de la production
- **Quand appelée :**
  - `edit_order_status()` dans `app/orders/routes.py` (ligne 335) — passage à `ready_at_shop`
  - **Note :** Cette méthode existe mais n'est **PAS appelée** dans `change_status_to_ready()` (qui utilise une logique inline)
- **Logique :**
  1. **Ingrédients :**
     - Pour chaque `OrderItem` → `Recipe` → `RecipeIngredient` :
       - Calcule `qty_per_unit = quantity_needed / yield_quantity`
       - Calcule `needed_qty = qty_per_unit * order_item.quantity`
       - Décrémente selon `production_location` (magasin ou local)
  2. **Consommables :**
     - **Ancien système :** `ConsumableRecipe` (par produit fini)
     - **Nouveau système :** `ConsumableCategory` (par catégorie de produit)
- **Impact :** ✅ Stock ingrédients - ✅ Stock consommables -

#### `mark_as_in_production()`
- **Fichier :** `models.py` (lignes 497-501)
- **Description :** Change le statut de `pending` à `in_production`
- **Impact sur stock :** ❌ Aucun (pas de décrémentation à ce stade)

#### `mark_as_received_at_shop()`
- **Fichier :** `models.py` (lignes 503-508)
- **Description :** Change le statut de `in_production` à `ready_at_shop`
- **Impact sur stock :** ✅ Appelle `_increment_shop_stock_with_value()`

#### `mark_as_delivered()`
- **Fichier :** `models.py` (lignes 510-515)
- **Description :** Change le statut de `ready_at_shop` à `delivered`
- **Impact sur stock :** ✅ Appelle `_decrement_stock_with_value_on_delivery()`

### 2.3 Fonctions Utilitaires

#### `update_stock_quantity()` (Module Stock)
- **Fichier :** `app/stock/models.py` (lignes 355-428)
- **Description :** Met à jour le stock et crée un mouvement de traçabilité
- **Paramètres :** `product_id`, `location_type`, `quantity_change`, `user_id`, `reason`, `order_id`
- **Appels :** Routes de transfert, ajustements manuels
- **Impact :** ✅ Stock + ✅ Traçabilité (StockMovement)

### 2.4 Tableau Récapitulatif des Fonctions

| Fonction | Fichier | Quand Appelée | Impact Stock | Impact Valeur |
|----------|---------|---------------|--------------|---------------|
| `Product.update_stock_by_location()` | `models.py:206` | Partout | ✅ Quantité | ✅ Valeur |
| `Order._increment_shop_stock_with_value()` | `models.py:524` | `mark_as_received_at_shop()`, `change_status_to_ready()` | ✅ Comptoir + | ✅ Valeur + |
| `Order._decrement_stock_with_value_on_delivery()` | `models.py:552` | `mark_as_delivered()` | ✅ Comptoir - | ✅ Valeur - |
| `Order.decrement_ingredients_stock_on_production()` | `models.py:572` | `edit_order_status()` (rare) | ✅ Ingrédients - | ❌ Non |
| `check_stock_availability()` | `app/orders/routes.py:15` | `new_customer_order()` | ❌ Vérification uniquement | ❌ |
| `update_stock_quantity()` | `app/stock/models.py:355` | Transferts, ajustements | ✅ Quantité | ✅ Traçabilité |

---

## 3. SÉQUENCE LOGIQUE COMPLÈTE

### 3.1 Création Commande Client (`customer_order`)

#### Route : `/orders/customer/new` (POST)
- **Fichier :** `app/orders/routes.py` (lignes 79-150)

#### Séquence :

1. **Validation formulaire** (`CustomerOrderForm`)
2. **Vérification stock ingrédients** :
   - Appel `check_stock_availability(form.items.data)` (ligne 88)
   - **Fonction :** `app/orders/routes.py:15-76`
   - **Logique :**
     - Pour chaque produit fini avec recette :
       - Calcule `qty_per_unit = quantity_needed / yield_quantity`
       - Calcule `needed_qty = qty_per_unit * quantity_ordered`
       - Vérifie stock disponible dans `production_location`
       - Flash message si insuffisant
   - **Résultat :** `stock_is_sufficient` (bool)
3. **Détermination statut initial** :
   - Si stock suffisant : `status = 'in_production'`
   - Si stock insuffisant : `status = 'pending'`
4. **Création commande** :
   - `Order` créé avec statut déterminé
   - `OrderItem` créés pour chaque produit
   - **Impact stock :** ❌ Aucun (pas encore de production)
5. **Commit base de données**

#### Impact sur Stock :
- ✅ **Vérification** : Stock ingrédients vérifié
- ❌ **Modification** : Aucune modification du stock à ce stade

### 3.2 Création Ordre de Production (`counter_production_request`)

#### Route : `/orders/production/new` (POST)
- **Fichier :** `app/orders/routes.py` (lignes 152-250)

#### Séquence :

1. **Validation formulaire**
2. **Création commande** :
   - `Order` avec `order_type='counter_production_request'`
   - `status='pending'` par défaut
3. **Création OrderItems**
4. **Commit base de données**

#### Impact sur Stock :
- ❌ **Aucun** : Pas de vérification ni modification à la création

### 3.3 Passage à "En Production" (`pending` → `in_production`)

#### Routes possibles :
- `Order.mark_as_in_production()` (méthode modèle)
- Changement manuel via `edit_order_status()`

#### Séquence :

1. **Vérification** : `order.status == 'pending'`
2. **Changement statut** : `order.status = 'in_production'`
3. **Commit base de données**

#### Impact sur Stock :
- ❌ **Aucun** : Pas de décrémentation à ce stade

### 3.4 Finalisation Production (`in_production` → `ready_at_shop`)

#### Route : `/orders/<id>/change-status-to-ready` (POST)
- **Fichier :** `app/orders/status_routes.py` (lignes 17-116)

#### Séquence :

1. **Vérification** : `order.can_be_received_at_shop()` (statut = `in_production`)
2. **Sélection employés** : Si non fournie, redirection vers formulaire
3. **Décrémentation ingrédients** (lignes 45-82) :
   - Pour chaque `OrderItem` → `Product` → `Recipe` :
     - Récupère `production_location` (magasin ou local)
     - Pour chaque `RecipeIngredient` :
       - Calcule `qty_per_unit = quantity_needed / yield_quantity`
       - Calcule `quantity_to_decrement = qty_per_unit * order_item.quantity`
       - Récupère PMP ingrédient : `cost_per_base_unit`
       - Calcule `value_to_decrement = quantity_to_decrement * cost_per_base_unit`
       - **Décrémente quantité** : `ingredient_product.update_stock_by_location(stock_attr, -quantity_to_decrement)`
       - **Décrémente valeur** : `ingredient_product.total_stock_value -= value_to_decrement`
       - **Décrémente valeur par emplacement** : `valeur_stock_ingredients_magasin` ou `valeur_stock_ingredients_local`
4. **Incrémentation produits finis** (ligne 85) :
   - Appel `order._increment_shop_stock_with_value()`
   - Pour chaque `OrderItem` :
     - Incrémente `stock_comptoir`
     - Calcule valeur : `cost_per_unit * quantity` (depuis recette)
     - Incrémente `total_stock_value`
     - Recalcule PMP produit fini
5. **Détermination statut final** :
   - Si `counter_production_request` : `status = 'completed'`
   - Si `customer_order` + `pickup` : `status = 'waiting_for_pickup'`
   - Si `customer_order` + `delivery` : `status = 'ready_at_shop'`
6. **Assignation employés**
7. **Commit base de données**

#### Impact sur Stock :
- ✅ **Ingrédients** : Décrémentation quantité + valeur (magasin ou local)
- ✅ **Produits finis** : Incrémentation quantité + valeur (comptoir)
- ❌ **Consommables** : **NON DÉCRÉMENTÉS** dans cette route (logique manquante)

### 3.5 Livraison/Vente (`ready_at_shop` → `delivered`)

#### Route : `/orders/<id>/change-status-to-delivered` (POST)
- **Fichier :** `app/orders/status_routes.py` (lignes 121-141)

#### Séquence :

1. **Vérification** : `order.can_be_delivered()` (statut = `ready_at_shop`)
2. **Appel méthode** : `order.mark_as_delivered()`
3. **Décrémentation produits finis** :
   - Appel `_decrement_stock_with_value_on_delivery()`
   - Pour chaque `OrderItem` :
     - Décrémente `stock_comptoir`
     - Calcule valeur : `PMP_produit_fini * quantity`
     - Décrémente `total_stock_value`
4. **Changement statut** : `status = 'delivered'`
5. **Commit base de données**

#### Impact sur Stock :
- ✅ **Produits finis** : Décrémentation quantité + valeur (comptoir)

### 3.6 Vente Directe au Comptoir (`in_store`)

#### Route : `/sales/api/complete-sale` (POST)
- **Fichier :** `app/sales/routes.py` (lignes 137-276)

#### Séquence :

1. **Récupération données** : Items depuis JSON
2. **Création commande** :
   - `Order` avec `order_type='in_store'`, `status='completed'`
3. **Pour chaque item** :
   - **Vérification stock** (ligne 183) : `product.stock_comptoir >= quantity`
   - Si insuffisant : Erreur 400
   - **Création OrderItem**
   - **Décrémentation stock** (ligne 195) :
     - `product.update_stock_by_location('stock_comptoir', -float(quantity))`
   - **Décrémentation valeur** (lignes 198-200) :
     - `value_decrement = quantity * pmp`
     - `product.total_stock_value -= value_decrement`
   - **Décrémentation consommables** (lignes 202-218) :
     - Recherche `ConsumableCategory` par catégorie produit
     - Calcule consommables nécessaires
     - Décrémente `stock_consommables` pour chaque consommable
4. **Calcul total** : `order.total_amount`
5. **Gestion paiement** : `amount_paid`, `payment_status`
6. **Création CashMovement**
7. **Commit base de données**

#### Impact sur Stock :
- ✅ **Produits finis** : Décrémentation quantité + valeur (comptoir)
- ✅ **Consommables** : Décrémentation (selon catégorie)

### 3.7 Annulation / Suppression Commande

#### Routes d'Annulation :

**Aucune route dédiée trouvée** pour l'annulation de commandes avec rétablissement du stock.

#### Routes de Modification :

- **`/orders/<id>/edit`** (POST) : `app/orders/routes.py:290-320`
  - **Impact :** Supprime tous les `OrderItem` et les recrée
  - **Impact stock :** ❌ Aucun (pas de rétablissement si commande déjà produite)

#### Routes de Changement Statut :

- **`/orders/<id>/edit_status`** (POST) : `app/orders/routes.py:322-342`
  - **Impact :** Change statut manuellement
  - **Impact stock :** Décrémentation ingrédients si passage à `ready_at_shop` (ligne 335)

#### Impact sur Stock :
- ❌ **Rétablissement manquant** : Aucune logique pour rétablir le stock si commande annulée après production

### 3.8 Tableau Récapitulatif des Séquences

| Étape | Route/Méthode | Fichier | Impact Ingrédients | Impact Produits Finis | Impact Consommables |
|-------|---------------|---------|-------------------|----------------------|---------------------|
| Création `customer_order` | `/orders/customer/new` | `app/orders/routes.py:79` | ✅ Vérification | ❌ | ❌ |
| Création `counter_production_request` | `/orders/production/new` | `app/orders/routes.py:152` | ❌ | ❌ | ❌ |
| `pending` → `in_production` | `mark_as_in_production()` | `models.py:497` | ❌ | ❌ | ❌ |
| `in_production` → `ready_at_shop` | `/orders/<id>/change-status-to-ready` | `app/orders/status_routes.py:17` | ✅ Décrémente | ✅ Incrémente | ❌ **MANQUANT** |
| `ready_at_shop` → `delivered` | `/orders/<id>/change-status-to-delivered` | `app/orders/status_routes.py:121` | ❌ | ✅ Décrémente | ❌ |
| Vente directe (`in_store`) | `/sales/api/complete-sale` | `app/sales/routes.py:137` | ❌ | ✅ Décrémente | ✅ Décrémente |
| Annulation | ❌ **AUCUNE** | - | ❌ | ❌ | ❌ |

---

## 4. RELATIONS ENTRE MODÈLES

### 4.1 Modèles Principaux

#### `Order` (Commande)
- **Fichier :** `models.py` (lignes 380-695)
- **Relations :**
  - `items` → `OrderItem[]` (one-to-many)
  - `produced_by` → `Employee[]` (many-to-many via `order_employees`)
  - `deliveryman` → `Deliveryman` (many-to-one)
  - `customer_id` → `Customer` (many-to-one)

#### `OrderItem` (Article de Commande)
- **Fichier :** `models.py` (lignes 696-750)
- **Relations :**
  - `order_id` → `Order` (many-to-one)
  - `product_id` → `Product` (many-to-one)

#### `Product` (Produit)
- **Fichier :** `models.py` (lignes 101-298)
- **Relations :**
  - `recipe_definition` → `Recipe` (one-to-one, via `Recipe.product_id`)
  - `recipe_uses` → `RecipeIngredient[]` (one-to-many, via `RecipeIngredient.product_id`)
  - `order_items` → `OrderItem[]` (one-to-many)

#### `Recipe` (Recette)
- **Fichier :** `models.py` (lignes 345-378)
- **Relations :**
  - `product_id` → `Product` (many-to-one, unique)
  - `ingredients` → `RecipeIngredient[]` (one-to-many)
  - `finished_product` → `Product` (one-to-one)

#### `RecipeIngredient` (Ingrédient de Recette)
- **Fichier :** `models.py` (lignes 300-343)
- **Relations :**
  - `recipe_id` → `Recipe` (many-to-one)
  - `product_id` → `Product` (many-to-one)

### 4.2 Modèles Stock (Module Inventory)

#### `InventoryMovement` (Mouvement d'Inventaire)
- **Fichier :** `app/inventory/models.py`
- **Description :** Traçabilité des mouvements de stock
- **Relations :** `product_id` → `Product`

#### `StockMovement` (Mouvement de Stock)
- **Fichier :** `app/stock/models.py`
- **Description :** Traçabilité via module Stock
- **Relations :** `product_id` → `Product`, `order_id` → `Order` (optionnel)

### 4.3 Modèles Consommables

#### `ConsumableRecipe` (Ancien Système)
- **Fichier :** `app/consumables/models.py`
- **Relations :**
  - `finished_product_id` → `Product`
  - `consumable_product_id` → `Product`

#### `ConsumableCategory` (Nouveau Système)
- **Fichier :** `app/consumables/models.py`
- **Relations :**
  - `product_category_id` → `Category`

### 4.4 Diagramme des Relations

```
Order
 ├── OrderItem[] (items)
 │    └── Product (product)
 │         ├── Recipe (recipe_definition) [one-to-one]
 │         │    ├── RecipeIngredient[] (ingredients)
 │         │    │    └── Product (product) [ingrédient]
 │         │    └── Product (finished_product) [produit fini]
 │         └── OrderItem[] (order_items)
 │
 └── Employee[] (produced_by)
      └── Order[] (orders_produced)

Product
 ├── Recipe (recipe_definition) [si produit fini]
 ├── RecipeIngredient[] (recipe_uses) [si ingrédient]
 ├── ConsumableRecipe[] (si consommable, ancien système)
 └── Category (category)
      └── ConsumableCategory (nouveau système)
```

### 4.5 Comment les Recettes Relient Produits Finis ↔ Ingrédients ↔ Inventaire

#### Chaîne de Liaison :

1. **Produit Fini** (`Product`) :
   - Possède une **recette** (`Recipe`) via `recipe_definition` (one-to-one)

2. **Recette** (`Recipe`) :
   - Définit le **rendement** : `yield_quantity` (ex: 12 galettes)
   - Définit le **lieu de production** : `production_location` (`ingredients_magasin` ou `ingredients_local`)
   - Contient des **ingrédients** : `RecipeIngredient[]`

3. **Ingrédient de Recette** (`RecipeIngredient`) :
   - Référence un **produit ingrédient** (`Product`) via `product_id`
   - Définit la **quantité nécessaire** : `quantity_needed` (ex: 4000g)
   - Définit l'**unité** : `unit` (ex: "g")

4. **Calcul des Besoins** :
   - **Quantité par unité produite** : `qty_per_unit = quantity_needed / yield_quantity`
   - **Quantité totale pour commande** : `needed_qty = qty_per_unit * order_item.quantity`

5. **Décrémentation Stock** :
   - Selon `production_location` de la recette :
     - Si `ingredients_magasin` → Décrémente `stock_ingredients_magasin`
     - Si `ingredients_local` → Décrémente `stock_ingredients_local`

#### Exemple Concret :

```
Produit Fini: "Galette" (id: 10)
  └── Recipe: "Recette Galette" (yield_quantity: 12, production_location: "ingredients_magasin")
       ├── RecipeIngredient 1: Product "Semoule" (quantity_needed: 4000g)
       ├── RecipeIngredient 2: Product "Eau" (quantity_needed: 2000ml)
       └── RecipeIngredient 3: Product "Sel" (quantity_needed: 50g)

Commande: 20 galettes
  └── Calcul besoins:
       - Semoule: (4000g / 12) * 20 = 6666.67g
       - Eau: (2000ml / 12) * 20 = 3333.33ml
       - Sel: (50g / 12) * 20 = 83.33g
  └── Décrémentation: stock_ingredients_magasin pour chaque ingrédient
```

---

## 5. ROUTES ET ENDPOINTS

### 5.1 Routes Commandes (`app/orders/routes.py`)

#### `/orders/customer/new` (GET, POST)
- **Fonction :** `new_customer_order()`
- **Lignes :** 79-150
- **Rôle :** Création commande client
- **Impact stock :**
  - ✅ Vérification disponibilité ingrédients (`check_stock_availability()`)
  - ❌ Pas de modification du stock

#### `/orders/production/new` (GET, POST)
- **Fonction :** `new_production_order()`
- **Lignes :** 152-250
- **Rôle :** Création ordre de production
- **Impact stock :** ❌ Aucun

#### `/orders/<id>/edit` (GET, POST)
- **Fonction :** `edit_order()`
- **Lignes :** 290-320
- **Rôle :** Modification commande
- **Impact stock :** ❌ Aucun (note: devrait re-vérifier les stocks)

#### `/orders/<id>/edit_status` (GET, POST)
- **Fonction :** `edit_order_status()`
- **Lignes :** 322-342
- **Rôle :** Changement statut manuel
- **Impact stock :**
  - ✅ Si passage à `ready_at_shop` : Appelle `decrement_ingredients_stock_on_production()` (ligne 335)

### 5.2 Routes Changement Statut (`app/orders/status_routes.py`)

#### `/orders/<id>/change-status-to-ready` (POST)
- **Fonction :** `change_status_to_ready()`
- **Lignes :** 17-116
- **Rôle :** Finalisation production (passage à `ready_at_shop`)
- **Impact stock :**
  - ✅ Décrémente ingrédients (quantité + valeur)
  - ✅ Incrémente produits finis (quantité + valeur)
  - ❌ **MANQUE** : Décrémentation consommables

#### `/orders/<id>/change-status-to-delivered` (POST)
- **Fonction :** `change_status_to_delivered()`
- **Lignes :** 121-141
- **Rôle :** Livraison commande
- **Impact stock :**
  - ✅ Décrémente produits finis (quantité + valeur)

#### `/orders/<id>/manual-status-change` (GET, POST)
- **Fonction :** `manual_status_change()`
- **Lignes :** 158-200
- **Rôle :** Changement statut manuel avec sélection employés
- **Impact stock :** ❌ Aucun (changement statut uniquement)

### 5.3 Routes Ventes (`app/sales/routes.py`)

#### `/sales/api/complete-sale` (POST)
- **Fonction :** `complete_sale()`
- **Lignes :** 137-276
- **Rôle :** Finalisation vente directe au comptoir
- **Impact stock :**
  - ✅ Vérification stock comptoir
  - ✅ Décrémente produits finis (quantité + valeur)
  - ✅ Décrémente consommables (selon catégorie)

### 5.4 Routes Achats (`app/purchases/routes.py`)

#### `/purchases/new` (GET, POST)
- **Fonction :** `new_purchase()`
- **Lignes :** 109-250
- **Rôle :** Création bon d'achat
- **Impact stock :**
  - ✅ Incrémente ingrédients/consommables (quantité + valeur)
  - ✅ Recalcule PMP

#### `/purchases/<id>/cancel` (POST)
- **Fonction :** `cancel_purchase()`
- **Lignes :** 321-365
- **Rôle :** Annulation bon d'achat
- **Impact stock :**
  - ✅ Décrémente ingrédients/consommables (quantité + valeur)
  - ✅ Recalcule PMP

### 5.5 Routes Stock (`app/stock/routes.py`)

#### `/stock/quick-entry` (POST)
- **Fonction :** `quick_stock_entry()`
- **Rôle :** Entrée rapide de stock
- **Impact stock :** ✅ Incrémente

#### `/stock/adjust` (POST)
- **Fonction :** `stock_adjustment()`
- **Rôle :** Ajustement manuel de stock
- **Impact stock :** ✅ Modifie (via `update_stock_quantity()`)

#### `/stock/transfer` (POST)
- **Fonction :** `transfer_stock()`
- **Rôle :** Transfert entre emplacements
- **Impact stock :** ✅ Décrémente source, incrémente destination

### 5.6 Tableau Récapitulatif des Routes

| Route | Méthode | Fichier | Rôle | Impact Ingrédients | Impact Produits Finis | Impact Consommables |
|-------|---------|---------|------|-------------------|----------------------|---------------------|
| `/orders/customer/new` | POST | `app/orders/routes.py:79` | Création commande client | ✅ Vérification | ❌ | ❌ |
| `/orders/production/new` | POST | `app/orders/routes.py:152` | Création ordre production | ❌ | ❌ | ❌ |
| `/orders/<id>/edit_status` | POST | `app/orders/routes.py:322` | Changement statut manuel | ✅ Si `ready_at_shop` | ❌ | ❌ |
| `/orders/<id>/change-status-to-ready` | POST | `app/orders/status_routes.py:17` | Finalisation production | ✅ Décrémente | ✅ Incrémente | ❌ **MANQUANT** |
| `/orders/<id>/change-status-to-delivered` | POST | `app/orders/status_routes.py:121` | Livraison | ❌ | ✅ Décrémente | ❌ |
| `/sales/api/complete-sale` | POST | `app/sales/routes.py:137` | Vente directe | ❌ | ✅ Décrémente | ✅ Décrémente |
| `/purchases/new` | POST | `app/purchases/routes.py:109` | Bon d'achat | ✅ Incrémente | ❌ | ✅ Incrémente |
| `/purchases/<id>/cancel` | POST | `app/purchases/routes.py:321` | Annulation achat | ✅ Décrémente | ❌ | ✅ Décrémente |

---

## 6. GESTION DES STOCKS INSUFFISANTS

### 6.1 Vérification Avant Production

#### Fonction : `check_stock_availability()`
- **Fichier :** `app/orders/routes.py` (lignes 15-76)
- **Quand appelée :** `new_customer_order()` (ligne 88)

#### Logique de Vérification :

1. **Pour chaque produit fini** dans la commande :
   - Si produit a une recette (`recipe_definition`) :
     - Récupère `production_location` (magasin ou local)
     - Pour chaque ingrédient de la recette :
       - Calcule `qty_per_unit = quantity_needed / yield_quantity`
       - Calcule `needed_qty = qty_per_unit * quantity_ordered`
       - Récupère stock disponible : `available_stock = ingredient_product.get_stock_by_location(stock_attr)`
       - **Vérification** : `if not available_stock or available_stock < needed_qty`
       - Si insuffisant : Flash message d'erreur, `is_sufficient = False`

2. **Résultat** :
   - Si `is_sufficient == True` : Commande créée avec `status='in_production'`
   - Si `is_sufficient == False` : Commande créée avec `status='pending'`

#### Points Forts :
- ✅ Vérification **avant création** de la commande
- ✅ Calcul précis des besoins (prise en compte du rendement)
- ✅ Messages d'erreur clairs (besoin vs disponible)

#### Points Faibles :
- ❌ **Pas de blocage** : La commande est créée même si stock insuffisant (statut `pending`)
- ❌ **Pas de vérification** lors du passage à `in_production` (si changement manuel)
- ❌ **Pas de vérification** pour les ordres de production (`counter_production_request`)

### 6.2 Vérification Avant Vente Directe

#### Route : `/sales/api/complete-sale`
- **Fichier :** `app/sales/routes.py` (ligne 183)

#### Logique :

```python
if product.stock_comptoir < float(quantity):
    return jsonify({'success': False, 'message': f'Stock insuffisant pour {product.name}'}), 400
```

#### Points Forts :
- ✅ **Blocage** : La vente ne peut pas être finalisée si stock insuffisant
- ✅ Erreur HTTP 400 avec message clair

#### Points Faibles :
- ❌ Vérification uniquement au moment de la vente (pas de réservation)

### 6.3 Vérification Avant Finalisation Production

#### Route : `/orders/<id>/change-status-to-ready`
- **Fichier :** `app/orders/status_routes.py`

#### Logique Actuelle :
- ❌ **Aucune vérification** : La décrémentation se fait directement sans vérifier si le stock est suffisant

#### Risque :
- **Stock négatif possible** : Si le stock a été consommé entre la création et la finalisation

### 6.4 Où Intégrer une Vérification Renforcée

#### Point d'Accroche 1 : Passage à `in_production`
- **Route :** `mark_as_in_production()` ou changement manuel
- **Action :** Vérifier stock ingrédients avant de permettre le passage
- **Bénéfice :** Éviter de démarrer une production sans stock

#### Point d'Accroche 2 : Finalisation Production
- **Route :** `/orders/<id>/change-status-to-ready`
- **Action :** Vérifier stock avant décrémentation
- **Bénéfice :** Éviter stock négatif

#### Point d'Accroche 3 : Ordres de Production
- **Route :** `/orders/production/new`
- **Action :** Vérifier stock à la création
- **Bénéfice :** Cohérence avec commandes client

---

## 7. CARTE FONCTIONNELLE DU FLUX

### 7.1 Diagramme de Flux Complet

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRÉATION COMMANDE CLIENT                      │
│              Route: /orders/customer/new (POST)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Vérification Stock  │
                    │ check_stock_        │
                    │ availability()      │
                    └─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Stock OK          Stock Insuffisant
                    │                   │
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ status =          │  │ status =         │
        │ 'in_production'   │  │ 'pending'        │
        └──────────────────┘  └──────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  COMMANDE CRÉÉE (Aucun impact stock) │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  PASSAGE À "EN PRODUCTION"            │
        │  (Aucun impact stock)                 │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  FINALISATION PRODUCTION              │
        │  Route: change-status-to-ready       │
        └──────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ DÉCRÉMENTATION    │  │ INCRÉMENTATION   │
        │ INGRÉDIENTS       │  │ PRODUITS FINIS  │
        │                   │  │                  │
        │ - Quantité        │  │ - Quantité       │
        │ - Valeur          │  │ - Valeur         │
        │ - Valeur par loc  │  │ - Recalcul PMP   │
        └──────────────────┘  └──────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  STATUT: ready_at_shop /             │
        │  waiting_for_pickup / completed      │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  LIVRAISON / VENTE                   │
        │  Route: change-status-to-delivered   │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  DÉCRÉMENTATION PRODUITS FINIS        │
        │  - Quantité (stock_comptoir)          │
        │  - Valeur (total_stock_value)        │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  STATUT: delivered / completed       │
        └──────────────────────────────────────┘
```

### 7.2 Flux Vente Directe au Comptoir

```
┌─────────────────────────────────────────────────────────────────┐
│                    VENTE DIRECTE AU COMPTOIR                     │
│              Route: /sales/api/complete-sale (POST)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Vérification Stock  │
                    │ stock_comptoir >=   │
                    │ quantity            │
                    └─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Stock OK          Stock Insuffisant
                    │                   │
                    ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Création Order    │  │ Erreur 400       │
        │ (in_store)        │  │ Vente annulée    │
        └──────────────────┘  └──────────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────┐
        │  POUR CHAQUE ITEM:                    │
        │  - Décrémente stock_comptoir          │
        │  - Décrémente total_stock_value       │
        │  - Décrémente consommables (si catégorie) │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  STATUT: completed                    │
        └──────────────────────────────────────┘
```

### 7.3 Tableau Détaillé des Étapes

| Étape | Route/Méthode | Fichier | Action Stock | Fichiers/Fonctions Impliqués |
|-------|---------------|---------|--------------|------------------------------|
| **1. Création Commande Client** | `/orders/customer/new` | `app/orders/routes.py:79` | ✅ Vérification | `check_stock_availability()` (ligne 15) |
| **2. Statut Initial** | `new_customer_order()` | `app/orders/routes.py:89` | ❌ Aucun | Détermination selon stock |
| **3. Passage à Production** | `mark_as_in_production()` | `models.py:497` | ❌ Aucun | Changement statut uniquement |
| **4. Finalisation Production** | `/orders/<id>/change-status-to-ready` | `app/orders/status_routes.py:17` | ✅ Décrémente ingrédients<br>✅ Incrémente produits finis | `Product.update_stock_by_location()` (ligne 73)<br>`Order._increment_shop_stock_with_value()` (ligne 85) |
| **5. Livraison** | `/orders/<id>/change-status-to-delivered` | `app/orders/status_routes.py:121` | ✅ Décrémente produits finis | `Order._decrement_stock_with_value_on_delivery()` (ligne 513) |
| **6. Vente Directe** | `/sales/api/complete-sale` | `app/sales/routes.py:137` | ✅ Décrémente produits finis<br>✅ Décrémente consommables | `Product.update_stock_by_location()` (ligne 195)<br>`ConsumableCategory.calculate_consumables_needed()` (ligne 212) |

### 7.4 Fichiers et Fonctions par Étape

#### Étape 1 : Création Commande Client
- **Fichier principal :** `app/orders/routes.py`
- **Fonctions :**
  - `new_customer_order()` (ligne 79)
  - `check_stock_availability()` (ligne 15)
- **Modèles :** `Order`, `OrderItem`, `Product`, `Recipe`, `RecipeIngredient`

#### Étape 2 : Passage à Production
- **Fichier principal :** `models.py`
- **Fonctions :**
  - `Order.mark_as_in_production()` (ligne 497)
- **Modèles :** `Order`

#### Étape 3 : Finalisation Production
- **Fichier principal :** `app/orders/status_routes.py`
- **Fonctions :**
  - `change_status_to_ready()` (ligne 17)
  - `Product.update_stock_by_location()` (appel ligne 73)
  - `Order._increment_shop_stock_with_value()` (appel ligne 85)
- **Modèles :** `Order`, `OrderItem`, `Product`, `Recipe`, `RecipeIngredient`, `Employee`

#### Étape 4 : Livraison
- **Fichier principal :** `app/orders/status_routes.py`
- **Fonctions :**
  - `change_status_to_delivered()` (ligne 121)
  - `Order.mark_as_delivered()` (appel ligne 133)
  - `Order._decrement_stock_with_value_on_delivery()` (appel ligne 513)
- **Modèles :** `Order`, `OrderItem`, `Product`

#### Étape 5 : Vente Directe
- **Fichier principal :** `app/sales/routes.py`
- **Fonctions :**
  - `complete_sale()` (ligne 137)
  - `Product.update_stock_by_location()` (appel ligne 195)
  - `ConsumableCategory.calculate_consumables_needed()` (appel ligne 212)
- **Modèles :** `Order`, `OrderItem`, `Product`, `ConsumableCategory`

---

## 8. POINTS FAIBLES ET INCOHÉRENCES

### 8.1 Double Décrémentation Potentielle

#### Problème :
- **Route 1 :** `change_status_to_ready()` décrémente les ingrédients **inline** (lignes 45-82)
- **Route 2 :** `edit_order_status()` appelle `decrement_ingredients_stock_on_production()` (ligne 335)
- **Risque :** Si une commande passe à `ready_at_shop` via `edit_order_status()`, les ingrédients sont décrémentés **deux fois** (une fois inline dans `change_status_to_ready()` si appelée avant, une fois via `decrement_ingredients_stock_on_production()`)

#### Impact :** Stock ingrédients incorrect (sous-évalué)

### 8.2 Consommables Non Décrémentés lors de Production

#### Problème :
- **Route :** `/orders/<id>/change-status-to-ready`
- **Logique actuelle :** Décrémente ingrédients et incrémente produits finis
- **Manque :** Décrémentation des consommables
- **Comparaison :** La vente directe (`complete_sale`) décrémente bien les consommables

#### Impact :** Stock consommables incorrect (sur-évalué)

### 8.3 Absence de Vérification lors de Finalisation

#### Problème :
- **Route :** `/orders/<id>/change-status-to-ready`
- **Logique actuelle :** Décrémente directement sans vérifier si le stock est suffisant
- **Risque :** Stock négatif possible si ingrédients consommés entre création et finalisation

#### Impact :** Stock négatif, incohérence comptable

### 8.4 Absence de Rétablissement Stock lors d'Annulation

#### Problème :
- **Aucune route** pour annuler une commande avec rétablissement du stock
- **Scénario :** Commande produite (`ready_at_shop`) puis annulée
  - Ingrédients déjà décrémentés ❌
  - Produits finis déjà incrémentés ❌
  - **Aucun rétablissement** ❌

#### Impact :** Stock incorrect, perte comptable

### 8.5 Incohérence entre Routes de Changement Statut

#### Problème :
- **Route 1 :** `change_status_to_ready()` (spécialisée, avec logique inline)
- **Route 2 :** `edit_order_status()` (générique, appelle `decrement_ingredients_stock_on_production()`)
- **Risque :** Comportements différents selon la route utilisée

#### Impact :** Incohérence, maintenance difficile

### 8.6 Méthode `decrement_ingredients_stock_on_production()` Non Utilisée

#### Problème :
- **Méthode définie :** `Order.decrement_ingredients_stock_on_production()` (lignes 572-654)
- **Utilisation :** Seulement dans `edit_order_status()` (ligne 335)
- **Route principale :** `change_status_to_ready()` utilise une logique **inline** au lieu d'appeler cette méthode

#### Impact :** Code dupliqué, maintenance difficile

### 8.7 Pas de Vérification pour Ordres de Production

#### Problème :
- **Route :** `/orders/production/new`
- **Logique actuelle :** Aucune vérification de stock
- **Comparaison :** Les commandes client vérifient le stock

#### Impact :** Risque de production sans stock

### 8.8 Tableau Récapitulatif des Problèmes

| Problème | Fichier/Route | Impact | Gravité |
|----------|---------------|--------|---------|
| Double décrémentation possible | `change_status_to_ready()` vs `edit_order_status()` | Stock incorrect | 🔴 Haute |
| Consommables non décrémentés | `change_status_to_ready()` | Stock incorrect | 🟠 Moyenne |
| Pas de vérification finalisation | `change_status_to_ready()` | Stock négatif possible | 🟠 Moyenne |
| Pas de rétablissement annulation | ❌ Aucune route | Stock incorrect | 🟠 Moyenne |
| Incohérence routes statut | `change_status_to_ready()` vs `edit_order_status()` | Comportement différent | 🟡 Faible |
| Méthode non utilisée | `decrement_ingredients_stock_on_production()` | Code dupliqué | 🟡 Faible |
| Pas de vérification ordres prod | `/orders/production/new` | Risque production sans stock | 🟡 Faible |

---

## 9. OPPORTUNITÉS D'AMÉLIORATION

### 9.1 Points d'Accroche pour "Préparation de Demain"

#### 9.1.1 Prévision des Besoins en Ingrédients

**Point d'Accroche :** Fonction `check_stock_availability()` existante

**Amélioration proposée :**
- **Créer un service** : `ProductionPlanningService`
- **Méthode :** `calculate_ingredients_needed_for_date(target_date)`
- **Logique :**
  1. Récupérer toutes les commandes avec `due_date = target_date` et `status IN ('pending', 'in_production')`
  2. Pour chaque commande, calculer les besoins en ingrédients (logique similaire à `check_stock_availability()`)
  3. Agréger par ingrédient et emplacement
  4. Comparer avec stock disponible
  5. Générer liste des ingrédients à commander

**Fichiers à modifier :**
- Créer : `app/orders/services.py` (nouveau fichier)
- Utiliser : `check_stock_availability()` comme base

#### 9.1.2 Blocage si Stock Insuffisant

**Point d'Accroche :** Route `change_status_to_ready()`

**Amélioration proposée :**
- **Avant décrémentation** : Vérifier stock disponible
- **Si insuffisant :** Bloquer la finalisation, afficher message avec besoins manquants
- **Option :** Permettre finalisation partielle (si certains produits peuvent être produits)

**Fichiers à modifier :**
- `app/orders/status_routes.py` (ligne 42, avant décrémentation)

#### 9.1.3 Réservation de Stock

**Point d'Accroche :** Création commande (`new_customer_order()`)

**Amélioration proposée :**
- **Créer modèle** : `StockReservation`
  - `order_id`, `product_id`, `quantity`, `location`, `reserved_at`, `expires_at`
- **Lors création commande** : Réserver le stock nécessaire
- **Lors finalisation** : Convertir réservation en consommation réelle
- **Lors annulation** : Libérer la réservation

**Fichiers à créer/modifier :**
- Créer : `app/inventory/models.py` (ajouter `StockReservation`)
- Modifier : `app/orders/routes.py` (créer réservations)
- Modifier : `app/orders/status_routes.py` (libérer réservations)

#### 9.1.4 Dashboard "Préparation de Demain"

**Point d'Accroche :** Module dashboards existant

**Amélioration proposée :**
- **Route :** `/dashboards/preparation-tomorrow`
- **Fonctionnalités :**
  - Liste des commandes prévues pour demain
  - Besoins en ingrédients (agrégés)
  - Alertes stock insuffisant
  - Suggestions d'achats
  - Planning de production

**Fichiers à créer/modifier :**
- Créer : `app/dashboards/routes.py` (ajouter route)
- Créer : `app/templates/dashboards/preparation_tomorrow.html`
- Utiliser : `ProductionPlanningService` (à créer)

### 9.2 Corrections des Points Faibles

#### 9.2.1 Unifier la Logique de Décrémentation

**Action :**
- Utiliser uniquement `Order.decrement_ingredients_stock_on_production()`
- Supprimer la logique inline dans `change_status_to_ready()`
- Ajouter la décrémentation des consommables dans cette méthode

**Fichiers à modifier :**
- `app/orders/status_routes.py` (lignes 45-82 → remplacer par appel méthode)
- `models.py` (lignes 572-654 → ajouter consommables)

#### 9.2.2 Ajouter Vérification lors de Finalisation

**Action :**
- Créer méthode : `Order.check_ingredients_availability()`
- Appeler avant décrémentation dans `change_status_to_ready()`
- Bloquer si insuffisant

**Fichiers à modifier :**
- `models.py` (ajouter méthode)
- `app/orders/status_routes.py` (appeler avant décrémentation)

#### 9.2.3 Implémenter Rétablissement Stock lors d'Annulation

**Action :**
- Créer route : `/orders/<id>/cancel` (POST)
- Créer méthode : `Order.restore_stock_on_cancellation()`
- Logique :
  - Si statut `ready_at_shop` ou `delivered` :
    - Rétablir ingrédients (incrémenter)
    - Rétablir produits finis (décrémenter si pas encore livré)
  - Si statut `delivered` :
    - Rétablir produits finis (incrémenter)

**Fichiers à créer/modifier :**
- `app/orders/routes.py` (ajouter route)
- `models.py` (ajouter méthode)

#### 9.2.4 Vérification Stock pour Ordres de Production

**Action :**
- Appeler `check_stock_availability()` dans `new_production_order()`
- Bloquer création si stock insuffisant

**Fichiers à modifier :**
- `app/orders/routes.py` (ligne 152, ajouter vérification)

### 9.3 Améliorations Architecturales

#### 9.3.1 Service de Gestion Stock Centralisé

**Action :**
- Créer : `app/inventory/services.py`
- Méthodes :
  - `StockService.reserve_stock(order_id, items)`
  - `StockService.consume_stock(order_id, items)`
  - `StockService.restore_stock(order_id, items)`
  - `StockService.check_availability(items)`

**Bénéfice :** Logique centralisée, réutilisable, testable

#### 9.3.2 Traçabilité Complète

**Action :**
- Utiliser `StockMovement` pour tous les mouvements
- Créer mouvements lors de :
  - Décrémentation ingrédients
  - Incrémentation produits finis
  - Décrémentation produits finis
  - Annulation

**Bénéfice :** Audit trail complet, traçabilité

#### 9.3.3 Validation Transactionnelle

**Action :**
- Encapsuler toutes les opérations de stock dans des transactions
- Rollback automatique en cas d'erreur
- Vérifications avant commit

**Bénéfice :** Cohérence garantie, pas de stock partiellement modifié

### 9.4 Priorisation des Améliorations

#### Priorité Haute (Impact Immédiat)
1. ✅ Unifier logique décrémentation (éviter double décrémentation)
2. ✅ Ajouter décrémentation consommables dans `change_status_to_ready()`
3. ✅ Ajouter vérification stock lors finalisation

#### Priorité Moyenne (Amélioration Continue)
4. ✅ Implémenter rétablissement stock lors annulation
5. ✅ Vérification stock pour ordres de production
6. ✅ Service gestion stock centralisé

#### Priorité Basse (Évolutions Futures)
7. ✅ Réservation de stock
8. ✅ Dashboard "Préparation de Demain"
9. ✅ Traçabilité complète avec StockMovement

---

## 📊 CONCLUSION

### 9.5 Résumé des Constats

#### Points Forts
- ✅ Vérification stock avant création commande client
- ✅ Calcul précis des besoins (prise en compte rendement)
- ✅ Gestion de la valeur du stock (PMP, total_stock_value)
- ✅ Décrémentation consommables pour ventes directes
- ✅ Traçabilité partielle (StockMovement pour certains mouvements)

#### Points Faibles
- ❌ Double décrémentation possible (routes différentes)
- ❌ Consommables non décrémentés lors production
- ❌ Pas de vérification lors finalisation (risque stock négatif)
- ❌ Pas de rétablissement stock lors annulation
- ❌ Incohérence entre routes de changement statut
- ❌ Pas de vérification pour ordres de production

#### Opportunités
- 🎯 Prévision besoins ingrédients (préparation demain)
- 🎯 Blocage si stock insuffisant
- 🎯 Réservation de stock
- 🎯 Dashboard "Préparation de Demain"
- 🎯 Service gestion stock centralisé

### 9.6 Recommandations Finales

1. **Court terme :** Corriger les incohérences (double décrémentation, consommables manquants)
2. **Moyen terme :** Implémenter vérifications renforcées et rétablissement stock
3. **Long terme :** Développer fonctionnalités avancées (réservation, prévision, dashboard)

---

**Fin du rapport d'audit technique**


