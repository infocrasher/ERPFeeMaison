# 📊 Analyse des Encaissements - Tiroir et Ticket

## ✅ Endroits où l'encaissement déclenche Tiroir + Ticket

### 1. **POS - Vente directe** (`/sales/pos/checkout`)
- **Route** : `app/sales/routes.py` ligne 376-506
- **Impression ticket** : ✅ OUI (ligne 481)
- **Ouverture tiroir** : ✅ OUI (ligne 488)
- **Détails** : 
  - Utilise `printer_service.print_ticket()` avec `amount_received` et `change_amount`
  - Utilise `printer_service.open_cash_drawer()`

### 2. **Vente complète** (`/sales/api/complete-sale`)
- **Route** : `app/sales/routes.py` ligne 190-335
- **Impression ticket** : ✅ OUI (ligne 314)
- **Ouverture tiroir** : ✅ OUI (ligne 321)
- **Détails** :
  - Utilise `printer_service.print_ticket()` avec `amount_received` et `change_amount`
  - Utilise `printer_service.open_cash_drawer()`

### 3. **Paiement commande client** (`/orders/<id>/pay`)
- **Route** : `app/orders/routes.py` ligne 569-678
- **Impression ticket** : ✅ OUI (ligne 658)
- **Ouverture tiroir** : ✅ OUI (ligne 659)
- **Détails** :
  - Utilise `printer_service.print_ticket(order.id)` sans montants détaillés
  - Utilise `printer_service.open_cash_drawer()`
  - ⚠️ **Note** : Ne passe pas `amount_received` et `change_amount` au ticket

### 4. **Cashout - Dépôt en banque** (`/sales/cash/cashout`)
- **Route** : `app/sales/routes.py` ligne 722-800
- **Impression reçu** : ✅ OUI (ligne 779)
- **Ouverture tiroir** : ✅ OUI (ligne 785)
- **Détails** :
  - Utilise `printer_service.print_cashout_receipt()` (reçu spécial cashout)
  - Utilise `printer_service.open_cash_drawer()`

## ❌ Endroits où l'encaissement NE déclenche PAS Tiroir + Ticket

### 5. **Paiement dette livreur** (`/sales/cash/delivery_debts/<id>/pay`)
- **Route** : `app/sales/routes.py` ligne 692-721
- **Impression ticket** : ❌ NON
- **Ouverture tiroir** : ❌ NON
- **Détails** :
  - Crée seulement un `CashMovement` de type 'entrée'
  - Ne déclenche aucune impression ni ouverture de tiroir
  - ⚠️ **À CORRIGER** : Devrait imprimer un reçu et ouvrir le tiroir

## 📋 Résumé

| Endroit | Ticket | Tiroir | Statut |
|---------|--------|--------|--------|
| POS Vente directe | ✅ | ✅ | OK |
| Vente complète | ✅ | ✅ | OK |
| Paiement commande | ✅ | ✅ | ⚠️ Manque montants |
| Cashout | ✅ | ✅ | OK |
| Paiement dette livreur | ❌ | ❌ | ❌ À corriger |

## 🔧 Actions recommandées

1. **Corriger le paiement de dette livreur** : Ajouter impression reçu + ouverture tiroir
2. **Améliorer le paiement commande** : Passer `amount_received` et `change_amount` au ticket

