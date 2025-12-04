#!/bin/bash
# Script de test de la pointeuse en local
# Usage: ./test_pointeuse_local.sh [IP_POINTEUSE]

POINTEUSE_IP=${1:-192.168.100.16}

echo "🧪 TEST DE LA POINTEUSE EN LOCAL"
echo "================================="
echo ""
echo "IP Pointeuse locale: $POINTEUSE_IP"
echo ""

# Exporter les variables d'environnement pour le test
export ZKTECO_IP=$POINTEUSE_IP
export ZKTECO_PORT=4370
export ZKTECO_API_TOKEN=TokenSecretFeeMaison2025
export FLASK_ENV=development

# Activer l'environnement virtuel
source venv/bin/activate

echo "1️⃣  Test diagnostic pointeuse..."
python3 scripts/diagnostic_pointeuse_zkteco.py

echo ""
echo "2️⃣  Test API ping..."
curl http://127.0.0.1:5000/zkteco/api/ping

echo ""
echo ""
echo "3️⃣  Test pointage (user_id=3, Machair)..."
curl -X POST http://127.0.0.1:5000/zkteco/api/test-attendance \
     -H 'Content-Type: application/json' \
     -H 'Authorization: Bearer TokenSecretFeeMaison2025' \
     -d '{
       "user_id": 3,
       "timestamp": "2025-12-04 14:00:00",
       "punch_type": "in"
     }'

echo ""
echo ""
echo "✅ Tests terminés"
echo ""
echo "Pour voir les pointages:"
echo "  http://127.0.0.1:5000/employees/attendance/live"

