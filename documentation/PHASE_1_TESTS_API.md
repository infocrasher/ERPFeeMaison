# 🧪 PHASE 1 - TESTS API À EXÉCUTER

**Date** : Novembre 2025  
**Objectif** : Valider l'intégration IA du module Dashboards (Phase 1)

---

## 📋 PRÉ-REQUIS

1. **Serveur Flask lancé** :
   ```bash
   cd /Users/sofiane/Documents/Save\ FM/fee_maison_gestion_cursor
   source venv/bin/activate
   python app.py
   ```

2. **Authentification** :
   - Se connecter à l'interface admin
   - Récupérer le cookie de session

3. **Outil de test** :
   - Postman (recommandé)
   - cURL
   - Navigateur (pour endpoints GET simples)

---

## ✅ TESTS ENDPOINTS MODIFIÉS (INTÉGRATION REPORTS)

### Test 1 : /daily/sales

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/daily/sales`

**Objectif** : Vérifier l'intégration de `DailySalesReportService`

**Vérifications** :
- ✅ `stats.daily_revenue` présent (float)
- ✅ `stats.total_orders` présent (int)
- ✅ `stats.growth_rate` présent (NOUVEAU - métadonnée IA)
- ✅ `stats.trend_direction` présent (NOUVEAU - métadonnée IA)
- ✅ `orders_by_status` présent (dict)

**Log attendu** :
```
[REPORT] Data loaded from DailySalesReportService
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "stats": {
      "daily_revenue": 45000.0,
      "total_orders": 25,
      "delivered_orders": 20,
      "cash_session_open": true,
      "cash_in_today": 5000.0,
      "cash_out_today": 2000.0,
      "net_cash_flow": 3000.0,
      "growth_rate": 5.2,
      "trend_direction": "up"
    },
    "orders_by_status": { ... },
    "cash_session": { ... }
  }
}
```

---

### Test 2 : /daily/stock

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/daily/stock`

**Objectif** : Vérifier l'intégration de `StockAlertReportService`

**Vérifications** :
- ✅ `stats.out_of_stock_count` présent (int)
- ✅ `stats.low_stock_count` présent (int)
- ✅ `stats.benchmark` présent (NOUVEAU - métadonnée IA)
- ✅ `out_of_stock` présent (array)
- ✅ `low_stock` présent (array)

**Log attendu** :
```
[REPORT] Data loaded from StockAlertReportService
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "stats": {
      "out_of_stock_count": 3,
      "low_stock_count": 8,
      "total_stock_value": 150000.0,
      "today_movements": 15,
      "benchmark": {
        "target": 5,
        "current": 3,
        "variance": -2,
        "is_healthy": true
      }
    },
    "out_of_stock": [...],
    "low_stock": [...]
  }
}
```

---

### Test 3 : /monthly/overview

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/monthly/overview?year=2025&month=11`

**Objectif** : Vérifier l'intégration de `MonthlyProfitLossService`

**Vérifications** :
- ✅ `kpis.monthly_revenue` présent (float)
- ✅ `kpis.monthly_expenses` présent (float)
- ✅ `kpis.net_profit` présent (float)
- ✅ `kpis.profit_margin` présent (float)
- ✅ `kpis.growth_rate` présent (NOUVEAU - métadonnée IA)
- ✅ `kpis.trend_direction` présent (NOUVEAU - métadonnée IA)
- ✅ `kpis.variance` présent (NOUVEAU - métadonnée IA)
- ✅ `kpis.benchmark` présent (NOUVEAU - métadonnée IA)

**Log attendu** :
```
[REPORT] Data loaded from MonthlyProfitLossService
```

**Exemple réponse** :
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
      "monthly_revenue": 1500000.0,
      "monthly_orders": 500,
      "monthly_expenses": 900000.0,
      "net_profit": 600000.0,
      "profit_margin": 40.0,
      "stock_value": 150000.0,
      "active_employees": 10,
      "total_salary_cost": 200000.0,
      "revenue_per_employee": 150000.0,
      "growth_rate": 8.5,
      "trend_direction": "up",
      "variance": 25000.0,
      "benchmark": {
        "target": 35.0,
        "current": 40.0,
        "variance": 5.0,
        "is_healthy": true
      }
    }
  }
}
```

---

