#!/bin/bash

# ========================================
# SCRIPT DE DÉMARRAGE ERP FÉE MAISON
# ========================================
# Script alternatif pour démarrer l'ERP manuellement
# Utile pour les tests et le débogage

set -e

echo "🚀 Démarrage ERP Fée Maison"
echo "============================"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "wsgi.py" ]; then
    echo "❌ Erreur: wsgi.py non trouvé. Assurez-vous d'être dans le répertoire du projet."
    exit 1
fi

# Charger les variables d'environnement
if [ -f ".env" ]; then
    echo "📋 Chargement des variables d'environnement depuis .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Fichier .env non trouvé, utilisation des variables système"
fi

# Vérifier les variables critiques
if [ -z "$FLASK_ENV" ]; then
    export FLASK_ENV=production
    echo "ℹ️  FLASK_ENV défini à 'production'"
fi

if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -base64 32)
    echo "ℹ️  SECRET_KEY généré automatiquement"
fi

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Création..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Environnement virtuel trouvé"
    source venv/bin/activate
fi

# Vérifier Gunicorn
if ! command -v gunicorn &> /dev/null; then
    echo "📦 Installation de Gunicorn..."
    pip install gunicorn
fi

# Créer le répertoire de logs
mkdir -p logs

echo "🔧 Configuration:"
echo "   - FLASK_ENV: $FLASK_ENV"
echo "   - SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "   - POSTGRES_USER: ${POSTGRES_USER:-non défini}"
echo "   - POSTGRES_HOST: ${POSTGRES_HOST:-localhost}"
echo "   - POSTGRES_DB_NAME: ${POSTGRES_DB_NAME:-non défini}"

# Test de diagnostic rapide
echo ""
echo "🔍 Test de diagnostic rapide..."
python3 diagnostic_erp.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Diagnostic réussi, démarrage de l'application..."
    echo ""
    echo "🌐 L'application sera accessible sur:"
    echo "   - Local: http://127.0.0.1:8080"
    echo "   - Réseau: http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📝 Logs disponibles dans:"
    echo "   - Access: logs/access.log"
    echo "   - Error: logs/error.log"
    echo ""
    echo "🛑 Pour arrêter: Ctrl+C"
    echo ""
    
    # Démarrer Gunicorn
    exec gunicorn \
        --bind 0.0.0.0:8080 \
        --workers 3 \
        --timeout 120 \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level info \
        wsgi:app
else
    echo ""
    echo "❌ Diagnostic échoué. Vérifiez les erreurs ci-dessus."
    exit 1
fi 