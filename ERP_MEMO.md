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

### ✅ **LIVREURS** (Terminé - 02/07/2025)
- **Fonctionnalités** : Gestion des livreurs indépendants, assignation aux commandes
- **Fichiers** : `app/deliverymen/`, `app/templates/deliverymen/`
- **Logique** : Livreurs séparés des employés, assignation optionnelle aux commandes
- **Modèle** : `Deliveryman` avec `name`, `phone`, relation `orders`
- **Interface** : CRUD complet, intégration dans formulaires de commande
- **Migration** : Table `deliverymen` + colonne `deliveryman_id` dans `orders`

### ✅ **RH & PAIE** (Terminé - 05/07/2025)
- **Fonctionnalités** : Gestion employés, analytics, paie complète, pointage
- **Fichiers** : `app/employees/`, `app/templates/employees/`
- **Logique** : Employés assignés aux commandes, gestion des sessions, calcul paie automatique
- **Module Paie** : Dashboard, heures de travail, calcul automatique, bulletins, analytics
- **Analytics** : KPI par rôle, score composite A+ à D, performance financière
- **Modèles** : `Employee`, `WorkHours`, `Payroll`, `OrderIssue`, `AbsenceRecord`
- **Templates** : 12 templates complets avec interfaces modernes
- **Routes** : 8 routes principales pour gestion complète RH et paie
- **Calculs** : Taux horaire, heures supplémentaires, charges sociales, salaire net
- **Validation** : Système de validation des paies avec traçabilité
- **URLs importantes** :
  - Dashboard Paie : `/employees/payroll/dashboard`
  - Heures de Travail : `/employees/payroll/work-hours`
  - Calcul de Paie : `/employees/payroll/calculate`
  - Bulletins : `/employees/payroll/generate-payslips`
  - Analytics : `/employees/{id}/analytics`
  - Planification : `/employees/{id}/schedule`
  - Résumé Période : `/employees/payroll/period-summary/{month}/{year}`

### ✅ **COMPTABILITÉ** (Terminé - 04/07/2025)
- **Fonctionnalités** : Plan comptable, écritures, journaux, exercices, rapports, calcul profit net
- **Fichiers** : `app/accounting/`, `app/templates/accounting/`, `app/accounting/services.py`
- **Logique** : Comptabilité générale conforme aux normes, balance générale, compte de résultat
- **Modèles** : `Account`, `Journal`, `JournalEntry`, `JournalEntryLine`, `FiscalYear`
- **Architecture** : Classes comptables 1-7, nature débit/crédit, validation écritures
- **Templates** : Dashboard, CRUD complet, balance avec profit net, compte de résultat détaillé
- **Migration** : 5 tables avec préfixe `accounting_`
- **Corrections** : Import circulaire résolu, endpoints manquants ajoutés
- **Rapports** : Balance générale, compte de résultat, calcul automatique profit net
- **Intégrations** : Écritures automatiques depuis ventes, achats, caisse (services.py)
- **Formule profit** : `PROFIT NET = CLASSE 7 (Produits) - CLASSE 6 (Charges)`
- **URLs importantes** :
  - Dashboard : `/admin/accounting/`
  - Rapports : `/admin/accounting/reports`
  - Balance : `/admin/accounting/reports/trial-balance`
  - Compte résultat : `/admin/accounting/reports/profit-loss`

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

# Modèles livreurs (app/deliverymen/models.py)
- Deliveryman : Livreurs indépendants

# Modèles comptabilité (app/accounting/models.py)
- Account : Plan comptable avec hiérarchie
- Journal : Journaux comptables (VT, AC, CA, BQ, OD)
- JournalEntry : Écritures comptables
- JournalEntryLine : Lignes d'écritures
- FiscalYear : Exercices comptables

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
├── employees/     # Gestion RH
├── deliverymen/   # Gestion livreurs
└── accounting/    # Comptabilité générale

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
- **Profit Net** : `CLASSE 7 (Produits) - CLASSE 6 (Charges)`
- **Marge Bénéficiaire** : `(Résultat Net / Chiffre d'Affaires) × 100`
- **Balance comptable** : `Total Débit = Total Crédit` (équilibre obligatoire)

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

