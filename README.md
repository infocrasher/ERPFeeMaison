# 🏪 ERP Fée Maison

## 📋 Description

ERP Flask complet pour la gestion d'une entreprise de production alimentaire artisanale.

## 🚀 Démarrage Rapide

### Développement Local
```bash
# Installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres

# Base de données
flask db upgrade
python seed.py

# Démarrage
flask run
```

### Production (VPS)
```bash
# Démarrage service
sudo systemctl start erp-fee-maison

# Logs
sudo journalctl -u erp-fee-maison -f

# Mise à jour
cd /opt/erp/app && git pull origin main
sudo systemctl restart erp-fee-maison
```

## 📚 Documentation

Consultez le dossier `documentation/` pour la documentation complète :

- **[Guide Principal](documentation/ERP_COMPLETE_GUIDE.md)** - Vue d'ensemble du système
- **[Workflow Métier](documentation/WORKFLOW_METIER_DETAIL.md)** - Processus métier détaillés
- **[Architecture Technique](documentation/ARCHITECTURE_TECHNIQUE.md)** - Structure technique
- **[Déploiement VPS](documentation/DEPLOIEMENT_VPS.md)** - Guide de déploiement
- **[Troubleshooting](documentation/TROUBLESHOOTING_GUIDE.md)** - Solutions aux problèmes

### 🔧 Maintenance Automatique

La documentation est maintenue automatiquement par des scripts dans le dossier `scripts/` :

```bash
# Mise à jour de la documentation
./update_documentation

# Nettoyage des fichiers temporaires
./cleanup_documentation

# Plus d'infos
cat scripts/README.md
```

## 🏗️ Architecture

- **Backend** : Flask + SQLAlchemy + PostgreSQL
- **Frontend** : Bootstrap 5 + Jinja2
- **Serveur** : Gunicorn + Nginx
- **Authentification** : Flask-Login + bcrypt

## 📊 Modules

- ✅ **Stock** - Gestion multi-emplacements
- ✅ **Achats** - Workflow complet
- ✅ **Production** - Recettes et transformation
- ✅ **Ventes** - POS et caisse
- ✅ **Commandes** - Workflow client
- ✅ **Livreurs** - Gestion indépendants
- ✅ **RH & Paie** - Employés et analytics
- ✅ **Comptabilité** - Plan comptable complet
- ✅ **Pointage** - Intégration ZKTeco

## 🔐 Sécurité

- Variables d'environnement pour les secrets
- Authentification par rôles
- Protection CSRF
- Mots de passe hachés

## 📞 Support

- **Développeur** : Sofiane (Admin)
- **Gérante** : Amel (Gestion quotidienne)

---

**Status** : ✅ **OPÉRATIONNEL** - VPS Ubuntu fonctionnel 