#!/usr/bin/env python3
"""
zkteco_bridge.py
================
Script relais pour capter les données de la pointeuse en local et les envoyer au VPS.
À lancer sur le PC du magasin (192.168.8.104).

Usage:
  python3 scripts/zkteco_bridge.py
  
Configuration ZKTeco:
  Serveur: 192.168.8.104
  Port: 5000
  URL: /zkteco/api/attendance
"""

import logging
from datetime import datetime
import requests
from flask import Flask, request, jsonify

# --- CONFIGURATION ---
VPS_URL = "https://erp.declaimers.com/zkteco/api/attendance"  # URL du VPS
LOCAL_PORT = 5000                                            # Port d'écoute local
ZKTECO_TOKEN = "TokenSecretFeeMaison2025"                    # Doit matcher le VPS

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zkteco_bridge.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/zkteco/api/attendance', methods=['POST'])
def relay_attendance():
    """Reçoit les données de la pointeuse et les relaie au VPS"""
    try:
        # 1. Capter les données brutes
        data = request.get_data()
        json_data = request.get_json(silent=True)
        headers = dict(request.headers)
        
        logger.info(f"📥 Données reçues de {request.remote_addr} ({len(data)} bytes)")
        if json_data:
            logger.info(f"   Contenu: {json_data}")

        # 2. Préparer l'envoi au VPS
        forward_headers = {
            'Content-Type': headers.get('Content-Type', 'application/json'),
            'Authorization': f"Bearer {ZKTECO_TOKEN}",
            'User-Agent': 'ZKTeco-Bridge/1.0'
        }

        # 3. Envoyer au VPS
        logger.info(f"📤 Relai vers {VPS_URL}...")
        try:
            response = requests.post(
                VPS_URL,
                data=data,
                headers=forward_headers,
                timeout=10,
                verify=False # Ignorer erreurs SSL si besoin (ex: certificat let's encrypt expiré)
            )
            
            logger.info(f"✅ Réponse VPS: {response.status_code} - {response.text}")
            
            # 4. Répondre à la pointeuse
            return jsonify({
                "message": "Relay successful",
                "vps_status": response.status_code,
                "timestamp": datetime.now().isoformat()
            }), response.status_code

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur connexion VPS: {str(e)}")
            return jsonify({"message": "VPS connection failed", "error": str(e)}), 502

    except Exception as e:
        logger.error(f"❌ Erreur interne Bridge: {str(e)}")
        return jsonify({"message": "Bridge internal error", "error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "Bridge is running", "vps_target": VPS_URL})

if __name__ == '__main__':
    print(f"🚀 ZKTeco Bridge démarré sur le port {LOCAL_PORT}")
    print(f"   Cible VPS: {VPS_URL}")
    print(f"   Logs: zkteco_bridge.log")
    app.run(host='0.0.0.0', port=LOCAL_PORT, debug=True)
