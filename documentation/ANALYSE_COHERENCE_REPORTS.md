# Analyse de Cohérence - Module Reports

## 📋 Résumé Exécutif

Cette analyse compare la logique de calcul du module `app/reports/` avec la logique de référence du `RealKpiService` (utilisée par le dashboard).

**Conclusion :** ❌ **Plusieurs incohérences majeures détectées**

---

## 🎯 Logique de Référence (RealKpiService)

### Chiffre d'Affaires (CA)

1. **POS (Comptoir)** :
   - Filtre : `Order.order_type == 'in_store'` ET `func.date(Order.created_at) == target_date`
   - Statut : Tous (payé au comptoir)

2. **Shop (Livraison/Click&Collect)** :
   - Filtre : `Order.order_type != 'in_store'` ET `Order.status.in_(['delivered', 'completed', 'delivered_unpaid'])` ET `func.date(Order.due_date) == target_date`
   - **Important** : Utilise `due_date` (date de livraison), pas `created_at`

### COGS (Coûts des Ventes)

- Calcule le coût uniquement pour les commandes incluses dans le CA ci-dessus
- Matière : Via recettes ou `Product.cost_price`
- Main d'œuvre : Via `AttendanceRecord.get_daily_summary()` (temps réel)

---

## ❌ Incohérences Détectées

### 1. Fonction `_compute_revenue()` (services.py:75-109)

**Problème :** Utilise `Order.created_at` pour TOUTES les commandes

```python
# ❌ CODE ACTUEL (INCOHÉRENT)
query = query.filter(func.date(Order.created_at) == report_date)
```

**Impact :** 
- Les commandes Shop créées hier mais livrées aujourd'hui ne sont PAS comptabilisées
- Les commandes Shop créées aujourd'hui mais livrées demain SONT comptabilisées (incorrect)

**Utilisé par :**
- `DailySalesReportService.generate()`
- `MonthlyProfitLossService.generate()`
- `CashFlowForecastService.generate()`
- Tous les rapports qui utilisent `_compute_revenue()`

---

### 2. `DailySalesReportService.generate()` (services.py:310-436)

**Problèmes multiples :**

#### 2.1. Utilise `_compute_revenue()` qui est incohérent
```python
# ❌ Ligne 322
total_revenue = _compute_revenue(report_date=report_date)
```

#### 2.2. Filtre les commandes par `created_at` au lieu de la logique POS/Shop
```python
# ❌ Ligne 316-319
orders = Order.query.filter(
    func.date(Order.created_at) == report_date,
    Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
).all()
```

#### 2.3. Tous les calculs (top products, catégories, ventes horaires) utilisent `created_at`
```python
# ❌ Lignes 336, 360, 378
func.date(Order.created_at) == report_date
```

**Impact :** Le rapport de ventes quotidien ne reflète pas la réalité des livraisons

---

### 3. `PrimeCostReportService.generate()` (services.py:439-600)

**Problèmes multiples :**

#### 3.1. Utilise `DailySalesReportService` pour le revenue (incohérent)
```python
# ❌ Ligne 449
revenue = DailySalesReportService.generate(report_date)['total_revenue']
```

#### 3.2. Filtre les commandes pour COGS par `created_at` au lieu de la logique POS/Shop
```python
# ❌ Lignes 458-461
orders = Order.query.filter(
    func.date(Order.created_at) == report_date,
    Order.status.in_(['completed', 'delivered'])
).all()
```

**Impact :** 
- Le CA et le COGS ne correspondent pas aux mêmes commandes
- Risque de marges négatives ou incorrectes
- Le COGS peut être calculé sur des commandes qui ne sont pas dans le CA

---

### 4. `MonthlyGrossMarginService.generate()` (services.py:1316-1425)

**Problème :** Filtre par `created_at` au lieu de la logique POS/Shop

```python
# ❌ Lignes 1345-1346
func.date(Order.created_at) >= start_date,
func.date(Order.created_at) <= end_date,
```

**Impact :** Les marges mensuelles par catégorie sont incorrectes

---

### 5. `MonthlyProfitLossService.generate()` (services.py:1428-1476)

**Problèmes multiples :**

#### 5.1. Utilise `_compute_revenue()` qui est incohérent
```python
# ❌ Ligne 1446
revenue = _compute_revenue(start_date=start_date, end_date=end_date)
```

#### 5.2. Filtre COGS par `created_at` au lieu de la logique POS/Shop
```python
# ❌ Lignes 1456-1457
func.date(Order.created_at) >= start_date,
func.date(Order.created_at) <= end_date,
```

**Impact :** Le compte de résultat mensuel est incorrect

---

### 6. Autres Services

