# Prompt pour IA : Recherche du problème de décrémentation du stock_comptoir

## Contexte

Je travaille sur une application Flask/SQLAlchemy de gestion ERP. J'ai un problème critique où le `stock_comptoir` (stock disponible à la vente) est incorrectement décrémenté lors de la réception d'une commande client.

## Problème

Lors de la réception d'une commande client (changement de statut de `in_production` à `ready_at_shop`), le `stock_comptoir` est décrémenté alors qu'il ne devrait PAS l'être. Les produits des commandes client sont réservés pour le client et ne doivent pas être disponibles à la vente.

### Symptômes

- **Avant réception** : Stock comptoir = 20 pièces
- **Après réception** : Stock comptoir = 15 pièces (décrémentation de 5, qui correspond à la quantité de la commande)
- **Logs** : Les logs indiquent que le stock_comptoir reste à 20.0 (pas de modification détectée dans le code Python)
- **PDV** : Le point de vente affiche la valeur décrémentée (15 au lieu de 20)

### Code Concerné

1. **Route de réception** : `app/orders/status_routes.py` - fonction `change_status_to_ready()`
2. **Méthode pour commandes client** : `models.py` - méthode `_increment_stock_value_only_for_customer_order()`
3. **Méthode de mise à jour** : `models.py` - méthode `update_stock_by_location()`

### Logique Attendue

Pour une **commande client** (`order_type = 'customer_order'`):
- ✅ La **valeur du stock** doit être mise à jour (pour la comptabilité)
- ❌ Le **stock_comptoir** ne doit **PAS** être modifié (produits réservés)

Pour un **ordre de production** (`order_type = 'counter_production_request'`):
- ✅ Le **stock_comptoir** doit être incrémenté (produits disponibles à la vente)

## Tâche

Analysez le codebase pour identifier **TOUS** les endroits où le `stock_comptoir` pourrait être modifié lors de la réception d'une commande client. Recherchez :

1. **Tous les appels à `update_stock_by_location('stock_comptoir', ...)` avec une valeur négative**
   - Cherchez dans tout le codebase
   - Vérifiez les conditions qui pourraient faire que `location_key` soit `'stock_comptoir'` au lieu de `'stock_ingredients_magasin'` ou `'stock_ingredients_local'`

2. **Tous les appels à `_increment_shop_stock_with_value()` pour les commandes client**
   - Cette méthode ne devrait être appelée que pour `counter_production_request`
   - Vérifiez si elle est appelée par erreur pour `customer_order`

3. **Tous les appels à `mark_as_received_at_shop()`**
   - Cette méthode pourrait être appelée quelque part et modifier le stock_comptoir

4. **Événements SQLAlchemy sur le modèle `Product`**
   - `before_update`, `after_update`, `before_flush`, `after_flush`
   - Ces événements pourraient modifier le stock_comptoir

5. **Modifications directes de `stock_comptoir`**
   - `product.stock_comptoir = ...`
   - `product.stock_comptoir -= ...`
   - `product.stock_comptoir += ...`
   - `setattr(product, 'stock_comptoir', ...)`

6. **Cas où un ingrédient est le même produit que le produit fini**
   - Si un ingrédient dans la recette est le même produit que le produit fini
   - Lors de la décrémentation des ingrédients, vérifiez si le stock_comptoir est modifié par erreur

7. **Triggers de base de données**
   - Des triggers SQL pourraient modifier le stock_comptoir

8. **Cache ou autres mécanismes**
   - Vérifiez si un cache ou un autre mécanisme pourrait causer ce problème

## Structure du Code

### Modèle Product

```python
class Product(db.Model):
    stock_comptoir = db.Column(db.Float, default=0.0, nullable=False)
    
    def update_stock_by_location(self, location_key: str, quantity_change: float, ...):
        # Met à jour le stock à un emplacement spécifique
        # Si location_key == 'stock_comptoir' et quantity_change < 0, décrémente le stock_comptoir
```

### Modèle Order

```python
class Order(db.Model):
    order_type = db.Column(db.String(50))  # 'customer_order' ou 'counter_production_request'
    
    def _increment_stock_value_only_for_customer_order(self):
        # Met à jour uniquement la valeur (PAS le stock_comptoir)
    
    def _increment_shop_stock_with_value(self):
        # Incrémente le stock_comptoir (UNIQUEMENT pour counter_production_request)
```

### Route de réception

```python
@status_bp.route('/<int:order_id>/change-status-to-ready', methods=['POST'])
def change_status_to_ready(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Décrémente les ingrédients
    for order_item in order.items:
        # ... décrémente les ingrédients ...
        ingredient_product.update_stock_by_location(stock_attr, -quantity_to_decrement)
    
    # Incrémente les produits finis
    if order.order_type == 'counter_production_request':
        order._increment_shop_stock_with_value()  # ✅ Correct
    else:
        order._increment_stock_value_only_for_customer_order()  # ✅ Devrait être correct
    
    db.session.commit()
```

## Points d'Attention

1. **Le problème se produit APRÈS les vérifications dans le code Python**
   - Les logs montrent que le stock_comptoir reste à 20.0 dans le code
   - Mais le PDV et le dashboard affichent 15

2. **La décrémentation correspond exactement à la quantité de la commande**
   - Commande de 5 → Décrémentation de 5
   - Cela suggère un appel direct avec la quantité de la commande

3. **Les logs ne détectent pas la modification**
   - Des logs ont été ajoutés dans `update_stock_by_location()` pour détecter tous les appels avec `stock_comptoir`
   - Aucun appel n'est détecté dans les logs fournis

## Résultat Attendu

Fournissez une liste complète de :
1. **Tous les endroits** où le `stock_comptoir` pourrait être modifié
2. **Tous les chemins de code** possibles qui pourraient causer ce problème
3. **Des suggestions de corrections** pour chaque cas identifié
4. **Des tests à effectuer** pour confirmer chaque hypothèse

## Fichiers à Analyser

- `models.py` : Modèles Product et Order
- `app/orders/status_routes.py` : Route de réception
- `app/orders/routes.py` : Autres routes de commandes
- Tous les fichiers qui appellent `update_stock_by_location()`
- Tous les fichiers qui modifient `stock_comptoir` directement
- Configuration SQLAlchemy pour les événements

## Instructions Spécifiques

1. **Utilisez la recherche sémantique** pour trouver tous les endroits pertinents
2. **Analysez le flux d'exécution** complet lors de la réception d'une commande client
3. **Vérifiez les conditions** qui pourraient faire que le mauvais chemin de code soit exécuté
4. **Identifiez les race conditions** ou problèmes de timing possibles
5. **Vérifiez les side effects** des opérations SQLAlchemy

Merci de fournir une analyse complète et détaillée.

