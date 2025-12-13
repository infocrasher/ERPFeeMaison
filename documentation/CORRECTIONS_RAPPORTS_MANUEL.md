# Corrections Manuelles des Rapports - Analyse Complète

## 📋 Résumé

Analyse manuelle de tous les services de rapports pour identifier les incohérences avec la logique `RealKpiService`.

## ❌ Problèmes Identifiés

### 1. Services utilisant `_compute_revenue()` (ancienne méthode)

#### LaborCostReportService (ligne 1236)
- **Problème** : Utilise `_compute_revenue()` au lieu de `_compute_revenue_real()`
- **Impact** : CA incorrect pour les périodes
- **Correction** : Remplacer par `_compute_revenue_real()`

#### CashFlowForecastService (ligne 1316)
- **Problème** : Utilise `_compute_revenue()` au lieu de `_compute_revenue_real()`
- **Impact** : Encaissements prévus incorrects
- **Correction** : Remplacer par `_compute_revenue_real()`

#### MonthlyProfitLossService (ligne 1552)
- **Problème** : Utilise `_compute_revenue()` au lieu de `_compute_revenue_real()`
- **Impact** : CA mensuel incorrect
- **Correction** : Remplacer par `_compute_revenue_real()`

### 2. Services filtrant par `Order.created_at` au lieu de la logique POS/Shop

#### MonthlyProfitLossService (ligne 1562)
- **Problème** : COGS filtré par `Order.created_at` au lieu de la logique POS/Shop
- **Impact** : COGS ne correspond pas au CA
- **Correction** : Utiliser `_get_orders_filter_real()` ou logique POS/Shop

#### WasteLossReportService (ligne 908)
- **Problème** : COGS filtré par `Order.created_at` au lieu de la logique POS/Shop
- **Impact** : Pourcentage de gaspillage incorrect
- **Correction** : Utiliser `_get_orders_filter_real()` ou logique POS/Shop

#### StockRotationReportService (ligne 1114)
- **Problème** : COGS filtré par `Order.created_at` au lieu de la logique POS/Shop
- **Impact** : Ratio de rotation incorrect
- **Correction** : Utiliser `_get_orders_filter_real()` ou logique POS/Shop

#### MonthlyGrossMarginService (ligne 1451)
- **Problème** : Filtre par `Order.created_at` au lieu de la logique POS/Shop
- **Impact** : Marges par catégorie incorrectes
- **Correction** : Utiliser `_get_orders_filter_real()` ou logique POS/Shop

#### WeeklyProductPerformanceService (ligne 1008)
- **Problème** : Filtre par `Order.created_at` au lieu de la logique POS/Shop
- **Impact** : Performance produits incorrecte
- **Correction** : Utiliser `_get_orders_filter_real()` ou logique POS/Shop

### 3. Services OK (déjà corrigés)

✅ **DailySalesReportService** : Utilise `_compute_revenue_real()` et `_get_orders_filter_real()`
✅ **PrimeCostReportService** : Utilise `DailySalesReportService` (cohérent) et `_get_orders_filter_real()` pour COGS

### 4. Services sans CA (pas de problème)

✅ **ProductionReportService** : Pas de calcul de CA (OK)
✅ **StockAlertReportService** : Pas de calcul de CA (OK)

## 🔧 Plan de Correction

### Priorité 1 (Critique - Impact CA)
1. ✅ DailySalesReportService - DÉJÀ CORRIGÉ
2. ✅ PrimeCostReportService - DÉJÀ CORRIGÉ
3. ⏳ LaborCostReportService - À CORRIGER
4. ⏳ CashFlowForecastService - À CORRIGER
5. ⏳ MonthlyProfitLossService - À CORRIGER

### Priorité 2 (Important - Impact COGS/Marges)
6. ⏳ MonthlyProfitLossService (COGS) - À CORRIGER
7. ⏳ WasteLossReportService - À CORRIGER
8. ⏳ StockRotationReportService - À CORRIGER
9. ⏳ MonthlyGrossMarginService - À CORRIGER
10. ⏳ WeeklyProductPerformanceService - À CORRIGER

## 📝 Notes

- Pour les périodes (start_date, end_date), `_compute_revenue_real()` gère déjà la logique POS/Shop
- Pour les filtres de commandes, utiliser `_get_orders_filter_real(start_date=..., end_date=...)`
- Pour le COGS, utiliser les mêmes IDs de commandes que pour le CA

---

**Date de l'analyse** : 2025-12-13  
**Analysé par** : Assistant IA

