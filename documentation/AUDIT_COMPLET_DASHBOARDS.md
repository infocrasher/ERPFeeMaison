# 📊 AUDIT COMPLET DU SYSTÈME DE DASHBOARDS
## ERP Fée Maison - Rapport Technique Exhaustif

**Date de l'audit :** 2025-01-XX  
**Version du système :** Production  
**Périmètre :** Analyse complète sans modification de code

---

## 📋 TABLE DES MATIÈRES

1. [BACKEND — ROUTES ET LOGIQUE MÉTIER](#1-backend--routes-et-logique-métier)
2. [FRONTEND — STRUCTURE DES TEMPLATES HTML](#2-frontend--structure-des-templates-html)
3. [JAVASCRIPT — INTERACTIONS ET API](#3-javascript--interactions-et-api)
4. [INTÉGRATIONS IA ET PRÉDICTIONS](#4-intégrations-ia-et-prédictions)
5. [INTÉGRATION COMPTABLE ET MÉTIER](#5-intégration-comptable-et-métier)
6. [PROBLÈMES ET LIMITES IDENTIFIÉS](#6-problèmes-et-limites-identifiés)
7. [RECOMMANDATIONS FINALES](#7-recommandations-finales)

---

## 1. BACKEND — ROUTES ET LOGIQUE MÉTIER

### 1.1 Architecture Générale

Le système de dashboards est organisé en **deux modules distincts** :

#### Module Principal : `app/dashboards/`
- **Blueprint principal :** `dashboards_bp` (préfixe `/dashboards`)
- **Structure :**
  ```
  app/dashboards/
  ├── __init__.py         # Blueprint principal et organisation
  ├── api.py              # Endpoints API JSON (/dashboards/api/*)
  └── routes.py          # Routes templates HTML (/dashboards/*)
  ```

#### Module Secondaire : `app/orders/dashboard_routes.py`
- **Blueprint :** `dashboard_bp` (sans préfixe, routes directes)
- **Routes spécialisées :** Production, Shop, Ingredients Alerts

### 1.2 Routes Templates HTML

#### 1.2.1 Module `app/dashboards/routes.py`

| Endpoint | Fonction | Description | Variables Template |
|----------|----------|-------------|-------------------|
| `/dashboards/daily` | `daily_dashboard()` | Dashboard journalier opérationnel | `title` |
| `/dashboards/monthly` | `monthly_dashboard()` | Dashboard mensuel stratégique | `title`, `now`, `months` (liste 12 mois) |

**Décorateurs :** `@login_required`, `@admin_required`

#### 1.2.2 Module `app/orders/dashboard_routes.py`

| Endpoint | Fonction | Description | Variables Template |
|----------|----------|-------------|-------------------|
| `/dashboard/production` | `production_dashboard()` | Vue production temps réel | `orders`, `orders_on_time`, `orders_soon`, `orders_overdue`, `total_orders`, `title` |
| `/dashboard/shop` | `shop_dashboard()` | Gestion commandes magasin | `orders_in_production`, `orders_waiting_pickup`, `orders_ready_delivery`, `orders_at_counter`, `orders_delivered_unpaid`, `cash_session_open`, `title` |
| `/dashboard/ingredients-alerts` | `ingredients_alerts()` | Alertes ingrédients | `low_stock_ingredients`, `out_of_stock_ingredients`, `title` |
| `/dashboard/admin` | `admin_dashboard()` | Dashboard administrateur | `orders_today`, `active_employees`, `low_stock_count`, `overdue_orders`, `title` |
| `/dashboard/sales` | `sales_dashboard()` | Dashboard ventes | `delivered_orders`, `title` |
| `/dashboard/api/orders-stats` | `orders_stats_api()` | API stats commandes (JSON) | Retourne JSON avec `pending`, `in_production`, `ready_at_shop`, `delivered` |

**Décorateurs :** `@login_required`, `@admin_required`

### 1.3 Routes API JSON (`app/dashboards/api.py`)

#### 1.3.1 Dashboard Journalier — Pilotage Opérationnel

##### `/dashboards/api/daily/production` (GET)
- **Fonction :** `daily_production()`
- **Description :** Commandes en retard, urgentes et normales
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "stats": {
        "overdue_count": int,
        "urgent_count": int,
        "normal_count": int,
        "total_production": int
      },
      "overdue_orders": [...],
      "urgent_orders": [...],
      "normal_orders": [...]
    }
  }
  ```
- **Logique métier :**
  - Commandes en retard : `due_date < now` ET statut `pending` ou `in_production`
  - Commandes urgentes : `due_date` dans les 2h
  - Commandes normales : `due_date > now + 2h`
- **Dépendances :** `Order`, `OrderItem`

##### `/dashboards/api/daily/stock` (GET)
- **Fonction :** `daily_stock()`
- **Description :** Alertes stock et niveaux critiques
- **Intégration Reports :** Utilise `StockAlertReportService.generate()` (Phase 1)
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "stats": {
        "out_of_stock_count": int,
        "low_stock_count": int,
        "total_stock_value": float,
        "today_movements": int,
        "benchmark": {}  // Métadonnées IA
      },
      "out_of_stock": [...],
      "low_stock": [...]
    }
  }
  ```
- **Fallback :** Si `StockAlertReportService` échoue, calcul direct via `Product.query`
- **Dépendances :** `Product`, `Category`, `StockAlertReportService`

##### `/dashboards/api/daily/sales` (GET)
- **Fonction :** `daily_sales()`
- **Description :** CA et commandes du jour
- **Intégration Reports :** Utilise `DailySalesReportService.generate(today)` (Phase 1)
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "stats": {
        "daily_revenue": float,
        "total_orders": int,
        "delivered_orders": int,
        "cash_session_open": bool,
        "cash_in_today": float,
        "cash_out_today": float,
        "net_cash_flow": float,
        "growth_rate": float,      // Métadonnées IA
        "trend_direction": str     // Métadonnées IA
      },
      "orders_by_status": {...},
      "cash_session": {...}
    }
  }
  ```
- **Fallback :** Calcul direct si service échoue
- **Dépendances :** `Order`, `CashRegisterSession`, `CashMovement`, `DailySalesReportService`

##### `/dashboards/api/daily/employees` (GET)
- **Fonction :** `daily_employees()`
- **Description :** Présence et performance employés
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "stats": {
        "total_employees": int,
        "present_today": int,
        "absent_today": int,
        "total_hours_worked": float,
        "attendance_rate": float
      },
      "employees": [...]
    }
  }
  ```
- **Dépendances :** `Employee`, `AttendanceRecord`

#### 1.3.2 Dashboard Mensuel — Analyse Stratégique

##### `/dashboards/api/monthly/overview` (GET)
- **Fonction :** `monthly_overview()`
- **Paramètres :** `year` (int), `month` (int) — défaut : mois actuel
- **Intégration Reports :** Utilise `MonthlyProfitLossService.generate(year, month)` (Phase 1)
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "period": {
        "year": int,
        "month": int,
        "start_date": "ISO",
        "end_date": "ISO"
      },
      "kpis": {
        "monthly_revenue": float,
        "monthly_orders": int,
        "monthly_expenses": float,
        "net_profit": float,
        "profit_margin": float,
        "stock_value": float,
        "active_employees": int,
        "total_salary_cost": float,
        "revenue_per_employee": float,
        "growth_rate": float,        // Métadonnées IA
        "trend_direction": str,      // Métadonnées IA
        "variance": float,           // Métadonnées IA
        "benchmark": {}              // Métadonnées IA
      }
    }
  }
  ```
- **Dépendances :** `Order`, `Product`, `Employee`, `Account`, `JournalEntry`, `JournalEntryLine`, `MonthlyProfitLossService`

##### `/dashboards/api/monthly/revenue-trend` (GET)
- **Fonction :** `monthly_revenue_trend()`
- **Paramètres :** `months` (int, défaut: 12)
- **Description :** Tendance des revenus sur N mois
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": [
      {
        "period": "YYYY-MM",
        "year": int,
        "month": int,
        "revenue": float,
        "orders": int,
        "avg_order_value": float
      },
      ...
    ]
  }
  ```
- **Dépendances :** `Order`

##### `/dashboards/api/monthly/product-performance` (GET)
- **Fonction :** `monthly_product_performance()`
- **Paramètres :** `year`, `month`, `limit` (défaut: 10)
- **Intégration Reports :** Utilise `WeeklyProductPerformanceService.generate(start_date, end_date)` (Phase 1)
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "top_by_revenue": [...],
      "top_by_quantity": [...]
    }
  }
  ```
- **Dépendances :** `Product`, `OrderItem`, `Order`, `Category`, `WeeklyProductPerformanceService`

##### `/dashboards/api/monthly/employee-performance` (GET)
- **Fonction :** `monthly_employee_performance()`
- **Paramètres :** `year`, `month`
- **Description :** Performance employés (ROI, erreurs, productivité)
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "employees": [...],
      "summary": {
        "total_employees": int,
        "total_revenue": float,
        "total_cost": float,
        "avg_roi": float,
        "avg_error_rate": float
      }
    }
  }
  ```
