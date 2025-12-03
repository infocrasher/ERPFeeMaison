# 🚨 PROBLÈME CRITIQUE : Décrémentation du stock_comptoir lors de la réception d'une commande client

## 📋 Résumé du Problème

Lors de la réception d'une commande client (changement de statut de `in_production` à `ready_at_shop`), le **stock_comptoir** est incorrectement décrémenté alors qu'il ne devrait **PAS** être modifié.

### Symptômes Observés

1. **Avant la réception** : Stock comptoir = 20 pièces (exemple : Msamen grand taille doublé)
2. **Après la réception** : Stock comptoir = 15 pièces (décrémentation de 5, qui correspond exactement à la quantité de la commande)
3. **Logs** : Les logs indiquent que le stock_comptoir reste à 20.0 (pas de modification détectée dans le code)
4. **PDV** : Le point de vente affiche la valeur décrémentée (15 au lieu de 20)
5. **Dashboard** : Le dashboard stock/comptoir affiche parfois 0

### Exemple Concret

- **Commande** : 5 pièces de "Msamen grand taille doublé"
- **Stock initial** : 20 pièces
- **Stock après réception** : 15 pièces (au lieu de 20)
- **Perte** : 5 pièces (correspond exactement à la quantité de la commande)

## 🔍 Analyse Technique

### Comportement Attendu

Pour une **commande client** (`order_type = 'customer_order'`), lors de la réception au magasin :
- ✅ La **valeur du stock** doit être mise à jour (pour la comptabilité et le PMP)
- ✅ Le **stock_comptoir** ne doit **PAS** être modifié (les produits sont réservés pour le client, pas disponibles à la vente)
- ✅ Seuls les **ordres de production pour le comptoir** (`order_type = 'counter_production_request'`) doivent incrémenter le stock_comptoir

### Comportement Observé

- ❌ Le stock_comptoir est décrémenté de la quantité de la commande
- ❌ Les logs ne détectent pas la modification (elle se produit probablement après le commit ou via un autre chemin)
- ❌ La décrémentation correspond exactement à la quantité de la commande

### Code Concerné

#### 1. Route de réception : `app/orders/status_routes.py`

```python
@status_bp.route('/<int:order_id>/change-status-to-ready', methods=['POST'])
def change_status_to_ready(order_id):
    # ...
    if order.order_type == 'counter_production_request':
        order._increment_shop_stock_with_value()  # ✅ Correct pour ordres de production
    else:
        order._increment_stock_value_only_for_customer_order()  # ✅ Devrait être correct
```

#### 2. Méthode pour commandes client : `models.py`

```python
def _increment_stock_value_only_for_customer_order(self):
    """
    Met à jour uniquement la valeur du stock pour les commandes client.
    N'incrémente PAS le stock_comptoir car les produits sont réservés pour le client.
    """
    # Sauvegarde du stock_comptoir avant modification
    stock_comptoir_avant = float(product_fini.stock_comptoir or 0.0)
    
    # Mise à jour de la valeur (PAS du stock_comptoir)
    product_fini.total_stock_value = ...
    product_fini.cost_price = ...
    
    # Vérification que stock_comptoir n'a pas changé
    # Les logs montrent que cette vérification passe (stock_comptoir = 20.0 inchangé)
```

#### 3. Méthode de mise à jour du stock : `models.py`

```python
def update_stock_by_location(self, location_key: str, quantity_change: float, ...):
    """
    Met à jour le stock d'un produit à un emplacement spécifique.
    """
    # Si location_key == 'stock_comptoir' et quantity_change < 0, décrémente le stock_comptoir
    # Des logs ont été ajoutés pour détecter tous les appels avec stock_comptoir
```

## 🔬 Hypothèses sur la Cause

### Hypothèse 1 : Appel à `update_stock_by_location` avec `stock_comptoir` et valeur négative

**Probabilité** : ⭐⭐⭐⭐⭐ (Très élevée)

Un appel à `update_stock_by_location('stock_comptoir', -quantity)` se produit quelque part, probablement :
- Lors de la décrémentation des ingrédients (si un ingrédient est le même produit que le produit fini)
- Via un événement SQLAlchemy déclenché lors du commit
- Dans une autre méthode appelée en parallèle

**Vérification** : Des logs ont été ajoutés dans `update_stock_by_location` pour détecter tous les appels avec `stock_comptoir`.

### Hypothèse 2 : Modification via SQLAlchemy après le commit

**Probabilité** : ⭐⭐⭐ (Moyenne)

SQLAlchemy pourrait déclencher un événement ou un trigger qui modifie le stock_comptoir après le commit, mais avant la lecture suivante.

**Vérification** : Des vérifications ont été ajoutées avant et après le commit.

### Hypothèse 3 : Ingrédient = Produit fini

**Probabilité** : ⭐⭐ (Faible)

Si un ingrédient dans la recette est le même produit que le produit fini, lors de la décrémentation des ingrédients, le stock_comptoir pourrait être modifié par erreur.

**Vérification** : Des vérifications ont été ajoutées pour détecter ce cas.

### Hypothèse 4 : Calcul du PMP déclenche une modification

**Probabilité** : ⭐ (Très faible)

