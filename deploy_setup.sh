#!/bin/bash

# Script de déploiement automatisé pour ERP Fée Maison
# Configuration VPS Ubuntu 24.10

echo "🚀 Déploiement ERP Fée Maison - Démarrage"
echo "=========================================="

# Mise à jour système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation Python 3.13 et pip
echo "🐍 Installation Python 3.13..."
sudo apt install -y python3.13 python3.13-venv python3.13-dev python3-pip

# Installation PostgreSQL
echo "🐘 Installation PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Installation Nginx
echo "🌐 Installation Nginx..."
sudo apt install -y nginx

# Installation Redis (optionnel pour cache)
echo "🔴 Installation Redis..."
sudo apt install -y redis-server

# Installation des outils de développement
echo "🔧 Installation outils développement..."
sudo apt install -y git curl wget unzip build-essential

# Installation supervisor pour gestion des processus
echo "👨‍💼 Installation Supervisor..."
sudo apt install -y supervisor

# Installation certbot pour SSL
echo "🔒 Installation Certbot pour SSL..."
sudo apt install -y certbot python3-certbot-nginx

# Création utilisateur pour l'application
echo "👤 Création utilisateur erp..."
sudo adduser --system --group --home /opt/erp erp

# Création des répertoires
echo "📁 Création structure répertoires..."
sudo mkdir -p /opt/erp/app
sudo mkdir -p /opt/erp/logs
sudo mkdir -p /var/log/erp

# Configuration PostgreSQL
echo "🐘 Configuration PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Création base de données
sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'erp_password_2025';"
sudo -u postgres psql -c "CREATE DATABASE fee_maison_db OWNER erp_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fee_maison_db TO erp_user;"

# Configuration Redis
echo "🔴 Configuration Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Configuration Nginx
echo "🌐 Configuration Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Affichage des informations
echo ""
echo "✅ Installation terminée !"
echo "=========================="
echo "🐘 PostgreSQL : Démarré"
echo "🔴 Redis : Démarré"
echo "🌐 Nginx : Démarré"
echo ""
echo "📋 Informations de connexion :"
echo "Base de données : fee_maison_db"
echo "Utilisateur DB : erp_user"
echo "Mot de passe DB : erp_password_2025"
echo ""
echo "🎯 Prochaines étapes :"
echo "1. Transférer le code source"
echo "2. Configurer l'environnement virtuel"
echo "3. Installer les dépendances Python"
echo "4. Configurer Nginx"
echo "5. Démarrer l'application" 