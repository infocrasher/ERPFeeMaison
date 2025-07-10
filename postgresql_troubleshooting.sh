#!/bin/bash

# Script de diagnostic et dépannage PostgreSQL pour ERP Fée Maison
# VPS Ubuntu 24.10 - IP: 51.254.36.25

echo "🔧 Diagnostic et dépannage PostgreSQL"
echo "====================================="

# Variables de configuration
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
DB_PASSWORD="FeeMaison_ERP_2025_Secure!"

echo "📋 Configuration à diagnostiquer :"
echo "   Base de données : $DB_NAME"
echo "   Utilisateur     : $DB_USER"
echo "   Host            : localhost"
echo "   Port            : 5432"
echo ""

# Fonction pour afficher un séparateur
separator() {
    echo ""
    echo "----------------------------------------"
    echo "$1"
    echo "----------------------------------------"
}

# 1. Diagnostic du service PostgreSQL
separator "1. DIAGNOSTIC DU SERVICE POSTGRESQL"

echo "🔍 Statut du service PostgreSQL :"
sudo systemctl status postgresql --no-pager -l

echo ""
echo "🔍 Vérification des processus PostgreSQL :"
ps aux | grep postgres | grep -v grep

echo ""
echo "🔍 Ports d'écoute PostgreSQL :"
sudo netstat -tlnp | grep postgres || echo "Aucun port PostgreSQL trouvé"

# 2. Diagnostic de la configuration
separator "2. DIAGNOSTIC DE LA CONFIGURATION"

