# 🏗️ Architecture Core ERP - Fée Maison

## 📋 Vue d'Ensemble

### **Architecture Générale**
L'ERP Fée Maison est une application Flask modulaire conçue pour la gestion complète d'une entreprise de production alimentaire artisanale.

### **Technologies Utilisées**
- **Backend** : Flask + SQLAlchemy + PostgreSQL
- **Frontend** : Bootstrap 5 + Jinja2 + JavaScript
- **Serveur** : Gunicorn + Nginx
- **Base de données** : PostgreSQL (production), SQLite (développement)
- **Authentification** : Flask-Login + bcrypt
- **Migrations** : Alembic

---

## 📁 Structure des Modèles

### **Source Unique des Modèles**
Tous les modèles principaux sont centralisés dans **`racine/models.py`** (623 lignes)

### **Structure des Déploiements**
```
Machine Locale (Développement)
fee_maison_gestion_cursor/
├── models.py              # Modèles principaux
├── app/
│   ├── sales/
│   │   └── models.py      # CashRegisterSession, CashMovement
│   ├── employees/
│   │   └── models.py      # Employee, WorkHours, Payroll
│   └── ...

VPS (Production)
/opt/erp/app/              # Dépôt Git
├── models.py              # Modèles principaux
├── app/
│   ├── sales/
│   │   └── models.py      # CashRegisterSession, CashMovement
│   ├── employees/
│   │   └── models.py      # Employee, WorkHours, Payroll
│   └── ...
```

### **Modules avec leurs propres modèles**
```
app/
├── employees/
│   ├── models.py       # Employee, AttendanceRecord, Payroll, WorkHours, etc.
├── accounting/
│   ├── models.py       # Account, Journal, Entry, Period, Expense, etc.
├── stock/
│   ├── models.py       # StockMovement, StockAdjustment, etc.
├── sales/
│   ├── models.py       # CashRegisterSession, CashMovement, etc.
├── purchases/
│   ├── models.py       # Purchase, PurchaseItem, etc.
├── deliverymen/
│   ├── models.py       # Deliveryman
└── dashboards/         # 🆕 Module unifié pour les dashboards
    ├── __init__.py     # Blueprint principal et imports
    ├── api.py          # Endpoints API JSON
    └── routes.py       # Routes templates HTML
```

### **Modèles dans racine/models.py**
```python
# Authentification & Utilisateurs
- User (UserMixin, db.Model)

# Produits & Catégories
- Category (db.Model)
- Product (db.Model)

# Recettes & Ingrédients
- Recipe (db.Model)
- RecipeIngredient (db.Model)

# Commandes & Items
- Order (db.Model)
- OrderItem (db.Model)

# Unités & Conversions
- Unit (db.Model)

# Livraisons
- DeliveryDebt (db.Model)
```

---

## 🔗 Relations entre Modules

### **Imports depuis racine/models.py**
```python
# Tous les modules utilisent :
from models import Product, Category, Order, OrderItem, Recipe, RecipeIngredient, User, Unit, DeliveryDebt
```

### **Modules qui utilisent racine/models.py**
- ✅ `app/products/` → Product, Category
- ✅ `app/recipes/` → Recipe, RecipeIngredient, Product
- ✅ `app/orders/` → Order, OrderItem, Product, Recipe
- ✅ `app/stock/` → Product
- ✅ `app/employees/` → Order (pour les relations)
- ✅ `app/sales/` → Product, Order, OrderItem, DeliveryDebt
- ✅ `app/purchases/` → Product, Unit
- ✅ `app/auth/` → User
- ✅ `app/main/` → Order, Product, Recipe
- ✅ `app/dashboards/` → Order, Product, Category

---

## 📋 Règles d'Architecture

### **1. Source Unique**
- **TOUS** les modèles principaux dans `racine/models.py`
- **AUCUN** modèle dupliqué dans `app/models.py` (supprimé)

### **2. Imports Standardisés**
```python
# ✅ CORRECT
from models import Product, Order, Recipe

# ❌ INCORRECT (n'existe plus)
from app.models import Product
```