### Test 4 : /monthly/product-performance

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/monthly/product-performance?year=2025&month=11&limit=10`

**Objectif** : Vérifier l'intégration de `WeeklyProductPerformanceService`

**Vérifications** :
- ✅ `top_by_revenue` présent (array, max 10 items)
- ✅ `top_by_quantity` présent (array, max 10 items)
- ✅ Chaque produit contient : `id`, `name`, `category`, `total_quantity`, `total_revenue`, `avg_price`

**Log attendu** :
```
[REPORT] Data loaded from WeeklyProductPerformanceService
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "top_by_revenue": [
      {
        "id": 1,
        "name": "Gâteau au chocolat",
        "category": "Pâtisserie",
        "total_quantity": 150,
        "total_revenue": 45000.0,
        "avg_price": 300.0
      },
      ...
    ],
    "top_by_quantity": [...]
  }
}
```

---

## 🤖 TESTS NOUVEAUX ENDPOINTS IA

### Test 5 : /daily/ai-insights

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/daily/ai-insights`

**Objectif** : Vérifier l'analyse IA multi-rapports

**Vérifications** :
- ✅ `data.sales` présent (objet ou fallback)
- ✅ `data.stock` présent (objet ou fallback)
- ✅ `data.production` présent (objet ou fallback)
- ✅ `data.timestamp` présent (ISO datetime)
- ✅ `source` = "ai_manager"

**Logs attendus** :
```
[AI] Requesting daily AI insights
[AI] Sales analysis completed
[AI] Stock analysis completed
[AI] Production analysis completed
```

**Exemple réponse (succès)** :
```json
{
  "success": true,
  "data": {
    "sales": {
      "analysis": "📊 ANALYSE DES VENTES...",
      "provider": "groq",
      "model": "llama-3.1-70b-versatile"
    },
    "stock": {
      "analysis": "⚠️ ALERTES STOCK...",
      "anomalies": [...]
    },
    "production": {
      "analysis": "🏭 PRODUCTION...",
      "recommendations": [...]
    },
    "timestamp": "2025-11-04T10:30:00"
  },
  "source": "ai_manager"
}
```

**Exemple réponse (fallback)** :
```json
{
  "success": true,
  "data": {
    "sales": {
      "status": "fallback",
      "message": "Analyse IA indisponible pour les ventes (mode hors ligne)",
      "analysis": "Consultez les rapports standards pour plus de détails."
    },
    ...
  }
}
```

---

### Test 6 : /daily/sales-forecast

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/daily/sales-forecast?days=7`

**Objectif** : Vérifier les prévisions Prophet

**Vérifications** :
- ✅ `data.forecast` présent (array)
- ✅ Chaque prévision contient : `ds`, `yhat`, `yhat_lower`, `yhat_upper`
- ✅ `data.components` présent (tendance, saisonnalité)
- ✅ `data.metrics` présent (MAE, MAPE)
- ✅ `source` = "prophet"

**Logs attendus** :
```
[AI] Requesting sales forecast for 7 days
[AI] Sales forecast completed
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "forecast": [
      {
        "ds": "2025-11-05T00:00:00",
        "yhat": 45000.5,
        "yhat_lower": 40000.0,
        "yhat_upper": 50000.0
      },
      ...
    ],
    "components": {
      "trend": { ... },
      "weekly_seasonality": [...]
    },
    "metrics": {
      "mae": 1250.5,
      "mape": 8.2,
      "confidence": "élevée"
    }
  },
  "source": "prophet",
  "timestamp": "2025-11-04T10:30:00"
}
```

**Note** : Si le modèle Prophet n'est pas encore entraîné, vous obtiendrez une erreur 500 avec un message clair.

---

### Test 7 : /daily/anomalies

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/daily/anomalies`

**Objectif** : Vérifier la détection d'anomalies IA

**Vérifications** :
- ✅ `data.anomalies` présent (array)
- ✅ `data.z_scores` présent (objet avec z-scores par KPI)
- ✅ `data.llm_analysis` présent (analyse textuelle)
- ✅ `source` = "ai_manager"

**Logs attendus** :
```
[AI] Requesting anomaly detection
[AI] Anomaly detection completed
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "anomalies": [
      {
        "kpi": "daily_revenue",
        "value": 52000.0,
        "z_score": 2.8,
        "severity": "high",
        "message": "CA anormalement élevé (+40% vs moyenne)"
      }
    ],
    "z_scores": {
      "daily_revenue": 2.8,
      "total_orders": 1.2,
      "average_basket": 0.5
    },
    "llm_analysis": "🔍 DÉTECTION D'ANOMALIES..."
  },
  "source": "ai_manager",
  "timestamp": "2025-11-04T10:30:00"
}
```

---

### Test 8 : /monthly/ai-summary

**Endpoint** : `GET http://127.0.0.1:5000/dashboards/api/monthly/ai-summary?year=2025&month=11`

