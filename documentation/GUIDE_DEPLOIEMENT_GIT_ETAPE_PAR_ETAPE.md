# 🚀 Guide de Déploiement via Git - Étape par Étape

## 📋 Pour les Non-Développeurs

Ce guide vous explique **exactement** ce qu'il faut faire, commande par commande.

## 🎯 Vue d'ensemble

```
MacBook (Développement) → GitHub → VPS (Production)
     ↓                        ↓              ↓
  Modifications          Push code      Pull code
```

## 📦 PARTIE 1 : Préparer le Code sur le MacBook

### Étape 1.1 : Vérifier que Git est installé

Ouvrez le **Terminal** sur votre MacBook et tapez :

```bash
git --version
```

**Résultat attendu** : `git version 2.x.x` (ou similaire)

**Si erreur** : Git n'est pas installé. Installez-le avec :
```bash
# Sur macOS, Git est généralement déjà installé
# Sinon, installez Xcode Command Line Tools :
xcode-select --install
```

### Étape 1.2 : Vérifier l'état du projet

Dans le Terminal, allez dans le dossier du projet :

```bash
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"
```

Vérifiez si Git est déjà initialisé :

```bash
git status
```

**Si vous voyez** : `fatal: not a git repository`
→ **PAS DE PROBLÈME**, on va l'initialiser à l'étape suivante.

**Si vous voyez** : une liste de fichiers
→ Git est déjà configuré, passez à l'étape 1.4.

### Étape 1.3 : Initialiser Git (si nécessaire)

**SEULEMENT si Git n'était pas initialisé** :

```bash
git init
```

### Étape 1.4 : Créer un fichier .gitignore

Ce fichier empêche Git de sauvegarder des fichiers sensibles (mots de passe, etc.).

Créez un fichier `.gitignore` dans le dossier du projet :

```bash
cat > .gitignore << 'EOF'
# Environnement virtuel
venv/
env/
.venv/

# Fichiers Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Fichiers sensibles
.env
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Fichiers système
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Migrations (optionnel - on peut les garder)
# migrations/

# Backups
*.sql
backups/
EOF
```

### Étape 1.5 : Ajouter tous les fichiers à Git

```bash
git add .
```

**Explication** : Cela prépare tous les fichiers à être sauvegardés.

### Étape 1.6 : Faire le premier commit

```bash
git commit -m "Initial commit - ERP Fée Maison prêt pour déploiement"
```

**Explication** : Cela sauvegarde l'état actuel du projet.

## 🔗 PARTIE 2 : Créer un Dépôt sur GitHub

### Étape 2.1 : Créer un compte GitHub (si nécessaire)

1. Allez sur [github.com](https://github.com)
2. Cliquez sur "Sign up"
3. Créez un compte (gratuit)

### Étape 2.2 : Créer un nouveau dépôt

1. Connectez-vous à GitHub
2. Cliquez sur le bouton **"+"** en haut à droite
3. Cliquez sur **"New repository"**
4. Remplissez :
   - **Repository name** : `fee-maison-erp` (ou le nom que vous voulez)
   - **Description** : `ERP Fée Maison - Gestion de pâtisserie`
   - **Visibility** : **Private** (recommandé pour la sécurité)
5. **NE COCHEZ PAS** "Initialize with README"
6. Cliquez sur **"Create repository"**

### Étape 2.3 : Copier l'URL du dépôt

Après la création, GitHub affiche une page avec des instructions.

**Copiez l'URL HTTPS** (elle ressemble à) :
```
https://github.com/VOTRE_USERNAME/fee-maison-erp.git
```

**⚠️ IMPORTANT** : Remplacez `VOTRE_USERNAME` par votre vrai nom d'utilisateur GitHub.

## 📤 PARTIE 3 : Connecter le Projet à GitHub

### Étape 3.1 : Ajouter GitHub comme "remote"

Dans le Terminal sur votre MacBook :

```bash
# Remplacez VOTRE_USERNAME et fee-maison-erp par vos valeurs
git remote add origin https://github.com/VOTRE_USERNAME/fee-maison-erp.git
```

**Exemple concret** :
```bash
# Si votre username est "sofiane" et le dépôt "fee-maison-erp"
git remote add origin https://github.com/sofiane/fee-maison-erp.git
```

### Étape 3.2 : Vérifier que c'est bien connecté

```bash
git remote -v
```

**Résultat attendu** :
```
origin  https://github.com/VOTRE_USERNAME/fee-maison-erp.git (fetch)
origin  https://github.com/VOTRE_USERNAME/fee-maison-erp.git (push)
```

### Étape 3.3 : Pousser le code sur GitHub

```bash
git branch -M main
git push -u origin main
```

**⚠️ GitHub va vous demander vos identifiants** :
- **Username** : Votre nom d'utilisateur GitHub
- **Password** : **PAS votre mot de passe GitHub**, mais un **Personal Access Token**

### Étape 3.4 : Créer un Personal Access Token (si nécessaire)

Si GitHub demande un token :

1. Allez sur GitHub → **Settings** (votre profil)
2. Dans le menu de gauche : **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. Cliquez sur **"Generate new token (classic)"**
5. Donnez un nom : `ERP Deployment`
6. Cochez la case **`repo`** (toutes les permissions repo)
7. Cliquez sur **"Generate token"**
8. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)
9. Utilisez ce token comme mot de passe lors du `git push`

