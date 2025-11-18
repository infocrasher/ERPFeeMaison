#!/bin/bash

# 🖨️ Script de démarrage ERP Fée Maison avec support imprimante
# Vérifie la configuration et démarre l'application

echo "🖨️ ERP FÉE MAISON - DÉMARRAGE AVEC IMPRIMANTE"
echo "============================================="

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "💡 Créez-le avec: python3 -m venv venv"
    exit 1
fi

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier les dépendances imprimante
echo "📦 Vérification des dépendances imprimante..."
python -c "import usb.core; print('✅ pyusb installé')" 2>/dev/null || {
    echo "❌ pyusb manquant"
    echo "💡 Installation: pip install pyusb"
    pip install pyusb
}

python -c "import escpos; print('✅ python-escpos installé')" 2>/dev/null || {
    echo "❌ python-escpos manquant"
    echo "💡 Installation: pip install python-escpos"
    pip install python-escpos
}

# Test rapide de détection imprimante
echo "🔍 Test de détection imprimante..."
python -c "
import usb.core
dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)
if dev:
    print('✅ Imprimante détectée')
    print(f'   VID: 0x{dev.idVendor:04x}, PID: 0x{dev.idProduct:04x}')
else:
    print('⚠️ Imprimante non détectée')
    print('💡 Vérifiez que l\'imprimante est connectée et allumée')
"

# Configuration par défaut si pas de .env
if [ ! -f ".env" ]; then
    echo "⚙️ Création configuration par défaut..."
    cat > .env << EOF
# Configuration Imprimante ERP Fée Maison
PRINTER_ENABLED=true
PRINTER_VENDOR_ID=0471
PRINTER_PRODUCT_ID=0055
PRINTER_INTERFACE=0
PRINTER_TIMEOUT=5000

# Réseau (pour VPS)
PRINTER_NETWORK_ENABLED=false
PRINTER_AGENT_HOST=localhost
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=change_me_in_production
EOF
    echo "✅ Fichier .env créé avec configuration par défaut"
fi

# Afficher la configuration
echo ""
echo "📋 Configuration actuelle:"
echo "  PRINTER_ENABLED=$(grep PRINTER_ENABLED .env | cut -d'=' -f2)"
echo "  PRINTER_VENDOR_ID=$(grep PRINTER_VENDOR_ID .env | cut -d'=' -f2)"
echo "  PRINTER_PRODUCT_ID=$(grep PRINTER_PRODUCT_ID .env | cut -d'=' -f2)"

# Test rapide du service
echo ""
echo "🧪 Test rapide du service d'impression..."
python -c "
try:
    from app.services.printer_service import get_printer_service
    service = get_printer_service()
    status = service.get_status()
    print(f'✅ Service initialisé')
    print(f'   Activé: {status[\"enabled\"]}')
    print(f'   Connecté: {status[\"connected\"]}')
    print(f'   Queue: {status[\"queue_size\"]} jobs')
except Exception as e:
    print(f'❌ Erreur service: {e}')
"

echo ""
echo "🚀 Démarrage de l'ERP..."
echo "📍 URLs importantes:"
echo "   • Application: http://127.0.0.1:5000"
echo "   • Dashboard imprimante: http://127.0.0.1:5000/admin/printer/"
echo "   • Tests: http://127.0.0.1:5000/admin/printer/"
echo ""
echo "💡 Conseils:"
echo "   • Testez l'imprimante via le dashboard admin"
echo "   • Effectuez une vente pour tester l'automatisation"
echo "   • Consultez les logs en cas de problème"
echo ""

# Démarrer l'application
python run.py









