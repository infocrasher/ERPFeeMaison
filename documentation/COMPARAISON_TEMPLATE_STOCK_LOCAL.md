# Comparaison Template Stock Local - VPS vs Local

**Date:** 02/12/2025  
**Problème:** Le VPS affiche une version différente du template stock local

---

## 🔍 Différences Observées

### Sur le VPS (Ancienne Version)
- **Layout:** Section "PRODUCTION BLOQUÉE" affiche beaucoup d'ingrédients en colonnes multiples
- **Structure:** Probablement ancienne version avant les modifications

### Sur Local (Version Actuelle - Commit `eede7cd`)
- **Layout:** Section "PRODUCTION BLOQUÉE" dans colonne droite (col-lg-3)
- **Structure:** Réorganisée selon le nouveau layout
- **Tri:** Ingrédients triés (stock > 0 en haut, stock = 0 en bas)

---

## 🔧 Solution : Résoudre l'Erreur Git sur le VPS

### Étape 1 : Résoudre le conflit Git

```bash
ssh erp-admin@51.254.36.25
cd /opt/erp/app

# Sauvegarder les fichiers locaux
mv scripts/diagnostic_comptabilite_vps.py scripts/diagnostic_comptabilite_vps.py.backup
mv scripts/diagnostic_comptabilite_vps.sql scripts/diagnostic_comptabilite_vps.sql.backup

# Faire le pull
git pull origin main
```

### Étape 2 : Vérifier que le template est à jour

```bash
# Vérifier la version du template
git log --oneline app/templates/stock/dashboard_local.html | head -5

# Vérifier le contenu
grep -n "col-lg-9\|col-lg-3\|PRODUCTION BLOQUÉE" app/templates/stock/dashboard_local.html
```

**Résultat attendu:**
- Ligne 118: `<div class="col-lg-9">` (colonne gauche - ingrédients)
- Ligne 171: `<div class="col-lg-3">` (colonne droite - actions + production bloquée)
- Ligne 196: `🚨 PRODUCTION BLOQUÉE` (dans la colonne droite)

### Étape 3 : Redémarrer l'application

```bash
sudo systemctl restart erp-fee-maison
sudo systemctl status erp-fee-maison
```

---

## 📋 Structure du Template Actuel (Local)

### Layout en 2 Colonnes

```
┌─────────────────────────────────────────────────────────┐
│  En-tête + Boutons                                      │
├─────────────────────────────────────────────────────────┤
│  KPIs (4 cartes)                                        │
├──────────────────────────────┬──────────────────────────┤
│  COLONNE GAUCHE (col-lg-9)   │  COLONNE DROITE (col-lg-3)│
│                              │                          │
│  État des Ingrédients       │  Actions Rapides         │
│  - Liste des ingrédients     │  - Historique Transferts │
│  - Tri: stock > 0 en haut    │  - Vue d'Ensemble        │
│                              │  - Ajustement            │
│                              │                          │
│                              │  PRODUCTION BLOQUÉE      │
│                              │  - Liste ingrédients     │
│                              │    manquants             │
│                              │  - Bouton Transfert      │
│                              │    Urgent                │
└──────────────────────────────┴──────────────────────────┘
```

### Code Structure

```html
<div class="row">
    <!-- Colonne gauche : Ingrédients -->
    <div class="col-lg-9">
        <div class="card">
            <h5>État des Ingrédients - Production</h5>
            <!-- Liste des ingrédients triés -->
        </div>
    </div>

    <!-- Colonne droite : Actions + Production Bloquée -->
    <div class="col-lg-3">
        <!-- Actions Rapides -->
        <div class="card">
            <h6>Actions Rapides</h6>
            <!-- Boutons -->
        </div>

        <!-- Production Bloquée -->
        <div class="card mt-3">
            <h6>🚨 PRODUCTION BLOQUÉE</h6>
            <!-- Liste ingrédients manquants -->
        </div>
    </div>
</div>
```

---

## ✅ Vérifications Après Pull

### 1. Vérifier le Template

```bash
# Sur le VPS
cd /opt/erp/app
cat app/templates/stock/dashboard_local.html | grep -A 2 "col-lg-9\|col-lg-3"
```

**Doit afficher:**
```
        <div class="col-lg-9">
            <div class="card">
                <div class="card-header">
```

et

```
        <div class="col-lg-3">
            <!-- Actions Rapides -->
            <div class="card">
```

### 2. Vérifier le Tri

```bash
# Vérifier que le tri est appliqué dans routes.py
grep -A 5 "Trier les ingrédients" app/stock/routes.py
```

**Doit afficher:**
```python
# ✅ CORRECTION : Trier les ingrédients - stock > 0 en haut, stock = 0 en bas
ingredients_local.sort(
    key=lambda p: ((p.stock_ingredients_local or 0) > 0, (p.stock_ingredients_local or 0)),
    reverse=True
)
```

### 3. Vérifier la Valeur Totale

```bash
# Vérifier que valeur_stock_ingredients_local est utilisé
grep "total_value_local\|valeur_stock_ingredients_local" app/stock/routes.py
```

**Doit afficher:**
```python
total_value_local = sum(float(p.valeur_stock_ingredients_local or 0) for p in ingredients_local)
```

---

## 🎯 Résultat Attendu Après Pull

1. **Layout:** 2 colonnes (9/3) au lieu de l'ancien layout
2. **Tri:** Ingrédients avec stock > 0 en haut
3. **Production Bloquée:** Dans la colonne droite, sous "Actions Rapides"
4. **Valeur:** Utilise `valeur_stock_ingredients_local` au lieu de `stock × cost_price`

---

## 📝 Notes

- Le template sur le VPS est probablement l'ancienne version (avant commit `eede7cd`)
- Après le pull, le template sera identique à celui en local
- Les différences visuelles sont dues au fait que le VPS n'a pas encore fait le pull

---

**Fin du document**

