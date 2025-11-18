# 📊 Flux Complet des Analyses IA - ERP Fée Maison

## 🎯 Vue d'ensemble

Ce document trace **exactement** quand et où les analyses IA (LLM) et les prédictions Prophet sont lancées et affichées, pour optimiser les coûts.

## ⚠️ ÉTAT ACTUEL

**Dashboard unifié** (`/dashboard`) : **N'utilise PAS encore les analyses IA LLM**
- Les insights affichés sont calculés côté serveur (pas d'appels LLM)
- Aucune prédiction Prophet n'est affichée
- Fichier : `app/templates/dashboard/_insights.html` (insights basiques uniquement)

**Anciens dashboards** (toujours accessibles mais peut-être obsolètes) :
- `/dashboards/daily/operational` : Utilise les analyses IA (3 appels LLM + Prophet)
- `/dashboards/monthly/strategic` : Utilise les analyses IA (1 appel LLM)

---

## 1️⃣ ANALYSES LLM (OpenAI/Groq) - ANCIENS DASHBOARDS

### 📍 **Quand sont-elles lancées ?**

#### **Dashboard Journalier** (`/dashboards/daily/operational`)
- **Route API** : `GET /dashboards/api/daily/ai-insights`
- **Déclenchement** : Au chargement de la page (JavaScript `DOMContentLoaded`)
- **Fréquence** : **1 fois par chargement de page** + **auto-refresh toutes les 2 minutes** (120 secondes)
- **Fichier** : `app/templates/dashboards/daily_operational.html` (ligne 1275)

**Analyses effectuées** :
1. ✅ Analyse ventes (`daily_sales`) - **1 appel LLM**
2. ✅ Analyse stock (`daily_stock_alerts`) - **1 appel LLM**
3. ✅ Analyse production (`daily_production`) - **1 appel LLM**

**Total : 3 appels LLM par chargement + 3 appels toutes les 2 minutes**

#### **Dashboard Mensuel** (`/dashboards/monthly/strategic`)
- **Route API** : `GET /dashboards/api/monthly/ai-summary`
- **Déclenchement** : Au chargement de la page (JavaScript)
- **Fréquence** : **1 fois par chargement de page**
- **Fichier** : `app/templates/dashboards/monthly_strategic.html` (ligne 1160)

**Analyse effectuée** :
1. ✅ Résumé stratégique mensuel (`monthly`) - **1 appel LLM**

**Total : 1 appel LLM par chargement**

### 📍 **Où sont-elles affichées ?**

#### **Dashboard Journalier**
- **Section** : "Insights IA" (`.ai-insights-section`)
- **Emplacement** : Section dédiée avec 3 cartes (Ventes, Stock, Production)
- **Fichier** : `app/templates/dashboards/daily_operational.html` (lignes 929-1334)
- **Format** : Texte d'analyse tronqué à 200 caractères par carte

#### **Dashboard Mensuel**
- **Section** : "Résumé Stratégique IA" (`.ai-summary-strategic`)
- **Emplacement** : Section principale avec résumé + recommandations
- **Fichier** : `app/templates/dashboards/monthly_strategic.html` (lignes 900-905)
- **Format** : Résumé complet + liste de recommandations (max 5)

---

## 2️⃣ PRÉDICTIONS PROPHET

### 📍 **Quand sont-elles lancées ?**

#### **Dashboard Journalier** (`/dashboards/daily/operational`)
- **Route API** : `GET /dashboards/api/daily/sales-forecast?days=7`
- **Déclenchement** : Au chargement de la page (JavaScript)
- **Fréquence** : **1 fois par chargement de page** (pas d'auto-refresh)
- **Fichier** : `app/templates/dashboards/daily_operational.html` (ligne 1078)

**Prédiction effectuée** :
1. ✅ Prévisions ventes 7 jours (`daily_sales`, 7 jours) - **1 entraînement/chargement Prophet**

**Note** : Prophet charge un modèle sauvegardé (`.pkl`) s'il existe, sinon il entraîne un nouveau modèle.

### 📍 **Où sont-elles affichées ?**

#### **Dashboard Journalier**
- **Graphique** : "Évolution Commandes" avec prévisions
- **Emplacement** : Graphique Chart.js avec données réelles + prévisions Prophet
- **Fichier** : `app/templates/dashboards/daily_operational.html` (lignes 1077-1121)
- **Format** : Ligne de prévision sur le graphique (7 points futurs)

---

## 3️⃣ DÉTECTION D'ANOMALIES

### 📍 **Quand est-elle lancée ?**

#### **Dashboard Journalier** (`/dashboards/daily/operational`)
- **Route API** : `GET /dashboards/api/daily/anomalies`
- **Déclenchement** : Au chargement de la page (JavaScript)
- **Fréquence** : **1 fois par chargement de page** (pas d'auto-refresh)
- **Fichier** : `app/templates/dashboards/daily_operational.html` (ligne ~1265)

**Analyse effectuée** :
1. ✅ Détection anomalies ventes (`daily_sales`) - **1 appel LLM**

### 📍 **Où est-elle affichée ?**

- **Section** : Non visible actuellement (appel API fait mais pas d'affichage dans le template)
- **Note** : L'API existe mais n'est pas utilisée dans l'interface

---

## 📊 RÉSUMÉ DES COÛTS ACTUELS

### **Par chargement de Dashboard Journalier** :
- ✅ 3 appels LLM (ventes, stock, production)
- ✅ 1 appel LLM (anomalies) - **non affiché**
- ✅ 1 entraînement/chargement Prophet (prévisions)
- **Total : 4 appels LLM + 1 Prophet**

### **Par chargement de Dashboard Mensuel** :
- ✅ 1 appel LLM (résumé stratégique)
- **Total : 1 appel LLM**

### **Auto-refresh Dashboard Journalier** (toutes les 2 minutes) :
- ✅ 3 appels LLM (ventes, stock, production)
- **Total : 3 appels LLM toutes les 2 minutes**

---

## 💰 ESTIMATION DES COÛTS

### **OpenAI GPT-4o-mini** (modèle actuel)
- **Prix** : ~$0.15 / 1M tokens d'entrée, ~$0.60 / 1M tokens de sortie
- **Estimation par appel** : ~500 tokens entrée + ~500 tokens sortie = **~$0.00045 par appel**
- **Dashboard Journalier** : 4 appels = **~$0.0018 par chargement**
- **Auto-refresh** : 3 appels toutes les 2 min = **~$0.00135 toutes les 2 min**

### **Groq** (si utilisé)
- **Prix** : Gratuit jusqu'à 14,400 requêtes/jour
- **Limite** : 30 requêtes/minute

---

## 🎯 RECOMMANDATIONS POUR OPTIMISER LES COÛTS

### **1. Réduire la fréquence d'auto-refresh**
- Actuellement : Toutes les 2 minutes
- **Recommandation** : Toutes les 15-30 minutes (ou sur demande manuelle)

### **2. Mettre en cache les analyses**
- **Recommandation** : Cache de 15-30 minutes pour les analyses LLM
- Les données changent peu dans l'intervalle

### **3. Désactiver l'analyse d'anomalies non affichée**
- **Recommandation** : Retirer l'appel API `/daily/anomalies` s'il n'est pas utilisé

### **4. Lazy loading des analyses**
- **Recommandation** : Charger les analyses seulement quand l'utilisateur scroll vers la section IA

### **5. Option A : Combiner OpenAI + Groq**
- **Stratégie** : Utiliser Groq pour les analyses rapides (gratuit), OpenAI pour les analyses critiques (mensuel)
- **Économie** : ~75% des appels gratuits avec Groq

---

## 📝 FICHIERS CONCERNÉS

### **Routes API** :
- `app/dashboards/api.py` :
  - Ligne 790 : `daily_ai_insights()` - 3 appels LLM
  - Ligne 862 : `daily_sales_forecast()` - 1 Prophet
  - Ligne 895 : `daily_anomalies()` - 1 appel LLM (non utilisé)
  - Ligne 927 : `monthly_ai_summary()` - 1 appel LLM

### **Templates** :
- `app/templates/dashboards/daily_operational.html` :
  - Ligne 1078 : Appel prévisions Prophet
  - Ligne 1275 : Appel insights IA (3 analyses)
  - Ligne ~1265 : Appel anomalies (non affiché)
  - Ligne 1347 : Auto-refresh toutes les 2 minutes

- `app/templates/dashboards/monthly_strategic.html` :
  - Ligne 1160 : Appel résumé mensuel IA

### **Services IA** :
- `app/ai/ai_manager.py` : Orchestrateur principal
- `app/ai/services/llm_analyzer.py` : Service LLM (OpenAI/Groq)
- `app/ai/services/prophet_predictor.py` : Service Prophet

---

## ✅ PROCHAINES ÉTAPES

### **Priorité 1 : Intégrer l'IA dans le nouveau dashboard unifié**
1. **Ajouter les analyses IA au dashboard `/dashboard`** :
   - Intégrer `AIManager` dans `app/routes/dashboard.py`
   - Créer une section IA dans `app/templates/dashboard/_insights.html`
   - Ajouter les appels API pour les analyses LLM

### **Priorité 2 : Optimiser les coûts**
1. **Implémenter l'Option A** : Combiner OpenAI + Groq
2. **Ajouter un système de cache** : Redis ou cache mémoire (15-30 min)
3. **Réduire la fréquence d'auto-refresh** : 2 min → 15-30 min (si auto-refresh activé)
4. **Lazy loading** : Charger les analyses à la demande
5. **Retirer les appels inutilisés** : `/daily/anomalies` si non affiché

### **Priorité 3 : Nettoyer les anciens dashboards**
1. **Décider** : Garder ou supprimer `/dashboards/daily/operational` et `/dashboards/monthly/strategic`
2. **Si gardés** : Optimiser leurs appels IA
3. **Si supprimés** : Migrer leurs fonctionnalités vers `/dashboard`

