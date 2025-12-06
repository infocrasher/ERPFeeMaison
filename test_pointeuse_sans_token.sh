#!/bin/bash

echo "🧪 TEST POINTEUSE SANS TOKEN (Simulation de la pointeuse physique)"
echo "================================================================"
echo ""

echo "1️⃣  Test avec AUCUN header Authorization (comme la vraie pointeuse)..."
echo ""

curl -X POST http://127.0.0.1:5000/zkteco/api/attendance \
     -H 'Content-Type: application/json' \
     -d '{
       "user_id": 3,
       "timestamp": "2025-12-06 15:30:00",
       "punch_type": "in"
     }' \
     -w "\nStatus: %{http_code}\n" \
     -s

echo ""
echo "================================================================"
echo ""

echo "2️⃣  Test GET sans token..."
echo ""

curl -X GET http://127.0.0.1:5000/zkteco/api/attendance \
     -w "\nStatus: %{http_code}\n" \
     -s

echo ""
echo "================================================================"
echo ""

echo "3️⃣  Test PING sans token..."
echo ""

curl -X GET http://127.0.0.1:5000/zkteco/api/ping \
     -w "\nStatus: %{http_code}\n" \
     -s

echo ""
echo "================================================================"
echo ""
echo "✅ Si les 3 tests retournent Status: 200, la pointeuse DEVRAIT fonctionner"
echo "❌ Si Status: 400 ou 401, il y a un problème de sécurité"