### ❌ **Import circulaire module comptabilité**
```python
# Problème : Import des routes dans __init__.py
from . import routes

# Solution : Import dans app/__init__.py
from app.accounting import bp as accounting_blueprint
from app.accounting import routes as accounting_routes
app.register_blueprint(accounting_blueprint)
```

### ❌ **Endpoints manquants dans templates**
```bash
# Solution : Utiliser le script de diagnostic
python test_all_endpoints_and_suggest.py
# Puis ajouter les endpoints manquants dans routes.py
```

### ❌ **Erreur AttributeError sur formulaires**
```python
# Problème : Noms de champs incorrects
form.start_date.data  # Erreur

# Solution : Vérifier les noms dans forms.py
form.date_from.data   # Correct
```

### ❌ **Stock non décrémenté**
- Vérifier la clé d'emplacement (`stock_comptoir`, `stock_ingredients_magasin`, etc.)
- Vérifier le mapping dans `get_stock_by_location_type()`
- Tester avec `print()` pour débugger

### ❌ **Erreur ForeignKey**
- Vérifier que la table référencée existe
- Vérifier le nom de la colonne (`employees.id` vs `users.id`)

### ❌ **Erreur "invalid keyword argument" pour Order**
- **Problème** : `'deliveryman_id' is an invalid keyword argument for Order`
- **Cause** : Le modèle `Order` n'a pas encore la colonne `deliveryman_id`
- **Solution** : Vérifier que la migration a été appliquée correctement
- **Vérification** : `\d orders` dans PostgreSQL pour voir les colonnes

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
  - Commande client uniquement (`order.delivery_debts|length > 0`)
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
  - **RÉSOLUTION URGENTE** : Corriger l'erreur `deliveryman_id` dans le modèle Order
  - Tester le workflow complet : création → production → réception → livraison → encaissement
  - Vérifier l'intégration avec les dettes livreurs
  - Tester les différents scénarios (retrait magasin vs livraison)
  - Optimiser l'interface utilisateur si nécessaire

### [2025-07-01] ✅ Mise en place des tests automatisés Selenium

- **Tests créés:**
  - `test_workflow_selenium.py` : Test de base du workflow complet
  - `advanced_workflow_analyzer.py` : Test avancé avec vérifications logique métier
  - `analyze_test_logs.py` : Analyseur automatique des logs d'erreurs
  - `run_selenium_tests.py` : Script de démarrage rapide

- **Fonctionnalités des tests:**
  - **Test de base** : Simulation complète du workflow via l'interface
  - **Test avancé** : Vérifications automatiques de la logique métier :
    - Incrémentations/décrémentations de stock
    - Calculs de valeurs de stock
    - Création de mouvements de caisse
    - Vérification des montants et descriptions
    - Validation des statuts de commande

- **Vérifications logique métier:**
  - Stock comptoir inchangé lors de création de commande
  - Stock comptoir incrémenté lors du statut "Prête au magasin"
  - Stock comptoir décrémenté lors du statut "Livrée"
  - Mouvement de caisse créé avec montant correct
  - Valeurs de stock mises à jour correctement

- **Rapports générés:**
  - Logs détaillés avec timestamps
  - Rapports JSON avec métriques
  - Analyse automatique des erreurs
  - Suggestions de corrections

- **Utilisation:**
  ```bash
  # Installation et exécution complète
  python run_selenium_tests.py
  
  # Test de base uniquement
  python test_workflow_selenium.py
  
  # Test avancé avec vérifications métier
  python advanced_workflow_analyzer.py
  
  # Analyse des logs
  python analyze_test_logs.py
  ```

- **Prochaines étapes:**
  - Exécuter les tests pour valider le workflow complet
  - Corriger les erreurs identifiées automatiquement
  - Optimiser les performances des tests
  - Ajouter des tests pour d'autres modules (achats, production, etc.)