**Objectif** : Vérifier le résumé stratégique mensuel IA

**Vérifications** :
- ✅ `data.summary` présent (texte markdown)
- ✅ `data.recommendations` présent (array)
- ✅ `data.top_3_successes` présent (array)
- ✅ `data.top_3_improvements` présent (array)
- ✅ `period.year` et `period.month` présents
- ✅ `source` = "ai_manager"

**Logs attendus** :
```
[AI] Requesting monthly AI summary for 2025-11
[AI] Monthly AI summary completed
```

**Exemple réponse** :
```json
{
  "success": true,
  "data": {
    "summary": "📊 ANALYSE STRATÉGIQUE NOVEMBRE 2025\n\n...",
    "recommendations": [
      "Optimiser les stocks de produits à forte rotation",
      "Former les employés sur la gestion des pics de production",
      "Diversifier les canaux de vente"
    ],
    "top_3_successes": [
      "CA en hausse de 8.5% vs octobre",
      "Marge bénéficiaire à 40% (cible dépassée)",
      "Taux d'erreur production en baisse de 15%"
    ],
    "top_3_improvements": [
      "Gestion des stocks (ruptures fréquentes)",
      "Délais de livraison (5% de retards)",
      "Formation continue RH"
    ]
  },
  "source": "ai_manager",
  "period": {
    "year": 2025,
    "month": 11
  },
  "timestamp": "2025-11-04T10:30:00"
}
```

---

## 🧪 TESTS FRONT-END

### Test 9 : Dashboard Journalier

**URL** : `http://127.0.0.1:5000/dashboards/daily`

**Vérifications** :
- ✅ Tous les KPIs s'affichent correctement
- ✅ Graphiques Chart.js fonctionnent
- ✅ Aucune erreur console
- ✅ Données cohérentes avec les endpoints API

---

### Test 10 : Dashboard Mensuel

**URL** : `http://127.0.0.1:5000/dashboards/monthly`

**Vérifications** :
- ✅ Tous les KPIs s'affichent correctement
- ✅ Sélecteur de période fonctionne
- ✅ Graphiques Chart.js fonctionnent
- ✅ Aucune erreur console
- ✅ Données cohérentes avec les endpoints API

---

## 📊 GRILLE DE VALIDATION

| Test | Endpoint | Statut | Notes |
|------|----------|--------|-------|
| 1 | `/daily/sales` | ⬜ | |
| 2 | `/daily/stock` | ⬜ | |
| 3 | `/monthly/overview` | ⬜ | |
| 4 | `/monthly/product-performance` | ⬜ | |
| 5 | `/daily/ai-insights` | ⬜ | |
| 6 | `/daily/sales-forecast` | ⬜ | |
| 7 | `/daily/anomalies` | ⬜ | |
| 8 | `/monthly/ai-summary` | ⬜ | |
| 9 | Dashboard Journalier | ⬜ | |
| 10 | Dashboard Mensuel | ⬜ | |

**Légende** : ⬜ Non testé | ✅ Succès | ❌ Échec

---

## 🐛 DÉBOGAGE

### Si erreur 500 sur endpoints AI

1. **Vérifier les logs** :
   ```bash
   tail -f app.log | grep "\[AI\]"
   ```

2. **Vérifier AIManager** :
   - Module `app/ai/__init__.py` importable ?
   - Clés API configurées (GROQ_API_KEY, OPENAI_API_KEY) ?
   - Modèles Prophet entraînés ?

3. **Fallback attendu** :
   - Les endpoints AI ont des fallbacks
   - Mode hors ligne avec message clair si API indisponible

### Si erreur 500 sur endpoints reports

1. **Vérifier les logs** :
   ```bash
   tail -f app.log | grep "\[REPORT\]"
   ```

2. **Vérifier services reports** :
   - Module `app/reports/services.py` importable ?
   - Base de données accessible ?
   - Données suffisantes pour calculs ?

3. **Fallback attendu** :
   - Les endpoints ont des fallbacks sur calcul direct

---

## ✅ CRITÈRES DE SUCCÈS

**Phase 1 validée si** :
- ✅ 8/8 endpoints API fonctionnent (même en mode fallback)
- ✅ 2/2 dashboards front-end s'affichent correctement
- ✅ Logs `[REPORT]` et `[AI]` présents
- ✅ Compatibilité front-end confirmée (aucune régression)
- ✅ 0 erreur linter

---

**Auteur** : Phase 1 Tests API - Novembre 2025  
**Version** : 1.0  
**Statut** : Prêt pour exécution

