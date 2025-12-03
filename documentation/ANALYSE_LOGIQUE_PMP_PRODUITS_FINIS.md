# 📊 ANALYSE DE LA LOGIQUE PMP POUR LES PRODUITS FINIS

**Date:** 3 décembre 2025  
**Statut:** ⚠️ PROBLÈME IDENTIFIÉ - Aucune modification effectuée

---

## 🎯 Clarification de la logique métier

### PMP (Prix Moyen Pondéré) = Coût de revient
- ✅ Le PMP représente le **coût de revient** uniquement
- ✅ Le PMP n'a **aucun lien** avec le prix de vente
- ✅ Le prix de vente est géré séparément dans l'attribut `price`

---

## 📦 Deux types de produits finis

### 1️⃣ Produits finis AVEC RECETTE (produits)

**Comment le coût de revient est calculé :**

```python
# models.py - Recipe
@property
def cost_per_unit(self):
    return self.total_cost / Decimal(self.yield_quantity)

@property
def total_cost(self):
    return sum(ing.cost for ing in self.ingredients)
```

**Logique :**
- ✅ Le coût de revient = somme des coûts des ingrédients / quantité produite
- ✅ Le coût de chaque ingrédient = `quantity_needed * ingredient.cost_price` (PMP de l'ingrédient)
- ✅ **DYNAMIQUE** : Quand le PMP d'un ingrédient change (nouvel achat), le `cost_per_unit` de la recette est automatiquement recalculé (propriété Python)
- ✅ Pas besoin de stocker le coût dans `product.cost_price` car il se calcule à la volée

**Exemple :**
```
Recette Mhadjeb (10 pièces) :
- 1000g Farine (PMP: 0.05 DA/g) = 50 DA
- 200g Margarine (PMP: 0.10 DA/g) = 20 DA
- 50g Sel (PMP: 0.02 DA/g) = 1 DA
Total : 71 DA
Coût par pièce : 71 DA / 10 = 7.10 DA/pièce

Si le PMP de la Margarine passe à 0.12 DA/g :
- Nouveau total : 74 DA
- Nouveau coût par pièce : 7.40 DA/pièce
```

---

### 2️⃣ Produits finis SANS RECETTE (achetables)

**Comment le coût de revient est calculé :**

```python
# app/purchases/routes.py - new_purchase()
elif product.product_type == 'finished':
    product.update_stock_by_location(
        'stock_comptoir',
        quantity_in_base_unit,
        unit_cost_override=price_per_base_unit  # Prix d'achat
    )
    
    # Recalculer le PMP
    if total_qty > 0:
        new_cost_price = total_stock_value / total_qty
        product.cost_price = new_cost_price
```

**Logique :**
- ✅ Le coût de revient = **PMP classique** basé sur les achats
- ✅ Chaque achat met à jour `total_stock_value` et `stock_comptoir`
- ✅ Le PMP est recalculé : `cost_price = total_stock_value / total_stock`
- ✅ Le coût évolue avec chaque nouvel achat

**Exemple :**
```
Barquette 1185 :
- Achat 1 : 50 pièces à 30 DA/pièce = 1500 DA
  → Stock : 50, Valeur : 1500 DA, PMP : 30 DA/pièce
  
- Achat 2 : 100 pièces à 35 DA/pièce = 3500 DA
  → Stock : 150, Valeur : 5000 DA, PMP : 33.33 DA/pièce
  
- Vente : 80 pièces
  → Stock : 70, Valeur : 2333.10 DA, PMP : 33.33 DA/pièce (inchangé)
```

---

## 🐛 PROBLÈME IDENTIFIÉ

### Code actuel - `app/purchases/routes.py`

#### ✅ Fonction `new_purchase()` (ligne ~200-290)
```python
# Bloc pour produits finis (ligne 256-277)
elif product.product_type == 'finished':
    product.update_stock_by_location(
        'stock_comptoir',
        quantity_in_base_unit,
        unit_cost_override=price_per_base_unit
    )
    
    # Recalculer le PMP
    if total_qty_decimal > 0:
        new_cost_price = (total_value_decimal / total_qty_decimal)
        product.cost_price = new_cost_price
```
**Statut :** ✅ Correct

---

#### ❌ Fonction `edit_purchase()` (ligne ~440-660)
```python
# Ligne 600-633 : Bloc pour ingrédients
elif product.product_type == 'ingredient':
    product.update_stock_by_location(...)
    # ... recalcul PMP ...

# Ligne 635-650 : Pas de bloc pour 'finished' !
# Le code passe directement à la création de PurchaseItem
purchase_item = PurchaseItem(...)
```
**Statut :** ❌ **BLOC MANQUANT POUR LES PRODUITS FINIS**

---

### Impact du problème

1. **Création d'un bon d'achat** (`new_purchase`) :
   - ✅ Produit fini achetable → PMP correctement calculé
   
2. **Modification d'un bon d'achat** (`edit_purchase`) :
   - ❌ Produit fini achetable → PMP **NON** calculé
   - ❌ Stock ajouté mais `cost_price` reste à 0 ou inchangé
   - ❌ `total_stock_value` non mise à jour
   - ❌ Résultat : Valeur de stock = 0 DA sur le dashboard

---

### Les 13 produits sans PMP sur le VPS

```
ID     Produit                             Stock        Prix Vente  
----------------------------------------------------------------------
205    Barquette 1185                      70.00        35.00       
135    Ke3ike3ate Messekerine              14.00        160.00      
140    Gheribya                            10.00        60.00       
146    Mekiret aux Amandes                 4.00         1000.00     
195    Beniwen                             10.00        120.00      
141    Halwet Tabaa                        16.00        60.00       
142    Les Russes                          3.00         140.00      
150    Griwech                             11.00        70.00       
138    Makroute La3essel Aux Amandes       17.00        150.00      
134    Tcharak Messeker                    14.00        160.00      
147    Mekiret aux Dattes                  5.00         600.00      
130    Sablé Confiture Rayures Chocolat    3.00         70.00       
148    Djouza                              6.00         120.00      
```

**Hypothèse :**
- Ces produits sont des **produits finis achetables** (sans recette)
- Ils ont été reçus via des bons d'achat **modifiés** (et non créés directement)
- Le bug dans `edit_purchase()` a empêché le calcul de leur PMP

---

## 🔧 SOLUTION REQUISE

### 1. Corriger `edit_purchase()` dans `app/purchases/routes.py`

Ajouter un bloc pour les produits finis après le bloc des ingrédients :

```python
elif product.product_type == 'ingredient':
    # ... code existant ...

elif product.product_type == 'finished':
    # ✅ AJOUT : Traitement des produits finis achetables
    stock_location = 'stock_comptoir'
    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
    
    current_app.logger.info(f"DEBUG - Mise à jour produit fini achetable: {stock_location}")
    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
    
    # Utiliser update_stock_by_location avec le prix d'achat
    product.update_stock_by_location(
        stock_location,
        quantity_in_base_unit,
        unit_cost_override=price_per_base_unit
    )
    
    # Recalculer le PMP
    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
    total_value_decimal = Decimal(str(product.total_stock_value or 0))
    
    if total_qty_decimal > 0:
        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        product.cost_price = new_cost_price
        current_app.logger.info(f"DEBUG - PMP recalculé: {new_cost_price} DA")
    else:
        product.cost_price = Decimal(str(price_per_base_unit))
        current_app.logger.info(f"DEBUG - Stock total = 0, PMP défini au prix d'achat: {price_per_base_unit}")
```

---

### 2. Pour les 13 produits sans PMP existants

Deux approches possibles :

#### Option A : Initialiser avec le coût de la recette (si disponible)
```python
if product.recipe_definition:
    product.cost_price = product.recipe_definition.cost_per_unit
```

#### Option B : Retrouver le dernier bon d'achat et utiliser son prix
```python
# Requête sur PurchaseItem pour trouver le dernier achat de ce produit
last_purchase_item = PurchaseItem.query.filter_by(product_id=product.id).order_by(PurchaseItem.id.desc()).first()
if last_purchase_item:
    product.cost_price = last_purchase_item.unit_price
```

#### Option C : Demander à l'utilisateur de définir manuellement
- Via l'interface admin : modifier chaque produit et définir le coût de revient
- Via un script SQL : `UPDATE products SET cost_price = XXX WHERE id = YYY;`

---

## 📋 RÉCAPITULATIF

### ✅ Ce qui fonctionne
1. Produits finis avec recette : coût calculé dynamiquement ✅
2. Création de bons d'achat pour produits finis achetables ✅
3. Calcul du PMP pour ingrédients et consommables ✅

### ❌ Ce qui ne fonctionne pas
1. **Modification de bons d'achat pour produits finis** → Pas de mise à jour du PMP ❌
2. Conséquence : Valeurs de stock affichées à 0 DA ❌

### 🔧 Action requise
1. Corriger `edit_purchase()` en ajoutant le bloc pour `product.product_type == 'finished'`
2. Initialiser le PMP des 13 produits existants (méthode à définir)
3. Recalculer les valeurs de stock via `scripts/correction_valorisation_stock.py`

---

## ⚠️ NOTE IMPORTANTE

Le script `scripts/init_pmp_produits_finis.py` que j'ai créé précédemment est **INCORRECT** car :
- ❌ Il utilise un pourcentage du prix de vente (70%) comme fallback
- ❌ Cela ne correspond PAS à la logique métier (PMP = coût de revient, pas lié au prix de vente)

**À NE PAS UTILISER** tant que la correction n'est pas validée.

---

**Statut :** En attente de validation avant correction