### [2025-07-02] ✅ Implémentation du système de gestion des livreurs

**🎯 Objectif :** Ajouter un champ "livreur" indépendant des employés pour suivre qui livre quoi, sans lier ce champ à la table des employés.

**📋 Travail réalisé :**

#### **1. Création du modèle Deliveryman**
- **Fichier** : `app/deliverymen/models.py`
- **Modèle** : `Deliveryman` avec champs `name`, `phone`, `created_at`
- **Relations** : `orders` (one-to-many avec Order)
- **Migration** : `5a7dc22f426f_add_deliveryman_table_and_deliveryman_`

#### **2. Routes et interface de gestion**
- **Fichier** : `app/deliverymen/routes.py`
- **Routes CRUD** :
  - `GET /admin/deliverymen` : Liste des livreurs
  - `GET/POST /admin/deliverymen/new` : Créer un livreur
  - `GET/POST /admin/deliverymen/<id>/edit` : Modifier un livreur
  - `POST /admin/deliverymen/<id>/delete` : Supprimer un livreur
- **Sécurité** : Vérification des commandes associées avant suppression

#### **3. Templates d'interface**
- **Liste** : `app/templates/deliverymen/list_deliverymen.html`
  - Tableau avec actions (modifier/supprimer)
  - Modal de confirmation pour suppression
  - Compteur de commandes par livreur
- **Formulaire** : `app/templates/deliverymen/deliveryman_form.html`
  - Formulaire réutilisable (création/modification)
  - Validation côté client et serveur

#### **4. Intégration dans les commandes**
- **Modification formulaires** : `app/orders/forms.py`
  - Ajout champ `deliveryman` dans `OrderForm` et `CustomerOrderForm`
  - Population dynamique des choix de livreurs
  - Champ optionnel (pas obligatoire)
- **Modification routes** : `app/orders/routes.py`
  - Traitement du `deliveryman_id` lors de la création de commande
- **Modification templates** :
  - `app/templates/orders/customer_order_form.html` : Ajout du champ livreur
  - `app/templates/orders/view_order.html` : Affichage du livreur assigné

#### **5. Enregistrement du blueprint**
- **Fichier** : `app/__init__.py`
- **URL prefix** : `/admin` (même espace que les autres modules admin)

#### **6. Intégration dans le menu**
- **Fichier** : `app/templates/base.html`
- **Emplacement** : Menu "Gestion > Livreurs"
- **Icône** : `bi-truck`

**🔧 Problème technique rencontré :**
- **Erreur** : `'deliveryman_id' is an invalid keyword argument for Order`
- **Cause** : Le modèle `Order` n'a pas encore la colonne `deliveryman_id`
- **Statut** : À résoudre demain en vérifiant l'application de la migration

**✅ Fonctionnalités opérationnelles :**
- Interface de gestion des livreurs complète
- Intégration dans les formulaires de commande
- Affichage du livreur dans les vues de commande
- Menu de navigation fonctionnel

**🚀 Prochaines étapes (03/07/2025) :**
1. **Résoudre l'erreur de migration** : Vérifier que la colonne `deliveryman_id` existe dans la table `orders`
2. **Tester la création de commande** avec assignation de livreur
3. **Valider le workflow complet** : création → assignation → affichage
4. **Ajouter des fonctionnalités avancées** si nécessaire (statistiques, planning, etc.)

### [2025-07-03] ✅ Finalisation complète du workflow livreur - Fin de Phase 5

**🎯 Objectif atteint :** Système complet de gestion des livreurs avec workflow de bout en bout.

**📋 Travail finalisé :**

#### **1. Système de statuts complet**
- `waiting_for_pickup` = "En attente de retrait"
- `delivered_unpaid` = "Livrée Non Payé" 
- `ready_at_shop` = "Prêt à livrer"
- Logique de transition selon `delivery_option` (pickup/delivery)

#### **2. Dashboard shop opérationnel**
- **5 sections distinctes** : En Production, En Attente Retrait, Prêt à Livrer, Au Comptoir, Livré Non Payé
- **Boutons conditionnels** : Reçu, Encaisser, Assigner Livreur selon statut et session caisse
- **Statistiques temps réel** : Compteurs par section

