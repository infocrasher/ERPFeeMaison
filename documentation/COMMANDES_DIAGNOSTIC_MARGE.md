# 🔍 Commandes de Diagnostic - Marge Négative

**Date :** 11 décembre 2025  
**Problème :** Dashboard affiche marge -49k DA

---

## 📋 Commandes à exécuter sur le VPS

### 1. Diagnostic complet KPI (comme hier)

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/verifier_kpi_dashboard.py 2025-12-11
```

Ce script affiche :
- ✅ CA du jour
- ✅ COGS (Coût des marchandises)
- ✅ Coût main d'œuvre
- ✅ Prime Cost
- ✅ Marge brute (avec pourcentage)
- ✅ Vérification des calculs
- ✅ Comparaison avec les services

---

### 2. Diagnostic toutes données dashboard

```bash
python3 scripts/diagnostic_toutes_donnees_dashboard.py 2025-12-11
```

Ce script vérifie :
- ✅ Valeur stock
- ✅ Achats du jour
- ✅ Toutes les incohérences

---

### 3. Analyse problèmes restants

```bash
python3 scripts/analyser_problemes_restants.py 2025-12-11
```

Ce script analyse :
- ✅ Flux caisse
- ✅ Présence
- ✅ Valeur stock

---

## 🎯 Script principal recommandé

**Utilisez d'abord celui-ci :**

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/verifier_kpi_dashboard.py 2025-12-11
```

Ce script va identifier :
- Si le CA est correct
- Si le COGS est correct
- Si le coût main d'œuvre est correct
- Pourquoi la marge est négative

---

## 📊 Ce qu'il faut vérifier

1. **CA du jour** : Est-ce que le CA est correct ?
2. **COGS** : Est-ce que le coût des marchandises est trop élevé ?
3. **Coût main d'œuvre** : Est-ce que le coût main d'œuvre est correct ?
4. **Calcul marge** : Marge = CA - COGS - Main d'œuvre

Si la marge est négative, c'est que :
- Soit le CA est trop bas
- Soit le COGS est trop élevé
- Soit le coût main d'œuvre est trop élevé

---

## 🔧 Après le diagnostic

Une fois le diagnostic exécuté, envoyez-moi les résultats et je pourrai :
1. Identifier la cause exacte
2. Proposer une correction
3. Vérifier si c'est le même problème qu'hier

