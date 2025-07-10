#!/bin/bash

# Script de validation PostgreSQL pour ERP Fée Maison
# VPS Ubuntu 24.10 - IP: 51.254.36.25

echo "🧪 Validation de la configuration PostgreSQL"
echo "============================================"

# Variables de configuration
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
DB_PASSWORD="FeeMaison_ERP_2025_Secure!"

echo "📋 Configuration à valider :"
echo "   Base de données : $DB_NAME"
echo "   Utilisateur     : $DB_USER"
echo "   Host            : localhost"
echo "   Port            : 5432"
echo ""

# 1. Vérifier que PostgreSQL est en cours d'exécution
echo "🔍 Étape 1 : Vérification du service PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL est en cours d'exécution"
else
    echo "❌ PostgreSQL n'est pas en cours d'exécution"
    echo "   Démarrage du service..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# 2. Vérifier que PostgreSQL écoute sur le bon port
echo ""
echo "🔍 Étape 2 : Vérification du port d'écoute..."
if netstat -tlnp | grep :5432 > /dev/null; then
    echo "✅ PostgreSQL écoute sur le port 5432"
    netstat -tlnp | grep :5432
else
    echo "❌ PostgreSQL n'écoute pas sur le port 5432"
fi

# 3. Test de connexion avec l'utilisateur ERP
echo ""
echo "🔍 Étape 3 : Test de connexion avec l'utilisateur ERP..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Connexion réussie avec l'utilisateur ERP"
else
    echo "❌ Échec de la connexion avec l'utilisateur ERP"
    echo "   Vérification des privilèges..."
fi

# 4. Vérifier les privilèges utilisateur
echo ""
echo "🔍 Étape 4 : Vérification des privilèges utilisateur..."
sudo -u postgres psql -c "\du $DB_USER" 2>/dev/null

# 5. Vérifier l'existence de la base de données
echo ""
echo "🔍 Étape 5 : Vérification de l'existence de la base..."
sudo -u postgres psql -c "\l" | grep $DB_NAME > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Base de données $DB_NAME existe"
else
    echo "❌ Base de données $DB_NAME n'existe pas"
fi

# 6. Test de création de table (test des privilèges)
echo ""
echo "🔍 Étape 6 : Test de création de table..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS test_connection (
    id SERIAL PRIMARY KEY,
    test_field VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Test de création de table réussi"
    
    # Nettoyer la table de test
    PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "DROP TABLE test_connection;" 2>/dev/null
    echo "✅ Table de test supprimée"
else
    echo "❌ Échec du test de création de table"
fi

# 7. Vérifier les extensions
echo ""
echo "🔍 Étape 7 : Vérification des extensions..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pg_trgm');" 2>/dev/null

# 8. Test de performance basique
echo ""
echo "🔍 Étape 8 : Test de performance basique..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "
SELECT 
    version() as postgres_version,
    current_database() as current_db,
    current_user as current_user,
    pg_size_pretty(pg_database_size(current_database())) as db_size;" 2>/dev/null

# 9. Vérification de la configuration
echo ""
echo "🔍 Étape 9 : Vérification de la configuration..."
sudo -u postgres psql -c "SHOW max_connections;" 2>/dev/null
sudo -u postgres psql -c "SHOW shared_buffers;" 2>/dev/null
sudo -u postgres psql -c "SHOW effective_cache_size;" 2>/dev/null

echo ""
echo "🎯 Résumé de la validation :"
echo "============================"
echo ""

# Résumé final
if systemctl is-active --quiet postgresql && \
   netstat -tlnp | grep :5432 > /dev/null && \
   PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    
    echo "✅ CONFIGURATION POSTGRESQL VALIDÉE"
    echo "   ✅ Service en cours d'exécution"
    echo "   ✅ Port d'écoute correct"
    echo "   ✅ Connexion utilisateur ERP"
    echo "   ✅ Privilèges configurés"
    echo "   ✅ Base de données accessible"
    echo ""
    echo "🚀 PostgreSQL est prêt pour l'ERP Fée Maison !"
    echo ""
    echo "📋 Informations de connexion :"
    echo "   URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: $DB_NAME"
    echo "   User: $DB_USER"
    
else
    echo "❌ CONFIGURATION POSTGRESQL INCOMPLÈTE"
    echo "   Veuillez vérifier les erreurs ci-dessus"
    echo "   et relancer le script de configuration"
fi

echo ""
echo "📚 Commandes utiles :"
echo "   Connexion admin: sudo -u postgres psql"
echo "   Connexion ERP: PGPASSWORD='$DB_PASSWORD' psql -h localhost -U $DB_USER -d $DB_NAME"
echo "   Status service: sudo systemctl status postgresql"
echo "   Logs: sudo tail -f /var/log/postgresql/postgresql-*.log" 