#### **3. Page "Assigner livreur" fonctionnelle**
- **Formulaire complet** : Sélection livreur + statut paiement + notes
- **Logique métier** : Distinction produits vs frais de livraison
- **Validation** : CSRF token, validation WTForms
- **Intégration caisse** : Mouvement automatique si payé

#### **4. Système de dettes livreur**
- **Table `delivery_debts`** : Référence correcte vers `deliverymen`
- **Migration** : Correction clé étrangère `employees` → `deliverymen`
- **Logique financière** : Dette = montant produits (sans frais livraison)

#### **5. Tests et validation**
- **Workflow complet testé** : Création → Production → Assignation → Livraison → Encaissement
- **Logs détaillés** : Vérification stock, mouvements caisse, calculs
- **Interface utilisateur** : Navigation fluide, messages clairs

**💾 Sauvegarde effectuée :**
- **Base de données** : `FM_Gestion_DB_20250703_031114.backup`
- **Code source** : `FM_Gestion_APP_20250703_031116.zip`
- **Tables CSV** : 22 tables sauvegardées individuellement

**✅ Phase 5 TERMINÉE - Prêt pour Phase 6**

### [2025-07-05] ✅ Finalisation complète du Module Paie - Phase 7 RH

**🎯 Objectif atteint :** Module paie 100% opérationnel avec toutes les fonctionnalités avancées.

**📋 Fonctionnalités développées :**

#### **1. Dashboard Paie Central**
- **URL** : `/employees/payroll/dashboard`
- **Fonctionnalités** :
  - Vue d'ensemble des KPI paie (employés actifs, paies validées, en attente)
  - Statistiques financières (masse salariale, charges, net à payer)
  - Actions rapides (nouvelles paies, exports, rapports)
  - Liens vers tous les modules paie

#### **2. Gestion des Heures de Travail**
- **URL** : `/employees/payroll/work-hours`
- **Fonctionnalités** :
  - Saisie heures normales et supplémentaires
  - Gestion des absences (maladie, congé, autres)
  - Primes (performance, transport, repas)
  - Déductions (avances, autres)
  - Historique complet des heures par employé

#### **3. Calcul Automatique de Paie**
- **URL** : `/employees/payroll/calculate`
- **Fonctionnalités** :
  - Sélection employé et période
  - Calcul automatique taux horaire (base 173.33h/mois)
  - Majoration heures supplémentaires (50%)
  - Calcul charges sociales automatique :
    - Sécurité sociale : 9%
    - Assurance chômage : 1.5%
    - Retraite : 7%
  - Salaire brut et net calculés automatiquement

#### **4. Génération de Bulletins de Paie**
- **URL** : `/employees/payroll/generate-payslips`
- **Fonctionnalités** :
  - Génération individuelle ou en lot
  - Formats PDF et Excel
  - Paramètres personnalisables
  - Historique des générations

#### **5. Analytics Employé Avancés**
- **URL** : `/employees/{id}/analytics`
- **Fonctionnalités** :
  - Sélecteur de période flexible (semaine, mois, trimestre, semestre, année, personnalisé)
  - KPI adaptés par rôle (Production vs Vente vs Support)
  - Score composite avec grades A+ à D
  - Sections détaillées :
    - Score global avec performance
    - Performance financière (CA, objectifs)
    - Productivité (commandes, taux succès)
    - Qualité & Polyvalence
    - Évolution mensuelle
    - Présence (placeholder pointeuse)

#### **6. Planification et Horaires**
- **URL** : `/employees/{id}/schedule`
- **Fonctionnalités** :
  - Gestion des horaires de travail
  - Planification des équipes
  - Suivi des présences
  - Interface moderne avec calendrier

#### **7. Résumé de Période**
- **URL** : `/employees/payroll/period-summary/{month}/{year}`
- **Fonctionnalités** :
  - Résumé financier par période
  - Statistiques détaillées (employés, paies validées, en attente)
  - Tableaux des paies par statut
  - Actions globales (génération, impression)