- **Dépendances :** `Employee`, `Order`, `OrderIssue`

#### 1.3.3 Endpoints Utilitaires

##### `/dashboards/api/refresh` (POST)
- **Fonction :** `refresh_dashboard()`
- **Description :** Forcer le rafraîchissement des données (cache invalidation future)
- **Retour :** `{"success": true, "message": "...", "timestamp": "ISO"}`

##### `/dashboards/api/export/monthly` (GET)
- **Fonction :** `export_monthly_dashboard()`
- **Description :** Export PDF du dashboard mensuel
- **Dépendances :** `weasyprint` (optionnel)
- **Paramètres :** `year`, `month`

### 1.4 Endpoints IA (Phase 1 — Intégration)

#### `/dashboards/api/daily/ai-insights` (GET)
- **Fonction :** `daily_ai_insights()`
- **Description :** Analyses IA multi-rapports (ventes, stock, production)
- **Intégration :** `AIManager.analyze_reports()`
- **Données retournées :**
  ```json
  {
    "success": true,
    "data": {
      "sales": {...},      // Analyse LLM ventes
      "stock": {...},      // Analyse LLM stock
      "production": {...}, // Analyse LLM production
      "timestamp": "ISO"
    },
    "source": "ai_manager"
  }
  ```
- **Fallback :** Messages d'erreur si IA indisponible
- **Dépendances :** `AIManager` (`app/ai`)

#### `/dashboards/api/daily/sales-forecast` (GET)
- **Fonction :** `daily_sales_forecast()`
- **Paramètres :** `days` (int, défaut: 7)
- **Description :** Prévisions Prophet pour les ventes
- **Intégration :** `AIManager.generate_forecasts('daily_sales', days=days)`
- **Dépendances :** `AIManager`, Prophet

#### `/dashboards/api/daily/anomalies` (GET)
- **Fonction :** `daily_anomalies()`
- **Description :** Détection d'anomalies IA (z-score + LLM)
- **Intégration :** `AIManager.detect_anomalies('daily_sales')`
- **Dépendances :** `AIManager`

#### `/dashboards/api/monthly/ai-summary` (GET)
- **Fonction :** `monthly_ai_summary()`
- **Paramètres :** `year`, `month`
- **Description :** Résumé stratégique IA mensuel avec recommandations
- **Intégration :** `AIManager.get_ai_summary('monthly', reference_date=...)`
- **Dépendances :** `AIManager`

### 1.5 Hiérarchie des Dashboards

```
Dashboard Principal (main/dashboard.html)
 ├── Dashboard Journalier (/dashboards/daily)
 │    ├── Section Production
 │    ├── Section Stock
 │    ├── Section Ventes
 │    ├── Section Employés
 │    └── Section IA (insights, anomalies, prévisions)
 │
 ├── Dashboard Mensuel (/dashboards/monthly)
 │    ├── Vue d'ensemble (KPIs)
 │    ├── Tendance revenus
 │    ├── Performance produits
 │    ├── Performance employés
 │    └── Résumé stratégique IA
 │
 ├── Dashboard Production (/dashboard/production)
 │    └── Commandes en temps réel
 │
 ├── Dashboard Shop (/dashboard/shop)
 │    ├── En Production
 │    ├── Attente Retrait
 │    ├── Prêt à Livrer
 │    ├── Au Comptoir
 │    └── Livré Non Payé
 │
 └── Dashboard Comptabilité (/accounting/)
      └── KPIs financiers
```

