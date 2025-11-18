# 🏠 ERP Fée Maison - Guide Complet

## ℹ️ État du VPS & Production

- **ERP déployé sur VPS OVH Ubuntu 24.10**
- **Accès principal** : http://erp.declaimers.com (ou http://51.254.36.25)
- **Stack** : Nginx → Gunicorn → Flask → PostgreSQL
- **Services supervisés** : systemd
- **Guide complet VPS & sécurité** : [documentation/DEPLOIEMENT_VPS.md](DEPLOIEMENT_VPS.md)

---

## 📋 Table des Matières

### 📚 **Documentation Principale**
- [📖 Workflow Métier Détaillé](WORKFLOW_METIER_DETAIL.md)
- [🏗️ Architecture Technique](ARCHITECTURE_TECHNIQUE.md)
- [🚀 Déploiement VPS](DEPLOIEMENT_VPS.md)
- [🔒 Sécurité & Permissions](SECURITE_ET_PERMISSIONS.md)
- [🔧 Troubleshooting](TROUBLESHOOTING_GUIDE.md)
- [📋 Documentation Technique Complète](../DOCUMENTATION_V5.md) *(Nouvelle documentation exhaustive)*

### 🔧 **Guides Spécialisés**
- [📊 Configuration Dashboards](CONFIGURATION_DASHBOARDS.md)
- [⏰ Configuration Pointeuse ZKTeco](CONFIGURATION_POINTEUSE_ZKTECO.md)

---

## 🏪 Vue d'Ensemble du Système

### **Nature de l'Activité**
"Fée Maison" est une entreprise de production et vente de produits alimentaires artisanaux opérant sur deux sites :
- **Magasin principal** : Vente au comptoir et prise de commandes
- **Local de production** : Fabrication des produits (200m du magasin)

### **Produits Principaux**
- Produits à base de semoule (couscous, msamen, etc.)
- Gâteaux traditionnels
- Produits frais et secs

### **Gestion Multi-Emplacements**
Le stock est géré sur 4 emplacements distincts :
- **Comptoir** : Stock de vente directe
- **Magasin (Labo A)** : Réserve d'ingrédients
- **Local (Labo B)** : Stock de production
- **Consommables** : Matériel et emballages

### **Nouvelles Fonctionnalités (Version 5)**
- **Inventaires Physiques** : Inventaires mensuels avec gestion des écarts
- **Gestion des Invendus** : Déclarations quotidiennes et inventaires hebdomadaires
- **Module Consommables** : Suivi automatique des emballages et matériaux
- **Autocomplétion** : Recherche intelligente dans les formulaires
- **Analyses Périodiques** : Graphiques et statistiques des pertes

---

## 👥 Rôles Utilisateurs

| Rôle | Utilisateur | Accès | Permissions |
|------|-------------|-------|-------------|
| **Admin** | Sofiane | Accès total | Tous les modules, configuration système |
| **Gérante** | Amel | Gestion complète | Tous les modules + caisse, prix, recettes |
| **Vendeuse** | Yasmine | Opérationnel | Commandes, caisse, dashboards shop/prod |
| **Production** | Rayan | Lecture seule | Dashboard production uniquement |

---

## 🏗️ Architecture Générale

### **Structure Technique**
```
ERP Flask Application
├── 📁 app/                    # Modules Flask
│   ├── 📦 stock/             # Gestion stock multi-emplacements
│   ├── 🛒 purchases/         # Achats et fournisseurs
│   ├── 🏭 recipes/           # Recettes et production
│   ├── 🛍️ sales/            # Ventes POS et caisse
│   ├── 📋 orders/            # Commandes clients
│   ├── 🚚 deliverymen/       # Livreurs indépendants
│   ├── 👥 employees/         # RH et paie
│   ├── 🧮 accounting/        # Comptabilité générale
│   ├── 📊 dashboards/        # Dashboards unifiés
│   └── ⏰ zkteco/            # Intégration pointeuse
├── 📄 models.py              # Modèles principaux (623 lignes)
├── ⚙️ config.py              # Configuration
└── 🚀 run.py                 # Point d'entrée
```

### **Base de Données**
- **SGBD** : PostgreSQL
- **ORM** : SQLAlchemy
- **Migrations** : Alembic
- **Modèles** : 15+ modèles principaux

