#!/usr/bin/env python3
"""
Service de pont (bridge) entre la pointeuse ZKTeco et le VPS ERP
Ce service tourne en continu sur le PC du magasin et :
1. Détecte automatiquement l'IP de la pointeuse (par MAC)
2. Se connecte à la pointeuse ZKTeco pour récupérer les pointages
3. Les envoie au VPS avec authentification

À installer comme service Windows sur le PC du magasin.
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import re
import platform

# Configuration
POINTEUSE_MAC = "8C:AA:B5:D7:44:29"
POINTEUSE_PORT = 4370
VPS_URL = "https://erp.declaimers.com/zkteco/api/attendance"
VPS_TOKEN = "TokenSecretFeeMaison2025"  # À mettre dans un .env
CHECK_INTERVAL = 30  # Vérifier toutes les 30 secondes
LOG_FILE = "pointeuse_bridge.log"

def log(message):
    """Logger les messages avec timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # Écrire dans le fichier log
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

def normalize_mac(mac):
    """Normalise une adresse MAC"""
    return mac.upper().replace(":", "").replace("-", "")

def detect_pointeuse_ip():
    """Détecte l'IP de la pointeuse par son MAC"""
    try:
        # Ping broadcast pour peupler ARP
        system = platform.system()
        if system == "Windows":
            subprocess.run(['ping', '-n', '1', '192.168.8.255'], 
                          capture_output=True, timeout=2)
        else:
            subprocess.run(['ping', '-c', '1', '192.168.8.255'], 
                          capture_output=True, timeout=2)
        
        time.sleep(0.5)
        
        # Lire la table ARP
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        target_mac = normalize_mac(POINTEUSE_MAC)
        
        for line in lines:
            # Chercher l'IP et MAC
            if system == "Windows":
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\w\-:]+)', line)
            else:
                match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\w:]+)', line)
            
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                if normalize_mac(mac) == target_mac:
                    return ip
        
        return None
        
    except Exception as e:
        log(f"❌ Erreur détection IP: {e}")
        return None

def connect_to_pointeuse(ip):
    """Se connecte à la pointeuse ZKTeco via zk library"""
    try:
        from zk import ZK
        
        zk = ZK(ip, port=POINTEUSE_PORT, timeout=5)
        conn = zk.connect()
        return conn
        
    except ImportError:
        log("⚠️  Bibliothèque 'pyzk' non installée. Installation: pip install pyzk")
        return None
    except Exception as e:
        log(f"❌ Erreur connexion pointeuse {ip}: {e}")
        return None

def get_recent_attendances(conn, last_check_time):
    """Récupère les pointages récents depuis la pointeuse"""
    try:
        attendances = conn.get_attendance()
        
        # Filtrer les pointages après last_check_time
        recent = []
        for att in attendances:
            if att.timestamp > last_check_time:
                recent.append({
                    'user_id': att.user_id,
                    'timestamp': att.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'punch_type': 'in' if att.punch == 0 else 'out',
                    'status': att.status
                })
        
        return recent
        
    except Exception as e:
        log(f"❌ Erreur récupération pointages: {e}")
        return []

def send_to_vps(attendance_data):
    """Envoie un pointage au VPS"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {VPS_TOKEN}'
        }
        
        response = requests.post(
            VPS_URL,
            json=attendance_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            log(f"✅ Pointage envoyé au VPS: user_id={attendance_data.get('user_id')}")
            return True
        else:
            log(f"❌ Erreur VPS: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Erreur envoi VPS: {e}")
        return False

def run_bridge_service():
    """Service principal qui tourne en boucle"""
    log("=" * 80)
    log("🚀 DÉMARRAGE DU SERVICE PONT POINTEUSE → VPS")
    log("=" * 80)
    log(f"Pointeuse MAC: {POINTEUSE_MAC}")
    log(f"VPS: {VPS_URL}")
    log(f"Intervalle vérification: {CHECK_INTERVAL}s")
    log("")
    
    last_check_time = datetime.now() - timedelta(hours=1)  # Récupérer la dernière heure au démarrage
    last_known_ip = None
    conn = None
    
    while True:
        try:
            # 1. Détecter l'IP actuelle de la pointeuse
            current_ip = detect_pointeuse_ip()
            
            if not current_ip:
                log("⚠️  Pointeuse non détectée sur le réseau. Réessai dans 30s...")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 2. Si l'IP a changé, reconnecter
            if current_ip != last_known_ip:
                log(f"🔄 IP de la pointeuse détectée/changée: {current_ip}")
                
                if conn:
                    try:
                        conn.disconnect()
                    except:
                        pass
                
                conn = connect_to_pointeuse(current_ip)
                
                if not conn:
                    log(f"❌ Impossible de se connecter à la pointeuse {current_ip}")
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                log(f"✅ Connecté à la pointeuse {current_ip}")
                last_known_ip = current_ip
            
            # 3. Récupérer les pointages récents
            recent_attendances = get_recent_attendances(conn, last_check_time)
            
            if recent_attendances:
                log(f"📊 {len(recent_attendances)} nouveau(x) pointage(s) détecté(s)")
                
                # 4. Envoyer chaque pointage au VPS
                for att in recent_attendances:
                    send_to_vps(att)
                
                # Mettre à jour le dernier check
                last_check_time = datetime.now()
            
            # 5. Attendre avant la prochaine vérification
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("🛑 Arrêt du service demandé (Ctrl+C)")
            if conn:
                try:
                    conn.disconnect()
                except:
                    pass
            break
            
        except Exception as e:
            log(f"❌ Erreur inattendue: {e}")
            log("   Réessai dans 30s...")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Vérifier si pyzk est installé
    try:
        import zk
    except ImportError:
        print("❌ Bibliothèque 'pyzk' manquante")
        print("Installation: pip install pyzk")
        sys.exit(1)
    
    run_bridge_service()

