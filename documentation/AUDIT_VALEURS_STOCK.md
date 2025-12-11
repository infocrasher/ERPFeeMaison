# AUDIT DES MÉTHODES QUI MODIFIENT LES VALEURS DE STOCK

> **Date de l'audit** : 11 décembre 2025  
> **Statut** : ✅ TOUS LES BUGS CORRIGÉS

---

## Résumé des corrections

| Fichier | Méthode | Problème | Statut |
|---------|---------|----------|--------|
| models.py | `update_stock_by_location` | Méthode centrale - synchronise valeur_stock_* et total_stock_value | ✅ OK |
| models.py | `_increment_shop_stock_with_value` | Double comptabilisation total_stock_value | ✅ CORRIGÉ |
| models.py | `_decrement_stock_with_value_on_delivery` | Double décrémentation total_stock_value | ✅ CORRIGÉ |
| models.py | `restore_stock_on_cancellation` | Double incrémentation total_stock_value | ✅ CORRIGÉ |
| app/sales/routes.py | `create_delivery_order` | Double décrémentation total_stock_value | ✅ CORRIGÉ |
| app/sales/routes.py | `quick_sale` | Double décrémentation total_stock_value | ✅ CORRIGÉ |
| app/purchases/routes.py | `cancel_purchase` | Modification manuelle de total_stock_value | ✅ CORRIGÉ |
| app/purchases/routes.py | `edit_purchase` | Double modification total_stock_value + valeur_stock_* | ✅ CORRIGÉ |
| models.py | `_increment_stock_value_only_for_customer_order` | Cas spécial commandes client (intentionnel) | ⚠️ À SURVEILLER |

---

## 🔴 RÈGLE D'OR POUR LE DÉVELOPPEMENT

> **`update_stock_by_location()` gère TOUT automatiquement :**
> - La quantité de stock (`stock_comptoir`, `stock_ingredients_*`, etc.)
> - La valeur par emplacement (`valeur_stock_comptoir`, `valeur_stock_ingredients_*`, etc.)
> - La valeur totale (`total_stock_value`)
>
> **NE JAMAIS modifier `total_stock_value` ou `valeur_stock_*` manuellement après l'appel !**

---

## Détail des bugs corrigés

### 1. `_increment_shop_stock_with_value` (models.py)

**Bug** : Double incrémentation de `total_stock_value`
```python
# AVANT (bugué)
product.update_stock_by_location('stock_comptoir', qty)  # Ajoute à total_stock_value
product.total_stock_value = ... + value_to_increment      # ENCORE !!! ❌
```

**Correction** : Utilisation de `unit_cost_override` pour passer le coût de la recette
```python
# APRÈS (corrigé)
product.update_stock_by_location('stock_comptoir', qty, unit_cost_override=float(cost_per_unit))
# C'est tout ! Pas de modification manuelle de total_stock_value
```

---

### 2. `_decrement_stock_with_value_on_delivery` (models.py)

**Bug** : Double décrémentation de `total_stock_value`
```python
# AVANT (bugué)
product.update_stock_by_location('stock_comptoir', -qty)  # Décrémente total_stock_value
product.total_stock_value = ... - value_to_decrement      # ENCORE !!! ❌
```

**Correction** : Suppression de la modification manuelle
```python
# APRÈS (corrigé)
product.update_stock_by_location('stock_comptoir', -qty)
# C'est tout !
```

---

### 3. `restore_stock_on_cancellation` (models.py)

**Bug** : Double incrémentation de `total_stock_value`

**Correction** : Même approche - suppression de la modification manuelle

---

### 4. Ventes PDV - `create_delivery_order` et `quick_sale` (app/sales/routes.py)

**Bug** : Double décrémentation de `total_stock_value`
```python
# AVANT (bugué)
product.update_stock_by_location('stock_comptoir', -qty)
product.total_stock_value = ... - value_decrement  # ENCORE !!! ❌
```

**Correction** : Suppression des lignes de modification manuelle

---

### 5. Annulation d'achats - `cancel_purchase` et `edit_purchase` (app/purchases/routes.py)

**Bug** : Modification manuelle de `total_stock_value` et `valeur_stock_*` après `update_stock_by_location`

**Correction** : Utilisation de `unit_cost_override` avec le prix d'achat original
```python
# APRÈS (corrigé)
product.update_stock_by_location(
    stock_location, 
    -quantity,
    unit_cost_override=float(item.unit_price)  # Prix d'achat original
)
```

---

## Cas spécial : `_increment_stock_value_only_for_customer_order`

Cette méthode modifie `total_stock_value` SANS modifier `valeur_stock_comptoir`.

**C'est INTENTIONNEL** car pour les commandes client :
- Les produits sont "réservés" (pas disponibles au comptoir)
- On veut comptabiliser leur valeur (pour le COGS)
- Mais ils ne doivent pas apparaître dans le stock comptoir

⚠️ Cela crée une incohérence structurelle entre `total_stock_value` et la somme des `valeur_stock_*`.

**Solution future possible** : Créer un champ `valeur_stock_reserve` pour les produits réservés.

---

## Script de correction des données

Si des incohérences sont détectées, exécuter :

```bash
cd /opt/erp/app
python3 scripts/diagnostic_valeurs_stock.py
# Tapez 'CORRIGER' pour synchroniser total_stock_value avec la somme des valeurs
```

---

## Commits de correction

- `b22e84a` : Fix bug double comptabilisation dans `_increment_shop_stock_with_value`
- `a1bb140` : Fix multiples bugs de double modification de `total_stock_value`

