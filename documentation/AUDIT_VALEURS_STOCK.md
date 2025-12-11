# AUDIT DES MÉTHODES QUI MODIFIENT LES VALEURS DE STOCK

## Résumé

| Fichier | Méthode | Problème | Statut |
|---------|---------|----------|--------|
| models.py | `update_stock_by_location` | Base - synchronise valeur_stock_* et total_stock_value | ✅ OK |
| models.py | `_increment_shop_stock_with_value` | Double comptabilisation | ✅ CORRIGÉ |
| models.py | `_increment_stock_value_only_for_customer_order` | Modifie total_stock_value SANS valeur_stock_* | ⚠️ BUG |
| models.py | `_decrement_stock_with_value_on_delivery` | Modifie total_stock_value SANS valeur_stock_comptoir | ⚠️ BUG |
| models.py | `restore_stock_on_cancellation` | Modifie total_stock_value SANS valeur_stock_comptoir | ⚠️ BUG |
| app/sales/routes.py | `create_sale` (ligne 256) | Modifie total_stock_value SANS valeur_stock_comptoir | ⚠️ BUG |
| app/sales/routes.py | `quick_sale` (ligne 359) | Modifie total_stock_value SANS valeur_stock_comptoir | ⚠️ BUG |
| app/purchases/routes.py | `cancel_purchase` | Modifie total_stock_value séparément | ⚠️ À VÉRIFIER |

---

## Détail des bugs trouvés

### 1. `_increment_stock_value_only_for_customer_order` (models.py ligne 700)

```python
# Incrémente SEULEMENT total_stock_value
product_fini.total_stock_value = ... + value_to_increment
# ❌ Ne modifie PAS valeur_stock_comptoir
```

**Impact** : Pour les commandes client, `total_stock_value` augmente mais `valeur_stock_comptoir` reste inchangé → incohérence.

**Note** : C'est intentionnel car les produits sont "réservés", mais crée une incohérence structurelle.

---

### 2. `_decrement_stock_with_value_on_delivery` (models.py ligne 776)

```python
# Décrémente SEULEMENT total_stock_value
product_fini.total_stock_value = ... - value_to_decrement
# ❌ Ne modifie PAS valeur_stock_comptoir
```

**Impact** : Lors de la livraison, `total_stock_value` diminue mais `valeur_stock_comptoir` reste inchangé.

---

### 3. `restore_stock_on_cancellation` (models.py ligne 797)

```python
# Réincrémente SEULEMENT total_stock_value
product_fini.total_stock_value = ... + value_to_restore
# ❌ Ne modifie PAS valeur_stock_comptoir
```

**Impact** : Lors d'une annulation, `total_stock_value` augmente mais `valeur_stock_comptoir` reste inchangé.

---

### 4. Ventes PDV - `create_sale` (app/sales/routes.py ligne 256)

```python
# Décrémente SEULEMENT total_stock_value
product.total_stock_value = (product.total_stock_value or Decimal('0.0')) - value_decrement
# ❌ Ne modifie PAS valeur_stock_comptoir via update_stock_by_location
```

**Impact** : Les ventes au comptoir diminuent `total_stock_value` mais pas `valeur_stock_comptoir`.

---

### 5. Ventes PDV - `quick_sale` (app/sales/routes.py ligne 359)

Même problème que `create_sale`.

---

## Solution recommandée

Toutes ces méthodes devraient utiliser `update_stock_by_location` avec le paramètre approprié pour que les valeurs restent synchronisées, ou bien modifier les deux champs (`total_stock_value` ET `valeur_stock_*`) ensemble.

### Option A : Utiliser update_stock_by_location partout

```python
# Au lieu de :
product.total_stock_value = ... - value_decrement

# Utiliser :
product.update_stock_by_location('stock_comptoir', -quantity, unit_cost_override=pmp)
```

### Option B : Modifier les deux valeurs ensemble

```python
# Décrémentation
product.total_stock_value = ... - value_decrement
product.valeur_stock_comptoir = ... - value_decrement  # ← AJOUTER
```

---

## Priorité des corrections

1. **HAUTE** : `app/sales/routes.py` - Ventes PDV (utilisé quotidiennement)
2. **HAUTE** : `_decrement_stock_with_value_on_delivery` - Livraisons
3. **MOYENNE** : `restore_stock_on_cancellation` - Annulations
4. **BASSE** : `_increment_stock_value_only_for_customer_order` - Cas spécial commandes client

