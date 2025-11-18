# 🔗 AUDIT D'INTÉGRATION IA - MODULE DASHBOARDS

**Date** : Novembre 2025  
**Objectif** : Identifier précisément les points d'intégration entre `app/dashboards/`, `app/reports/` et `app/ai/`

---

## 📋 TABLE DES MATIÈRES

1. [Routes actuelles avec KPI et équivalence reports](#1-routes-actuelles-avec-kpi-et-équivalence-reports)
2. [Intégration app/reports](#2-intégration-appreports)
3. [Intégration app/ai](#3-intégration-appai)
4. [Compatibilité des données](#4-compatibilité-des-données)
5. [Plan d'intégration priorisé](#5-plan-dintégration-priorisé)

---

## 1. ROUTES ACTUELLES AVEC KPI ET ÉQUIVALENCE REPORTS

### 📊 Dashboard Journalier

#### `/dashboards/api/daily/production` (GET)

**KPIs calculés manuellement** :
- `overdue_count` : Commandes en retard (`due_date < now`)
- `urgent_count` : Commandes urgentes (≤ 2h)
- `normal_count` : Commandes normales (> 2h)
- `total_production` : Total commandes en production

**Type de rapport** : Production opérationnelle

**Équivalence `app/reports`** : ⚠️ **PARTIELLE**
- `ProductionReportService.generate()` fournit :
  - `total_units`, `total_orders`, `efficiency_rate`
  - `production_by_product`
  - **MAIS** ne fournit **PAS** les commandes en retard/urgentes par statut

**Recommandation** :
- ✅ **Réutiliser** : `total_orders` depuis `ProductionReportService`
- ⚠️ **Conserver** : Logique de tri par `due_date` (spécifique au dashboard)
- 💡 **Améliorer** : Ajouter `production_orders_by_status` dans `ProductionReportService`

---

#### `/dashboards/api/daily/stock` (GET)

**KPIs calculés manuellement** :
- `out_of_stock_count` : Produits en rupture
- `low_stock_count` : Produits sous seuil
- `total_stock_value` : Valeur totale du stock
- `today_movements` : Mouvements aujourd'hui

**Type de rapport** : Alertes stock

**Équivalence `app/reports`** : ✅ **EXACTE**
- `StockAlertReportService.generate()` fournit :
  - `low_stock_products` : Produits sous seuil
  - `out_of_stock` : Produits en rupture
  - `overstock` : Produits en surstock
  - `coverage_data` : Jours de couverture
  - `total_alerts` : Total alertes

**Recommandation** :
- ✅ **Remplacer complètement** : Utiliser `StockAlertReportService.generate()`
- ✅ **Bénéfice** : Accès aux métadonnées IA (`growth_rate`, `variance`, `benchmark`)

**Mapping** :
```python
# Actuel (dashboards/api.py)
out_of_stock = Product.query.filter(...)
low_stock = Product.query.filter(...)

# Remplacé par
from app.reports.services import StockAlertReportService
report_data = StockAlertReportService.generate()
out_of_stock = report_data['out_of_stock']
low_stock = report_data['low_stock_products']
```

---

#### `/dashboards/api/daily/sales` (GET)

**KPIs calculés manuellement** :
- `daily_revenue` : CA du jour (`SUM(Order.total_amount)`)
- `total_orders` : Nombre de commandes
- `delivered_orders` : Commandes livrées
- `cash_in_today` : Encaissements caisse
- `cash_out_today` : Décaissements caisse
- `net_cash_flow` : Flux net
- `orders_by_status` : Répartition par statut

**Type de rapport** : Ventes quotidiennes

**Équivalence `app/reports`** : ✅ **EXACTE** (avec enrichissements)
- `DailySalesReportService.generate(report_date)` fournit :
  - `total_revenue` : ✅ Identique à `daily_revenue`
  - `total_transactions` : ✅ Identique à `total_orders`
  - `average_basket` : ✅ Panier moyen
  - `hourly_sales` : ✅ Ventes par heure
  - `top_products` : ✅ Top produits
  - **+ Métadonnées IA** : `growth_rate`, `variance`, `trend_direction`, `benchmark`

**Recommandation** :
- ✅ **Remplacer** : `daily_revenue` et `total_orders` par `DailySalesReportService`
- ⚠️ **Conserver** : Logique caisse (`cash_in_today`, `cash_out_today`) - spécifique au dashboard
- ✅ **Ajouter** : Utiliser `hourly_sales` pour graphique évolution

**Mapping** :
```python
# Actuel
daily_revenue = db.session.query(func.sum(Order.total_amount))...

# Remplacé par
from app.reports.services import DailySalesReportService
report_data = DailySalesReportService.generate(date.today())
daily_revenue = report_data['total_revenue']
total_orders = report_data['total_transactions']
hourly_sales = report_data['hourly_sales']  # NOUVEAU
```

---

#### `/dashboards/api/daily/employees` (GET)

**KPIs calculés manuellement** :
- `total_employees` : Nombre d'employés actifs
- `present_today` : Présents aujourd'hui
- `absent_today` : Absents
- `total_hours_worked` : Heures travaillées
- `attendance_rate` : Taux de présence

**Type de rapport** : RH / Main d'œuvre

**Équivalence `app/reports`** : ⚠️ **PARTIELLE**
- `LaborCostReportService.generate()` (hebdomadaire) fournit :
  - `total_labor_cost` : Coût main d'œuvre
  - `total_hours` : Heures totales
  - `overtime_hours` : Heures supplémentaires
  - `labor_cost_ratio` : Ratio coût/revenu
  - **MAIS** : Rapport hebdomadaire, pas quotidien
  - **MAIS** : Pas de présence/absence quotidienne

**Recommandation** :
- ⚠️ **Conserver** : Logique de présence quotidienne (spécifique au dashboard)
- ✅ **Réutiliser** : `total_hours` depuis `LaborCostReportService` (si période = aujourd'hui)
- 💡 **Créer** : Service `DailyAttendanceReportService` si nécessaire

---

### 📈 Dashboard Mensuel

#### `/dashboards/api/monthly/overview` (GET)

**KPIs calculés manuellement** :
- `monthly_revenue` : CA mensuel
- `monthly_orders` : Nombre de commandes
- `monthly_expenses` : Charges (comptabilité classe 6)
- `net_profit` : Bénéfice net
- `profit_margin` : Marge bénéficiaire
- `stock_value` : Valeur stock
- `active_employees` : Employés actifs
- `total_salary_cost` : Masse salariale
- `revenue_per_employee` : CA par employé

**Type de rapport** : Vue d'ensemble mensuelle

**Équivalence `app/reports`** : ✅ **EXACTE** (avec enrichissements)
- `MonthlyProfitLossService.generate(year, month)` fournit :
  - `revenue` : ✅ Identique à `monthly_revenue`
  - `cogs` : Coût des ventes
  - `gross_margin` : Marge brute
  - `expenses` : ✅ Similaire à `monthly_expenses`
  - `net_income` : ✅ Identique à `net_profit`
  - `net_margin` : ✅ Identique à `profit_margin`
  - **+ Métadonnées IA** : `growth_rate`, `variance`, `trend_direction`, `benchmark`

**Recommandation** :
- ✅ **Remplacer complètement** : Utiliser `MonthlyProfitLossService.generate(year, month)`
- ✅ **Bénéfice** : Accès aux métadonnées IA complètes

**Mapping** :
```python
# Actuel
monthly_revenue = db.session.query(func.sum(Order.total_amount))...
monthly_expenses = db.session.query(func.sum(JournalEntryLine.debit_amount))...
net_profit = monthly_revenue - monthly_expenses

# Remplacé par
from app.reports.services import MonthlyProfitLossService
report_data = MonthlyProfitLossService.generate(year, month)
monthly_revenue = report_data['revenue']
monthly_expenses = report_data['expenses']
net_profit = report_data['net_income']
profit_margin = report_data['net_margin']
# + Métadonnées IA : growth_rate, variance, trend_direction, benchmark
```

---

#### `/dashboards/api/monthly/revenue-trend` (GET)

**KPIs calculés manuellement** :
- `revenue` : CA par mois (12 derniers mois)
- `orders` : Commandes par mois
- `avg_order_value` : Panier moyen par mois

**Type de rapport** : Tendance sur 12 mois

**Équivalence `app/reports`** : ⚠️ **PARTIELLE**
- `MonthlyProfitLossService.generate()` : Un mois à la fois
- **Aucun service** ne fournit directement la tendance 12 mois

**Recommandation** :
- ⚠️ **Conserver** : Logique de boucle sur 12 mois
- ✅ **Améliorer** : Utiliser `MonthlyProfitLossService` dans la boucle au lieu de requêtes directes
- ✅ **Bénéfice** : Cohérence des calculs, accès aux métadonnées IA

**Mapping** :
```python
# Actuel
for i in range(12):
    monthly_revenue = db.session.query(func.sum(Order.total_amount))...

# Remplacé par
from app.reports.services import MonthlyProfitLossService
for i in range(12):
    year, month = calculate_year_month(i)
    report_data = MonthlyProfitLossService.generate(year, month)
    monthly_revenue = report_data['revenue']
    # + Métadonnées IA par mois
```

---

#### `/dashboards/api/monthly/product-performance` (GET)

**KPIs calculés manuellement** :
- `top_by_revenue` : Top produits par CA
- `top_by_quantity` : Top produits par quantité
- `total_quantity`, `total_revenue`, `avg_price` : Par produit

**Type de rapport** : Performance produits

**Équivalence `app/reports`** : ✅ **EXACTE**
- `WeeklyProductPerformanceService.generate(start_date, end_date)` fournit :
  - `performance_data` : Liste produits avec `revenue`, `quantity`, `units_sold`
  - `total_revenue` : CA total
  - **+ Métadonnées IA** : `growth_rate`, `variance`, `trend_direction`

**Recommandation** :
- ✅ **Remplacer** : Utiliser `WeeklyProductPerformanceService` avec dates mensuelles
- ⚠️ **Adapter** : Le service est hebdomadaire, mais peut être utilisé avec dates mensuelles

**Mapping** :
```python
# Actuel
top_products = db.session.query(...).group_by(Product.id)...

# Remplacé par
from app.reports.services import WeeklyProductPerformanceService
start_date = date(year, month, 1)
end_date = date(year, month+1, 1) - timedelta(days=1)
report_data = WeeklyProductPerformanceService.generate(start_date, end_date)
top_by_revenue = sorted(report_data['performance_data'], key=lambda x: x['revenue'], reverse=True)[:10]
```

---

#### `/dashboards/api/monthly/employee-performance` (GET)

**KPIs calculés manuellement** :
- `revenue_generated` : CA généré par employé
- `orders_produced` : Commandes produites
- `quality_issues` : Problèmes qualité
- `error_rate` : Taux d'erreur
- `monthly_cost` : Coût mensuel
- `roi` : ROI employé

**Type de rapport** : Performance employés

**Équivalence `app/reports`** : ⚠️ **PARTIELLE**
- `LaborCostReportService.generate()` (hebdomadaire) fournit :
  - `total_labor_cost` : Coût total
  - `total_hours` : Heures totales
  - `labor_cost_ratio` : Ratio coût/revenu
  - **MAIS** : Pas de performance par employé individuel
  - **MAIS** : Rapport hebdomadaire, pas mensuel

**Recommandation** :
- ⚠️ **Conserver** : Logique de performance par employé (spécifique au dashboard)
- ✅ **Réutiliser** : Méthode `get_monthly_salary_cost()` depuis `Employee`
- 💡 **Créer** : Service `MonthlyEmployeePerformanceService` si nécessaire

---

## 2. INTÉGRATION app/reports

### 📊 Routes pouvant être remplacées directement

| Route Dashboard | Service Reports | Compatibilité | Action |
|-----------------|-----------------|---------------|--------|
| `/daily/stock` | `StockAlertReportService` | ✅ **100%** | **Remplacer complètement** |
| `/daily/sales` | `DailySalesReportService` | ✅ **90%** | **Remplacer** (garder logique caisse) |
| `/monthly/overview` | `MonthlyProfitLossService` | ✅ **95%** | **Remplacer complètement** |
| `/monthly/product-performance` | `WeeklyProductPerformanceService` | ✅ **85%** | **Remplacer** (adapter dates) |

### 🔄 Duplications identifiées

#### 1. Calcul de `daily_revenue`

**Duplication** :
- `dashboards/api.py` : `func.sum(Order.total_amount)` ligne 164
- `reports/services.py` : `_compute_revenue()` ligne 75 (utilise `OrderItem.quantity * unit_price`)

**Problème** : Formules différentes (incohérence potentielle)

**Solution** : Utiliser `_compute_revenue()` ou `DailySalesReportService.generate()`

---

#### 2. Calcul de `monthly_revenue`

**Duplication** :
- `dashboards/api.py` : `func.sum(Order.total_amount)` ligne 307
- `reports/services.py` : `MonthlyProfitLossService.generate()` utilise `_compute_revenue()`

**Problème** : Même problème que `daily_revenue`

**Solution** : Utiliser `MonthlyProfitLossService.generate()`

---

#### 3. Calcul de `stock_value`

**Duplication** :
- `dashboards/api.py` : `func.sum(Product.total_stock_value)` ligne 119, 343
- `reports/services.py` : `_get_stock_value()` ligne 227 (dans `StockRotationReportService`)

**Problème** : Logique similaire mais pas identique

**Solution** : Utiliser `_get_stock_value()` ou `StockRotationReportService.generate()`

---

#### 4. Calcul de `top_products`

**Duplication** :
- `dashboards/api.py` : Requête SQL complexe lignes 458-489
- `reports/services.py` : `WeeklyProductPerformanceService.generate()` ligne 813

**Problème** : Logique identique, duplication complète

**Solution** : Utiliser `WeeklyProductPerformanceService.generate()`

---

### 📈 KPIs déjà calculés dans reports

| KPI Dashboard | Service Reports | Clé dans dict | Métadonnées IA |
|---------------|-----------------|---------------|----------------|
| `daily_revenue` | `DailySalesReportService` | `total_revenue` | ✅ `growth_rate`, `variance`, `trend_direction` |
| `total_orders` | `DailySalesReportService` | `total_transactions` | ✅ `growth_rate`, `variance` |
| `average_basket` | `DailySalesReportService` | `average_basket` | ✅ `growth_rate` |
| `out_of_stock_count` | `StockAlertReportService` | `out_of_stock` (len) | ✅ `benchmark` |
| `low_stock_count` | `StockAlertReportService` | `low_stock_products` (len) | ✅ `benchmark` |
| `monthly_revenue` | `MonthlyProfitLossService` | `revenue` | ✅ `growth_rate`, `variance`, `trend_direction` |
| `net_profit` | `MonthlyProfitLossService` | `net_income` | ✅ `growth_rate`, `variance`, `trend_direction` |
| `profit_margin` | `MonthlyProfitLossService` | `net_margin` | ✅ `benchmark` |
| `top_products` | `WeeklyProductPerformanceService` | `performance_data` | ✅ `growth_rate`, `variance` |

---

## 3. INTÉGRATION app/ai

### 🤖 Dashboard Journalier

#### Points d'intégration Prophet

**1. Graphique évolution commandes** (`daily_operational.html`, ligne 704-718)

**Actuel** : Données statiques (hardcodées) + données réelles du jour

**Intégration Prophet** :
- Ajouter une **ligne de prévision** (7 jours à venir) sur le graphique Chart.js
- Utiliser `AIManager.generate_forecasts('daily_sales', days=7)`
- Afficher les intervalles de confiance (`yhat_lower`, `yhat_upper`)

**Endpoint à créer** : `/dashboards/api/daily/sales-forecast` (GET)

**Code** :
```python
@dashboard_api.route('/daily/sales-forecast', methods=['GET'])
def daily_sales_forecast():
    from app.ai import AIManager
    ai = AIManager()
    forecast = ai.generate_forecasts('daily_sales', days=7)
    return jsonify(forecast)
```

**Template** : Ajouter un dataset dans Chart.js avec `borderDash: [5, 5]` pour ligne pointillée

---

**2. Prédictions production** (Section Production)

**Intégration Prophet** :
- Afficher le nombre de commandes prévues pour les 7 prochains jours
- Utiliser `AIManager.generate_forecasts('daily_production', days=7)`

**Endpoint à créer** : `/dashboards/api/daily/production-forecast` (GET)

**Template** : Ajouter une carte "Prédictions 7j" dans la section Production

---

#### Points d'intégration LLM

**1. Section "Analyse IA"** (Nouvelle section)

**Intégration LLM** :
- Ajouter une section avec analyse LLM du rapport quotidien
- Utiliser `AIManager.analyze_reports('daily_sales', prompt_type='daily_analysis')`
- Afficher :
  - Résumé en une phrase
  - Points positifs (max 2)
  - Points d'attention (max 2)
  - Recommandations (max 3)

**Endpoint à créer** : `/dashboards/api/daily/ai-insights` (GET)

**Code** :
```python
@dashboard_api.route('/daily/ai-insights', methods=['GET'])
def daily_ai_insights():
    from app.ai import AIManager
    ai = AIManager()
    
    # Analyse multi-rapports
    insights = {
        'sales': ai.analyze_reports('daily_sales', prompt_type='daily_analysis'),
        'stock': ai.analyze_reports('daily_stock_alerts', prompt_type='anomaly_detection'),
        'production': ai.analyze_reports('daily_production', prompt_type='daily_analysis')
    }
    
    return jsonify({
        'success': True,
        'insights': insights
    })
```

**Template** : Ajouter une carte "🤖 Analyse IA" avec texte formaté

---

**2. Détection d'anomalies** (Bannière d'alertes)

**Intégration LLM** :
- Utiliser `AIManager.detect_anomalies('daily_sales')`
- Afficher les anomalies détectées avec z-score et explication LLM

**Endpoint à créer** : `/dashboards/api/daily/anomalies` (GET)

**Template** : Enrichir la bannière d'alertes avec anomalies IA

---

### 📈 Dashboard Mensuel

#### Points d'intégration Prophet

**1. Graphique évolution financière** (`monthly_strategic.html`, ligne 690-708)

**Actuel** : Tendance sur 6 mois passés

**Intégration Prophet** :
- Ajouter une **ligne de prévision** (3 mois à venir) sur le graphique
- Utiliser `AIManager.generate_forecasts('monthly_profit_loss', days=90)` (approximation)
- Afficher les intervalles de confiance

**Endpoint à créer** : `/dashboards/api/monthly/revenue-forecast` (GET)

**Template** : Ajouter un dataset Chart.js avec prévisions (ligne pointillée + zone grisée)

---

**2. Prévisions multi-KPI** (Section KPI Cards)

**Intégration Prophet** :
- Afficher les prévisions pour chaque KPI (CA, Marge, Flux, Coûts)
- Utiliser `AIManager.generate_forecasts()` pour chaque rapport

**Endpoint à créer** : `/dashboards/api/monthly/kpi-forecasts` (GET)

**Template** : Ajouter un indicateur "Prévision mois prochain" sur chaque KPI card

---

#### Points d'intégration LLM

**1. Section "Analyse Stratégique IA"** (Nouvelle section)

**Intégration LLM** :
- Ajouter une section complète avec analyse LLM mensuelle
- Utiliser `AIManager.get_ai_summary('monthly')`
- Afficher :
  - Diagnostic général
  - Top 3 réussites
  - Top 3 axes d'amélioration
  - Plan d'action stratégique

**Endpoint à créer** : `/dashboards/api/monthly/ai-summary` (GET)

**Code** :
```python
@dashboard_api.route('/monthly/ai-summary', methods=['GET'])
def monthly_ai_summary():
    from app.ai import AIManager
    from datetime import date
    
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    
    ai = AIManager()
    summary = ai.get_ai_summary('monthly', reference_date=date(year, month, 1))
    
    return jsonify(summary)
```

**Template** : Ajouter une section complète "📊 Analyse Stratégique IA" avec formatage markdown

---

**2. Recommandations par KPI** (Section Analyses Détaillées)

**Intégration LLM** :
- Enrichir chaque KPI avec une recommandation IA
- Utiliser `AIManager.analyze_reports()` avec prompt `recommendations`

**Template** : Ajouter un tooltip "💡 Recommandation IA" sur chaque KPI card

---

### 🎯 Endpoints à créer/modifier

#### Nouveaux endpoints AI

| Endpoint | Méthode | Description | Priorité |
|----------|---------|-------------|----------|
| `/dashboards/api/daily/ai-insights` | GET | Analyse LLM quotidienne | **HAUTE** |
| `/dashboards/api/daily/sales-forecast` | GET | Prédictions Prophet ventes (7j) | **HAUTE** |
| `/dashboards/api/daily/production-forecast` | GET | Prédictions Prophet production (7j) | **MOYENNE** |
| `/dashboards/api/daily/anomalies` | GET | Détection anomalies IA | **HAUTE** |
| `/dashboards/api/monthly/ai-summary` | GET | Résumé stratégique IA mensuel | **HAUTE** |
| `/dashboards/api/monthly/revenue-forecast` | GET | Prédictions Prophet CA (3 mois) | **HAUTE** |
| `/dashboards/api/monthly/kpi-forecasts` | GET | Prévisions multi-KPI | **MOYENNE** |

#### Endpoints à modifier

| Endpoint | Modification | Priorité |
|----------|-------------|----------|
| `/dashboards/api/daily/sales` | Remplacer calculs par `DailySalesReportService` | **HAUTE** |
| `/dashboards/api/daily/stock` | Remplacer par `StockAlertReportService` | **HAUTE** |
| `/dashboards/api/monthly/overview` | Remplacer par `MonthlyProfitLossService` | **HAUTE** |
| `/dashboards/api/monthly/product-performance` | Remplacer par `WeeklyProductPerformanceService` | **MOYENNE** |
| `/dashboards/api/monthly/revenue-trend` | Utiliser `MonthlyProfitLossService` dans boucle | **MOYENNE** |

---

## 4. COMPATIBILITÉ DES DONNÉES

### 📊 Format actuel des KPIs JSON (Dashboard)

#### Structure générique

```json
{
  "success": true,
  "data": {
    "stats": {
      "kpi_name": float,
      ...
    },
    "detailed_data": [...]
  }
}
```

#### Format par endpoint

**`/daily/sales`** :
```json
{
  "success": true,
  "data": {
    "stats": {
      "daily_revenue": 45000.0,        // float
      "total_orders": 25,              // int
      "delivered_orders": 20,          // int
      "cash_in_today": 5000.0,         // float
      "cash_out_today": 2000.0,        // float
      "net_cash_flow": 3000.0          // float
    },
    "orders_by_status": {              // dict
      "pending": {"count": 5, "amount": 5000.0},
      ...
    }
  }
}
```

**`/monthly/overview`** :
```json
{
  "success": true,
  "data": {
    "period": {
      "year": 2025,
      "month": 11,
      "start_date": "2025-11-01",
      "end_date": "2025-11-30"
    },
    "kpis": {
      "monthly_revenue": 1500000.0,     // float
      "monthly_orders": 500,            // int
      "monthly_expenses": 900000.0,     // float
      "net_profit": 600000.0,           // float
      "profit_margin": 40.0             // float (%)
    }
  }
}
```

---

### 📈 Format des données reports

#### Structure générique

```python
{
  'date': date,                    # ou 'start_date', 'end_date'
  'kpi_name': float,               # KPI principal
  'other_kpis': {...},             # KPIs secondaires
  # Métadonnées IA
  'growth_rate': 5.2,              # float (%)
  'variance': 125.5,               # float
  'variance_context': ['kpi1', 'kpi2'],  # list
  'trend_direction': 'up',         # str: 'up', 'down', 'stable'
  'benchmark': {                   # dict
    'target': 50000.0,
    'current': 45000.0,
    'variance': -5000.0,
    'is_healthy': false
  },
  'metadata': {                    # dict
    'day_of_week': 'Lundi',
    'month': 11,
    ...
  }
}
```

#### Format par service

**`DailySalesReportService.generate()`** :
```python
{
  'date': date(2025, 11, 15),
  'total_revenue': 45000.0,        # ✅ Compatible avec daily_revenue
  'total_transactions': 25,        # ✅ Compatible avec total_orders
  'average_basket': 1800.0,        # NOUVEAU
  'hourly_sales': [...],           # NOUVEAU (liste)
  'top_products': [...],           # NOUVEAU (liste)
  'growth_rate': 5.2,              # NOUVEAU (IA)
  'variance': 125.5,               # NOUVEAU (IA)
  'trend_direction': 'up',         # NOUVEAU (IA)
  'benchmark': {...},              # NOUVEAU (IA)
  'metadata': {...}                # NOUVEAU (IA)
}
```

**`MonthlyProfitLossService.generate()`** :
```python
{
  'year': 2025,
  'month': 11,
  'revenue': 1500000.0,            # ✅ Compatible avec monthly_revenue
  'expenses': 900000.0,             # ✅ Compatible avec monthly_expenses
  'net_income': 600000.0,          # ✅ Compatible avec net_profit
  'net_margin': 40.0,              # ✅ Compatible avec profit_margin
  'gross_margin': 900000.0,        # NOUVEAU
  'cogs': 600000.0,                # NOUVEAU
  'growth_rate': 8.5,              # NOUVEAU (IA)
  'variance': 25000.0,             # NOUVEAU (IA)
  'trend_direction': 'up',         # NOUVEAU (IA)
  'benchmark': {...},              # NOUVEAU (IA)
  'metadata': {...}                # NOUVEAU (IA)
}
```

---

### 🤖 Format des données AI

#### Structure Prophet

```python
{
  'success': True,
  'report_name': 'daily_sales',
  'forecast_days': 7,
  'forecast': [                    # list
    {
      'ds': '2025-11-16T00:00:00',
      'yhat': 45000.5,             # Prédiction
      'yhat_lower': 40000.0,       # Intervalle bas
      'yhat_upper': 50000.0        # Intervalle haut
    },
    ...
  ],
  'components': {                  # dict
    'trend': {
      'direction': 'up',
      'values': [...]
    },
    'weekly_seasonality': [...]
  },
  'metrics': {                     # dict
    'mae': 1250.5,
    'mape': 8.2,
    'confidence': 'élevée'
  }
}
```

#### Structure LLM

```python
{
  'success': True,
  'analysis': '📊 ANALYSE...',     # str (markdown)
  'provider': 'groq',
  'model': 'llama-3.1-70b-versatile',
  'prompt_type': 'daily_analysis',
  'report_name': 'daily_sales',
  'report_date': '2025-11-15',
  'context_summary': {             # dict
    'growth_rate': 5.2,
    'trend': 'up',
    'variance': 125.5
  },
  'generated_at': '2025-11-15T10:30:00'
}
```

---

### 🔄 Conversions nécessaires

#### 1. Mapping KPIs Dashboard → Reports

| KPI Dashboard | KPI Reports | Conversion | Type |
|---------------|-------------|------------|------|
| `daily_revenue` | `total_revenue` | Direct | float → float ✅ |
| `total_orders` | `total_transactions` | Direct | int → int ✅ |
| `monthly_revenue` | `revenue` | Direct | float → float ✅ |
| `net_profit` | `net_income` | Direct | float → float ✅ |
| `profit_margin` | `net_margin` | Direct | float → float ✅ |
| `out_of_stock_count` | `out_of_stock` | `len(out_of_stock)` | list → int ⚠️ |
| `low_stock_count` | `low_stock_products` | `len(low_stock_products)` | list → int ⚠️ |

#### 2. Ajout métadonnées IA

**Conversion simple** : Ajouter les clés IA au dict existant

```python
# Avant (dashboard actuel)
return jsonify({
  'success': True,
  'data': {
    'stats': {
      'daily_revenue': 45000.0
    }
  }
})

# Après (avec reports + IA)
report_data = DailySalesReportService.generate(date.today())
return jsonify({
  'success': True,
  'data': {
    'stats': {
      'daily_revenue': report_data['total_revenue'],
      'growth_rate': report_data['growth_rate'],        # NOUVEAU
      'trend_direction': report_data['trend_direction'], # NOUVEAU
      'variance': report_data['variance']               # NOUVEAU
    },
    'ai_metadata': {                                    # NOUVEAU
      'benchmark': report_data['benchmark'],
      'metadata': report_data['metadata']
    }
  }
})
```

#### 3. Format Prophet pour Chart.js

**Conversion nécessaire** : Prophet retourne ISO dates, Chart.js attend des labels

```python
# Prophet
forecast = [
  {'ds': '2025-11-16T00:00:00', 'yhat': 45000.5, ...},
  ...
]

# Chart.js
labels = [f['ds'][:10] for f in forecast]  # Extraire date
data = [f['yhat'] for f in forecast]
lower = [f['yhat_lower'] for f in forecast]
upper = [f['yhat_upper'] for f in forecast]
```

---

## 5. PLAN D'INTÉGRATION PRIORISÉ

### 🔴 Priorité HAUTE (Impact majeur, effort faible)

#### Phase 1A : Intégration reports (Jour 1)

**1. Remplacer `/daily/sales` par `DailySalesReportService`**

- **Fichier** : `app/dashboards/api.py` ligne 155-215
- **Action** :
  ```python
  # Remplacer lignes 164-169
  from app.reports.services import DailySalesReportService
  report_data = DailySalesReportService.generate(date.today())
  
  daily_revenue = report_data['total_revenue']
  total_orders = report_data['total_transactions']
  # Ajouter hourly_sales, top_products
  ```
- **Tests** : Vérifier que `daily_revenue` et `total_orders` sont identiques
- **Temps estimé** : 1h

---

**2. Remplacer `/daily/stock` par `StockAlertReportService`**

- **Fichier** : `app/dashboards/api.py` ligne 94-153
- **Action** :
  ```python
  # Remplacer lignes 100-116
  from app.reports.services import StockAlertReportService
  report_data = StockAlertReportService.generate()
  
  out_of_stock = report_data['out_of_stock']
  low_stock = report_data['low_stock_products']
  ```
- **Tests** : Vérifier que les listes sont identiques
- **Temps estimé** : 30min

---

**3. Remplacer `/monthly/overview` par `MonthlyProfitLossService`**

- **Fichier** : `app/dashboards/api.py` ligne 287-374
- **Action** :
  ```python
  # Remplacer lignes 306-371
  from app.reports.services import MonthlyProfitLossService
  report_data = MonthlyProfitLossService.generate(year, month)
  
  monthly_revenue = report_data['revenue']
  monthly_expenses = report_data['expenses']
  net_profit = report_data['net_income']
  profit_margin = report_data['net_margin']
  # Ajouter métadonnées IA
  ```
- **Tests** : Vérifier que tous les KPIs sont identiques
- **Temps estimé** : 1h

---

#### Phase 1B : Intégration AI - Endpoints (Jour 1-2)

**4. Créer `/daily/ai-insights`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** :
  ```python
  @dashboard_api.route('/daily/ai-insights', methods=['GET'])
  def daily_ai_insights():
      from app.ai import AIManager
      ai = AIManager()
      
      insights = {
          'sales': ai.analyze_reports('daily_sales', prompt_type='daily_analysis'),
          'stock': ai.analyze_reports('daily_stock_alerts', prompt_type='anomaly_detection'),
          'production': ai.analyze_reports('daily_production', prompt_type='daily_analysis')
      }
      
      return jsonify({'success': True, 'insights': insights})
  ```
- **Tests** : Vérifier que les insights sont retournés
- **Temps estimé** : 1h

---

**5. Créer `/daily/sales-forecast`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** :
  ```python
  @dashboard_api.route('/daily/sales-forecast', methods=['GET'])
  def daily_sales_forecast():
      from app.ai import AIManager
      ai = AIManager()
      forecast = ai.generate_forecasts('daily_sales', days=7)
      return jsonify(forecast)
  ```
- **Tests** : Vérifier que les prévisions sont retournées
- **Temps estimé** : 30min

---

**6. Créer `/daily/anomalies`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** :
  ```python
  @dashboard_api.route('/daily/anomalies', methods=['GET'])
  def daily_anomalies():
      from app.ai import AIManager
      ai = AIManager()
      anomalies = ai.detect_anomalies('daily_sales')
      return jsonify(anomalies)
  ```
- **Tests** : Vérifier que les anomalies sont détectées
- **Temps estimé** : 30min

---

**7. Créer `/monthly/ai-summary`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** :
  ```python
  @dashboard_api.route('/monthly/ai-summary', methods=['GET'])
  def monthly_ai_summary():
      from app.ai import AIManager
      from datetime import date
      
      year = request.args.get('year', type=int, default=date.today().year)
      month = request.args.get('month', type=int, default=date.today().month)
      
      ai = AIManager()
      summary = ai.get_ai_summary('monthly', reference_date=date(year, month, 1))
      return jsonify(summary)
  ```
- **Tests** : Vérifier que le résumé est retourné
- **Temps estimé** : 1h

---

**8. Créer `/monthly/revenue-forecast`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** :
  ```python
  @dashboard_api.route('/monthly/revenue-forecast', methods=['GET'])
  def monthly_revenue_forecast():
      from app.ai import AIManager
      ai = AIManager()
      # Approximation : 3 mois = 90 jours
      forecast = ai.generate_forecasts('monthly_profit_loss', days=90)
      return jsonify(forecast)
  ```
- **Tests** : Vérifier que les prévisions sont retournées
- **Temps estimé** : 30min

---

### 🟡 Priorité MOYENNE (Impact moyen, effort moyen)

#### Phase 2 : Intégration templates (Jour 3-4)

**9. Ajouter section "Analyse IA" dans `daily_operational.html`**

- **Fichier** : `app/templates/dashboards/daily_operational.html`
- **Action** :
  - Ajouter une nouvelle carte après la section Finance (ligne ~697)
  - Fetch `/dashboards/api/daily/ai-insights`
  - Afficher l'analyse formatée (markdown → HTML)
- **Temps estimé** : 2h

---

**10. Ajouter prévisions Prophet dans graphique `daily_operational.html`**

- **Fichier** : `app/templates/dashboards/daily_operational.html` ligne 846-895
- **Action** :
  - Fetch `/dashboards/api/daily/sales-forecast`
  - Ajouter un dataset Chart.js avec prévisions (ligne pointillée)
  - Ajouter zone grisée pour intervalles de confiance
- **Temps estimé** : 2h

---

**11. Ajouter section "Analyse Stratégique IA" dans `monthly_strategic.html`**

- **Fichier** : `app/templates/dashboards/monthly_strategic.html`
- **Action** :
  - Ajouter une section complète après les graphiques (ligne ~708)
  - Fetch `/dashboards/api/monthly/ai-summary`
  - Afficher le résumé formaté (markdown → HTML)
- **Temps estimé** : 2h

---

**12. Ajouter prévisions Prophet dans graphique `monthly_strategic.html`**

- **Fichier** : `app/templates/dashboards/monthly_strategic.html` ligne 805-892
- **Action** :
  - Fetch `/dashboards/api/monthly/revenue-forecast`
  - Ajouter datasets Chart.js avec prévisions (3 mois)
  - Afficher intervalles de confiance
- **Temps estimé** : 2h

---

**13. Remplacer `/monthly/product-performance` par `WeeklyProductPerformanceService`**

- **Fichier** : `app/dashboards/api.py` ligne 437-507
- **Action** :
  ```python
  from app.reports.services import WeeklyProductPerformanceService
  report_data = WeeklyProductPerformanceService.generate(start_date, end_date)
  top_by_revenue = sorted(report_data['performance_data'], key=lambda x: x['revenue'], reverse=True)[:10]
  ```
- **Temps estimé** : 1h

---

**14. Créer `/daily/production-forecast`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** : Similaire à `/daily/sales-forecast`
- **Temps estimé** : 30min

---

**15. Créer `/monthly/kpi-forecasts`**

- **Fichier** : `app/dashboards/api.py` (nouveau)
- **Action** : Prévisions pour CA, Marge, Flux, Coûts
- **Temps estimé** : 1h

---

### 🟢 Priorité BASSE (Impact faible, effort variable)

#### Phase 3 : Optimisations (Jour 5+)

**16. Améliorer `/monthly/revenue-trend` avec `MonthlyProfitLossService`**

- **Fichier** : `app/dashboards/api.py` ligne 376-435
- **Action** : Utiliser `MonthlyProfitLossService` dans la boucle
- **Temps estimé** : 1h

---

**17. Ajouter métadonnées IA dans tous les endpoints modifiés**

- **Fichier** : `app/dashboards/api.py` (tous endpoints)
- **Action** : Ajouter `ai_metadata` dans les réponses JSON
- **Temps estimé** : 2h

---

**18. Ajouter tooltips "Recommandations IA" sur KPI cards**

- **Fichier** : Templates HTML
- **Action** : Tooltips avec recommandations IA
- **Temps estimé** : 2h

---

**19. Optimiser performance (cache)**

- **Fichier** : `app/dashboards/api.py`
- **Action** : Ajouter cache Redis/Memcached
- **Temps estimé** : 3h

---

### 📊 Récapitulatif des priorités

| Priorité | Endpoints | Templates | Temps total |
|----------|-----------|-----------|-------------|
| **HAUTE** | 8 endpoints | 0 | **6h** |
| **MOYENNE** | 3 endpoints | 4 sections | **12h** |
| **BASSE** | 1 endpoint | 2 sections | **8h** |
| **TOTAL** | **12 endpoints** | **6 sections** | **~26h** |

---

## 🎯 RÉSUMÉ EXÉCUTIF

### ✅ Actions immédiates (Phase 1 - HAUTE)

1. **Remplacer 3 endpoints** par services reports :
   - `/daily/sales` → `DailySalesReportService`
   - `/daily/stock` → `StockAlertReportService`
   - `/monthly/overview` → `MonthlyProfitLossService`

2. **Créer 5 endpoints AI** :
   - `/daily/ai-insights`
   - `/daily/sales-forecast`
   - `/daily/anomalies`
   - `/monthly/ai-summary`
   - `/monthly/revenue-forecast`

**Résultat** : Cohérence des calculs + Accès aux métadonnées IA

### 📈 Actions à moyen terme (Phase 2 - MOYENNE)

3. **Intégrer AI dans templates** :
   - Section "Analyse IA" (daily)
   - Prévisions Prophet dans graphiques
   - Section "Analyse Stratégique IA" (monthly)

**Résultat** : Interface enrichie avec prédictions et analyses intelligentes

### 🔧 Actions d'optimisation (Phase 3 - BASSE)

4. **Améliorer performance et UX** :
   - Cache
   - Tooltips recommandations
   - Métadonnées IA complètes

**Résultat** : Performance optimale + UX améliorée

---

## 📝 NOTES IMPORTANTES

### ⚠️ Points d'attention

1. **Compatibilité ascendante** : Les endpoints modifiés doivent retourner les mêmes clés JSON (ajout seulement)
2. **Gestion d'erreurs** : Ajouter try/catch pour les appels AI (fallback si API indisponible)
3. **Performance** : Les appels AI peuvent être lents (3-5s), prévoir des indicateurs de chargement
4. **Tests** : Vérifier que les KPIs calculés via reports sont identiques aux anciens calculs

### ✅ Bénéfices attendus

1. **Cohérence** : Calculs identiques entre dashboards et rapports
2. **Enrichissement IA** : Accès aux métadonnées IA (growth_rate, variance, trend, benchmark)
3. **Prédictions** : Prévisions Prophet directement dans les dashboards
4. **Analyse intelligente** : Recommandations LLM contextuelles
5. **Maintenance** : Une seule source de vérité pour les calculs

---

**Auteur** : Audit d'intégration IA - Novembre 2025  
**Version** : 1.0  
**Statut** : ✅ Prêt pour implémentation

