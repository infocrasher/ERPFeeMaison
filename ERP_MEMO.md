# 🏪 ERP Fée Maison – Mémo Technique & Métier

## 📋 Table des Matières
1. [Résumé Métier et Contexte](#1-résumé-métier-et-contexte)
2. [Modules Principaux](#2-modules-principaux)
3. [Architecture Technique](#3-architecture-technique)
4. [Conventions et Bonnes Pratiques](#4-conventions-et-bonnes-pratiques)
5. [Problèmes Récurrents et Solutions](#5-problèmes-récurrents-et-solutions)
6. [Roadmap et TODO](#6-roadmap-et-todo)
7. [Prompts Utiles](#7-prompts-utiles)

---

## 1. Résumé Métier et Contexte

### 🏪 Nature de l'Activité
"Fée Maison" est une entreprise de production et vente de produits alimentaires artisanaux opérant sur deux sites :
- **Magasin principal** : Vente au comptoir et prise de commandes
- **Local de production** : Fabrication des produits (200m du magasin)

### 🎯 Produits Principaux
- Produits à base de semoule (couscous, msamen, etc.)
- Gâteaux traditionnels
- Produits frais et secs

### 📊 Gestion Multi-Emplacements
Le stock est géré sur 4 emplacements distincts :
- **Comptoir** : Stock de vente directe
- **Magasin (Labo A)** : Réserve d'ingrédients
- **Local (Labo B)** : Stock de production
- **Consommables** : Matériel et emballages

---

## 2. Modules Principaux

### ✅ **STOCK** (Terminé)
- **Fonctionnalités** : Suivi par emplacement, valeur, PMP, alertes seuil
- **Fichiers** : `app/stock/`, `models.py` (Product)
- **Logique** : Stock séparé par emplacement, valeur calculée, PMP mis à jour à chaque achat
- **Dashboards** : Vue par emplacement, alertes, mouvements

### ✅ **ACHATS** (Terminé)
- **Fonctionnalités** : Incrémentation stock, calcul PMP, gestion fournisseurs
- **Fichiers** : `app/purchases/`
- **Logique** : À chaque achat → incrémente stock + recalcule PMP + met à jour valeur

### ✅ **PRODUCTION** (Terminé)
- **Fonctionnalités** : Transformation ingrédients → produits finis, décrémentation stock
- **Fichiers** : `app/recipes/`, `models.py` (Recipe, RecipeIngredient)
- **Logique** : Recettes avec ingrédients, coût calculé, production par emplacement

### ✅ **VENTES (POS)** (Terminé)
- **Fonctionnalités** : Interface tactile moderne, panier, validation stock
- **Fichiers** : `app/sales/routes.py` (POS), `templates/sales/pos_interface.html`
- **Logique** : Pas de TVA, total = sous-total, décrémente stock comptoir
- **Interface** : Catégories, recherche, panier dynamique, responsive

### ✅ **CAISSE** (Terminé)
- **Fonctionnalités** : Sessions, mouvements (vente, entrée, sortie, acompte, encaissement commandes)
- **Fichiers** : `app/sales/models.py` (CashRegisterSession, CashMovement)
- **Logique** : Ouverture/fermeture session, historique mouvements, employé responsable
- **Intégration commandes** : Encaissement automatique avec création mouvement de caisse
- **Dettes livreurs** : Gestion des dettes avec encaissement et mouvement de caisse

### ✅ **COMMANDES** (Terminé)
- **Fonctionnalités** : Commandes clients, production, livraison, encaissement
- **Fichiers** : `app/orders/`, `models.py` (Order, OrderItem)
- **Logique** : Workflow commande → production → réception → livraison → encaissement
- **Encaissement** : Bouton "Encaisser" sur liste commandes et dashboard shop
- **Intégration caisse** : Mouvements automatiques lors de l'encaissement

### 🔄 **RH** (En cours)
- **Fonctionnalités** : Gestion employés, droits, pointage
- **Fichiers** : `app/employees/`
- **Logique** : Employés assignés aux commandes, gestion des sessions

### ⏳ **COMPTABILITÉ** (À venir)
- **Fonctionnalités** : Comptabilité générale, rapports, trésorerie
- **Logique** : Intégration avec caisse et achats

---

## 3. Architecture Technique

### 🗄️ **Modèles SQLAlchemy**
```python
# Modèles principaux (models.py)
- User : Authentification et rôles
- Product : Produits avec stock multi-emplacements
- Category : Catégories de produits
- Recipe : Recettes de production
- RecipeIngredient : Ingrédients des recettes
- Order : Commandes clients
- OrderItem : Lignes de commande
- Unit : Unités de mesure

# Modèles caisse (app/sales/models.py)
- CashRegisterSession : Sessions de caisse
- CashMovement : Mouvements de caisse

# Modèles employés (app/employees/models.py)
- Employee : Employés et gestion RH
```

### 🛣️ **Routes Flask (Blueprints)**
```python
# Structure des blueprints
app/
├── auth/          # Authentification
├── admin/         # Administration
├── main/          # Dashboard principal
├── products/      # Gestion produits
├── stock/         # Gestion stock
├── purchases/     # Gestion achats
├── recipes/       # Gestion recettes
├── orders/        # Gestion commandes
├── sales/         # Ventes et POS
└── employees/     # Gestion RH
```

### 📊 **Base de Données**
- **Moteur** : SQLite (développement)
- **Migrations** : Alembic
- **Structure** : Tables normalisées avec relations
- **Stock** : Colonnes séparées par emplacement + valeur

### 🎨 **Frontend**
- **Framework** : Bootstrap 5 + CSS personnalisé
- **Templates** : Jinja2
- **JavaScript** : Vanilla JS + AJAX
- **Responsive** : Mobile-first design
- **POS** : Interface tactile optimisée

---

## 4. Conventions et Bonnes Pratiques

### 📝 **Nommage**
- **Code** : Anglais (variables, fonctions, classes)
- **UI** : Français (labels, messages, interface)
- **Base de données** : Snake_case
- **Routes** : Kebab-case

### 💾 **Gestion Stock**
```python
# Emplacements de stock
stock_comptoir          # Vente directe
stock_ingredients_magasin  # Réserve (Labo A)
stock_ingredients_local    # Production (Labo B)
stock_consommables      # Matériel/emballages

# Valeurs de stock
valeur_stock_ingredients_magasin
valeur_stock_ingredients_local
total_stock_value
```

### 🧮 **Calculs Métier**
- **PMP** : Prix Moyen Pondéré recalculé à chaque achat
- **Valeur stock** : Stock × PMP par emplacement
- **POS** : Pas de TVA, total = sous-total
- **Commandes** : Workflow avec statuts

### 🔧 **Développement**
- **Linter Cursor** : Ajouter en haut des templates Jinja2 :
  ```html
  <!-- eslint-disable -->
  <!-- @ts-nocheck -->
  ```
- **Migrations** : Une migration par modification de modèle
- **Tests** : Scripts de test dans `/tests/`

---

## 5. Problèmes Récurrents et Solutions

### ❌ **Erreur Alembic "Working outside of application context"**
```bash
# Solution : Utiliser flask db au lieu d'alembic directement
flask db revision --autogenerate -m "description"
flask db upgrade
```

### ❌ **Linter Cursor sur templates Jinja2**
```html
<!-- Solution : Ajouter en haut du fichier -->
<!-- eslint-disable -->
<!-- @ts-nocheck -->
```

### ❌ **Stock non décrémenté**
- Vérifier la clé d'emplacement (`stock_comptoir`, `stock_ingredients_magasin`, etc.)
- Vérifier le mapping dans `get_stock_by_location_type()`
- Tester avec `print()` pour débugger

### ❌ **Erreur ForeignKey**
- Vérifier que la table référencée existe
- Vérifier le nom de la colonne (`employees.id` vs `users.id`)

### ❌ **Problème de migration**
```bash
# Si migration cassée
flask db stamp head
flask db migrate
flask db upgrade
```

### [2025-06-30] Bug persistant sur la création de recette (product_id)

- **Contexte :**
  - Lors de la création d'une recette, tout fonctionne côté front (autocomplétion, coût affiché, champs bien remplis).
  - À la soumission, le serveur affiche :
    - "Le formulaire contient des erreurs. Veuillez les corriger."
    - Erreur de validation WTForms : {'ingredients': [{'product_id': ['Veuillez choisir un ingrédient valide.']}, {}, {}, ...]}
  - Après POST, tous les coûts ligne passent à 0 DA.

- **Actions déjà tentées :**
  - Vérification du JS/autocomplétion : le champ caché est bien rempli avant POST.
  - Correction du type du champ `product_id` (IntegerField + filtre int/None).
  - Vérification du template : les noms des champs sont corrects.
  - Le problème persiste malgré le filtre WTForms.

- **Hypothèses restantes :**
  - Problème de structure du POST (données mal envoyées ou mal reconstruites par WTForms ?)
  - Problème de synchronisation entre le JS et le FieldList WTForms lors du POST.
  - Autre bug dans la logique de parsing côté Flask/WTForms.

- **À faire à la reprise :**
  - Inspecter le payload POST exact envoyé au serveur (via l'onglet Réseau).
  - Ajouter des logs côté Flask pour afficher la valeur reçue pour chaque `product_id` dans `form.ingredients.data`.
  - Vérifier la reconstruction du FieldList côté serveur.

### [2025-07-01] Résolution du bug de validation du champ product_id dans le formulaire de recette

- **Cause trouvée :**
  - Le champ caché `product_id` généré par WTForms n'avait pas la classe `ingredient-id-input` attendue par le JavaScript.
  - Résultat : le JS ne remplissait jamais la valeur du champ caché lors de la sélection d'un ingrédient, donc le POST envoyait une valeur vide et la validation WTForms échouait systématiquement.

- **Solution appliquée :**
  - Ajout de `class_='ingredient-id-input'` dans le template Jinja sur le champ caché `product_id`.
  - Le JS peut désormais remplir correctement la valeur lors de la sélection d'un ingrédient.
  - La validation WTForms passe, la recette est créée et tous les coûts sont calculés correctement.

- **À retenir :**
  - Toujours synchroniser les classes JS attendues entre les templates générés par WTForms et les templates JS dynamiques.
  - Vérifier systématiquement la valeur des champs cachés dans le DOM avant soumission en cas de bug de validation côté serveur.

### [2025-07-01] ✅ Finalisation de l'intégration caisse-commandes

- **Fonctionnalités ajoutées :**
  - Bouton "Encaisser" sur la liste des commandes (`list_orders.html`)
  - Bouton "Encaisser" sur le dashboard shop (`shop_dashboard.html`)
  - Bouton "Encaisser" sur la fiche commande (`view_order.html`)
  - Vérification automatique si commande déjà encaissée
  - Création automatique du mouvement de caisse lors de l'encaissement

- **Logique d'affichage :**
  - Commande client uniquement (`order_type == 'customer_order'`)
  - Session de caisse ouverte (`cash_session_open`)
  - Pas de mouvement de caisse existant pour cette commande
  - Confirmation utilisateur avant encaissement

- **Corrections techniques :**
  - Correction erreur template `view_order.html` : vérification `order.delivery_debts|length > 0`
  - Ajout vérifications sécurisées dans tous les templates
  - Passage de `cash_session_open` aux routes `list_orders` et `shop_dashboard`

- **Workflow complet :**
  1. Commande client créée → Statut "En attente" ou "En production"
  2. Production terminée → Statut "Prête au magasin"
  3. Réception au magasin → Statut "Prête à livrer"
  4. Livraison → Statut "Livrée"
  5. Encaissement → Mouvement de caisse créé automatiquement

- **Prochaines étapes (demain) :**
  - Tester le workflow complet : création → production → réception → livraison → encaissement
  - Vérifier l'intégration avec les dettes livreurs
  - Tester les différents scénarios (retrait magasin vs livraison)
  - Optimiser l'interface utilisateur si nécessaire

---

## 6. Roadmap et TODO

### ✅ **PHASE 1 : FOUNDATION (TERMINÉE)**
- [x] Infrastructure Flask + SQLAlchemy
- [x] Modèles de base (User, Product, Category)
- [x] Authentification et rôles
- [x] Interface d'administration

### ✅ **PHASE 2 : GESTION STOCK (TERMINÉE)**
- [x] Stock multi-emplacements
- [x] Valeur de stock et PMP
- [x] Alertes et seuils
- [x] Dashboards par emplacement

### ✅ **PHASE 3 : ACHATS & PRODUCTION (TERMINÉE)**
- [x] Gestion des achats
- [x] Calcul automatique PMP
- [x] Système de recettes
- [x] Production et transformation

### ✅ **PHASE 4 : VENTES & POS (TERMINÉE)**
- [x] Interface POS moderne
- [x] Gestion de caisse
- [x] Sessions et mouvements
- [x] Validation stock

### 🔄 **PHASE 5 : COMMANDES & RH (EN COURS)**
- [x] Système de commandes
- [x] Workflow production
- [ ] Gestion RH complète
- [ ] Pointage et planning

### ⏳ **PHASE 6 : COMPTABILITÉ (À VENIR)**
- [ ] Comptabilité générale
- [ ] Rapports financiers
- [ ] Trésorerie
- [ ] Bilan et compte de résultat

### ⏳ **PHASE 7 : OPTIMISATION (À VENIR)**
- [ ] Performance et cache
- [ ] Sauvegarde automatique
- [ ] Monitoring
- [ ] Formation utilisateurs

---

## 7. Prompts Utiles

### 🎨 **Design et UI**
```
"Modern POS interface design for bakery, touch-friendly, responsive, 
basket management, product categories, no VAT calculation, French style, 
Bootstrap 5, mobile-first"
```

### 🔧 **Développement Cursor**
```
"Ajoute les directives linter en haut des templates Jinja2 pour éviter 
les erreurs JavaScript/TypeScript dans Cursor"
```

### 📊 **Base de Données**
```
"Crée une migration Alembic pour ajouter le champ X au modèle Y, 
avec gestion des valeurs par défaut et contraintes"
```

### 🧪 **Tests**
```
"Crée un script de test pour vérifier que la route X fonctionne 
correctement avec les données Y et retourne Z"
```

---

## 📚 **Fichiers de Référence**

### 📄 **Architecture**
- `ERP_CORE_ARCHITECTURE.md` : Architecture détaillée
- `structure.txt` : Structure complète du projet
- `models.py` : Tous les modèles SQLAlchemy

### 🔧 **Configuration**
- `config.py` : Configuration Flask
- `extensions.py` : Extensions Flask
- `alembic.ini` : Configuration migrations

### 🧪 **Tests**
- `tests/` : Tests unitaires
- `test_*.py` : Scripts de test spécifiques
- `run_diagnostics.py` : Diagnostic complet

### 💾 **Sauvegarde**
- `Save_Project.py` : Script de sauvegarde
- `backup_*.sql` : Sauvegardes base de données

---

## 🚀 **Commandes Utiles**

```bash
# Démarrage
flask run

# Migrations
flask db revision --autogenerate -m "description"
flask db upgrade

# Tests
python -m pytest tests/
python run_diagnostics.py

# Sauvegarde
python Save_Project.py
```

---

**💡 À chaque évolution majeure, pense à mettre à jour ce fichier !**

*Dernière mise à jour : 01/07/2025* 