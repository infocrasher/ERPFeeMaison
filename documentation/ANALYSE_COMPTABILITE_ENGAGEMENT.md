# 📊 ANALYSE TECHNIQUE : TRANSITION VERS COMPTABILITÉ D'ENGAGEMENT (IFRS 15)

**Date :** 13/12/2025  
**Objectif :** Séparer strictement la **Trésorerie** (Cash Flow) de la **Performance** (Revenue/P&L)

---

## 🔍 ÉTAT ACTUEL (AS-IS)

### 1. Structure des Données (Models)

#### ✅ **Order** (`models.py:463-612`)
- **Champs existants :**
  - `created_at` : Date de création de la commande
  - `due_date` : Date de livraison **prévue** (utilisée comme date de livraison réelle actuellement)
  - `amount_paid` : Montant total payé (cumulatif, pas de traçabilité par paiement)
  - `payment_paid_at` : Date du dernier paiement (pas de traçabilité historique)
  - `payment_status` : Statut de paiement (pending/partial/paid)
  - `status` : Statut de la commande (pending, delivered, completed, etc.)

- **❌ Manque :**
  - `delivery_date` : Date réelle de livraison (distincte de `due_date`)
  - Table `Payment` dédiée pour tracer chaque paiement avec sa date

#### ✅ **CashMovement** (`app/sales/models.py:19-29`)
- **Champs existants :**
  - `created_at` : Date du mouvement
  - `type` : Type (vente, entrée, sortie, acompte, etc.)
  - `amount` : Montant
  - `session_id` : Session de caisse
  - `employee_id` : Employé

- **❌ Manque :**
  - `order_id` : Lien explicite vers la commande (pour tracer les encaissements par commande)
  - `payment_type` : Type de paiement (acompte, solde, paiement complet)

#### ✅ **DeliveryDebt** (`models.py:1065-1082`)
- **Champs existants :**
  - `order_id` : Commande liée
  - `amount` : Montant de la dette
  - `paid` : Boolean (payé ou non)
  - `paid_at` : Date de paiement
  - `created_at` : Date de création

- **⚠️ Limitation :**
  - Gère uniquement les dettes livreur, pas tous les paiements
  - Pas de traçabilité des acomptes/soldes

---

### 2. Logique Actuelle des Rapports

#### **RealKpiService** (`app/reports/kpi_service.py:18-59`)

