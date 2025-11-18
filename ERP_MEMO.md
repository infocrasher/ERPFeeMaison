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
9. [Résolution Problème Connexion VPS](#9-résolution-problème-connexion-vps)
10. [Documentation Organisée](#10-documentation-organisée)

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

### 👥 Rôles Utilisateurs
| Rôle | Utilisateur | Accès | Permissions |
|------|-------------|-------|-------------|
| **Admin** | Sofiane | Accès total | Tous les modules, configuration système |
| **Gérante** | Amel | Gestion complète | Tous les modules + caisse, prix, recettes |
| **Vendeuse** | Yasmine | Opérationnel | Commandes, caisse, dashboards shop/prod |
| **Production** | Rayan | Lecture seule | Dashboard production uniquement |

---

## 2. Modules Principaux

### ✅ **STOCK** (Terminé)
- **Fonctionnalités** : Suivi par emplacement, valeur, PMP, alertes seuil
- **Fichiers** : `app/stock/`, `models.py` (Product)
- **Logique** : Stock séparé par emplacement, valeur calculée, PMP mis à jour à chaque achat
- **Dashboards** : Vue par emplacement, alertes, mouvements
- **Transferts** : Magasin ↔ Local (formulaire dédié, à vérifier fonctionnement)

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
- **Sessions** : Quotidiennes, ouverture/fermeture par Amel ou Yasmine

### ✅ **COMMANDES** (Terminé)
- **Fonctionnalités** : Commandes clients, production, livraison, encaissement
- **Fichiers** : `app/orders/`, `models.py` (Order, OrderItem)
- **Logique** : Workflow commande → production → réception → livraison → encaissement
- **Encaissement** : Bouton "Encaisser" sur liste commandes et dashboard shop
- **Intégration caisse** : Mouvements automatiques lors de l'encaissement
- **Numérotation** : #21, #22, etc. (système automatique)
- **Statut initial** : "En production" (automatique)
- **Gestion manque** : Commande passe en "En attente" si ingrédient manquant

### ✅ **LIVREURS** (Terminé - 02/07/2025)
- **Fonctionnalités** : Gestion des livreurs indépendants, assignation aux commandes
- **Fichiers** : `app/deliverymen/`, `app/templates/deliverymen/`
- **Logique** : Livreurs séparés des employés, assignation optionnelle aux commandes
- **Modèle** : `Deliveryman` avec `name`, `phone`, relation `orders`
- **Interface** : CRUD complet, intégration dans formulaires de commande
- **Migration** : Table `deliverymen` + colonne `deliveryman_id` dans `orders`
- **Assignation** : Manuelle par Amel
- **Suivi** : Pas de GPS, suivi manuel

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
- **Pointage** : ZKTeco (tous les employés)
- **Heures supplémentaires** : Payées par heure supplémentaire travaillée
- **Plannings** : Pas de système de planning de travail
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

### ✅ **FACTURATION B2B** (Terminé - 19/07/2025)
- **Fonctionnalités** : Gestion des commandes B2B avec produits composés, facturation professionnelle
- **Fichiers** : `app/b2b/`, `app/templates/b2b/`
- **Logique** : Interface dédiée aux commandes B2B avec gestion des produits composés
- **Produits composés** : Sélection de recettes prédéfinies qui génèrent automatiquement plusieurs lignes de produits finis
- **Interface** : Formulaire dynamique avec modal de sélection des produits composés
- **JavaScript** : Gestion dynamique de l'ajout/suppression de lignes, calcul automatique des totaux
- **Templates** : Interface moderne avec Bootstrap 5, modals et formulaires dynamiques
- **Routes** : Gestion complète des commandes B2B avec validation et traitement
- **Intégration** : Compatible avec le système de commandes existant et la gestion des recettes
- **URLs importantes** :
  - Commandes B2B : `/b2b/orders/new`
  - Liste commandes B2B : `/b2b/orders`
  - Gestion produits composés : Interface intégrée dans le formulaire de commande

---

## 3. Architecture Technique

### 📁 **Structure des Déploiements**

#### **Machine Locale (Développement)**
```
fee_maison_gestion_cursor/
├── app/                    # Modules Flask
├── models.py              # Modèles principaux
├── run.py                 # Point d'entrée
├── config.py              # Configuration
├── requirements.txt       # Dépendances
└── .env                   # Variables d'environnement
```

#### **VPS (Production)**
```
/opt/erp/
├── app/                   # Application complète (dépôt Git)
│   ├── app/              # Modules Flask
│   ├── models.py         # Modèles principaux
│   ├── run.py            # Point d'entrée
│   ├── config.py         # Configuration
│   ├── requirements.txt  # Dépendances
│   ├── .env              # Variables d'environnement
│   ├── .git/             # Dépôt Git
│   └── venv/             # Environnement virtuel
└── venv/                 # Environnement virtuel global
```

**Important** : Sur le VPS, le projet complet est dans `/opt/erp/app/` et c'est là que se trouve le dépôt Git.

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
# Blueprints enregistrés
- main : Routes principales
- auth : Authentification (/auth/*)
- products : Produits (/products/*)
- orders : Commandes (/orders/*)
- stock : Stock (/stock/*)
- sales : Ventes et caisse (/sales/*)
- purchases : Achats (/purchases/*)
- recipes : Recettes (/recipes/*)
- employees : RH et paie (/employees/*)
- accounting : Comptabilité (/admin/accounting/*)
- deliverymen : Livreurs (/deliverymen/*)
- dashboards : Dashboards (/dashboards/*)
- zkteco : Pointage (/zkteco/*)
- b2b : Facturation B2B (/b2b/*)
```

---

## 4. Conventions et Bonnes Pratiques

### 📝 **Nommage**
- **Fichiers Python** : snake_case (`models.py`, `routes.py`)
- **Classes** : PascalCase (`User`, `Product`, `Order`)
- **Variables** : snake_case (`user_id`, `product_name`)
- **Fonctions** : snake_case (`get_user`, `create_order`)

### 🗂️ **Organisation**
- **Modèles principaux** : `racine/models.py` (623 lignes)
- **Modèles spécialisés** : `app/module/models.py`
- **Routes** : `app/module/routes.py`
- **Templates** : `app/templates/module/`
- **Statiques** : `app/static/`

### 🔐 **Sécurité**
- **Variables d'environnement** : `.env` (jamais commité)
- **Mots de passe** : Hachés avec bcrypt
- **Sessions** : Gérées par Flask-Login
- **CSRF** : Protection activée

---

## 5. Problèmes Récurrents et Solutions

### 🔄 **Doublons de Modèles**
**Problème** : `CashRegisterSession` défini dans `models.py` ET `app/sales/models.py`
**Solution** : Garder uniquement dans `app/sales/models.py`, supprimer de `models.py`
**Prévention** : Vérifier les imports avant d'ajouter de nouveaux modèles

### 🗄️ **Erreurs Base de Données**
**Problème** : `permission denied for table users`
**Solution** : Vérifier les variables d'environnement PostgreSQL
**Commandes** :
```bash
sudo -u postgres psql -d fee_maison_db -c "SELECT 1;"
sudo systemctl status postgresql
```

### 🔧 **Erreurs Service Systemd**
**Problème** : Service échoue avec statut `1/FAILURE`
**Solution** : Vérifier configuration WSGI et variables d'environnement
**Commandes** :
```bash
sudo journalctl -u erp-fee-maison -f
sudo systemctl status erp-fee-maison
```

### 🌐 **Problèmes de Connexion**
**Problème** : Erreur 500 sur `/auth/login`
**Solution** : Vérifier base de données et variables d'environnement
**Diagnostic** : Utiliser `diagnostic_erp.py`

---

## 6. Roadmap et TODO

### 🚀 **Fonctionnalités Manquantes**
- [ ] **Transferts** : Amélioration du formulaire de transferts
- [ ] **Notifications** : Système d'alertes automatiques
- [ ] **Gestion bugs** : Processus formalisé de gestion des bugs
- [ ] **Plannings** : Système de planning de travail
- [ ] **Suivi GPS** : Intégration GPS pour livreurs

### 📈 **Améliorations Possibles**
- [ ] **Notifications** : Création/modification de commandes
- [ ] **Alertes stock** : Système automatique d'alertes
- [ ] **Rapports livreurs** : Performance et analytics des livreurs
- [ ] **Gestion retards** : Système automatisé de gestion des retards

### 🔧 **Optimisations Techniques**
- [ ] **Cache** : Mise en cache des requêtes fréquentes
- [ ] **Performance** : Optimisation des requêtes base de données
- [ ] **Monitoring** : Métriques de performance
- [ ] **Tests** : Couverture de tests complète

---

## 7. Prompts Utiles

### 🤖 **Pour l'IA Assistant**
```
"Je travaille sur un ERP Flask pour une entreprise de production alimentaire. 
L'application gère : stock multi-emplacements, commandes, production, caisse, RH, comptabilité.
Problème : [description du problème]
Contexte : [détails techniques]
Aide-moi à résoudre ce problème."
```

### 🔍 **Diagnostic Système**
```bash
# Diagnostic complet
python3 diagnostic_erp.py

# Vérification service
sudo systemctl status erp-fee-maison

# Logs en temps réel
sudo journalctl -u erp-fee-maison -f

# Test base de données
sudo -u postgres psql -d fee_maison_db -c "SELECT 1;"
```

---

## 8. État Actuel du Projet

### ✅ **Status Global** : OPÉRATIONNEL
- **Modules** : 11/11 terminés
- **Déploiement** : VPS Ubuntu fonctionnel
- **Base de données** : PostgreSQL opérationnel
- **Intégrations** : ZKTeco, email, comptabilité, facturation B2B

### 📊 **Métriques**
- **Lignes de code** : ~15,000 lignes
- **Modèles** : 15+ modèles principaux
- **Routes** : 50+ endpoints
- **Templates** : 30+ templates

### 🔄 **Dernière Mise à Jour** : 19/07/2025
- Ajout module facturation B2B avec produits composés
- Interface dynamique pour commandes professionnelles
- Intégration complète avec système de recettes existant
- Documentation mise à jour avec nouveau module

---

## 9. Résolution Problème Connexion VPS

### 🚨 **Problème Initial**
- **Erreur** : 500 sur `/auth/login`
- **Message** : `permission denied for table users`
- **Cause** : Variables d'environnement PostgreSQL incorrectes

### ✅ **Solutions Appliquées**

#### **1. Correction Variables d'Environnement**
```bash
# Variables PostgreSQL correctes
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB_NAME=fee_maison_db
```

#### **2. Configuration Service Systemd**
```ini
[Service]
Environment=FLASK_APP=wsgi.py
Environment=FLASK_ENV=production
Environment=POSTGRES_USER=erp_user
Environment=POSTGRES_PASSWORD=${DB_PASSWORD}
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB_NAME=fee_maison_db
Environment=SECRET_KEY=${SECRET_KEY}
ExecStart=/var/www/erp-fee-maison/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 --access-logfile /var/log/erp-fee-maison/access.log --error-logfile /var/log/erp-fee-maison/error.log wsgi:app
```

#### **3. Création Fichier WSGI**
```python
# wsgi.py
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV') or 'production')
application = app
```

#### **4. Nettoyage Secrets Exposés**
- Suppression des secrets de l'historique Git
- Régénération des clés de sécurité
- Mise à jour du `.gitignore`

### 🎯 **Résultat Final**
- **Status** : ✅ OPÉRATIONNEL
- **URL** : `http://erp.declaimers.com:8080`
- **Performance** : Stable
- **Monitoring** : Logs systemd et Nginx

---

## 10. Documentation Organisée

### 📚 **Nouvelle Structure de Documentation**
```
documentation/
├── ERP_COMPLETE_GUIDE.md           # Guide principal (vue d'ensemble)
├── WORKFLOW_METIER_DETAIL.md       # Workflow métier détaillé
├── ARCHITECTURE_TECHNIQUE.md       # Architecture technique
├── DEPLOIEMENT_VPS.md              # Guide de déploiement
├── SECURITE_ET_PERMISSIONS.md      # Sécurité et permissions
├── TROUBLESHOOTING_GUIDE.md        # Guide de dépannage
├── CONFIGURATION_DASHBOARDS.md     # Configuration dashboards
├── CONFIGURATION_POINTEUSE_ZKTECO.md # Configuration pointeuse
└── ERP_MEMO_COMPLET.md             # Ce fichier (référence complète)
```

### 🔗 **Liens vers la Documentation**
- **Guide Principal** : [ERP_COMPLETE_GUIDE.md](documentation/ERP_COMPLETE_GUIDE.md)
- **Workflow Métier** : [WORKFLOW_METIER_DETAIL.md](documentation/WORKFLOW_METIER_DETAIL.md)
- **Architecture** : [ARCHITECTURE_TECHNIQUE.md](documentation/ARCHITECTURE_TECHNIQUE.md)
- **Déploiement** : [DEPLOIEMENT_VPS.md](documentation/DEPLOIEMENT_VPS.md)

### 📋 **Avantages de la Nouvelle Structure**
- ✅ **Organisation** : Documentation structurée et facile à naviguer
- ✅ **Maintenance** : Chaque fichier a un objectif précis
- ✅ **Évolutivité** : Facile d'ajouter de nouveaux guides
- ✅ **Collaboration** : Chaque développeur peut se concentrer sur sa spécialité
- ✅ **Référence rapide** : Le guide principal sert de "cheat sheet"

---

## 📞 Support et Maintenance

### 👥 **Contact Principal**
- **Développeur** : Sofiane (Admin)
- **Gérante** : Amel (Gestion quotidienne)

### 🔧 **Maintenance**
- **Sauvegardes** : Automatiques PostgreSQL
- **Mises à jour** : Via Git pull
- **Monitoring** : Logs systemd et Nginx

### 🚨 **En Cas de Problème**
1. Consulter le [TROUBLESHOOTING_GUIDE.md](documentation/TROUBLESHOOTING_GUIDE.md)
2. Exécuter `python3 diagnostic_erp.py`
3. Vérifier les logs : `sudo journalctl -u erp-fee-maison -f`
4. Contacter le développeur si nécessaire

---

**📖 Ce mémo technique sert de référence complète pour comprendre et maintenir l'ERP Fée Maison.** 