Le calcul du PMP (`cost_price = total_stock_value / stock_pour_pmp`) pourrait déclencher un side effect qui modifie le stock_comptoir.

**Vérification** : Des logs ont été ajoutés à chaque étape du calcul du PMP.

### Hypothèse 5 : Autre méthode appelée en parallèle

**Probabilité** : ⭐⭐⭐ (Moyenne)

Une autre méthode pourrait être appelée en parallèle qui décrémente le stock_comptoir (par exemple, `mark_as_received_at_shop()` ou `_increment_shop_stock_with_value()`).

**Vérification** : Vérifier tous les appels de méthodes lors de la réception.

## 🛠️ Corrections Appliquées (Sans Résultat)

### 1. Logs de traçage dans `_increment_stock_value_only_for_customer_order()`

- Vérification du stock_comptoir avant toute modification
- Vérification après modification de `total_stock_value`
- Vérification après calcul du PMP
- Vérification après modification de `cost_price`
- Vérification après `db.session.add()`

**Résultat** : Les logs montrent que le stock_comptoir reste à 20.0 (pas de modification détectée).

### 2. Logs de traçage dans `update_stock_by_location()`

- Détection de tous les appels avec `stock_comptoir`
- Stack trace complète (3 niveaux d'appelants)
- Logs d'erreur avec emoji pour faciliter la détection

**Résultat** : Aucun appel détecté dans les logs fournis.

### 3. Vérifications dans `change_status_to_ready()`

- Vérification avant le commit
- Vérification après le commit avec rechargement depuis la base de données
- Restauration automatique du stock_comptoir si modification détectée

**Résultat** : Les vérifications ne détectent pas de modification, mais le stock_comptoir est quand même décrémenté.

### 4. Vérifications lors de la décrémentation des ingrédients

- Détection si un ingrédient est le même produit que le produit fini
- Vérification que le stock_comptoir n'est pas modifié lors de la décrémentation

**Résultat** : Aucun cas détecté dans les logs.

## 📊 Logs Observés

```
INFO:app:DEBUG - Commande #94 - Produit fini Messemen grand taile doublé - Stock comptoir AVANT: 20.0
INFO:app:TRACE - Commande #94 - Produit Messemen grand taile doublé (ID: 138) - Stock comptoir AVANT: 20.0
COMMANDE CLIENT - Valeur ajoutée (stock réservé): 5.0 pièce de Messemen grand taile doublé (Valeur: 0.00 DA) - Stock comptoir: 20.0 (inchangé)
```

**Observation** : Les logs indiquent que le stock_comptoir reste à 20.0, mais le PDV montre 15.

## 🎯 Points à Vérifier

1. **Vérifier tous les appels à `update_stock_by_location` avec `stock_comptoir`**
   - Chercher dans tout le codebase
   - Vérifier les événements SQLAlchemy
   - Vérifier les triggers de base de données

2. **Vérifier les appels à `mark_as_received_at_shop()`**
   - Cette méthode pourrait être appelée quelque part
   - Elle appelle `_increment_shop_stock_with_value()` qui incrémente le stock_comptoir

3. **Vérifier les événements SQLAlchemy sur le modèle `Product`**
   - `before_update`, `after_update`, `before_flush`, `after_flush`
   - Ces événements pourraient modifier le stock_comptoir

4. **Vérifier les triggers de base de données**
   - Des triggers SQL pourraient modifier le stock_comptoir

5. **Vérifier les appels à `_increment_shop_stock_with_value()` pour les commandes client**
   - Cette méthode ne devrait être appelée que pour `counter_production_request`

6. **Vérifier le cache du PDV**
   - Le PDV pourrait utiliser un cache qui n'est pas mis à jour correctement
   - Mais le dashboard affiche aussi la valeur décrémentée

## 🔧 Scripts de Diagnostic Créés

1. **`scripts/trace_stock_comptoir.py`** : Script de traçage avec monkey patching
2. **`scripts/analyse_stock_comptoir_probleme.py`** : Script d'analyse statique du code
3. **`scripts/trace_simple_stock.py`** : Script simple de traçage réutilisable

## 📝 Fichiers Modifiés

1. `models.py` : Ajout de logs dans `_increment_stock_value_only_for_customer_order()` et `update_stock_by_location()`
2. `app/orders/status_routes.py` : Ajout de vérifications avant et après le commit
3. `app/templates/orders/change_status_form.html` : Ajout du token CSRF

## 🚨 Impact Business

- **Perte de stock disponible** : Les produits réservés pour les clients sont incorrectement décrémentés du stock disponible
- **Erreurs de vente** : Le PDV peut afficher un stock insuffisant alors que le stock réel est disponible
- **Incohérence des données** : Le stock_comptoir ne reflète pas la réalité

## 📅 Date du Problème

- **Détecté** : 03/12/2025
- **Dernière vérification** : 03/12/2025 02:43:54
- **Commande de test** : #94 (5 pièces de "Msamen grand taille doublé")

## 🔍 Prochaines Étapes

1. Exécuter les scripts de diagnostic pour identifier la source exacte
2. Vérifier tous les appels à `update_stock_by_location` avec `stock_comptoir`
3. Vérifier les événements SQLAlchemy
4. Vérifier les triggers de base de données
5. Tester avec une commande client et analyser les logs complets