**CA (Revenue) :**
- **POS** : `created_at == target_date` ✅ (cohérent)
- **Shop** : `created_at == target_date` ET `due_date == target_date` ⚠️ (problématique)
  - Utilise `due_date` comme date de livraison (mais c'est la date prévue, pas réelle)
  - Ne comptabilise que les commandes créées ET livrées le même jour

**COGS :**
- Calculé sur les mêmes commandes que le CA ✅ (cohérent)
- Basé sur `Product.cost_price` actuel (pas historique) ⚠️

**Trésorerie :**
- Utilise `CashMovement.created_at` pour les sorties ✅
- Mais pas de calcul d'encaissements basé sur les paiements réels ❌

#### **DailySalesReportService** (`app/reports/services.py:442-568`)
- Utilise `_compute_revenue_real()` qui suit la logique RealKpiService ✅
- Même limitation : utilise `due_date` au lieu de `delivery_date`

#### **CashFlowForecastService** (`app/reports/services.py:1306-1409`)
- Utilise `_compute_revenue_real()` pour les encaissements prévus ⚠️
- **Problème :** Mélange trésorerie (encaissements) et performance (CA)
- Devrait utiliser `CashMovement` pour les encaissements réels

---

## 🎯 OBJECTIF (TO-BE)

### **Séparation Trésorerie / Performance**

#### **1. Trésorerie (Cash Flow)**
- **Source :** Table `CashMovement` (encaissements réels)
- **Date :** `CashMovement.created_at` (date réelle d'encaissement)
- **Logique :**
  - Somme des `CashMovement.amount` où `type == 'vente'` ou `type == 'acompte'`
  - Filtré par `created_at == target_date`
  - Inclut les acomptes, soldes, paiements partiels

#### **2. Performance (Revenue/P&L)**
- **Source :** Table `Order` (commandes livrées)
- **Date :** `Order.delivery_date` (date réelle de livraison) ⚠️ **À CRÉER**
- **Logique :**
  - CA = `Order.total_amount` pour les commandes avec `status IN ('delivered', 'completed', 'delivered_unpaid')`
  - Filtré par `delivery_date == target_date` (peu importe le statut de paiement)
  - COGS calculé sur les mêmes commandes (date de livraison)

---

## ❌ CE QUI MANQUE (GAPS)

### **1. Modèle de Données**

#### **A. Ajouter `delivery_date` à Order**
```python
# À ajouter dans models.py Order
delivery_date = db.Column(db.DateTime, nullable=True)  # Date réelle de livraison
```
- **Action :** Migration DB + Mettre à jour `mark_as_delivered()` pour setter `delivery_date`

#### **B. Créer table `Payment`**
```python
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_type = db.Column(db.String(20))  # 'acompte', 'solde', 'complet'
    payment_method = db.Column(db.String(20))  # 'cash', 'card', 'transfer'
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)  # Date réelle d'encaissement
    cash_movement_id = db.Column(db.Integer, db.ForeignKey('cash_movement.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```
- **Action :** Migration DB + Créer les relations

#### **C. Lier `CashMovement` à `Order`**
```python
# À ajouter dans CashMovement
order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
```
- **Action :** Migration DB + Mettre à jour les créations de CashMovement

---

### **2. Logique Métier**

#### **A. Mettre à jour `Order.mark_as_delivered()`**
```python
def mark_as_delivered(self):
    if self.status == 'ready_at_shop':
        self.status = 'delivered'
        self.delivery_date = datetime.utcnow()  # ⚠️ À AJOUTER
        # ... reste du code
```

#### **B. Créer service `CashFlowService`**
- Calculer les encaissements réels basés sur `CashMovement` ou `Payment`
- Séparer de `RealKpiService` qui calcule la Performance

#### **C. Mettre à jour `RealKpiService`**
- Utiliser `delivery_date` au lieu de `due_date` pour le CA Shop
- Ne plus filtrer par `created_at == due_date` (comptabiliser toutes les livraisons du jour)

---

### **3. Rapports**

#### **A. Séparer Cash Flow et Revenue**
- **CashFlowForecastService** : Utiliser `CashMovement` ou `Payment.paid_at`
- **RealKpiService** : Utiliser `Order.delivery_date` pour le CA

#### **B. Mettre à jour tous les rapports**
- Remplacer `due_date` par `delivery_date` dans les filtres Shop
- Utiliser `Payment.paid_at` pour les calculs de trésorerie

---

## 📋 PLAN D'ACTION MINIMUM

### **Phase 1 : Structure de Données (Migration DB)**
1. ✅ Ajouter `delivery_date` à `Order`
2. ✅ Créer table `Payment`
3. ✅ Ajouter `order_id` à `CashMovement`
4. ✅ Migration Flask-Migrate

### **Phase 2 : Logique Métier**
1. ✅ Mettre à jour `Order.mark_as_delivered()` pour setter `delivery_date`
2. ✅ Créer `Payment` lors des paiements (acomptes, soldes)
3. ✅ Lier `CashMovement` à `Order` lors des encaissements

### **Phase 3 : Services**
1. ✅ Créer `CashFlowService.get_daily_cash_flow(target_date)` basé sur `Payment.paid_at`
2. ✅ Mettre à jour `RealKpiService` pour utiliser `delivery_date` au lieu de `due_date`
3. ✅ Mettre à jour `_compute_revenue_real()` pour utiliser `delivery_date`

### **Phase 4 : Rapports**
1. ✅ Mettre à jour `CashFlowForecastService` pour utiliser `CashFlowService`
2. ✅ Mettre à jour tous les rapports utilisant `due_date` → `delivery_date`

---

## ⚠️ IMPACTS ET RISQUES

### **Risques**
1. **Données historiques :** Les commandes déjà livrées n'ont pas de `delivery_date`
   - **Solution :** Script de migration pour setter `delivery_date = due_date` pour les commandes livrées

2. **Paiements existants :** Pas de traçabilité historique des paiements
   - **Solution :** Script de migration pour créer des `Payment` à partir de `Order.amount_paid` et `Order.payment_paid_at`

3. **CashMovement existants :** Pas de lien vers `Order`
   - **Solution :** Script de migration pour lier les `CashMovement` de type 'vente' aux commandes

### **Bénéfices**
1. ✅ Séparation claire Trésorerie / Performance
2. ✅ Conformité IFRS 15 (Revenue Recognition)
3. ✅ Traçabilité complète des paiements (acomptes, soldes)
4. ✅ Calculs de trésorerie précis basés sur encaissements réels

---

## 📊 RÉSUMÉ EXÉCUTIF

| Aspect | AS-IS | TO-BE |
|--------|-------|-------|
| **Date CA Shop** | `due_date` (prévue) | `delivery_date` (réelle) |
| **Date Trésorerie** | `created_at` (CA) | `Payment.paid_at` (encaissement réel) |
| **Traçabilité Paiements** | `amount_paid` (cumulatif) | Table `Payment` (historique) |
| **Séparation Cash/Revenue** | ❌ Mélangé | ✅ Séparé |

**Changements minimum requis :**
1. Ajouter `delivery_date` à `Order`
2. Créer table `Payment`
3. Mettre à jour `RealKpiService` pour utiliser `delivery_date`
4. Créer `CashFlowService` basé sur `Payment`

