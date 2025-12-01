# Instructions : Injection de Stock depuis Excel sur le VPS

## 📋 Prérequis

1. Le fichier Excel `Stock V1.xlsx` doit être présent sur le VPS
2. Le script `scripts/inject_stock_from_excel.py` doit être présent (déjà poussé sur Git)

## 📁 Étape 1 : Copier le fichier Excel sur le VPS

### Option A : Via SCP (depuis votre machine locale)

**Utiliser l'adresse IP ou le domaine :**

```bash
# Option 1 : Avec l'adresse IP
scp "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor/excel_files/Stock V1.xlsx" erp-admin@51.254.36.25:/opt/erp/app/excel_files/

# Option 2 : Avec le domaine (si configuré dans ~/.ssh/config)
scp "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor/excel_files/Stock V1.xlsx" erp-admin@erp.declaimers.com:/opt/erp/app/excel_files/
```

### Option B : Via SFTP ou FileZilla

1. Connectez-vous au VPS via SFTP/FileZilla
2. Naviguez vers `/opt/erp/app/excel_files/`
3. Créez le dossier s'il n'existe pas : `mkdir -p excel_files`
4. Uploadez le fichier `Stock V1.xlsx`

### Option C : Le fichier est déjà sur le VPS

Si le fichier est déjà sur le VPS (dans un autre emplacement), notez son chemin.

## 🔄 Étape 2 : Mettre à jour le code sur le VPS

```bash
cd /opt/erp/app
git pull origin main
```

## ✅ Étape 3 : Vérifier les dépendances

Le script nécessite `pandas` et `openpyxl`. Vérifiez qu'ils sont installés :

```bash
cd /opt/erp/app
source venv/bin/activate
pip list | grep -E "pandas|openpyxl"
```

Si ce n'est pas le cas, installez-les :

```bash
pip install pandas openpyxl
```

## 🔍 Étape 4 : Test en mode simulation (OBLIGATOIRE)

**⚠️ IMPORTANT : Toujours tester en mode simulation avant l'injection réelle !**

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/inject_stock_from_excel.py --dry-run
```

Vérifiez le résumé :
- Nombre de produits trouvés
- Nombre de produits à modifier
- Détail des modifications par type de stock

## 💾 Étape 5 : Injection réelle

Une fois que vous avez vérifié le résumé en mode simulation :

### Option A : Avec confirmation interactive

```bash
python3 scripts/inject_stock_from_excel.py
# Tapez "oui" quand demandé
```

### Option B : Sans confirmation (toutes les modifications appliquées automatiquement)

```bash
python3 scripts/inject_stock_from_excel.py --confirm-all
```

## 📊 Étape 6 : Vérification

Vérifiez que les stocks ont bien été mis à jour dans l'interface ERP ou via SQL :

```sql
-- Exemple : Vérifier quelques produits
SELECT id, name, stock_comptoir, stock_ingredients_magasin, stock_consommables, last_stock_update 
FROM products 
WHERE last_stock_update > NOW() - INTERVAL '1 hour'
ORDER BY last_stock_update DESC 
LIMIT 10;
```

## 🎯 Résultat attendu

- ✅ Tous les produits avec un ID dans le fichier Excel devraient être trouvés
- ✅ Les stocks seront mis à jour selon le type :
  - `consommable` → `stock_consommables`
  - `finished` → `stock_comptoir`
  - `ingredient` → `stock_ingredients_magasin` (ou `stock_ingredients_local` si utilisé dans une recette)
- ✅ `last_stock_update` sera mis à jour pour chaque produit modifié

## ⚠️ Notes importantes

1. **Les problèmes d'encodage** (PÃ¢te FeuilletÃ©e) ne posent pas de problème car la recherche se fait par **ID**, pas par nom.

2. **Les produits non trouvés** en local sont normaux (ils n'existent peut-être pas dans votre base locale mais existent sur le VPS).

3. **Sur le VPS**, tous les produits avec un ID devraient être trouvés puisque le fichier vient de là-bas.

4. Le script fait un **commit** automatique après l'injection, donc les modifications sont persistantes.

## 🆘 En cas de problème

Si des produits ne sont pas trouvés sur le VPS :

1. Vérifiez que les IDs dans le fichier Excel correspondent bien aux IDs dans la base de données
2. Vérifiez que le fichier Excel est bien celui téléchargé depuis le VPS
3. Vérifiez les logs du script pour plus de détails

## 📝 Exemple de sortie attendue

```
📊 Analyse du fichier Excel : excel_files/Stock V1.xlsx

✅ Fichier chargé : 418 lignes
📋 Colonnes : id, nom, type, unite, stock_actuel, nouveau_stock

📦 Types de produits trouvés :
   - consommable: 70 produits
   - finished: 123 produits
   - ingredient: 225 produits

💾 MODE INJECTION
============================================================
✅ ID 1 (Semoule Fin): stock_ingredients_magasin 60357.14 → 30000.00
✅ ID 2 (Huile Civital): stock_ingredients_magasin 1175.30 → 250000.00
...

============================================================
📊 RÉSUMÉ
============================================================
Total lignes Excel      : 418
Produits trouvés        : 418
Produits non trouvés    : 0
Produits à modifier     : XXX
Produits ignorés (identique): XXX

✅ Stocks injectés avec succès dans la base de données !
```