### 1.6 Intégrations avec Autres Modules

#### Module Reports (`app/reports/services.py`)
- **Services utilisés :**
  - `DailySalesReportService` → `/dashboards/api/daily/sales`
  - `StockAlertReportService` → `/dashboards/api/daily/stock`
  - `MonthlyProfitLossService` → `/dashboards/api/monthly/overview`
  - `WeeklyProductPerformanceService` → `/dashboards/api/monthly/product-performance`
- **Métadonnées enrichies :** `growth_rate`, `trend_direction`, `variance`, `benchmark`

#### Module AI (`app/ai/`)
- **AIManager :** Orchestrateur principal
- **Méthodes utilisées :**
  - `analyze_reports()` → Insights quotidiens
  - `generate_forecasts()` → Prévisions Prophet
  - `detect_anomalies()` → Détection anomalies
  - `get_ai_summary()` → Résumé mensuel

#### Module Accounting (`app/accounting/services.py`)
- **DashboardService :** Utilisé par `main/dashboard` (pas directement par dashboards)
- **Méthodes :** `get_daily_revenue()`, `get_monthly_revenue()`, etc.

---

## 2. FRONTEND — STRUCTURE DES TEMPLATES HTML

### 2.1 Templates Principaux

#### 2.1.1 `daily_operational.html` (Dashboard Journalier)

**Fichier :** `app/templates/dashboards/daily_operational.html`  
**Route :** `/dashboards/daily`  
**Variables utilisées :** `title` (depuis backend)

**Sections visibles :**

1. **Header moderne** (`.modern-header`)
   - Titre "⚡ DASHBOARD LIVE"
   - Indicateur temps réel (`.live-indicator`)
   - Horloge dynamique (`#currentTime`)

2. **Bannière alertes** (`.alert-banner`)
   - Commandes urgentes (`#commandesUrgentes`)
   - Commandes proches (`#commandesProches`)
   - Bouton "Alerter Équipe"

3. **Bannière anomalies IA** (`.anomaly-banner`, Phase 2)
   - Affichage conditionnel si anomalies détectées
   - Message dynamique (`#anomalyMessage`)

4. **Métriques principales** (`.metrics-container`)
   - **Production** (`.metric-card.danger`)
     - Nombre retards (`#nbRetard`)
     - Liste commandes (`#prodStatusList`)
     - Barre progression (`#prodProgressFill`)
   - **Stock** (`.metric-card.warning`)
     - Ruptures (`#nbRuptures`)
     - Liste produits (`#stockStatusList`)
   - **Équipe** (`.metric-card.success`)
     - Présents (`#nbPresents`)
     - Liste employés (`#rhStatusList`)
     - Barre progression (`#rhProgressFill`)
   - **Finance** (`.metric-card.info`)
     - CA temps réel (`#caTempsReel`)
     - Liste statuts (`#financeStatusList`)

5. **Graphiques** (`.charts-container`)
   - **Évolution commandes** (`#ordersChart`)
     - Chart.js (type: `line`)
     - Intégration prévisions Prophet (Phase 2)
   - **Répartition statuts** (`#statusChart`)
     - Chart.js (type: `doughnut`)

6. **Section Analyse IA** (`.ai-insights-section`, Phase 2)
   - Badge "Intelligence Artificielle"
   - Grille insights (`#aiInsightsContent`)
   - Cartes insights (ventes, stock, production)

**KPIs affichés :**
- Commandes en retard/urgentes/normales
- Ruptures de stock / Stock faible
- Employés présents / Taux présence
- CA du jour / Flux de caisse

**Périodes temporelles :**
- Temps réel (mise à jour continue)
- Aujourd'hui (filtrage par date)

**Actions utilisateur :**
- Navigation vers détails (boutons "Voir Détails", "Commander", etc.)
- Rafraîchissement automatique (toutes les 2 minutes)

#### 2.1.2 `monthly_strategic.html` (Dashboard Mensuel)

**Fichier :** `app/templates/dashboards/monthly_strategic.html`  
**Route :** `/dashboards/monthly`  
**Variables utilisées :** `title`, `now`, `months` (liste 12 mois)

**Sections visibles :**

1. **Header moderne** (`.modern-header`)
   - Titre "📈 DASHBOARD MENSUEL"
   - Sélecteur période (`#periodSelect`)
   - Horloge dynamique

2. **KPI Cards** (`.kpi-container`)
   - **CA Mensuel** (`.kpi-card.revenue`)
     - Valeur (`#kpiCaMensuel`)
     - Changement (`#kpiCaChange`)
     - Progression (`#kpiCaProgress`)
   - **Marge Brute** (`.kpi-card.margin`)
     - Valeur (`#kpiMarge`)
     - Changement (`#kpiMargeChange`)
   - **Flux de Trésorerie** (`.kpi-card.cashflow`)
     - Valeur (`#kpiFlux`)
     - Changement (`#kpiFluxChange`)
   - **Coût Matières Premières** (`.kpi-card.costs`)
     - Valeur (`#kpiMP`)
     - Changement (`#kpiMPChange`)

3. **Graphiques** (`.charts-container`)
   - **Évolution Financière** (`#financialChart`)
     - Chart.js (type: `line`)
     - 3 datasets : CA, Charges, Bénéfice
   - **Répartition des Coûts** (`#costChart`)
     - Chart.js (type: `doughnut`)

4. **Section Résumé Stratégique IA** (`.ai-strategic-section`, Phase 2)
   - Badge "Intelligence Artificielle"
   - Contenu résumé (`#aiStrategicContent`)
   - Recommandations (`#ai-recommendations`)
   - Score de confiance IA