### Étape 3.5 : Vérifier sur GitHub

Allez sur votre dépôt GitHub dans le navigateur. Vous devriez voir tous vos fichiers.

## 🖥️ PARTIE 4 : Déployer sur le VPS

### Étape 4.1 : Se connecter au VPS

Ouvrez le Terminal et connectez-vous :

```bash
ssh user@VOTRE_IP_VPS
```

**Exemple** :
```bash
ssh root@51.254.36.25
# ou
ssh erp-admin@51.254.36.25
```

### Étape 4.2 : Installer Git sur le VPS (si nécessaire)

```bash
sudo apt update
sudo apt install -y git
```

### Étape 4.3 : Cloner le dépôt GitHub

```bash
# Créer le dossier de l'application
sudo mkdir -p /opt/erp
sudo chown $USER:$USER /opt/erp
cd /opt/erp

# Cloner le dépôt (remplacez par votre URL)
git clone https://github.com/VOTRE_USERNAME/fee-maison-erp.git app
```

**Exemple** :
```bash
git clone https://github.com/sofiane/fee-maison-erp.git app
```

### Étape 4.4 : Suivre le guide de déploiement

Maintenant, suivez le guide `GUIDE_DEPLOIEMENT_VPS_COMPLET.md` à partir de l'étape 3.2 (créer l'environnement virtuel).

## 🔄 PARTIE 5 : Mettre à Jour le Code (Déploiements Futurs)

### Sur le MacBook : Après chaque modification

```bash
# 1. Aller dans le dossier du projet
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"

# 2. Voir ce qui a changé
git status

# 3. Ajouter les fichiers modifiés
git add .

# 4. Sauvegarder (commit)
git commit -m "Description de ce qui a changé"

# 5. Envoyer sur GitHub
git push origin main
```

### Sur le VPS : Récupérer les mises à jour

```bash
# 1. Aller dans le dossier de l'application
cd /opt/erp/app

# 2. Récupérer les dernières modifications
git pull origin main

# 3. Mettre à jour les dépendances (si requirements.txt a changé)
venv/bin/pip install -r requirements.txt

# 4. Appliquer les migrations (si nouvelles migrations)
venv/bin/flask db upgrade

# 5. Redémarrer l'application
sudo systemctl restart erp-fee-maison
```

## 📝 Résumé des Commandes Essentielles

### Sur MacBook (Développement)

```bash
# Voir l'état
git status

# Ajouter les changements
git add .

# Sauvegarder
git commit -m "Description"

# Envoyer sur GitHub
git push origin main
```

### Sur VPS (Production)

```bash
# Récupérer les mises à jour
cd /opt/erp/app
git pull origin main

# Redémarrer
sudo systemctl restart erp-fee-maison
```

## ❓ Questions Fréquentes

### Q: Que faire si j'ai oublié de mettre à jour GitHub avant de déployer ?

**R:** Pas de problème ! Sur le VPS :
```bash
cd /opt/erp/app
git pull origin main
```

### Q: Comment savoir ce qui a changé ?

**R:** Sur le MacBook :
```bash
git status          # Voir les fichiers modifiés
git diff            # Voir les changements détaillés
```

### Q: J'ai fait une erreur, comment annuler ?

**R:** 
```bash
# Annuler les modifications non sauvegardées
git checkout -- fichier.py

# Annuler le dernier commit (mais garder les fichiers)
git reset --soft HEAD~1
```

### Q: Le VPS ne peut pas se connecter à GitHub

**R:** Vérifiez :
1. L'URL du dépôt est correcte
2. Le dépôt est public OU vous avez configuré SSH keys
3. Internet fonctionne sur le VPS : `ping github.com`

## 🔐 Sécurité : Utiliser SSH au lieu de HTTPS (Optionnel)

Pour éviter de taper le token à chaque fois :

### Sur MacBook : Générer une clé SSH

```bash
ssh-keygen -t ed25519 -C "votre_email@example.com"
# Appuyez sur Entrée pour accepter les valeurs par défaut
```

### Copier la clé publique sur GitHub

```bash
cat ~/.ssh/id_ed25519.pub
```

Copiez le résultat et ajoutez-le sur GitHub :
1. GitHub → Settings → SSH and GPG keys
2. New SSH key
3. Collez la clé
4. Save

### Changer l'URL du remote

```bash
git remote set-url origin git@github.com:VOTRE_USERNAME/fee-maison-erp.git
```

## ✅ Checklist Complète

- [ ] Git installé sur MacBook
- [ ] Projet initialisé avec Git
- [ ] Fichier .gitignore créé
- [ ] Premier commit fait
- [ ] Compte GitHub créé
- [ ] Dépôt GitHub créé
- [ ] Projet connecté à GitHub
- [ ] Code poussé sur GitHub
- [ ] Git installé sur VPS
- [ ] Dépôt cloné sur VPS
- [ ] Application déployée et fonctionnelle

## 🆘 En Cas de Problème

1. **Erreur "repository not found"** :
   - Vérifiez l'URL du dépôt
   - Vérifiez que vous avez les droits d'accès

2. **Erreur "authentication failed"** :
   - Utilisez un Personal Access Token, pas votre mot de passe
   - Vérifiez que le token a les permissions `repo`

3. **Erreur "permission denied" sur VPS** :
   - Vérifiez les permissions : `ls -la /opt/erp/app`
   - Utilisez `sudo` si nécessaire