echo "🔍 Fichier de configuration principal :"
if [ -f /etc/postgresql/*/main/postgresql.conf ]; then
    echo "✅ Fichier postgresql.conf trouvé"
    ls -la /etc/postgresql/*/main/postgresql.conf
else
    echo "❌ Fichier postgresql.conf non trouvé"
fi

echo ""
echo "🔍 Fichier pg_hba.conf (authentification) :"
if [ -f /etc/postgresql/*/main/pg_hba.conf ]; then
    echo "✅ Fichier pg_hba.conf trouvé"
    ls -la /etc/postgresql/*/main/pg_hba.conf
    echo ""
    echo "📋 Contenu pg_hba.conf (lignes importantes) :"
    grep -E "(local|host)" /etc/postgresql/*/main/pg_hba.conf | head -10
else
    echo "❌ Fichier pg_hba.conf non trouvé"
fi

# 3. Diagnostic des logs
separator "3. DIAGNOSTIC DES LOGS"

echo "🔍 Logs PostgreSQL récents :"
if [ -f /var/log/postgresql/postgresql-*.log ]; then
    echo "✅ Fichiers de logs trouvés"
    ls -la /var/log/postgresql/postgresql-*.log | tail -3
    echo ""
    echo "📋 Dernières erreurs (10 lignes) :"
    sudo tail -10 /var/log/postgresql/postgresql-*.log | grep -i error || echo "Aucune erreur récente"
else
    echo "❌ Aucun fichier de log PostgreSQL trouvé"
fi

# 4. Test de connexion admin
separator "4. TEST DE CONNEXION ADMIN"

echo "🔍 Test de connexion en tant qu'admin PostgreSQL :"
if sudo -u postgres psql -c "SELECT version();" 2>/dev/null; then
    echo "✅ Connexion admin réussie"
else
    echo "❌ Échec de la connexion admin"
    echo "   Tentative de redémarrage du service..."
    sudo systemctl restart postgresql
    sleep 2
    sudo systemctl status postgresql --no-pager -l
fi

# 5. Diagnostic de la base de données
separator "5. DIAGNOSTIC DE LA BASE DE DONNÉES"

echo "🔍 Liste des bases de données :"
sudo -u postgres psql -c "\l" 2>/dev/null || echo "Impossible de lister les bases"

echo ""
echo "🔍 Vérification de l'existence de $DB_NAME :"
if sudo -u postgres psql -c "\l" 2>/dev/null | grep -q $DB_NAME; then
    echo "✅ Base de données $DB_NAME existe"
else
    echo "❌ Base de données $DB_NAME n'existe pas"
    echo "   Création de la base de données..."
    sudo -u postgres createdb $DB_NAME
fi

# 6. Diagnostic de l'utilisateur
separator "6. DIAGNOSTIC DE L'UTILISATEUR"

echo "🔍 Liste des utilisateurs PostgreSQL :"
sudo -u postgres psql -c "\du" 2>/dev/null || echo "Impossible de lister les utilisateurs"

echo ""
echo "🔍 Vérification de l'existence de $DB_USER :"
if sudo -u postgres psql -c "\du" 2>/dev/null | grep -q $DB_USER; then
    echo "✅ Utilisateur $DB_USER existe"
else
    echo "❌ Utilisateur $DB_USER n'existe pas"
    echo "   Création de l'utilisateur..."
    sudo -u postgres createuser --interactive $DB_USER
fi

# 7. Test de connexion utilisateur ERP
separator "7. TEST DE CONNEXION UTILISATEUR ERP"

echo "🔍 Test de connexion avec l'utilisateur ERP :"
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Connexion utilisateur ERP réussie"
else
    echo "❌ Échec de la connexion utilisateur ERP"
    echo "   Diagnostic des privilèges..."
    
    echo ""
    echo "🔍 Attribution des privilèges :"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null
    sudo -u postgres psql -c "GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null
    
    echo "   Nouveau test de connexion..."
    PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Connexion utilisateur ERP maintenant réussie"
    else
        echo "❌ Connexion utilisateur ERP toujours échouée"
    fi
fi

# 8. Diagnostic des performances
separator "8. DIAGNOSTIC DES PERFORMANCES"

echo "🔍 Configuration des performances :"
sudo -u postgres psql -c "SHOW max_connections;" 2>/dev/null
sudo -u postgres psql -c "SHOW shared_buffers;" 2>/dev/null
sudo -u postgres psql -c "SHOW effective_cache_size;" 2>/dev/null

echo ""
echo "🔍 Statistiques de connexion :"
sudo -u postgres psql -c "SELECT count(*) as active_connections FROM pg_stat_activity;" 2>/dev/null

# 9. Diagnostic des extensions
separator "9. DIAGNOSTIC DES EXTENSIONS"

echo "🔍 Extensions installées :"
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "
SELECT extname, extversion 
FROM pg_extension 
ORDER BY extname;" 2>/dev/null

echo ""
echo "🔍 Extensions nécessaires pour Flask-SQLAlchemy :"
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') 
         THEN '✅ uuid-ossp installé' 
         ELSE '❌ uuid-ossp manquant' 
    END as uuid_extension,
    CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') 
         THEN '✅ pg_trgm installé' 
         ELSE '❌ pg_trgm manquant' 
    END as trgm_extension;" 2>/dev/null

# 10. Recommandations
separator "10. RECOMMANDATIONS"

echo "📋 Actions recommandées :"
echo ""

# Vérifier si tout fonctionne
if systemctl is-active --quiet postgresql && \
   sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1 && \
   PGPASSWORD="$DB_PASSWORD" psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    
    echo "✅ PostgreSQL est correctement configuré"
    echo "✅ Base de données accessible"
    echo "✅ Utilisateur ERP fonctionnel"
    echo ""
    echo "🚀 PostgreSQL est prêt pour l'ERP Fée Maison !"
    
else
    echo "❌ Problèmes détectés :"
    echo "   - Vérifiez le statut du service PostgreSQL"
    echo "   - Vérifiez les permissions utilisateur"
    echo "   - Vérifiez la configuration pg_hba.conf"
    echo "   - Relancez le script de configuration"
    echo ""
    echo "🔧 Commandes de réparation :"
    echo "   sudo systemctl restart postgresql"
    echo "   sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""
    echo "   sudo -u postgres createdb $DB_NAME"
    echo "   sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
fi

echo ""
echo "📚 Commandes utiles pour le diagnostic :"
echo "   Status service: sudo systemctl status postgresql"
echo "   Logs temps réel: sudo tail -f /var/log/postgresql/postgresql-*.log"
echo "   Connexion admin: sudo -u postgres psql"
echo "   Connexion ERP: PGPASSWORD='$DB_PASSWORD' psql -h localhost -U $DB_USER -d $DB_NAME"
echo "   Configuration: sudo nano /etc/postgresql/*/main/postgresql.conf"
echo "   Authentification: sudo nano /etc/postgresql/*/main/pg_hba.conf" 