5. **Analyses Détaillées** (`.analysis-container`)
   - Grille analyses (`#analysisGrid`)
   - ROI Employés, Rotation Stock, Coût par Commande, Marge Nette

6. **Alertes Financières** (`.alert-container`)
   - Section alertes (`#alertSection`)
   - Alertes conditionnelles (coûts élevés, bénéfice négatif, marge faible)

**KPIs affichés :**
- CA mensuel / Objectif
- Marge brute / Performance
- Flux de trésorerie / Liquidité
- Coût matières premières / % du CA
- ROI employés
- Taux rotation stock
- Marge nette

**Périodes temporelles :**
- Mois sélectionné (sélecteur)
- 6 mois (graphique évolution)
- 12 mois (tendance revenus)

**Actions utilisateur :**
- Changement de période (`changePeriod()`)
- Export PDF (futur)

#### 2.1.3 `production_dashboard.html` (Dashboard Production)

**Fichier :** `app/templates/dashboards/production_dashboard.html`  
**Route :** `/dashboard/production`  
**Variables utilisées :** `orders`, `orders_on_time`, `orders_soon`, `orders_overdue`, `total_orders`, `title`

**Sections visibles :**

1. **Header production** (`.production-header`)
   - Titre "Dashboard Production"
   - Horloge dynamique

2. **Statistiques** (`.stats-container`)
   - À Temps (`#orders-on-time`)
   - Bientôt Dûes (`#orders-soon`)
   - En Retard (`#orders-overdue`)
   - Total Aujourd'hui (`#total-orders`)

3. **Cartes commandes** (`.order-card`)
   - Temps restant (`#countdown-{order.id}`)
   - Informations produits
   - Métadonnées (heure prévue, notes)
   - Badge priorité (`#priority-{order.id}`)
   - Actions rapides (Voir, Signaler Erreur)

**Code couleur temporel :**
- **Vert** : Plus de 2h restantes
- **Orange** : 30min à 2h
- **Rouge** : Moins de 30min ou en retard

**Actions utilisateur :**
- Clic carte → Détails commande
- Boutons actions (Voir, Signaler Erreur)
- Rafraîchissement automatique (5 minutes)

#### 2.1.4 `shop_dashboard.html` (Dashboard Magasin)

**Fichier :** `app/templates/dashboards/shop_dashboard.html`  
**Route :** `/dashboard/shop`  
**Variables utilisées :** `orders_in_production`, `orders_waiting_pickup`, `orders_ready_delivery`, `orders_at_counter`, `orders_delivered_unpaid`, `cash_session_open`, `title`

**Sections visibles :**

1. **Header shop** (`.shop-header`)
   - Titre "Dashboard Magasin"
   - Horloge dynamique

2. **Statistiques** (`.stats-grid`)
   - En Production
   - Attente Retrait
   - Prêt à Livrer
   - Au Comptoir
   - Livré Non Payé

3. **5 Sections de commandes** (`.section-card`)
   - **En Production** (`.order-production`)
     - Boutons : Voir, Reçu, Signaler Erreur
   - **En Attente de Retrait** (`.order-pickup`)
     - Boutons : Voir, Encaisser (si caisse ouverte)
   - **Prêt à Livrer** (`.order-delivery`)
     - Boutons : Voir, Assigner Livreur, Encaisser
   - **Au Comptoir** (`.order-counter`)
     - Ordres production terminés (visibles 24h)
   - **Livré Non Payé** (`.order-unpaid`)
     - Boutons : Voir, Encaisser

4. **Modal Paiement** (`#paymentModal`)
   - Champ montant reçu (`#paymentAmountInput`)
   - Affichage : Total, Déjà encaissé, Solde, Monnaie à rendre
   - Bouton Confirmer

**Actions utilisateur :**
- Encaisser (modal si paiement partiel, direct si total)
- Assigner livreur
- Signaler erreur
- Rafraîchissement automatique (2 minutes)

#### 2.1.5 `ingredients_alerts.html` (Alertes Ingrédients)

**Fichier :** `app/templates/dashboards/ingredients_alerts.html`  
**Route :** `/dashboard/ingredients-alerts`  
**Variables utilisées :** `low_stock_ingredients`, `out_of_stock_ingredients`, `title`

**Sections visibles :**

1. **Header alertes** (`.alerts-header`)
   - Icône animation
   - Titre "Alertes Ingrédients"

2. **Vue d'ensemble statistiques** (`.stats-overview`)
   - Ingrédients Manquants
   - Stock Critique
   - À Commander
   - Coût Estimé

3. **Cartes ingrédients** (`.ingredient-card`)
   - Nom, catégorie
   - Stock actuel / Besoin
   - Badge urgence
   - Détails (Manque, Commandes affectées, Coût, Fournisseur)

4. **Suggestions d'optimisation** (`.action-suggestions`)

**Note :** Module en développement (données simulées affichées)

### 2.2 Hiérarchie Visuelle

```
Dashboard Général (main/dashboard.html)
 ├── Section "Ventes"
 │    ├── CA du jour
 │    └── Commandes du jour
 │
 ├── Section "Production"
 │    ├── Commandes en cours
 │    └── Retards
 │
 ├── Section "Commandes"
 │    ├── Par statut
 │    └── Urgentes
 │
 ├── Section "Stock"
 │    ├── Alertes
 │    └── Valeur totale
 │
 └── Section "IA / Prévisions"
      ├── Insights quotidiens
      ├── Prévisions Prophet
      └── Anomalies détectées
```

### 2.3 Intégrations IA Visuelles

#### Dashboard Journalier
- **Bannière anomalies** : Affichage conditionnel si anomalies détectées
- **Section insights IA** : 3 cartes (ventes, stock, production)
- **Graphique prévisions** : Ligne pointillée sur graphique commandes (Prophet)

#### Dashboard Mensuel
- **Section résumé stratégique IA** : Texte résumé + recommandations + score confiance
- **Métadonnées enrichies** : `growth_rate`, `trend_direction`, `variance` dans KPIs

---

## 3. JAVASCRIPT — INTERACTIONS ET API

### 3.1 Scripts Inline (dans les templates)

#### 3.1.1 `daily_operational.html`

