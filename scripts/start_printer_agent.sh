#!/bin/bash
# 🖨️ Script de démarrage de l'Agent d'Impression
# À exécuter sur la machine POS (MacBook) pour permettre au VPS d'accéder à l'imprimante

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🖨️ AGENT D'IMPRESSION ERP FÉE MAISON${NC}"
echo "=========================================="
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "app/services/printer_agent.py" ]; then
    echo -e "${RED}❌ Erreur: Ce script doit être exécuté depuis la racine du projet${NC}"
    exit 1
fi

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Environnement virtuel non trouvé${NC}"
    echo "💡 Créez-le avec: python3 -m venv venv"
    exit 1
fi

# Activer l'environnement virtuel
echo -e "${YELLOW}🐍 Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Vérifier les dépendances
echo -e "${YELLOW}📦 Vérification des dépendances...${NC}"
python -c "import usb.core" 2>/dev/null || {
    echo -e "${RED}❌ pyusb manquant${NC}"
    echo "💡 Installation: pip install pyusb"
    pip install pyusb
}

# Charger la configuration depuis .env
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚙️ Chargement de la configuration depuis .env...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠️ Fichier .env non trouvé, utilisation des valeurs par défaut${NC}"
fi

# Configuration par défaut
PRINTER_AGENT_HOST=${PRINTER_AGENT_HOST:-"0.0.0.0"}
PRINTER_AGENT_PORT=${PRINTER_AGENT_PORT:-"8080"}
PRINTER_AGENT_TOKEN=${PRINTER_AGENT_TOKEN:-"default_token_change_me"}

# Afficher la configuration
echo ""
echo -e "${GREEN}📋 Configuration:${NC}"
echo "   Host: $PRINTER_AGENT_HOST"
echo "   Port: $PRINTER_AGENT_PORT"
echo "   Token: ${PRINTER_AGENT_TOKEN:0:10}..."
echo ""

# Obtenir l'IP locale
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d'/' -f1)
fi

echo -e "${GREEN}📍 Adresse IP locale: $LOCAL_IP${NC}"
echo ""
echo -e "${YELLOW}💡 Pour configurer le VPS, utilisez:${NC}"
echo "   PRINTER_NETWORK_ENABLED=true"
echo "   PRINTER_AGENT_HOST=$LOCAL_IP"
echo "   PRINTER_AGENT_PORT=$PRINTER_AGENT_PORT"
echo "   PRINTER_AGENT_TOKEN=$PRINTER_AGENT_TOKEN"
echo ""

# Vérifier si le port est déjà utilisé
if lsof -Pi :$PRINTER_AGENT_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}❌ Le port $PRINTER_AGENT_PORT est déjà utilisé${NC}"
    echo "💡 Arrêtez le processus existant ou changez le port"
    exit 1
fi

# Test rapide de détection imprimante
echo -e "${YELLOW}🔍 Test de détection imprimante...${NC}"
python -c "
import usb.core
dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)
if dev:
    print('✅ Imprimante détectée')
    print(f'   VID: 0x{dev.idVendor:04x}, PID: 0x{dev.idProduct:04x}')
else:
    print('⚠️ Imprimante non détectée')
    print('💡 Vérifiez que l\'imprimante est connectée et allumée')
" || echo "⚠️ Erreur lors de la détection"

echo ""
echo -e "${GREEN}🚀 Démarrage de l'agent...${NC}"
echo -e "${YELLOW}💡 Appuyez sur Ctrl+C pour arrêter${NC}"
echo ""

# Démarrer l'agent
python -m app.services.printer_agent \
    --host "$PRINTER_AGENT_HOST" \
    --port "$PRINTER_AGENT_PORT" \
    --token "$PRINTER_AGENT_TOKEN"

