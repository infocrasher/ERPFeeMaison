# 🏪 ERP Fée Maison – Mémo Technique & Métier

## 📋 Table des Matières
1. [Résumé Métier et Contexte](#1-résumé-métier-et-contexte)
2. [Modules Principaux](#2-modules-principaux)
3. [Architecture Technique](#3-architecture-technique)
4. [Conventions et Bonnes Pratiques](#4-conventions-et-bonnes-pratiques)
5. [Problèmes Récurrents et Solutions](#5-problèmes-récurrents-et-solutions)
6. [Roadmap et TODO](#6-roadmap-et-todo)
7. [Prompts Utiles](#7-prompts-utiles)
8. [État Actuel du Projet](#8-état-actuel-du-projet)

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

### ✅ **POINTAGE ZKTECO** (Terminé - 10/07/2025)
- **Fonctionnalités** : Intégration pointeuse ZKTime.Net, récupération données de pointage
- **Fichiers** : `app/zkteco/`, `CONFIGURATION_POINTEUSE_ZKTECO.md`
- **Logique** : Connexion TCP/IP à la pointeuse, récupération données de présence
- **API** : Endpoint `/zkteco/api/test-attendance` pour tester la connexion
- **Configuration** : IP, port, password configurés dans le fichier de configuration
- **Intégration RH** : Données de pointage utilisées pour les analytics employés

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
- WorkHours : Heures de travail
- Payroll : Bulletins de paie
- OrderIssue : Problèmes de commandes
- AbsenceRecord : Absences et congés

# Modèles livreurs (app/deliverymen/models.py)
- Deliveryman : Livreurs indépendants

# Modèles comptabilité (app/accounting/models.py)
- Account : Plan comptable avec hiérarchie
- Journal : Journaux comptables (VT, AC, CA, BQ, OD)
- JournalEntry : Écritures comptables
- JournalEntryLine : Lignes d'écritures
- FiscalYear : Exercices comptables

# Modèles dettes (models.py)
- DeliveryDebt : Dettes des livreurs
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
├── employees/     # Gestion RH
├── deliverymen/   # Gestion livreurs
├── accounting/    # Comptabilité générale
└── zkteco/        # Intégration pointeuse
```

### 📊 **Base de Données**
- **Moteur** : PostgreSQL (production), SQLite (développement)
- **Migrations** : Alembic avec 15+ migrations
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
valeur_stock_comptoir
valeur_stock_ingredients_magasin
valeur_stock_ingredients_local
valeur_stock_consommables
```

### 🔐 **Authentification**
- **Rôles** : admin, manager, employee
- **Décorateurs** : `@login_required`, `@admin_required`
- **Sessions** : Flask-Login

---

## 5. Problèmes Récurrents et Solutions

### ❌ **Erreurs SQLAlchemy Import Circulaire**
**Problème** : `Table 'users' is already defined for this MetaData instance`
**Solution** : 
- Vérifier les imports dans `models.py`
- Éviter les imports circulaires entre modules
- Utiliser `extend_existing=True` si nécessaire

### ❌ **Erreurs Type Decimal/Float**
**Problème** : `TypeError: unsupported operand type(s) for /: 'decimal.Decimal' and 'float'`
**Solution** :
- Convertir explicitement : `float(decimal_value)`
- Utiliser `Decimal` pour tous les calculs financiers
- Gérer les conversions dans les calculs d'analytics

### ❌ **Erreurs Méthodes Manquantes**
**Problème** : `AttributeError: 'WorkScheduleForm' object has no attribute 'load_from_schedule'`
**Solution** :
- Vérifier les noms des méthodes dans les formulaires
- Utiliser `populate_from_schedule` au lieu de `load_from_schedule`
- Maintenir la cohérence entre formulaires et routes

### ❌ **Erreurs Templates Jinja2**
**Problème** : Variables non définies dans les templates
**Solution** :
- Passer toutes les variables nécessaires depuis les routes
- Utiliser des valeurs par défaut : `{{ variable|default('') }}`
- Vérifier la structure des données passées aux templates

### ❌ **Problèmes Git Push**
**Problème** : Erreur HTTP 500 lors du push vers GitHub
**Solution** :
- Augmenter le buffer HTTP : `git config http.postBuffer 524288000`
- Vérifier la connexion internet
- Essayer avec différents protocoles (HTTPS/SSH)
- Attendre et réessayer (problème temporaire GitHub)

---

## 6. Roadmap et TODO

### 🚀 **Déploiement Production**
- [x] Configuration VPS Ubuntu 24.10
- [x] Scripts de déploiement créés
- [x] Configuration PostgreSQL
- [x] Fichier .env de production
- [ ] Déploiement effectif sur VPS
- [ ] Configuration Nginx
- [ ] Configuration SSL/HTTPS
- [ ] Tests de charge

### 🔧 **Améliorations Techniques**
- [x] Correction erreurs SQLAlchemy
- [x] Correction erreurs templates
- [x] Intégration pointeuse ZKTeco
- [ ] Optimisation performances
- [ ] Tests unitaires complets
- [ ] Documentation API

### 📊 **Nouvelles Fonctionnalités**
- [ ] Module reporting avancé
- [ ] Export données (Excel, PDF)
- [ ] Notifications push
- [ ] API REST complète
- [ ] Application mobile

---

## 7. Prompts Utiles

### 🛠️ **Développement**
```
"Corrige l'erreur SQLAlchemy dans le fichier models.py"
"Optimise les requêtes de base de données pour les analytics"
"Améliore l'interface utilisateur du dashboard RH"
"Implémente l'export Excel des rapports de vente"
```

### 🐛 **Debugging**
```
"Analyse l'erreur TypeError dans les calculs d'analytics"
"Vérifie les imports circulaires dans le module employees"
"Teste la connexion à la pointeuse ZKTeco"
"Valide la cohérence des données de stock"
```

### 📈 **Analytics**
```
"Calcule les KPI de performance par employé"
"Génère un rapport de rentabilité par produit"
"Analyse les tendances de vente mensuelles"
"Évalue l'efficacité des recettes de production"
```

---

## 8. État Actuel du Projet

### 📅 **Dernière Mise à Jour** : 10/07/2025

### ✅ **Modules Fonctionnels**
- **Stock** : 100% opérationnel
- **Achats** : 100% opérationnel  
- **Production** : 100% opérationnel
- **Ventes (POS)** : 100% opérationnel
- **Caisse** : 100% opérationnel
- **Commandes** : 100% opérationnel
- **Livreurs** : 100% opérationnel
- **RH & Paie** : 100% opérationnel
- **Comptabilité** : 100% opérationnel
- **Pointage ZKTeco** : 100% opérationnel

### 🔧 **Corrections Récentes**
- **10/07/2025** : Correction erreurs type Decimal/float dans analytics
- **10/07/2025** : Correction méthode `load_from_schedule` → `populate_from_schedule`
- **09/07/2025** : Intégration pointeuse ZKTeco fonctionnelle
- **09/07/2025** : Correction erreurs import circulaire SQLAlchemy
- **09/07/2025** : Nettoyage fichiers de test et optimisation

### 📊 **Statistiques Projet**
- **Fichiers** : 300 fichiers au total
- **Lignes de code** : ~50,000 lignes
- **Migrations** : 15+ migrations Alembic
- **Templates** : 50+ templates Jinja2
- **Routes** : 100+ endpoints Flask

### 🚀 **Préparation Déploiement**
- **VPS** : Ubuntu 24.10 configuré
- **Base de données** : PostgreSQL configuré
- **Scripts** : Scripts de déploiement prêts
- **Configuration** : Fichier .env de production créé
- **Documentation** : Guides de déploiement complets

### 🎯 **Prochaines Étapes**
1. **Déploiement** : Mise en production sur VPS
2. **Tests** : Validation complète en environnement réel
3. **Formation** : Formation utilisateurs finaux
4. **Maintenance** : Support et améliorations continues

---

## 📞 **Contact et Support**

### 🔧 **Développement**
- **Repository** : https://github.com/infocrasher/fee-maison-erp.git
- **Environnement** : Flask + SQLAlchemy + PostgreSQL
- **Version** : 1.0.0 (Production Ready)

### 📋 **Documentation**
- **Architecture** : `ERP_CORE_ARCHITECTURE.md`
- **Concepts Dashboard** : `GUIDE_CONCEPTS_DASHBOARD.md`
- **Configuration Pointeuse** : `CONFIGURATION_POINTEUSE_ZKTECO.md`
- **Déploiement** : `vps_preparation_guide.md`

---

*Dernière mise à jour : 10/07/2025 - ERP Fée Maison v1.0.0* 