---

## 🔄 Workflow Métier Principal

### **1. Commandes Clients**
```
Commande créée (Amel) → En production → Réception magasin → Livraison → Encaissement
```

### **2. Ordres de Production**
```
Ordre créé (Amel) → Production selon recette → Décrémentation stock → Réception
```

### **3. Gestion Stock**
```
Achat → Incrémentation stock + PMP → Production → Décrémentation → Alertes seuil
```

### **4. Caisse**
```
Ouverture session → Mouvements (ventes, entrées, sorties) → Fermeture → Rapports
```

---

## 📊 Modules Principaux

### ✅ **Modules Terminés**
- **Stock** : Gestion multi-emplacements, valeur, PMP, alertes
- **Achats** : Workflow complet, fournisseurs, incrémentation stock
- **Production** : Recettes, transformation, décrémentation
- **Ventes (POS)** : Interface tactile, panier, validation stock
- **Caisse** : Sessions, mouvements, intégration commandes
- **Commandes** : Workflow client, production, livraison, encaissement
- **Livreurs** : Gestion indépendants, assignation, dettes
- **RH & Paie** : Employés, analytics, paie automatique, pointage
- **Comptabilité** : Plan comptable, écritures, rapports, profit net
- **Pointage ZKTeco** : Intégration pointeuse, données présence
- **Facturation B2B** : Commandes professionnelles, produits composés

---

## 🚀 Déploiement Rapide

### **VPS Production**
```bash
# Structure sur VPS
/opt/erp/app/              # Dépôt Git complet
├── app/                   # Modules Flask
├── models.py              # Modèles principaux
├── .env                   # Variables d'environnement
└── venv/                  # Environnement virtuel
```

### **Commandes Essentielles**
```bash
# Démarrage
sudo systemctl start erp-fee-maison

# Logs
sudo journalctl -u erp-fee-maison -f

# Mise à jour
cd /opt/erp/app && git pull origin main
sudo systemctl restart erp-fee-maison
```

---

## 🔍 Troubleshooting Commun

### **Problèmes Fréquents**
1. **Erreur 500** : Vérifier variables d'environnement et base de données
2. **Connexion refusée** : Vérifier service systemd et logs
3. **Doublons modèles** : Vider cache Python et redémarrer
4. **Permissions** : Vérifier propriétaire fichiers (www-data)

### **Diagnostic Rapide**
```bash
# Test complet
python3 diagnostic_erp.py

# Vérification service
sudo systemctl status erp-fee-maison

# Test base de données
sudo -u postgres psql -d fee_maison_db -c "SELECT 1;"
```

---

## 📈 Métriques Clés

### **KPIs Disponibles**
- **Commandes** : Nombre/jour, statuts, CA généré
- **Production** : Commandes en cours, retards, temps restant
- **Stock** : Valeur totale, alertes, mouvements
- **Employés** : Actifs, performance, analytics
- **Finances** : CA, charges, bénéfices, trésorerie

### **URLs Importantes**
- **Dashboard Principal** : `/dashboard`
- **Dashboard Shop** : `/dashboards/shop`
- **Dashboard Production** : `/dashboards/production`
- **Caisse** : `/sales/cash-status`
- **Commandes** : `/orders/list`
- **Stock** : `/stock/overview`

---

## 🔄 État Actuel du Projet

### **Status Global** : ✅ **OPÉRATIONNEL**
- **Modules** : 11/11 terminés
- **Déploiement** : VPS Ubuntu fonctionnel
- **Base de données** : PostgreSQL opérationnel
- **Intégrations** : ZKTeco, email, comptabilité

### **Dernière Mise à Jour** : 15/07/2025
- Résolution problème connexion VPS
- Nettoyage secrets exposés
- Documentation complète

---

## 📞 Support et Maintenance

### **Contact Principal**
- **Développeur** : Sofiane (Admin)
- **Gérante** : Amel (Gestion quotidienne)

### **Maintenance**
- **Sauvegardes** : Automatiques PostgreSQL
- **Mises à jour** : Via Git pull
- **Monitoring** : Logs systemd et Nginx

---

**📖 Pour plus de détails, consultez les guides spécialisés dans ce dossier.** 