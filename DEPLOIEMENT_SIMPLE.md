# 🚀 Déploiement Simple - Étape par Étape

## ✅ Bonne Nouvelle !

Votre projet est **déjà connecté à GitHub** : `git@github.com:infocrasher/ERPFeeMaison.git`

## 📋 ÉTAPE 1 : Sur le MacBook - Envoyer les Modifications sur GitHub

### Ouvrir le Terminal

1. Appuyez sur `Cmd + Espace` (barre de recherche macOS)
2. Tapez `Terminal`
3. Appuyez sur Entrée

### Aller dans le Dossier du Projet

Copiez-collez cette commande dans le Terminal :

```bash
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"
```

### Voir ce qui a Changé

```bash
git status
```

Vous verrez une liste de fichiers modifiés.

### Ajouter Tous les Fichiers Modifiés

```bash
git add .
```

### Sauvegarder (Commit)

```bash
git commit -m "Mise à jour avant déploiement VPS"
```

### Envoyer sur GitHub

```bash
git push origin main
```

**✅ C'est fait !** Votre code est maintenant sur GitHub.

---

## 📋 ÉTAPE 2 : Sur le VPS - Récupérer le Code

### Se Connecter au VPS

Dans le Terminal, tapez :

```bash
ssh root@51.254.36.25
```

**Remplacez** `root` par votre utilisateur si différent.

**Si c'est la première fois**, vous devrez accepter la connexion (tapez `yes`).

### Installer Git (si nécessaire)

```bash
sudo apt update
sudo apt install -y git
```

### Cloner le Projet depuis GitHub

```bash
# Créer le dossier
sudo mkdir -p /opt/erp
sudo chown $USER:$USER /opt/erp
cd /opt/erp

# Cloner depuis GitHub
git clone git@github.com:infocrasher/ERPFeeMaison.git app
```

**⚠️ Si erreur SSH** : Utilisez HTTPS à la place :

```bash
git clone https://github.com/infocrasher/ERPFeeMaison.git app
```

### Vérifier que c'est Bien Cloné

```bash
cd /opt/erp/app
ls -la
```

Vous devriez voir tous vos fichiers.

---

## 📋 ÉTAPE 3 : Installer l'Application sur le VPS

### Suivre le Guide de Déploiement

Maintenant, suivez le guide complet :

```bash
# Lire le guide
cat /opt/erp/app/documentation/GUIDE_DEPLOIEMENT_VPS_COMPLET.md
```

**OU** utilisez le script automatique :

```bash
cd /opt/erp/app
sudo bash scripts/deploy_vps_complete.sh
```

Le script va :
- ✅ Installer Python, PostgreSQL, Nginx
- ✅ Créer la base de données
- ✅ Installer les dépendances
- ✅ Configurer le service
- ✅ Démarrer l'application

---

## 🔄 Pour les Mises à Jour Futures (Très Simple !)

### Sur le MacBook : Après chaque Modification

```bash
# 1. Aller dans le dossier
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"

# 2. Ajouter les changements
git add .

# 3. Sauvegarder
git commit -m "Description de ce qui a changé"

# 4. Envoyer sur GitHub
git push origin main
```

### Sur le VPS : Récupérer les Mises à Jour

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

**C'est tout !** 🎉

---

## ❓ Questions Fréquentes

### Q: Comment savoir si j'ai des modifications à envoyer ?

**R:** Sur le MacBook :
```bash
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"
git status
```

Si vous voyez des fichiers en rouge ou vert, il y a des modifications.

### Q: J'ai oublié de faire `git push`, que faire ?

**R:** Pas de problème ! Faites simplement :
```bash
git push origin main
```

### Q: Le VPS ne peut pas se connecter à GitHub

**R:** Vérifiez :
1. Internet fonctionne : `ping github.com`
2. Utilisez HTTPS au lieu de SSH :
   ```bash
   git clone https://github.com/infocrasher/ERPFeeMaison.git app
   ```

### Q: Comment annuler un commit si j'ai fait une erreur ?

**R:** 
```bash
# Annuler le dernier commit (mais garder les fichiers)
git reset --soft HEAD~1
```

---

## ✅ Checklist Rapide

### Avant de Déployer
- [ ] Modifications testées sur MacBook
- [ ] `git add .` exécuté
- [ ] `git commit` fait
- [ ] `git push origin main` réussi
- [ ] Vérifié sur GitHub que les fichiers sont là

### Sur le VPS
- [ ] Connecté au VPS via SSH
- [ ] Git installé
- [ ] Projet cloné depuis GitHub
- [ ] Script de déploiement exécuté
- [ ] Application accessible

---

## 🆘 En Cas de Problème

1. **Erreur "permission denied"** :
   - Utilisez `sudo` devant les commandes

2. **Erreur "repository not found"** :
   - Vérifiez l'URL : `git remote -v`
   - Vérifiez que vous avez accès au dépôt GitHub

3. **Erreur "authentication failed"** :
   - Utilisez HTTPS au lieu de SSH
   - Ou configurez une clé SSH sur le VPS

