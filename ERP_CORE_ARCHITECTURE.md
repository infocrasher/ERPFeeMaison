# Architecture Core ERP - Fée Maison

## 📁 Structure des Modèles

### **Source Unique des Modèles**
Tous les modèles principaux sont centralisés dans **`racine/models.py`** (623 lignes)

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

### **3. Modules Spécialisés**
- Chaque module peut avoir ses propres modèles **spécialisés**
- Les modèles **principaux** restent dans `racine/models.py`

### **4. Relations Cross-Modules**
```python
# Dans app/employees/models.py
from models import Order  # Pour les relations Order-Employee

# Dans app/stock/models.py  
from models import Product  # Pour les relations Product-StockMovement
```

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

## 🚀 Avantages de cette Architecture

### **Simplicité**
- Un seul endroit pour les modèles principaux
- Imports cohérents dans tout le projet
- Pas de duplication

### **Maintenance**
- Modifications centralisées
- Pas de risque de désynchronisation
- Tests plus simples

### **Évolutivité**
- Ajout facile de nouveaux modèles
- Relations claires entre modules
- Architecture prévisible

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

## 🔧 Migration Future (Optionnel)

Si le fichier devient trop volumineux (>1000 lignes), considérer :

```
app/
├── core/
│   ├── models/
│   │   ├── __init__.py      # Imports centralisés
│   │   ├── user.py          # User
│   │   ├── product.py       # Product, Category
│   │   ├── order.py         # Order, OrderItem
│   │   ├── recipe.py        # Recipe, RecipeIngredient
│   │   └── common.py        # Unit, DeliveryDebt
```

## 📝 Notes de Développement

### **Ajout d'un nouveau modèle principal**
1. Ajouter dans `racine/models.py`
2. Créer migration Alembic
3. Mettre à jour les imports si nécessaire

### **Ajout d'un modèle spécialisé**
1. Ajouter dans le module concerné (`app/module/models.py`)
2. Importer les modèles principaux depuis `racine/models.py`
3. Créer migration Alembic

### **Ajout d'un nouveau dashboard**
1. Ajouter route dans `app/dashboards/routes.py`
2. Ajouter endpoint API dans `app/dashboards/api.py`
3. Créer template dans `app/templates/dashboards/`

### **Tests**
```python
# tests/test_models.py
from models import User, Product, Order  # Import depuis racine

# tests/test_dashboards.py
from app.dashboards import dashboards_bp  # Test du module dashboards
```

---

**Dernière mise à jour :** $(date)
**Architecture validée :** ✅
**Tests passants :** ✅
**Module dashboards unifié :** ✅
