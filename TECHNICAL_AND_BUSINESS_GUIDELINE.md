# 🗂️ ERP Fée Maison : Source of Truth & Guidelines

Ce document est la référence absolue pour comprendre le fonctionnement interne de l'ERP. Toute intervention (humaine ou IA) doit se conformer aux règles décrites ici pour garantir la stabilité du système.

---

## 🏗️ 1. Architecture & Environnement

### Séparation Physique (Hybrid Cloud)
- **Scope A : VPS (Cloud - Ubuntu)** : Exécute Flask, PostgreSQL, Nginx. N'a pas d'accès direct au matériel local.
- **Scope B : Agents Locaux (Windows/Linux)** : Gèrent les imprimantes (via Ngrok) et la pointeuse ZKTeco (via ADMS Push).

### Règles d'Or
- **Zéro Mutation Side-Effect** : Ne jamais modifier `models.py` ou lancer une migration sans plan validé.
- **Pas de librairies locales sur le VPS** : Ne jamais importer `pyusb`, `win32print`, etc., dans le code du module Flask.

---

## 💰 2. Workflow des Revenus (Comptabilité)

La distinction entre la performance et le cash est critique pour le pilotage.

### CA Vente (Performance Commerciale)
- **Règle de Calcul** : Basé sur la date de **Réception/Livraison** de la commande.
- **Approximation Technique** : Champ `Order.due_date`.
- **Méthode** : `RealKpiService.get_daily_kpis()` filtre les ordres où `func.date(Order.due_date) == target_date`.

### CA Caisse (Encaissement Réel)
- **Règle de Calcul** : Flux de trésorerie réel entrant en caisse.
- **Source** : Modèle `CashMovement` où `type` in `['entrée']`.
- **Méthode** : `RealKpiService.get_ca_caisse()`.

---

## 👥 3. Workflow RH & Paie

Le flux suit une chaîne de validation stricte :

1. **Pointage (`Attendance`)** : Poussé par la pointeuse -> `AttendanceRecord`.
2. **Consolidation (`WorkHours`)** : Les pointages sont agrégés par mois.
3. **Calcul (`PayrollCalculation`)** :
    - Génère une écriture de **Charge** (Journal OD) : `641 (Débit)` / `421 (Crédit)`.
4. **Paiement (`Salaries Dashboard`)** :
    - Génère une écriture de **Sortie de Banque** (Journal BQ) : `421 (Débit)` / `512 (Crédit)`.

---

## 📦 4. Workflow Stock & Valorisation (PMP)

L'ERP gère 4 localisations de stock : `comptoir`, `ingredients_local`, `ingredients_magasin`, `consommables`.

### Mise à jour du Stock
- **Achats** : Le stock est incrémenté dès la réception (`status=RECEIVED`).
- **Production Comptoir** : Incrémente `stock_comptoir`.
- **Commandes Clients** : Ne décrémentent le stock que lors de la livraison (pour les produits frais).

### Calcul du PMP (Prix Moyen Pondéré)
- **Formule** : `Nouveau PMP = (Valeur Totale Existante + Valeur Entrée) / (Quantité Totale Existante + Quantité Entrante)`.
- **Sécurité** : La méthode `Product.update_stock_by_location` gère un "déficit de valeur" pour permettre les stocks négatifs temporaires sans fausser le PMP final.

---

## 🛠️ 5. Standards de Développement

### Manipulation des Données
- **Money** : Toujours utiliser le type `Decimal` (importé de `decimal`) et `.quantize(Decimal('0.01'))`. Jamais de `float` pour les calculs financiers complexes.
- **Stock** : Toujours passer par `product.update_stock_by_location(location, qty)` pour assurer la mise à jour synchronisée de la valeur et de la quantité.

### Intégration Comptable
- Toute action impactant la trésorerie ou les charges doit faire appel à `AccountingIntegrationService`.

---

**⚠️ AVERTISSEMENT :** Toute divergence par rapport à ces workflows entraînera des écarts de trésorerie ou des PMP aberrants. En cas de doute, consulter les fichiers d'audit (`tests/audit_...`).
