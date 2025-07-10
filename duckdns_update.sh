#!/bin/bash

# Configuration DuckDNS
DOMAIN="fee-maison-erp"
TOKEN="52db57a4-90cd-4ff2-a1ec-676e68b7dd9e"
IP="197.204.8.180"

# Mise à jour de l'IP
echo "Mise à jour de ${DOMAIN}.duckdns.org vers l'IP ${IP}..."
curl "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${IP}"

echo ""
echo "Mise à jour terminée !" 