**Fonctionnalités principales :**

1. **Mise à jour horloge** (`updateTime()`)
   - Format : `HH:MM:SS` (français)
   - Intervalle : 1 seconde

2. **Chargement données Production** (`/dashboards/api/daily/production`)
   - Mise à jour : `#nbRetard`, `#prodSubtitle`, `#prodStatusList`
   - Graphique statuts : Chart.js `doughnut`

3. **Chargement données Stock** (`/dashboards/api/daily/stock`)
   - Mise à jour : `#nbRuptures`, `#stockStatusList`

4. **Chargement données RH** (`/dashboards/api/daily/employees`)
   - Mise à jour : `#nbPresents`, `#rhStatusList`, `#rhProgressFill`

5. **Chargement données Finance** (`/dashboards/api/daily/sales`)
   - Mise à jour : `#caTempsReel`, `#financeStatusList`
   - Graphique commandes : Chart.js `line`
   - **Intégration prévisions Prophet** :
     - Appel `/dashboards/api/daily/sales-forecast?days=7`
     - Fusion données réelles + prévisions
     - Ligne pointillée orange pour prévisions

6. **Chargement anomalies IA** (`/dashboards/api/daily/anomalies`)
   - Affichage bannière si anomalies haute sévérité

7. **Chargement insights IA** (`/dashboards/api/daily/ai-insights`)
   - Rendu cartes insights (ventes, stock, production)
   - Fallback si IA indisponible

8. **Auto-refresh** : Toutes les 2 minutes

**Bibliothèques :**
- Chart.js (CDN)
- Font Awesome (icônes)

#### 3.1.2 `monthly_strategic.html`

**Fonctionnalités principales :**

1. **Mise à jour horloge** (`updateTime()`)

2. **Chargement KPIs** (`/dashboards/api/monthly/overview`)
   - Mise à jour : Tous les KPIs (CA, Marge, Flux, MP)
   - Calcul progressions
   - Mise à jour analyses détaillées
   - Génération alertes financières

3. **Graphique évolution financière** (`/dashboards/api/monthly/revenue-trend`)
   - Chart.js `line` avec 3 datasets

4. **Graphique répartition coûts** (`/dashboards/api/monthly/overview`)
   - Chart.js `doughnut`

5. **Chargement résumé IA** (`loadMonthlyAISummary()`)
   - Appel `/dashboards/api/monthly/ai-summary`
   - Rendu résumé + recommandations + score confiance
   - Fallback si IA indisponible

6. **Animation barres progression** : Délai 1 seconde

7. **Changement période** (`changePeriod()`) : Logique à implémenter

**Bibliothèques :**
- Chart.js (CDN)

#### 3.1.3 `shop_dashboard.html`

**Fonctionnalités principales :**

1. **Mise à jour horloge** (`updateClock()`)

2. **Gestion modal paiement** :
   - Écouteurs sur `.shop-pay-trigger`
   - Calcul solde après paiement
   - Calcul monnaie à rendre
   - Soumission formulaire

3. **Auto-refresh** : Toutes les 2 minutes

**Bibliothèques :**
- Bootstrap 5 (modal)

#### 3.1.4 `production_dashboard.html`

**Fonctionnalités principales :**

1. **Mise à jour horloge** (`updateClock()`)

2. **Calcul temps restants** (`updateCountdowns()`)
   - Calcul différence `due_date - now`
   - Application couleurs (vert/orange/rouge)
   - Mise à jour badges priorité

3. **Auto-refresh** : Toutes les 5 minutes

**Bibliothèques :**
- Bootstrap Icons

### 3.2 Scripts Externes

#### 3.2.1 `app/static/js/dashboards/production.js`
- **Fichier :** Vide (0 lignes)
- **Statut :** Non utilisé

#### 3.2.2 `app/static/js/dashboards/shop.js`
- **Fichier :** Vide (0 lignes)
- **Statut :** Non utilisé

#### 3.2.3 `app/static/js/dashboards/notifications.js`
- **Fichier :** Vide (0 lignes)
- **Statut :** Non utilisé (référencé dans `production_dashboard.html`)

### 3.3 Structure JSON des Réponses API

#### Format Standard
```json
{
  "success": true|false,
  "data": {...},
  "message": "...",  // Si erreur
  "timestamp": "ISO", // Optionnel
  "source": "..."     // Optionnel (ex: "ai_manager")
}
```

#### Exemples de Données

**Production :**
```json
{
  "stats": {
    "overdue_count": 2,
    "urgent_count": 5,
    "normal_count": 10,
    "total_production": 17
  },
  "overdue_orders": [
    {
      "id": 123,
      "customer_name": "Client A",
      "due_date": "2025-01-XXT10:00:00",
      "time_remaining_hours": -1.5,
      "total_amount": 5000.0,
      "status": "in_production",
      "items_count": 3,
      "priority": "overdue"
    }
  ]
}
```

**Stock :**
```json
{
  "stats": {
    "out_of_stock_count": 3,
    "low_stock_count": 8,
    "total_stock_value": 150000.0,
    "today_movements": 15,
    "benchmark": {}
  },
  "out_of_stock": [
    {
      "id": 45,
      "name": "Produit X",
      "category": "Catégorie Y",
      "stock_comptoir": 0.0,
      "stock_local": 0.0,
      "stock_magasin": 0.0,
      "seuil_comptoir": 5.0,
      "total_value": 0.0
    }
  ]
}
```

### 3.4 Variables Globales et Événements

#### Variables Globales
- `window.statusChartInstance` : Instance Chart.js statuts (daily)
- `window.ordersChartInstance` : Instance Chart.js commandes (daily)

#### Événements Déclencheurs
- `DOMContentLoaded` : Initialisation de tous les dashboards
- `setInterval` : Rafraîchissement automatique
- `onclick` : Actions utilisateur (boutons, cartes)

### 3.5 Scripts Redondants ou Non Utilisés

- `production.js` : Vide, non utilisé
- `shop.js` : Vide, non utilisé
- `notifications.js` : Vide, référencé mais non utilisé

---

