#!/bin/bash

# Script de création de la structure des répertoires pour ERP Fée Maison
# VPS Ubuntu 24.10 - IP: 51.254.36.25

echo "📁 Création de la structure des répertoires ERP"
echo "==============================================="

# Variables
ERP_USER="erp-admin"
ERP_GROUP="erp-admin"
ERP_BASE="/opt/erp"
LOG_DIR="/var/log/erp"

echo "📋 Configuration :"
echo "   Utilisateur : $ERP_USER"
echo "   Groupe      : $ERP_GROUP"
echo "   Base        : $ERP_BASE"
echo "   Logs        : $LOG_DIR"
echo ""

# 1. Créer la structure principale
echo "🔨 Étape 1 : Création de la structure principale..."
sudo mkdir -p $ERP_BASE/{app,backups,uploads,config,scripts}
sudo mkdir -p $ERP_BASE/app/{static,templates,logs}
sudo mkdir -p $LOG_DIR

# 2. Créer les sous-répertoires spécifiques
echo "🔨 Étape 2 : Création des sous-répertoires..."
sudo mkdir -p $ERP_BASE/uploads/{products,employees,documents}
sudo mkdir -p $ERP_BASE/backups/{daily,weekly,monthly}
sudo mkdir -p $ERP_BASE/config/{production,development}
sudo mkdir -p $ERP_BASE/scripts/{deployment,maintenance}

# 3. Créer les répertoires de logs spécifiques
echo "🔨 Étape 3 : Création des répertoires de logs..."
sudo mkdir -p $LOG_DIR/{app,nginx,postgresql,redis}
sudo mkdir -p $ERP_BASE/app/logs/{access,error,debug}

# 4. Créer les répertoires temporaires
echo "🔨 Étape 4 : Création des répertoires temporaires..."
sudo mkdir -p $ERP_BASE/temp/{sessions,cache,uploads}
sudo mkdir -p /tmp/erp/{backups,exports}

# 5. Définir les permissions
echo "🔨 Étape 5 : Configuration des permissions..."
sudo chown -R $ERP_USER:$ERP_GROUP $ERP_BASE
sudo chown -R $ERP_USER:$ERP_GROUP $LOG_DIR
sudo chown -R $ERP_USER:$ERP_GROUP /tmp/erp

# 6. Définir les permissions spécifiques
echo "🔨 Étape 6 : Configuration des permissions spécifiques..."
# Répertoires de logs (lecture/écriture pour l'utilisateur ERP)
sudo chmod 755 $LOG_DIR
sudo chmod 755 $ERP_BASE/app/logs

# Répertoires d'uploads (lecture/écriture pour l'utilisateur ERP)
sudo chmod 755 $ERP_BASE/uploads
sudo chmod 755 $ERP_BASE/uploads/{products,employees,documents}

# Répertoires de backup (lecture/écriture pour l'utilisateur ERP)
sudo chmod 755 $ERP_BASE/backups
sudo chmod 755 $ERP_BASE/backups/{daily,weekly,monthly}

# Répertoires temporaires (lecture/écriture pour l'utilisateur ERP)
sudo chmod 755 $ERP_BASE/temp
sudo chmod 755 $ERP_BASE/temp/{sessions,cache,uploads}
sudo chmod 755 /tmp/erp
sudo chmod 755 /tmp/erp/{backups,exports}

# 7. Créer les fichiers de configuration vides
echo "🔨 Étape 7 : Création des fichiers de configuration..."
sudo touch $ERP_BASE/config/production/.env
sudo touch $ERP_BASE/config/development/.env
sudo touch $ERP_BASE/app/logs/access/access.log
sudo touch $ERP_BASE/app/logs/error/error.log
sudo touch $ERP_BASE/app/logs/debug/debug.log

# 8. Définir les permissions des fichiers
sudo chown $ERP_USER:$ERP_GROUP $ERP_BASE/config/production/.env
sudo chown $ERP_USER:$ERP_GROUP $ERP_BASE/config/development/.env
sudo chown $ERP_USER:$ERP_GROUP $ERP_BASE/app/logs/access/access.log
sudo chown $ERP_USER:$ERP_GROUP $ERP_BASE/app/logs/error/error.log
sudo chown $ERP_USER:$ERP_GROUP $ERP_BASE/app/logs/debug/debug.log

sudo chmod 640 $ERP_BASE/config/production/.env
sudo chmod 640 $ERP_BASE/config/development/.env
sudo chmod 644 $ERP_BASE/app/logs/access/access.log
sudo chmod 644 $ERP_BASE/app/logs/error/error.log
sudo chmod 644 $ERP_BASE/app/logs/debug/debug.log

# 9. Créer les liens symboliques utiles
echo "🔨 Étape 8 : Création des liens symboliques..."
sudo ln -sf $ERP_BASE/config/production/.env $ERP_BASE/.env
sudo ln -sf $LOG_DIR/app/erp.log $ERP_BASE/app/logs/erp.log

# 10. Vérifier la structure créée
echo ""
echo "🔍 Étape 9 : Vérification de la structure..."
echo "Structure créée :"
tree $ERP_BASE -L 3 2>/dev/null || find $ERP_BASE -type d | head -20

echo ""
echo "📋 Permissions des répertoires principaux :"
ls -la $ERP_BASE/
echo ""
ls -la $LOG_DIR/

# 11. Test d'écriture
echo ""
echo "🔍 Étape 10 : Test d'écriture..."
sudo -u $ERP_USER touch $ERP_BASE/test_write.txt 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Test d'écriture réussi"
    sudo rm $ERP_BASE/test_write.txt
else
    echo "❌ Test d'écriture échoué"
fi

echo ""
echo "🎯 Résumé de la création :"
echo "=========================="
echo "✅ Structure des répertoires créée"
echo "✅ Permissions configurées"
echo "✅ Fichiers de configuration créés"
echo "✅ Liens symboliques établis"
echo ""
echo "📁 Répertoires principaux :"
echo "   Application : $ERP_BASE/app/"
echo "   Configuration : $ERP_BASE/config/"
echo "   Backups : $ERP_BASE/backups/"
echo "   Uploads : $ERP_BASE/uploads/"
echo "   Logs : $LOG_DIR/"
echo "   Temp : $ERP_BASE/temp/"
echo ""
echo "🚀 Structure prête pour le déploiement de l'ERP !" 