### **3. Gestion des Doublons**
```python
# ✅ CORRECT - CashRegisterSession uniquement dans app/sales/models.py
from app.sales.models import CashRegisterSession

# ❌ INCORRECT - Pas de doublon dans racine/models.py
# La classe CashRegisterSession ne doit PAS être dans racine/models.py
```

### **4. Modules Spécialisés**
- Chaque module peut avoir ses propres modèles **spécialisés**
- Les modèles **principaux** restent dans `racine/models.py`
- **Aucun doublon** : Un modèle ne doit être défini qu'une seule fois

### **5. Relations Cross-Modules**
```python
# Dans app/employees/models.py
from models import Order  # Pour les relations Order-Employee

# Dans app/stock/models.py  
from models import Product  # Pour les relations Product-StockMovement
```

---

## 🆕 Architecture Module Dashboards

### **Structure Unifiée**
```
app/dashboards/
├── __init__.py         # Blueprint principal et organisation
├── api.py              # Endpoints API JSON (/dashboards/api/*)
└── routes.py           # Routes templates HTML (/dashboards/*)
```

### **URLs Finales**
```
📊 Dashboards Templates
├── /dashboards/daily           # Dashboard journalier
└── /dashboards/monthly         # Dashboard mensuel

🔌 API Endpoints
├── /dashboards/api/daily/production
├── /dashboards/api/daily/stock
├── /dashboards/api/daily/sales
├── /dashboards/api/daily/employees
├── /dashboards/api/monthly/overview
├── /dashboards/api/monthly/revenue-trend
├── /dashboards/api/monthly/product-performance
└── /dashboards/api/monthly/employee-performance
```

### **Avantages de l'Architecture Unifiée**
- 🎯 **Cohérence** : Un seul module pour tous les dashboards
- 🔧 **Maintenance** : Logique centralisée
- 📈 **Évolutivité** : Ajout facile de nouveaux dashboards
- 🧪 **Tests** : Organisation claire pour les tests unitaires

---

## 🗄️ Base de Données

### **Configuration PostgreSQL**
```python
class ProductionConfig(Config):
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or os.environ.get('DB_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or os.environ.get('DB_PORT', '5432')
    POSTGRES_DB_NAME = os.environ.get('POSTGRES_DB_NAME') or os.environ.get('DB_NAME')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"
```

### **Migrations Alembic**
```bash
# Créer une migration
flask db migrate -m "Description de la migration"

# Appliquer les migrations
flask db upgrade

# Revenir en arrière
flask db downgrade
```

### **Structure des Tables**
- **15+ tables principales** dans `models.py`
- **Tables spécialisées** dans chaque module
- **Relations** : Foreign keys et backrefs SQLAlchemy
- **Index** : Optimisés pour les requêtes fréquentes

---

## 🔧 Configuration Flask

### **Factory Pattern**
```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Enregistrer les blueprints
    register_blueprints(app)
    
    return app
```

### **Blueprints Enregistrés (RÉEL)**
```python
# Enregistrement dans app/__init__.py
from app.main.routes import main as main_blueprint
app.register_blueprint(main_blueprint)

from app.auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

from app.products.routes import products as products_blueprint
app.register_blueprint(products_blueprint, url_prefix='/admin/products')

from app.orders.routes import orders as orders_blueprint
app.register_blueprint(orders_blueprint, url_prefix='/admin/orders')

from app.recipes.routes import recipes as recipes_blueprint
app.register_blueprint(recipes_blueprint, url_prefix='/admin/recipes')

from app.stock import bp as stock_blueprint
app.register_blueprint(stock_blueprint, url_prefix='/admin/stock')

from app.admin.routes import admin as admin_blueprint
app.register_blueprint(admin_blueprint, url_prefix='/admin')

from app.purchases import bp as purchases_blueprint
app.register_blueprint(purchases_blueprint, url_prefix='/admin/purchases')

from app.orders.dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

from app.orders.status_routes import status_bp
app.register_blueprint(status_bp, url_prefix='/orders')

from app.employees.routes import employees_bp
app.register_blueprint(employees_bp, url_prefix='/employees')

from app.deliverymen.routes import deliverymen_bp
app.register_blueprint(deliverymen_bp, url_prefix='/admin')

from app.sales.routes import sales as sales_blueprint
app.register_blueprint(sales_blueprint, url_prefix='/sales')

from app.dashboards import dashboards_bp
app.register_blueprint(dashboards_bp)

from app.accounting import bp as accounting_blueprint
app.register_blueprint(accounting_blueprint)

from app.zkteco import zkteco as zkteco_blueprint
app.register_blueprint(zkteco_blueprint, url_prefix='/zkteco')
```