## 4. INTÉGRATIONS IA ET PRÉDICTIONS

### 4.1 Module AI (`app/ai/`)

#### 4.1.1 AIManager

**Fichier :** `app/ai/ai_manager.py` (importé via `app/ai/__init__.py`)

**Méthodes utilisées par les dashboards :**

1. **`analyze_reports(report_type, prompt_type='daily_analysis')`**
   - **Utilisation :** `/dashboards/api/daily/ai-insights`
   - **Types de rapports :** `'daily_sales'`, `'daily_stock_alerts'`, `'daily_production'`
   - **Types de prompts :** `'daily_analysis'`, `'anomaly_detection'`
   - **Retour :** Analyse LLM (texte structuré)

2. **`generate_forecasts(report_type, days=7)`**
   - **Utilisation :** `/dashboards/api/daily/sales-forecast`
   - **Technologie :** Prophet (séries temporelles)
   - **Retour :** Prévisions avec intervalles de confiance

3. **`detect_anomalies(report_type)`**
   - **Utilisation :** `/dashboards/api/daily/anomalies`
   - **Méthode :** z-score + LLM pour interprétation
   - **Retour :** Liste anomalies avec sévérité

4. **`get_ai_summary(period_type, reference_date=None)`**
   - **Utilisation :** `/dashboards/api/monthly/ai-summary`
   - **Périodes :** `'monthly'`
   - **Retour :** Résumé stratégique + recommandations + score confiance

### 4.2 Intégration Prophet

#### Prévisions Ventes
- **Endpoint :** `/dashboards/api/daily/sales-forecast`
- **Paramètre :** `days` (défaut: 7)
- **Visualisation :** Ligne pointillée sur graphique commandes (daily)
- **Données :** `forecast` (liste avec `ds`, `yhat`, `yhat_lower`, `yhat_upper`)

### 4.3 Intégration LLM

#### Analyse Quotidienne
- **Endpoint :** `/dashboards/api/daily/ai-insights`
- **Rapports analysés :**
  - Ventes (`'daily_sales'`)
  - Stock (`'daily_stock_alerts'`)
  - Production (`'daily_production'`)
- **Affichage :** 3 cartes insights (daily)

#### Résumé Mensuel
- **Endpoint :** `/dashboards/api/monthly/ai-summary`
- **Contenu :**
  - Texte résumé stratégique
  - Recommandations (liste)
  - Score de confiance (0-100%)

### 4.4 Détection d'Anomalies

- **Endpoint :** `/dashboards/api/daily/anomalies`
- **Méthode :** z-score sur indicateurs clés
- **Affichage :** Bannière conditionnelle (daily) si anomalies haute sévérité
- **Format :** Liste anomalies avec `severity`, `message`, `metric`

### 4.5 Gestion des Erreurs IA

#### Fallback Système
Tous les endpoints IA incluent un système de fallback :

1. **Try/Except** dans les routes API
2. **Messages fallback** si IA indisponible
3. **Affichage conditionnel** dans les templates
4. **Logging** des erreurs (`logger.warning`, `logger.error`)

#### Exemples de Fallback
```json
{
  "status": "fallback",
  "message": "Analyse IA indisponible pour les ventes (mode hors ligne)",
  "analysis": "Consultez les rapports standards pour plus de détails."
}
```

### 4.6 Métadonnées IA Enrichies

Les services Reports enrichissent les données avec des métadonnées IA :

- **`growth_rate`** : Taux de croissance (%)
- **`trend_direction`** : `'up'`, `'down'`, `'stable'`
- **`variance`** : Écart-type
- **`benchmark`** : Données de référence (depuis `config/benchmarks.yaml`)

Ces métadonnées sont disponibles dans :
- `/dashboards/api/daily/sales` → `stats.growth_rate`, `stats.trend_direction`
- `/dashboards/api/daily/stock` → `stats.benchmark`
- `/dashboards/api/monthly/overview` → `kpis.growth_rate`, `kpis.trend_direction`, `kpis.variance`, `kpis.benchmark`

---

## 5. INTÉGRATION COMPTABLE ET MÉTIER

### 5.1 Indicateurs Financiers

#### Dashboard Journalier
- **CA du jour** : `daily_revenue` (depuis `DailySalesReportService`)
- **Flux de caisse** : `cash_in_today`, `cash_out_today`, `net_cash_flow`
- **Session caisse** : État ouverture, montant initial

#### Dashboard Mensuel
- **CA mensuel** : `monthly_revenue` (depuis `MonthlyProfitLossService`)
- **Charges mensuelles** : `monthly_expenses`
- **Bénéfice net** : `net_profit`
- **Marge bénéficiaire** : `profit_margin` (%)
- **Valeur stock** : `stock_value`
- **Masse salariale** : `total_salary_cost`
- **ROI employés** : `revenue_per_employee`

### 5.2 Liens avec Modules

#### Module Orders
- **Commandes** : Statuts, montants, dates
- **OrderItems** : Calcul CA via `quantity * unit_price`

#### Module Sales
- **CashRegisterSession** : État caisse
- **CashMovement** : Entrées/sorties caisse

#### Module Accounting
- **Account** : Comptes (ex: 701 Ventes, 601 Achats)
- **JournalEntry** / **JournalEntryLine** : Écritures comptables
- **DashboardService** : Utilisé par `main/dashboard` (pas directement par dashboards)

#### Module Employees
- **Employee** : Actifs, salaires
- **AttendanceRecord** : Pointages
- **OrderIssue** : Problèmes qualité

#### Module Stock
- **Product** : Stocks, seuils, valeurs
- **Category** : Catégories produits

### 5.3 Cohérence des Chiffres

#### Calcul CA
- **Méthode unifiée :** `_compute_revenue()` dans `app/reports/services.py`
- **Formule :** `sum(OrderItem.quantity * OrderItem.unit_price)`
- **Filtres :** Statuts `completed` ou `delivered`
- **Gestion NULL :** `coalesce()` pour éviter erreurs

