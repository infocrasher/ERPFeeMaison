# ERP Fée Maison – Documentation Technique Complète

## 📋 Table des Matières

1. [Présentation Générale](#1-présentation-générale)
2. [Structure du Projet](#2-structure-du-projet)
3. [Modules Fonctionnels](#3-modules-fonctionnels)
4. [Flux Métier](#4-flux-métier)
5. [Base de Données](#5-base-de-données)
6. [Services et Intégrations](#6-services-et-intégrations)
7. [Interface & Dashboards](#7-interface--dashboards)
8. [Sécurité & Utilisateurs](#8-sécurité--utilisateurs)
9. [Déploiement & Maintenance](#9-déploiement--maintenance)
10. [Annexes](#10-annexes)

---

## 1. Présentation Générale

### Objectif du Projet

L'ERP Fée Maison est un système de gestion intégré développé spécifiquement pour une entreprise de production et vente de produits alimentaires artisanaux. Il gère l'ensemble des opérations métier depuis la production jusqu'à la vente, en passant par la gestion des stocks, la comptabilité et les ressources humaines.

### Technologies Principales

- **Backend** : Flask (Python 3.13)
- **Base de données** : PostgreSQL (production) / SQLite (développement)
- **ORM** : SQLAlchemy avec Flask-Migrate (Alembic)
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentification** : Flask-Login avec gestion des rôles
- **Templates** : Jinja2 avec macros personnalisées
- **Intégrations** : ESC/POS (imprimante), ZKTeco (pointeuse)

### Architecture Globale

```mermaid
graph TB
    subgraph "Frontend"
        A[Interface Web] --> B[Dashboards]
        A --> C[POS Interface]
        A --> D[Admin Panel]
    end
    
    subgraph "Backend Flask"
        E[Routes & Controllers] --> F[Models SQLAlchemy]
        E --> G[Services]
        E --> H[Forms WTForms]
    end
    
    subgraph "Base de Données"
        I[(PostgreSQL)]
        F --> I
    end
    
    subgraph "Intégrations Matérielles"
        J[Imprimante ESC/POS]
        K[Pointeuse ZKTeco]
        L[Tiroir-caisse]
    end
    
    subgraph "Services Externes"
        M[Agent d'impression]
        N[API ZKTeco]
    end
    
    G --> J
    G --> K
    G --> L
    
    J --> M
    K --> N
```

---

## 2. Structure du Projet

### Arborescence du Code

```
fee_maison_gestion_cursor/
├── app/                          # Application Flask principale
│   ├── __init__.py              # Configuration et enregistrement des blueprints
│   ├── accounting/              # Module comptabilité
│   ├── admin/                   # Administration système
│   ├── auth/                    # Authentification et autorisation
│   ├── b2b/                     # Facturation B2B
│   ├── consumables/             # Gestion des consommables
│   ├── customers/               # Gestion des clients
│   ├── dashboards/              # Tableaux de bord
│   ├── deliverymen/             # Gestion des livreurs
│   ├── employees/               # RH et paie
│   ├── hr/                      # Ressources humaines
│   ├── inventory/               # Inventaires physiques
│   ├── main/                    # Routes principales
│   ├── orders/                  # Gestion des commandes
│   ├── products/                # Catalogue produits
│   ├── purchases/               # Achats et fournisseurs
│   ├── recipes/                 # Recettes de production
│   ├── sales/                   # Point de vente (POS)
│   ├── services/                # Services utilitaires
│   ├── stock/                   # Gestion des stocks
│   ├── suppliers/               # Fournisseurs
│   ├── templates/               # Templates HTML
│   ├── utils/                   # Utilitaires
│   └── zkteco/                  # Intégration pointeuse
├── models.py                    # Modèles de base de données
├── config.py                    # Configuration de l'application
├── extensions.py                # Extensions Flask
├── run.py                       # Point d'entrée de l'application
└── requirements.txt             # Dépendances Python
```

### Modules et Blueprints

L'application utilise l'architecture Blueprint de Flask pour organiser les fonctionnalités :

| Module | Blueprint | URL Prefix | Description |
|--------|-----------|------------|-------------|
| **Main** | `main` | `/` | Routes principales et dashboard |
| **Auth** | `auth` | `/auth` | Authentification et autorisation |
| **Products** | `products` | `/admin/products` | Gestion du catalogue |
| **Orders** | `orders` | `/admin/orders` | Commandes clients |
| **Recipes** | `recipes` | `/admin/recipes` | Recettes de production |
| **Stock** | `stock` | `/admin/stock` | Gestion des stocks |
| **Purchases** | `purchases` | `/admin/purchases` | Achats et fournisseurs |
| **Sales** | `sales` | `/sales` | Point de vente (POS) |
| **Employees** | `employees` | `/employees` | RH et gestion du personnel |
| **Accounting** | `accounting` | `/admin/accounting` | Comptabilité |
| **Inventory** | `inventory` | `/admin/inventory` | Inventaires physiques |
| **Consumables** | `consumables` | `/admin/consumables` | Gestion des consommables |
| **B2B** | `b2b` | `/admin/b2b` | Facturation B2B |
| **ZKTeco** | `zkteco` | `/zkteco` | Intégration pointeuse |

---

## 3. Modules Fonctionnels

### 3.1 Comptabilité

**Rôle métier** : Gestion complète de la comptabilité avec plan comptable, écritures, rapports et états financiers.

**Modèles principaux** :
- `Account` : Plan comptable (comptes de bilan et de résultat)
- `JournalEntry` : Écritures comptables
- `AccountingPeriod` : Périodes comptables
- `Expense` : Gestion des dépenses

**Routes principales** (`app/accounting/routes.py`) :
- `/admin/accounting/dashboard` : Tableau de bord comptable
- `/admin/accounting/entries/create` : Création d'écritures
- `/admin/accounting/reports/trial_balance` : Balance de vérification
- `/admin/accounting/reports/profit_loss` : Compte de résultat

**Templates** : `app/templates/accounting/`
- Dashboard comptable avec indicateurs clés
- Formulaires d'écritures comptables
- Rapports financiers (balance, résultat)

### 3.2 RH & Paie

**Rôle métier** : Gestion complète des ressources humaines, pointage, calcul de paie et bulletins de salaire.

**Modèles principaux** :
- `Employee` : Employés avec informations personnelles et contractuelles
- `AttendanceRecord` : Enregistrements de pointage
- `PayrollPeriod` : Périodes de paie
- `Payslip` : Bulletins de salaire

**Routes principales** (`app/employees/routes.py`) :
- `/employees/dashboard` : Dashboard RH
- `/employees/attendance` : Gestion des présences
- `/employees/payroll/calculate` : Calcul de paie
- `/employees/payslips` : Bulletins de salaire

**Intégration ZKTeco** : Synchronisation automatique des pointages depuis la pointeuse biométrique.

### 3.3 Achats

**Rôle métier** : Gestion des achats, fournisseurs, réceptions et factures fournisseurs.

**Modèles principaux** :
- `Supplier` : Fournisseurs avec informations commerciales
- `Purchase` : Commandes d'achat
- `PurchaseItem` : Articles commandés
- `PurchasePayment` : Paiements fournisseurs

**Routes principales** (`app/purchases/routes.py`) :
- `/admin/purchases/list` : Liste des achats
- `/admin/purchases/new` : Nouvel achat
- `/admin/purchases/<id>/receive` : Réception de marchandises

### 3.4 Ventes (POS)

**Rôle métier** : Point de vente avec gestion de caisse, tickets, et intégration matérielle.

**Modèles principaux** :
- `Order` : Commandes clients
- `OrderItem` : Articles commandés
- `CashRegisterSession` : Sessions de caisse
- `CashMovement` : Mouvements de caisse

**Routes principales** (`app/sales/routes.py`) :
- `/sales/pos` : Interface POS
- `/sales/cash/open` : Ouverture de caisse
- `/sales/cash/close` : Fermeture de caisse
- `/sales/cashout` : Sortie de caisse

**Intégrations matérielles** :
- Imprimante thermique ESC/POS pour tickets
- Tiroir-caisse automatique
- Gestion des sessions de caisse

### 3.5 Production / Recettes

**Rôle métier** : Gestion des recettes de production, calcul des coûts et planification.

**Modèles principaux** :
- `Recipe` : Recettes de production
- `RecipeIngredient` : Ingrédients des recettes
- `ProductionOrder` : Ordres de production

**Routes principales** (`app/recipes/routes.py`) :
- `/admin/recipes/list` : Liste des recettes
- `/admin/recipes/create` : Création de recette
- `/admin/recipes/<id>/view` : Détail d'une recette

### 3.6 Stock

**Rôle métier** : Gestion multi-emplacements des stocks avec alertes et transferts.

**Modèles principaux** :
- `Product` : Produits avec stocks multi-emplacements
- `StockMovement` : Mouvements de stock
- `StockTransfer` : Transferts entre emplacements

**Emplacements gérés** :
- Comptoir (vente directe)
- Magasin (réserve d'ingrédients)
- Local (stock de production)
- Consommables (emballages)

### 3.7 Inventaires Physiques

**Rôle métier** : Inventaires mensuels, gestion des écarts et ajustements automatiques.

**Modèles principaux** :
- `Inventory` : Sessions d'inventaire
- `InventoryItem` : Articles inventoriés
- `DailyWaste` : Déclarations d'invendus quotidiens
- `WeeklyComptoirInventory` : Inventaires hebdomadaires du comptoir

**Routes principales** (`app/inventory/routes.py`) :
- `/admin/inventory/create` : Création d'inventaire
- `/admin/inventory/<id>/count` : Saisie des quantités
- `/admin/inventory/waste/daily` : Déclaration d'invendus

### 3.8 Gestion des Consommables

**Rôle métier** : Suivi des consommables (emballages) avec estimation basée sur les ventes.

**Modèles principaux** :
- `ConsumableUsage` : Utilisation des consommables
- `ConsumableAdjustment` : Ajustements manuels
- `ConsumableRecipe` : Recettes de consommables par produit fini

**Routes principales** (`app/consumables/routes.py`) :
- `/admin/consumables/` : Dashboard consommables
- `/admin/consumables/usage/create` : Enregistrement d'usage
- `/admin/consumables/recipes/create` : Création de recettes

### 3.9 Clients / Fournisseurs

**Rôle métier** : Gestion centralisée des clients et fournisseurs avec historique.

**Modèles principaux** :
- `Customer` : Clients particuliers
- `B2BClient` : Clients entreprises
- `Supplier` : Fournisseurs

**Routes principales** :
- `/admin/customers/` : Gestion des clients
- `/admin/suppliers/` : Gestion des fournisseurs

### 3.10 Dashboards & Reporting

**Rôle métier** : Tableaux de bord opérationnels et stratégiques avec indicateurs temps réel.

**Dashboards disponibles** :
- **Opérationnel quotidien** : Ventes, stocks, production
- **Stratégique mensuel** : Performance, rentabilité, tendances
- **Production** : Planning, recettes, coûts
- **Magasin** : Ventes, stocks, alertes

**Routes principales** (`app/dashboards/routes.py`) :
- `/dashboards/daily` : Dashboard quotidien
- `/dashboards/monthly` : Dashboard mensuel
- `/dashboards/production` : Dashboard production

### 3.11 Administration & Sécurité

**Rôle métier** : Administration système, gestion des utilisateurs et configuration.

**Fonctionnalités** :
- Gestion des utilisateurs et rôles
- Configuration de l'imprimante
- Monitoring système
- Sauvegardes

**Routes principales** (`app/admin/routes.py`) :
- `/admin/dashboard` : Dashboard administrateur
- `/admin/printer` : Configuration imprimante

---

## 4. Flux Métier

### 4.1 Flux Principal : Achat → Stock → Vente → Comptabilité

```mermaid
graph LR
    A[Achat Fournisseur] --> B[Réception Marchandises]
    B --> C[Mise à jour Stock]
    C --> D[Production]
    D --> E[Vente POS]
    E --> F[Sortie Stock]
    F --> G[Écriture Comptable]
```

### 4.2 Flux RH : Pointage → Paie → Comptabilité

```mermaid
graph LR
    A[Pointage ZKTeco] --> B[Calcul Heures]
    B --> C[Calcul Paie]
    C --> D[Bulletin de Salaire]
    D --> E[Écriture Comptable]
```

### 4.3 Flux POS : Vente → Caisse → Journal

```mermaid
graph LR
    A[Interface POS] --> B[Calcul Total]
    B --> C[Impression Ticket]
    C --> D[Ouverture Tiroir]
    D --> E[Enregistrement Vente]
    E --> F[Écriture Comptable]
```

### 4.4 Flux Inventaire : Comptage → Écarts → Ajustements

```mermaid
graph LR
    A[Création Inventaire] --> B[Comptage Physique]
    B --> C[Calcul Écarts]
    C --> D[Validation]
    D --> E[Ajustement Stock]
    E --> F[Écriture Comptable]
```

---

## 5. Base de Données

### 5.1 Schéma Relationnel Synthétique

```mermaid
erDiagram
    User ||--o{ Order : creates
    Category ||--o{ Product : contains
    Product ||--o{ OrderItem : "ordered in"
    Product ||--o{ RecipeIngredient : "used in"
    Order ||--o{ OrderItem : contains
    Order }o--|| Customer : "belongs to"
    Order }o--|| Deliveryman : "delivered by"
    Employee ||--o{ AttendanceRecord : "has"
    Supplier ||--o{ Purchase : "supplies"
    Purchase ||--o{ PurchaseItem : contains
    Recipe ||--o{ RecipeIngredient : "contains"
    Inventory ||--o{ InventoryItem : "counts"
    CashRegisterSession ||--o{ CashMovement : "records"
```

### 5.2 Tables Principales et Relations

#### Tables Métier Principales

| Table | Description | Relations Clés |
|-------|-------------|----------------|
| `users` | Utilisateurs système | `orders` (1:N) |
| `products` | Catalogue produits | `categories` (N:1), `order_items` (1:N) |
| `orders` | Commandes clients | `customers` (N:1), `order_items` (1:N) |
| `employees` | Employés | `attendance_records` (1:N) |
| `suppliers` | Fournisseurs | `purchases` (1:N) |
| `recipes` | Recettes de production | `recipe_ingredients` (1:N) |

#### Tables de Gestion

| Table | Description | Relations Clés |
|-------|-------------|----------------|
| `inventory` | Sessions d'inventaire | `inventory_items` (1:N) |
| `cash_register_sessions` | Sessions de caisse | `cash_movements` (1:N) |
| `accounting_entries` | Écritures comptables | `accounts` (N:1) |
| `consumable_usage` | Utilisation consommables | `products` (N:1) |

### 5.3 Contraintes et Intégrités

- **Clés étrangères** : Toutes les relations sont contraintes par des FK
- **Index** : Index sur les champs de recherche fréquents (`product.name`, `order.status`)
- **Contraintes d'unicité** : SKU produits, email utilisateurs
- **Cascade** : Suppression en cascade pour les relations parent-enfant

---

## 6. Services et Intégrations

### 6.1 Imprimante & Tiroir-caisse (ESC/POS)

**Service** : `app/services/printer_service.py`

**Fonctionnalités** :
- Impression automatique de tickets de vente
- Ouverture du tiroir-caisse
- Gestion des files d'impression avec priorités
- Support réseau via agent distant

**Configuration** :
```python
# Configuration imprimante
PRINTER_VENDOR_ID = 0x0471
PRINTER_PRODUCT_ID = 0x0055
PRINTER_ENABLED = true
```

**Commandes ESC/POS** :
- `ESC_INIT` : Initialisation imprimante
- `ESC_CUT` : Coupe du papier
- `ESC_DRAWER` : Ouverture tiroir-caisse
- `ESC_BOLD` : Formatage texte

### 6.2 Pointeuse ZKTeco

**Service** : `app/zkteco/routes.py`

**Fonctionnalités** :
- Réception automatique des pointages
- Synchronisation avec la base de données
- Gestion des employés par ID ZKTeco
- API REST pour communication

**Endpoints** :
- `GET /zkteco/api/ping` : Test de connectivité
- `POST /zkteco/api/attendance` : Réception des pointages

### 6.3 Scripts de Communication

**Agent d'impression** : `app/services/printer_agent.py`
- Service HTTP pour impression distante
- Authentification par token
- Gestion des files d'impression

**Intégration POS** : `app/services/pos_integration.py`
- Décorateurs automatiques pour impression
- Gestion des sessions de caisse
- Intégration tiroir-caisse

### 6.4 Gestion du Réseau Local / VPS

**Configuration réseau** :
- Support multi-hôtes pour impression
- Agent d'impression distant
- Configuration VPS avec Nginx/Gunicorn

---

## 7. Interface & Dashboards

### 7.1 Pages Principales

#### Interface Utilisateur
- **Accueil** : `/` - Dashboard principal avec statistiques
- **Authentification** : `/auth/login` - Connexion utilisateur
- **POS** : `/sales/pos` - Interface point de vente

#### Administration
- **Dashboard Admin** : `/admin/dashboard` - Vue d'ensemble système
- **Gestion Produits** : `/admin/products/` - Catalogue et stocks
- **Commandes** : `/admin/orders/` - Gestion des commandes
- **Inventaires** : `/admin/inventory/` - Inventaires physiques

#### RH & Paie
- **Dashboard RH** : `/employees/dashboard` - Vue RH
- **Pointage** : `/employees/attendance` - Gestion des présences
- **Paie** : `/employees/payroll/` - Calcul et bulletins

### 7.2 Tableaux de Bord

#### Dashboard Opérationnel (`/dashboards/daily`)
- Ventes du jour
- Stocks critiques
- Commandes en cours
- Alertes production

#### Dashboard Stratégique (`/dashboards/monthly`)
- Performance mensuelle
- Rentabilité par produit
- Tendances de vente
- Analyse des coûts

#### Dashboard Production (`/dashboards/production`)
- Planning de production
- Coûts des recettes
- Utilisation des ingrédients
- Alertes stock

### 7.3 API de Données

**Endpoints API** (`app/dashboards/api.py`) :
- `/dashboards/api/sales/daily` : Données ventes quotidiennes
- `/dashboards/api/stock/alerts` : Alertes stock
- `/dashboards/api/production/status` : État production

---

## 8. Sécurité & Utilisateurs

### 8.1 Rôles et Permissions

**Rôles utilisateurs** :
- **Admin** : Accès total au système
- **Gérante** : Gestion complète (sauf config système)
- **Vendeuse** : POS, stocks, commandes, dashboards
- **Production** : Dashboard production uniquement

**Système d'autorisation** :
```python
# Décorateurs de sécurité
@login_required
@admin_required
def admin_function():
    pass
```

### 8.2 Authentification

**Flask-Login** :
- Gestion des sessions utilisateur
- Protection CSRF avec Flask-WTF
- Hachage sécurisé des mots de passe (Werkzeug)

**Configuration sécurité** :
```python
# Configuration CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600

# Configuration session
PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
```

### 8.3 Journaux et Traçabilité

**Logging** :
- Logs d'application dans `logs/fee_maison.log`
- Traçabilité des actions utilisateur
- Monitoring des erreurs système

**Audit trail** :
- Historique des modifications
- Traçabilité des mouvements de stock
- Journal des opérations comptables

---

## 9. Déploiement & Maintenance

### 9.1 Installation Locale

**Prérequis** :
- Python 3.13+
- PostgreSQL 14+
- Node.js (pour les assets)

**Installation** :
```bash
# Cloner le projet
git clone <repository>
cd fee_maison_gestion_cursor

# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Dépendances
pip install -r requirements.txt

# Configuration base de données
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost/db

# Migrations
flask db upgrade

# Lancement
python run.py
```

### 9.2 Configuration VPS

**Stack de production** :
- **OS** : Ubuntu 24.10
- **Web Server** : Nginx
- **WSGI** : Gunicorn
- **Database** : PostgreSQL
- **Process Manager** : systemd

**Configuration Nginx** (`nginx_erp.conf`) :
```nginx
server {
    listen 80;
    server_name erp.declaimers.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Service systemd** :
```ini
[Unit]
Description=ERP Fée Maison
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/erp
ExecStart=/opt/erp/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 9.3 Sauvegardes et Mise à Jour

**Sauvegardes automatiques** :
- Base de données PostgreSQL (pg_dump)
- Fichiers de configuration
- Logs système

**Scripts de maintenance** :
- `deploy_vps.sh` : Déploiement automatique
- `update_vps.sh` : Mise à jour du système
- `backup_database.sh` : Sauvegarde BDD

### 9.4 Fichiers de Configuration

**Variables d'environnement** (`.env`) :
```bash
# Base de données
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key

# Imprimante
PRINTER_ENABLED=true
PRINTER_VENDOR_ID=0x0471
PRINTER_PRODUCT_ID=0x0055

# ZKTeco
ZKTECO_ENABLED=true
ZKTECO_API_URL=http://pointeuse:8080
```

**Configuration imprimante** (`printer_config.example`) :
```json
{
    "vendor_id": "0x0471",
    "product_id": "0x0055",
    "enabled": true,
    "network_enabled": false
}
```

---

## 10. Annexes

### 10.1 API Endpoints

#### Endpoints Principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Page d'accueil |
| GET | `/dashboard` | Dashboard principal |
| POST | `/auth/login` | Connexion utilisateur |
| GET | `/admin/products/` | Liste des produits |
| POST | `/admin/orders/create` | Création commande |
| GET | `/sales/pos` | Interface POS |
| POST | `/zkteco/api/attendance` | Pointage ZKTeco |

#### API Dashboards

| Endpoint | Description | Format |
|----------|-------------|--------|
| `/dashboards/api/sales/daily` | Ventes quotidiennes | JSON |
| `/dashboards/api/stock/alerts` | Alertes stock | JSON |
| `/dashboards/api/production/status` | État production | JSON |

### 10.2 Commandes Utilitaires

#### Commandes Flask CLI

```bash
# Créer un administrateur
flask create-admin

# Afficher les statistiques
flask stats

# Migrations base de données
flask db migrate -m "Description"
flask db upgrade
```

#### Scripts de Maintenance

```bash
# Déploiement VPS
./deploy_vps.sh

# Mise à jour système
./update_vps.sh

# Sauvegarde base de données
./backup_database.sh
```

### 10.3 Performance et Extensions Futures

#### Optimisations Actuelles

- **Cache** : Variables globales en contexte Flask
- **Index** : Index sur champs de recherche fréquents
- **Pagination** : Pagination des listes importantes
- **Lazy Loading** : Relations SQLAlchemy en lazy loading

#### Extensions Futures

- **Cache Redis** : Mise en cache des données fréquentes
- **API REST** : API complète pour intégrations externes
- **Mobile App** : Application mobile pour POS
- **Analytics** : Intégration Google Analytics
- **Backup Cloud** : Sauvegardes automatiques cloud

#### Monitoring

- **Logs** : Logs structurés avec niveaux
- **Métriques** : Métriques de performance
- **Alertes** : Alertes stock et système
- **Health Checks** : Endpoints de santé système

---

## 📊 Diagramme d'Architecture Global

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[Mobile POS]
        C[Admin Interface]
    end
    
    subgraph "Load Balancer"
        D[Nginx]
    end
    
    subgraph "Application Layer"
        E[Flask Application]
        F[Gunicorn WSGI]
        G[Background Tasks]
    end
    
    subgraph "Data Layer"
        H[(PostgreSQL)]
        I[File Storage]
        J[Logs]
    end
    
    subgraph "Hardware Integration"
        K[ESC/POS Printer]
        L[ZKTeco Terminal]
        M[Cash Drawer]
    end
    
    subgraph "External Services"
        N[Print Agent]
        O[Backup Service]
        P[Monitoring]
    end
    
    A --> D
    B --> D
    C --> D
    D --> F
    F --> E
    E --> H
    E --> I
    E --> J
    E --> K
    E --> L
    E --> M
    E --> N
    E --> O
    E --> P
```

---

## 🔗 Références et Fichiers Source

### Documentation Existante
- `documentation/ERP_COMPLETE_GUIDE.md` - Guide utilisateur complet
- `documentation/ARCHITECTURE_TECHNIQUE.md` - Architecture technique détaillée
- `documentation/DEPLOIEMENT_VPS.md` - Guide de déploiement VPS
- `documentation/SECURITE_ET_PERMISSIONS.md` - Guide sécurité

### Fichiers de Configuration
- `config.py` - Configuration application
- `nginx_erp.conf` - Configuration Nginx
- `requirements.txt` - Dépendances Python
- `printer_config.example` - Configuration imprimante

### Scripts Utilitaires
- `deploy_vps.sh` - Déploiement automatique
- `update_vps.sh` - Mise à jour système
- `backup_database.sh` - Sauvegarde BDD

---

*Documentation générée automatiquement le 22 octobre 2025 - Version 5.0*
*ERP Fée Maison - Système de Gestion Intégré*