D'autres services dans `services.py` utilisent probablement `created_at` :
- `ProductionReportService` (ligne ~591, 604)
- `WeeklyProductPerformanceService` (ligne ~802-803)
- `StockRotationReportService` (ligne ~902-903)
- `LaborCostReportService` (ligne ~1008-1009)
- `CashFlowForecastService` (ligne ~1130, 1210)

**À vérifier individuellement**

---

## ✅ Services Cohérents

### `RealKpiService` (kpi_service.py)
- ✅ Utilise la logique correcte : `created_at` pour POS, `due_date` pour Shop
- ✅ Utilisé par le dashboard principal

---

## 🔧 Corrections Nécessaires

### Priorité 1 (Critique - Impact Dashboard)

1. **Créer une fonction utilitaire cohérente** `_compute_revenue_real()` qui utilise la logique du `RealKpiService`
2. **Corriger `DailySalesReportService`** pour utiliser la nouvelle logique
3. **Corriger `PrimeCostReportService`** pour que COGS corresponde au CA

### Priorité 2 (Important - Rapports)

4. **Corriger `MonthlyGrossMarginService`**
5. **Corriger `MonthlyProfitLossService`**
6. **Vérifier et corriger les autres services** (Production, Weekly, etc.)

### Priorité 3 (Amélioration)

7. **Déprécier `_compute_revenue()`** et créer une migration progressive
8. **Ajouter des tests unitaires** pour vérifier la cohérence

---

## 📝 Exemple de Correction

### Avant (Incohérent)
```python
def _compute_revenue(report_date=None, start_date=None, end_date=None):
    query = db.session.query(
        func.sum(func.coalesce(OrderItem.quantity, 0) * func.coalesce(OrderItem.unit_price, 0))
    ).select_from(OrderItem).join(Order, Order.id == OrderItem.order_id).filter(
        Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
    )
    
    if report_date:
        query = query.filter(func.date(Order.created_at) == report_date)  # ❌
```

### Après (Cohérent)
```python
def _compute_revenue_real(report_date=None, start_date=None, end_date=None):
    """
    Calcule le CA selon la logique RealKpiService :
    - POS : created_at == date
    - Shop : due_date == date ET status livré
    """
    from sqlalchemy import or_, and_
    
    if report_date:
        # POS
        pos_query = db.session.query(
            func.sum(func.coalesce(OrderItem.quantity, 0) * func.coalesce(OrderItem.unit_price, 0))
        ).select_from(OrderItem).join(Order, Order.id == OrderItem.order_id).filter(
            Order.order_type == 'in_store',
            func.date(Order.created_at) == report_date
        )
        
        # Shop
        shop_query = db.session.query(
            func.sum(func.coalesce(OrderItem.quantity, 0) * func.coalesce(OrderItem.unit_price, 0))
        ).select_from(OrderItem).join(Order, Order.id == OrderItem.order_id).filter(
            Order.order_type != 'in_store',
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.due_date) == report_date
        )
        
        pos_revenue = pos_query.scalar() or 0.0
        shop_revenue = shop_query.scalar() or 0.0
        return float(pos_revenue) + float(shop_revenue)
    
    # Pour les périodes (start_date, end_date), utiliser la même logique
    # ...
```

---

## 🎯 Plan d'Action Recommandé

1. **Phase 1 : Créer la fonction utilitaire cohérente**
   - Créer `_compute_revenue_real()` dans `services.py`
   - Tester avec des dates connues

2. **Phase 2 : Corriger les services quotidiens**
   - `DailySalesReportService`
   - `PrimeCostReportService`

3. **Phase 3 : Corriger les services mensuels**
   - `MonthlyGrossMarginService`
   - `MonthlyProfitLossService`

4. **Phase 4 : Vérifier et corriger les autres services**
   - Services hebdomadaires
   - Services de production
   - Services de prévision

5. **Phase 5 : Migration**
   - Déprécier `_compute_revenue()` (garder pour compatibilité)
   - Mettre à jour tous les appels
   - Supprimer après migration complète

---

## 📊 Impact Estimé

- **Dashboard** : ✅ Déjà cohérent (utilise `RealKpiService`)
- **Rapports Quotidiens** : ❌ Incohérents (impact moyen)
- **Rapports Mensuels** : ❌ Incohérents (impact élevé)
- **Prévisions** : ❌ Potentiellement incohérentes (impact moyen)

---

## ✅ Validation

Après correction, valider que :
1. Les rapports quotidiens correspondent au dashboard
2. Les rapports mensuels sont cohérents
3. Les marges calculées sont correctes
4. Les prévisions sont basées sur les bonnes données

---

**Date de l'analyse :** 2025-12-13  
**Analysé par :** Assistant IA  
**Fichiers analysés :** `app/reports/services.py`, `app/reports/kpi_service.py`, `app/reports/routes.py`