#### Services Reports
Les dashboards utilisent les services Reports pour garantir la cohérence :
- `DailySalesReportService` → CA journalier
- `MonthlyProfitLossService` → CA mensuel, charges, bénéfice
- `StockAlertReportService` → Alertes stock
- `WeeklyProductPerformanceService` → Performance produits

### 5.4 Indicateurs Logistiques

#### Production
- Commandes en retard / urgentes / normales
- Temps restant par commande
- Taux de production

#### Stock
- Ruptures de stock
- Stock faible
- Valeur totale stock
- Mouvements aujourd'hui

#### Employés
- Présence / Absence
- Heures travaillées
- Taux de présence
- Performance (ROI, erreurs)

---

## 6. PROBLÈMES ET LIMITES IDENTIFIÉS

### 6.1 Code Obsolète ou Non Utilisé

#### Scripts JavaScript Vides
- `app/static/js/dashboards/production.js` : 0 lignes
- `app/static/js/dashboards/shop.js` : 0 lignes
- `app/static/js/dashboards/notifications.js` : 0 lignes (référencé mais vide)

**Impact :** Fichiers inutiles, confusion potentielle

#### Routes Dupliquées
- **Dashboard Production :** Définie dans `app/orders/dashboard_routes.py` ET potentiellement ailleurs
- **Dashboard Shop :** Même situation

**Impact :** Risque de confusion, maintenance difficile

### 6.2 Sections Trop Lourdes ou Incohérentes

#### Dashboard Journalier
- **Graphique commandes :** Données simulées (labels `['6h','8h','10h','12h','14h','16h','18h']`, valeurs hardcodées)
- **Prévisions Prophet :** Intégration partielle (fusion données réelles/simulées)

**Impact :** Données non fiables pour décisions

#### Dashboard Mensuel
- **Graphique évolution financière :** Calcul charges/bénéfice approximatif (`charges = revenue - avg_order_value * orders`)
- **Analyses détaillées :** Calculs simplifiés (ex: `stock_value/10000` pour rotation)

**Impact :** KPIs potentiellement incorrects

### 6.3 Manque de Modularité

#### Architecture Duale
- **Deux modules dashboards :** `app/dashboards/` ET `app/orders/dashboard_routes.py`
- **Blueprints différents :** `dashboards_bp` vs `dashboard_bp`
- **URLs incohérentes :** `/dashboards/*` vs `/dashboard/*`

**Impact :** Confusion, maintenance difficile

#### Templates Non Réutilisables
- **CSS inline :** Styles définis dans chaque template (pas de composants réutilisables)
- **JavaScript inline :** Logique dupliquée (ex: `updateTime()` dans plusieurs templates)

**Impact :** Code dupliqué, maintenance lourde

### 6.4 Absence de Filtrage / Pagination

#### Dashboard Production
- **Toutes les commandes affichées :** Pas de limite, pas de pagination
- **Performance :** Risque de ralentissement avec beaucoup de commandes

#### Dashboard Shop
- **5 sections sans pagination :** Toutes les commandes chargées
- **Filtrage :** Aucun filtre par date, statut, etc.

**Impact :** Performance dégradée, UX médiocre

### 6.5 Responsive Design Partiel

#### Dashboard Journalier
- **Media queries présentes :** Mais certaines sections peuvent déborder sur mobile
- **Graphiques :** `pointer-events: none` peut gêner l'interaction

#### Dashboard Mensuel
- **Grilles adaptatives :** `grid-template-columns: repeat(auto-fit, minmax(...))`
- **Mais :** Certaines cartes peuvent être trop petites sur tablette

**Impact :** Expérience mobile sous-optimale

### 6.6 Appels API Redondants

#### Dashboard Journalier
- **Double appel `/dashboards/api/daily/sales` :**
  1. Pour données finance (`#caTempsReel`)
  2. Pour graphique commandes (`#ordersChart`)
- **Pas de cache :** Chaque chargement refait les requêtes

**Impact :** Charge serveur inutile, latence

#### Dashboard Mensuel
- **Double appel `/dashboards/api/monthly/overview` :**
  1. Pour KPIs
  2. Pour graphique coûts

**Impact :** Même problème

### 6.7 Gestion d'Erreurs Incomplète

#### Frontend
- **Pas de gestion d'erreurs fetch :** Si API échoue, affichage "..." ou valeurs par défaut
- **Pas de retry :** En cas d'échec réseau, pas de nouvelle tentative

#### Backend
- **Fallback Reports :** Présent mais peut masquer des erreurs réelles
- **Logging :** Présent mais peut être amélioré (niveaux, contexte)

**Impact :** Expérience utilisateur dégradée en cas d'erreur

### 6.8 Intégrations IA Partielles

#### Phase 2 Non Complète
- **Sections IA présentes :** Mais certaines fonctionnalités peuvent ne pas fonctionner
- **Fallback systématique :** Si IA indisponible, affichage messages génériques

**Impact :** Valeur ajoutée IA limitée

#### Prévisions Prophet
- **Intégration graphique :** Fusion données réelles/simulées peut être confuse
- **Pas de gestion erreurs Prophet :** Si modèle échoue, graphique sans prévisions

**Impact :** Prévisions non fiables

### 6.9 Sécurité et Performance

#### Pas de Rate Limiting
- **Endpoints API :** Accessibles sans limite de requêtes
- **Risque :** DDoS, surcharge serveur

#### Pas de Cache
- **Données recalculées :** À chaque requête
- **Impact :** Performance dégradée, charge DB

#### CSRF
- **Protection présente :** Sur formulaires (ex: paiement)
- **Mais :** Endpoints API GET non protégés (normal mais à noter)

---

## 7. RECOMMANDATIONS FINALES

### 7.1 Simplification des Routes / Unification des Dashboards

#### Recommandation 1 : Unifier les Modules
- **Action :** Migrer toutes les routes de `app/orders/dashboard_routes.py` vers `app/dashboards/routes.py`
- **Bénéfice :** Architecture cohérente, maintenance facilitée

#### Recommandation 2 : Standardiser les URLs
- **Action :** Utiliser uniquement `/dashboards/*` (supprimer `/dashboard/*`)
- **Bénéfice :** URLs cohérentes, navigation claire