**🛠️ Modèles de Données Créés :**

#### **1. Modèles Paie**
```python
# Modèles principaux (app/employees/models.py)
- WorkHours : Heures de travail par employé
- Payroll : Bulletins de paie
- OrderIssue : Problèmes qualité sur commandes
- AbsenceRecord : Enregistrement des absences
```

#### **2. Formulaires WTForms**
```python
# Formulaires (app/employees/forms.py)
- AnalyticsPeriodForm : Sélection période analytics
- OrderIssueForm : Signalement problèmes qualité
- AbsenceRecordForm : Enregistrement absences
```

**🎨 Templates Créés (12 templates) :**

1. **`payroll_dashboard.html`** : Dashboard principal paie
2. **`work_hours.html`** : Gestion heures de travail
3. **`payroll_calculation.html`** : Interface calcul paie
4. **`generate_payslips.html`** : Génération bulletins
5. **`view_payroll.html`** : Affichage bulletin détaillé
6. **`payroll_period_summary.html`** : Résumé période
7. **`employee_analytics.html`** : Analytics employé avancés
8. **`work_schedule.html`** : Planification horaires
9. **Autres templates** : Support et compléments

**📊 Fonctionnalités Avancées :**

#### **1. Système de Scoring**
- **Grades** : A+, A, B+, B, C+, C, D (basé sur performance globale)
- **Critères** : Performance financière, productivité, qualité, présence
- **Adaptation par rôle** : Production, Vente, Support (femme ménage, livreur)

#### **2. Calculs Automatiques**
- **Taux horaire** : Salaire fixe / 173.33 heures
- **Heures supplémentaires** : Majoration 50%
- **Charges sociales** : Calcul automatique selon taux légaux
- **Salaire net** : Brut - charges - déductions + primes

#### **3. Validation et Traçabilité**
- **Système de validation** : Paies validées vs en attente
- **Notes de validation** : Commentaires et justifications
- **Historique** : Suivi complet des modifications

**🔗 Intégration Menu Principal :**
- **Section "Employés & RH"** avec sous-menu "Module Paie"
- **7 liens principaux** : Dashboard, Heures, Calcul, Bulletins, Analytics, Planning, Résumé
- **Navigation fluide** entre tous les modules

**✅ État Final :**
- **100% fonctionnel** : Tous les templates et routes opérationnels
- **Interface moderne** : Bootstrap 5, responsive, UX optimisée
- **Calculs précis** : Logique métier complète et testée
- **Prêt production** : Système complet pour gestion paie

**🚀 Évolutions futures possibles :**
- **Pointeuse biométrique** : Intégration ZKTeco
- **Exports avancés** : Formats comptables, CNSS
- **Notifications** : Alertes paie, échéances
- **Rapports RH** : Statistiques avancées, tableaux de bord

---

## 6. État Actuel du Projet (05/07/2025)

### ✅ **Phase 7 - Module Paie RH : TERMINÉE**
- **Module paie complet** : Dashboard, heures, calcul, bulletins, analytics
- **7 routes principales** : Toutes fonctionnelles avec templates modernes
- **Calculs automatiques** : Taux horaire, heures sup, charges sociales, salaire net
- **Analytics avancés** : Scoring A+ à D, KPI par rôle, performance globale
- **Système de validation** : Paies validées, traçabilité complète
- **Interface moderne** : Bootstrap 5, responsive, UX optimisée
- **Intégration menu** : Section "Employés & RH" avec sous-menu "Module Paie"
- **Prêt production** : Système 100% opérationnel

### 🎯 **Modules Opérationnels**
1. ✅ **Stock** - Gestion multi-emplacements
2. ✅ **Achats** - Incrémentation stock + PMP
3. ✅ **Production** - Recettes et transformation
4. ✅ **Ventes (POS)** - Interface tactile moderne
5. ✅ **Caisse** - Sessions et mouvements
6. ✅ **Commandes** - Workflow complet
7. ✅ **Livreurs** - Gestion indépendante
8. ✅ **Comptabilité** - Module complet
9. ✅ **RH & Paie** - Module complet avec analytics