### **URLs Réelles par Module**
```
🏠 Main
├── /                    # Page d'accueil
└── /home               # Page d'accueil

🔐 Auth
├── /auth/login         # Connexion
├── /auth/logout        # Déconnexion
└── /auth/account       # Compte utilisateur

📦 Products (Admin)
├── /admin/products/    # Liste produits
├── /admin/products/new # Nouveau produit
└── /admin/products/<id> # Détail produit

📋 Orders (Admin)
├── /admin/orders/      # Liste commandes
├── /admin/orders/new   # Nouvelle commande
└── /admin/orders/<id>  # Détail commande

🏭 Recipes (Admin)
├── /admin/recipes/     # Liste recettes
├── /admin/recipes/new  # Nouvelle recette
└── /admin/recipes/<id> # Détail recette

📦 Stock (Admin)
├── /admin/stock/       # Vue d'ensemble stock
├── /admin/stock/overview # Vue d'ensemble
└── /admin/stock/quick-entry # Entrée rapide

🛒 Purchases (Admin)
├── /admin/purchases/   # Liste achats
├── /admin/purchases/new # Nouvel achat
└── /admin/purchases/<id> # Détail achat

👥 Employees
├── /employees/         # Liste employés
├── /employees/new      # Nouvel employé
└── /employees/<id>     # Détail employé

🚚 Deliverymen (Admin)
├── /admin/deliverymen/ # Liste livreurs
├── /admin/deliverymen/new # Nouveau livreur
└── /admin/deliverymen/<id> # Détail livreur

💰 Sales
├── /sales/             # Dashboard ventes
├── /sales/pos          # Interface POS
├── /sales/cash-status  # Statut caisse
└── /sales/cash-sessions # Sessions caisse

📊 Dashboards
├── /dashboards/daily   # Dashboard journalier
└── /dashboards/monthly # Dashboard mensuel

🧮 Accounting (Admin)
├── /admin/accounting/  # Dashboard comptabilité
├── /admin/accounting/accounts # Plan comptable
└── /admin/accounting/reports # Rapports

⏰ ZKTeco
├── /zkteco/api/ping    # Test connexion
├── /zkteco/api/attendance # Données pointage
└── /zkteco/api/employees # Employés pointeuse
```

---

## 🔐 Sécurité et Authentification

### **Système d'Authentification**
```python
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Décorateur pour protéger les routes
@login_required
def protected_route():
    pass
```

### **Gestion des Rôles**
```python
# Rôles définis
ROLES = {
    'admin': 'Administrateur',
    'gerante': 'Gérante',
    'vendeuse': 'Vendeuse',
    'production': 'Production'
}

# Vérification des permissions
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

## 📊 API et Endpoints

### **Structure API**
```
/api/
├── /dashboards/         # Endpoints dashboards
├── /orders/            # API commandes
├── /products/          # API produits
├── /stock/             # API stock
└── /zkteco/            # API pointeuse
```

### **Format des Réponses**
```python
# Succès
{
    "success": True,
    "data": {...},
    "message": "Opération réussie"
}