#### Recommandation 3 : Créer un Dashboard Principal Unifié
- **Action :** Refondre `main/dashboard.html` pour intégrer toutes les sections
- **Bénéfice :** Vue d'ensemble complète, navigation simplifiée

### 7.2 Refonte du Template Principal

#### Recommandation 4 : Architecture Modulaire
- **Action :** Créer des composants réutilisables (cartes KPI, graphiques, sections)
- **Bénéfice :** Code DRY, maintenance facilitée

#### Recommandation 5 : Système de Thèmes
- **Action :** Extraire CSS dans fichiers séparés, variables CSS pour thèmes
- **Bénéfice :** Personnalisation facile, cohérence visuelle

#### Recommandation 6 : Dashboard Responsive Complet
- **Action :** Tester et optimiser tous les breakpoints (mobile, tablette, desktop)
- **Bénéfice :** Expérience utilisateur optimale

### 7.3 Centralisation des Scripts JS

#### Recommandation 7 : Créer un Module Dashboard Commun
- **Action :** `app/static/js/dashboards/common.js` avec fonctions partagées (`updateTime`, `formatAmount`, etc.)
- **Bénéfice :** Code réutilisable, maintenance facilitée

#### Recommandation 8 : Implémenter les Scripts Manquants
- **Action :** Développer `production.js`, `shop.js`, `notifications.js` ou supprimer les références
- **Bénéfice :** Code propre, fonctionnalités complètes

#### Recommandation 9 : Gestion d'Erreurs Frontend
- **Action :** Wrapper `fetch()` avec retry, gestion erreurs, messages utilisateur
- **Bénéfice :** Robustesse, meilleure UX

### 7.4 Ajout de Sections Manquantes

#### Recommandation 10 : Suivi Paiements
- **Action :** Section dédiée aux paiements en attente, historique paiements
- **Bénéfice :** Visibilité trésorerie

#### Recommandation 11 : Marge Détaillée
- **Action :** Section marge par produit, catégorie, période
- **Bénéfice :** Analyse rentabilité fine

#### Recommandation 12 : Production Avancée
- **Action :** Planning production, capacité, optimisation
- **Bénéfice :** Pilotage opérationnel amélioré

### 7.5 Amélioration Ergonomie ou Performance

#### Recommandation 13 : Pagination et Filtres
- **Action :** Implémenter pagination côté serveur, filtres (date, statut, etc.)
- **Bénéfice :** Performance, UX améliorée

#### Recommandation 14 : Cache et Optimisation
- **Action :** Cache Redis/Memcached pour données fréquentes, requêtes optimisées
- **Bénéfice :** Latence réduite, charge serveur allégée

#### Recommandation 15 : WebSockets pour Temps Réel
- **Action :** Remplacement auto-refresh par WebSockets (Socket.IO)
- **Bénéfice :** Données temps réel, moins de charge réseau

#### Recommandation 16 : Rate Limiting
- **Action :** Implémenter rate limiting sur endpoints API
- **Bénéfice :** Protection DDoS, stabilité

### 7.6 Amélioration Intégrations IA

#### Recommandation 17 : Compléter Phase 2 IA
- **Action :** Finaliser toutes les fonctionnalités IA (prévisions, anomalies, insights)
- **Bénéfice :** Valeur ajoutée maximale

#### Recommandation 18 : Gestion Erreurs IA Robuste
- **Action :** Améliorer fallback, messages utilisateur clairs, retry automatique
- **Bénéfice :** Fiabilité, confiance utilisateur

#### Recommandation 19 : Visualisations IA Améliorées
- **Action :** Graphiques dédiés prévisions, heatmaps anomalies, etc.
- **Bénéfice :** Compréhension facilitée

### 7.7 Documentation et Tests

#### Recommandation 20 : Documentation API
- **Action :** Swagger/OpenAPI pour tous les endpoints
- **Bénéfice :** Intégration facilitée, maintenance

#### Recommandation 21 : Tests Automatisés
- **Action :** Tests unitaires services, tests intégration routes, tests E2E dashboards
- **Bénéfice :** Qualité, régression évitée

### 7.8 Priorisation des Recommandations

#### Priorité Haute (Impact Immédiat)
1. Unifier modules dashboards (Rec. 1, 2)
2. Implémenter pagination/filtres (Rec. 13)
3. Gestion erreurs frontend (Rec. 9)
4. Supprimer code obsolète (scripts vides)

#### Priorité Moyenne (Amélioration Continue)
5. Refonte template principal (Rec. 4, 5, 6)
6. Centralisation scripts JS (Rec. 7, 8)
7. Cache et optimisation (Rec. 14)
8. Sections manquantes (Rec. 10, 11, 12)

#### Priorité Basse (Évolutions Futures)
9. WebSockets temps réel (Rec. 15)
10. Compléter Phase 2 IA (Rec. 17, 18, 19)
11. Documentation API (Rec. 20)
12. Tests automatisés (Rec. 21)

---

## 📊 CONCLUSION

Le système de dashboards de l'ERP Fée Maison présente une **architecture fonctionnelle** avec des **intégrations IA avancées** (Phase 1 complète, Phase 2 partielle). Cependant, plusieurs **points d'amélioration** ont été identifiés :

### Points Forts
- ✅ Architecture modulaire (blueprints Flask)
- ✅ Intégration Reports pour cohérence données
- ✅ Intégration IA (Prophet, LLM) avec fallback
- ✅ Design moderne et responsive (partiel)
- ✅ KPIs métier complets

### Points Faibles
- ❌ Architecture duale (deux modules dashboards)
- ❌ Code JavaScript dupliqué et scripts vides
- ❌ Données simulées dans certains graphiques
- ❌ Absence pagination/filtres
- ❌ Pas de cache, performance sous-optimale
- ❌ Gestion erreurs incomplète

### Prochaines Étapes Recommandées
1. **Court terme :** Unifier modules, supprimer code obsolète, implémenter pagination
2. **Moyen terme :** Refonte template principal, centralisation JS, cache
3. **Long terme :** WebSockets, compléter Phase 2 IA, documentation complète

---

**Fin du rapport d'audit**

