# 🧹 Guide de Nettoyage du Projet

## 📋 Fichiers Exclus du Dépôt Git

Pour éviter de surcharger le dépôt et le VPS, les fichiers suivants sont **exclus** :

### ❌ Fichiers Exclus (ne seront PAS sur le VPS)

1. **Fichiers Excel de comptabilité** :
   - `Téléchargements Comptabilité/*.xlsx`
   - Tous les fichiers Excel de comptabilité

2. **Fichiers CSV de données historiques** :
   - `donnees_historiques*.csv`
   - `test_extraction*.csv`

3. **Fichiers de test** :
   - `tests/` (sauf README si nécessaire)
   - `test_*.py`
   - `*_test.py`

4. **Fichiers temporaires** :
   - `flask_form_debug.html`
   - `cookies.txt`
   - `*.tmp`, `*.temp`

5. **Fichiers sensibles** :
   - `.env` (contient les mots de passe)
   - `*.db`, `*.sqlite`

## ✅ Fichiers Inclus (seront sur le VPS)

- ✅ Code source Python (`app/`)
- ✅ Templates HTML (`app/templates/`)
- ✅ Fichiers statiques (`app/static/`)
- ✅ Migrations (`migrations/`)
- ✅ Scripts de déploiement (`scripts/`)
- ✅ Documentation (`documentation/`)
- ✅ Configuration (`config.py`, `requirements.txt`, `wsgi.py`)

## 🔄 Comment Ajouter des Fichiers au Dépôt (si nécessaire)

Si vous voulez forcer l'ajout d'un fichier normalement ignoré :

```bash
git add -f chemin/vers/fichier.xlsx
```

## 📦 Transfert des Fichiers Volumineux

### Option 1 : Transfert Direct (Recommandé)

Pour les fichiers Excel et CSV, transférez-les directement sur le VPS :

```bash
# Depuis le MacBook
scp -r "Téléchargements Comptabilité" user@vps:/opt/erp/data/
scp donnees_historiques_comptabilite.csv user@vps:/opt/erp/data/
```

### Option 2 : Stockage Externe

- Google Drive
- Dropbox
- Serveur de fichiers séparé

## 🧹 Nettoyer le Dépôt Local

Si vous voulez nettoyer votre dépôt local (sans affecter les fichiers) :

```bash
# Retirer les fichiers du suivi Git (mais les garder sur le disque)
git rm --cached -r "Téléchargements Comptabilité"
git rm --cached donnees_historiques*.csv

# Commiter les changements
git commit -m "Retrait des fichiers volumineux du dépôt"
git push origin main
```

## 📊 Taille du Dépôt

Pour vérifier la taille du dépôt :

```bash
# Taille totale
du -sh .git

# Fichiers les plus volumineux
git ls-files | xargs du -h | sort -rh | head -20
```

## ✅ Vérification

Pour vérifier qu'un fichier est bien ignoré :

```bash
git check-ignore -v chemin/vers/fichier.xlsx
```

Si le fichier est ignoré, Git vous dira quelle règle l'ignore.

