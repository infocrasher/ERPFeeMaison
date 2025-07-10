#!/bin/bash

# Script de configuration PostgreSQL pour ERP Fée Maison
# VPS Ubuntu 24.10 - IP: 51.254.36.25

echo "🗄️ Configuration PostgreSQL pour ERP Fée Maison"
echo "================================================"

# Variables de configuration
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
DB_PASSWORD="FeeMaison_ERP_2025_Secure!"

echo "📋 Variables de configuration :"
echo "   Base de données : $DB_NAME"
echo "   Utilisateur     : $DB_USER"
echo "   Mot de passe    : [SÉCURISÉ]"
echo ""

# 1. Se connecter à PostgreSQL en tant qu'admin
echo "🔐 Étape 1 : Connexion PostgreSQL admin..."
sudo -u postgres psql << EOF

-- 2. Créer la base de données
echo "📊 Étape 2 : Création de la base de données..."
CREATE DATABASE $DB_NAME
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- 3. Créer l'utilisateur avec mot de passe sécurisé
echo "👤 Étape 3 : Création de l'utilisateur..."
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- 4. Attribuer tous les privilèges sur la base
echo "🔑 Étape 4 : Attribution des privilèges..."
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;
GRANT CREATE ON DATABASE $DB_NAME TO $DB_USER;
GRANT TEMPORARY ON DATABASE $DB_NAME TO $DB_USER;

-- 5. Permettre la création de bases de test
echo "🧪 Étape 5 : Permissions pour bases de test..."
ALTER USER $DB_USER CREATEDB;

-- 6. Vérifier la création
echo "✅ Étape 6 : Vérification..."
\l
\du

-- 7. Se connecter à la nouvelle base et configurer les extensions
echo "🔧 Étape 7 : Configuration des extensions..."
\c $DB_NAME

-- Activer les extensions nécessaires pour Flask-SQLAlchemy
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Donner les privilèges sur les extensions
GRANT USAGE ON SCHEMA public TO $DB_USER;
GRANT ALL ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

-- Configurer les privilèges futurs
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;

-- Quitter PostgreSQL
\q
EOF

echo ""
echo "✅ Configuration PostgreSQL terminée !"
echo ""

# 8. Test de connexion avec le nouvel utilisateur
echo "🧪 Test de connexion avec l'utilisateur ERP..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Connexion réussie !"
else
    echo "❌ Erreur de connexion. Vérification de la configuration..."
fi

echo ""
echo "📋 Résumé de la configuration :"
echo "   Base de données : $DB_NAME"
echo "   Utilisateur     : $DB_USER"
echo "   Host            : localhost"
echo "   Port            : 5432"
echo "   Encodage        : UTF8"
echo ""
echo "🚀 PostgreSQL est prêt pour l'ERP Fée Maison !" 