# Erreur
{
    "success": False,
    "error": "Message d'erreur",
    "code": 400
}
```

---

## 🧪 Tests et Qualité

### **Structure des Tests**
```
tests/
├── conftest.py         # Configuration pytest
├── test_app.py         # Tests d'application
├── test_models.py      # Tests des modèles
├── test_products.py    # Tests produits
├── test_stock.py       # Tests stock
└── test_categories.py  # Tests catégories
```

### **Configuration Pytest**
```python
# conftest.py
@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()
```

---

## 🚀 Déploiement et Performance

### **Configuration WSGI**
```python
# wsgi.py
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV') or 'production')
application = app  # Pour compatibilité
```

### **Configuration Gunicorn**
```bash
# Commandes de démarrage
gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 wsgi:app

# Configuration systemd
ExecStart=/var/www/erp-fee-maison/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 --access-logfile /var/log/erp-fee-maison/access.log --error-logfile /var/log/erp-fee-maison/error.log wsgi:app
```

### **Optimisations Performance**
- **Workers** : 3 processus Gunicorn
- **Timeout** : 120 secondes
- **Logs** : Séparés access/error
- **Cache** : Redis pour les sessions
- **Base de données** : Connection pooling

---

## 🏪 Workflow Métier Intégré

### **Rôles Utilisateurs**
| Rôle | Utilisateur | Accès | Permissions |
|------|-------------|-------|-------------|
| **Admin** | Sofiane | Accès total | Tous les modules, configuration système |
| **Gérante** | Amel | Gestion complète | Tous les modules + caisse, prix, recettes |
| **Vendeuse** | Yasmine | Opérationnel | Commandes, caisse, dashboards shop/prod |
| **Production** | Rayan | Lecture seule | Dashboard production uniquement |

### **Workflows Principaux**

#### **1. Commandes Clients**
```
Commande créée (Amel) → En production → Réception magasin → Livraison → Encaissement
```

#### **2. Gestion Stock Multi-Emplacements**
```
Achat → Incrémentation stock + PMP → Production → Décrémentation → Alertes seuil
```

#### **3. Caisse**
```
Ouverture session → Mouvements (ventes, entrées, sorties) → Fermeture → Rapports
```

### **Intégrations**
- **Pointeuse ZKTeco** : Données de présence pour analytics RH
- **Email** : Notifications système via Gmail
- **Comptabilité** : Écritures automatiques depuis ventes, achats, caisse

---

## ⚠️ Points d'Attention

### **1. Taille du fichier**
- `racine/models.py` fait 623 lignes
- Considérer la séparation si > 1000 lignes

### **2. Couplage**
- Tous les modules dépendent de `racine/models.py`
- Changements impactent tout le projet

### **3. Tests**
- Tests unitaires doivent importer depuis `racine/models.py`
- Configuration des tests dans `tests/conftest.py`

### **4. Déploiement**
- **VPS** : `/opt/erp/app/` contient le dépôt Git complet
- **Synchronisation** : `git pull origin main` sur le VPS

---

## 🔄 Évolutions Futures

### **Améliorations Architecture**
- **Microservices** : Séparation des modules en services indépendants
- **API REST** : Standardisation complète des endpoints
- **Cache** : Mise en cache des requêtes fréquentes
- **Monitoring** : Métriques de performance

### **Nouvelles Fonctionnalités**
- **Notifications** : Système d'alertes en temps réel
- **Mobile** : Application mobile pour les employés
- **Analytics** : Tableaux de bord avancés
- **Intégrations** : APIs externes (paiement, livraison)

---

## 📚 Documentation Associée

### **Fichiers de Référence**
- **Guide Principal** : `documentation/ERP_COMPLETE_GUIDE.md`
- **Workflow Métier** : `documentation/WORKFLOW_METIER_DETAIL.md`
- **Déploiement** : `documentation/DEPLOIEMENT_VPS.md`
- **Troubleshooting** : `documentation/TROUBLESHOOTING_GUIDE.md`

### **Liens Utiles**
- **Mémo Technique** : `ERP_MEMO.md`
- **Configuration Pointeuse** : `documentation/CONFIGURATION_POINTEUSE_ZKTECO.md`
- **Configuration Dashboards** : `documentation/CONFIGURATION_DASHBOARDS.md`

---

**🏗️ Cette architecture technique garantit la maintenabilité, l'évolutivité et la performance du système ERP Fée Maison.**