### 🎉 **Prochaines Étapes**
- **Optimisations** : Performance et cache
- **Rapports** : Tableaux de bord métier avancés
- **Intégrations** : Pointeuse biométrique, exports CNSS
- **Documentation** : Guide utilisateur complet

## 7. Roadmap et TODO

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

### ✅ **PHASE 5 : COMMANDES & LIVREURS (TERMINÉE - 03/07/2025)**
- [x] Système de commandes
- [x] Workflow production complet
- [x] Gestion des livreurs (02/07/2025)
- [x] Système de dettes livreur (03/07/2025)
- [x] Dashboard shop 5 sections (03/07/2025)
- [x] Page assignation livreur (03/07/2025)

### ✅ **PHASE 6 : COMPTABILITÉ (TERMINÉE - 03/07/2025)**
- [x] **Modèles comptables** : Account, Journal, JournalEntry, JournalEntryLine, FiscalYear
- [x] **Plan comptable** : Structure hiérarchique avec classes 1-7, nature débit/crédit
- [x] **Saisie d'écritures** : Interface complète avec validation équilibre
- [x] **Rapports financiers** : Balance générale, dashboard KPIs
- [x] **Templates HTML** : CRUD complet pour toutes les entités
- [x] **Migration BDD** : 5 nouvelles tables avec préfixe accounting_
- [x] **Corrections techniques** : Import circulaire, endpoints manquants, champs formulaires

### ✅ **PHASE 6.5 : DASHBOARD COMPTABILITÉ (TERMINÉE - 04/07/2025)**
- [x] **Calcul profit net** : Formule automatique `Produits (Classe 7) - Charges (Classe 6)`
- [x] **Balance enrichie** : Affichage total produits, charges, résultat net avec type (Bénéfice/Perte)
- [x] **Compte de résultat** : Page dédiée avec détail produits vs charges et marge bénéficiaire
- [x] **Page rapports** : Hub central avec accès balance générale et compte de résultat
- [x] **Templates avancés** : `trial_balance.html`, `profit_loss.html`, `reports.html`
- [x] **Routes nouvelles** : `/reports/profit-loss`, `/reports` avec logique calcul intégrée
- [x] **Intégration dashboard** : Lien "Rapports" ajouté dans dashboard comptable
- [x] **Analyse financière** : Marge bénéficiaire, ratios, visualisation colorée par résultat

### ✅ **PHASE 7 : MODULE PAIE RH (TERMINÉE - 05/07/2025)**
- [x] **Dashboard paie central** : KPI, statistiques, actions rapides
- [x] **Gestion heures travail** : Saisie, absences, primes, déductions
- [x] **Calcul automatique** : Taux horaire, heures sup, charges sociales
- [x] **Génération bulletins** : Formats PDF/Excel, paramètres personnalisables
- [x] **Analytics employé** : Scoring A+ à D, KPI par rôle, performance globale
- [x] **Planification horaires** : Gestion équipes, suivi présences
- [x] **Résumé période** : Statistiques détaillées, actions globales
- [x] **Modèles données** : WorkHours, Payroll, OrderIssue, AbsenceRecord
- [x] **Templates modernes** : 12 templates Bootstrap 5 responsive
- [x] **Intégration menu** : Section "Employés & RH" avec sous-menu "Module Paie"
- [x] **Validation système** : Paies validées, traçabilité, historique
- [x] **Calculs métier** : Base 173.33h/mois, majoration 50%, charges légales

### ⏳ **PHASE 8 : OPTIMISATION (À VENIR)**
- [ ] Performance et cache
- [ ] Sauvegarde automatique
- [ ] Monitoring et logs
- [ ] Formation utilisateurs
- [ ] Intégrations avancées (pointeuse, exports)

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

*Dernière mise à jour : 03/07/2025 - Phase 6 Comptabilité terminée* 