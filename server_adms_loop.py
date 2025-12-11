#!/usr/bin/env python3
"""
Script de synchronisation pointeuse en boucle continue
Récupère les pointages toutes les 30 secondes
"""

from zk import ZK
import requests
import time
import sys
import subprocess
import re
import platform
from datetime import datetime

# ================= CONFIGURATION =================
POINTEUSE_MAC = "8C:AA:B5:D7:44:29"
ZK_IP_FALLBACK = "192.168.8.104"
ZK_PORT = 4370

API_URL = "https://erp.declaimers.com/zkteco/api/attendance"
TOKEN = "TokenSecretFeeMaison2025"

CHECK_INTERVAL = 30  # Vérifier toutes les 30 secondes
# =================================================


def normalize_mac(mac):
    if not mac:
        return ""
    return mac.upper().replace(":", "").replace("-", "")


def detect_pointeuse_ip_fast():
    """Détection rapide de l'IP par MAC (cache ARP uniquement)"""
    try:
        system = platform.system()
        target_mac = normalize_mac(POINTEUSE_MAC)
        
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=2)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if system == "Windows":
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\w\-:]+)', line)
            else:
                match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\w:]+)', line)
            
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                if normalize_mac(mac) == target_mac:
                    return ip
        
        return ZK_IP_FALLBACK
    except:
        return ZK_IP_FALLBACK


def sync_once():
    """Une synchronisation complète"""
    try:
        ZK_IP = detect_pointeuse_ip_fast()
        
        zk = ZK(ZK_IP, port=ZK_PORT, timeout=5, password=0, force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()
        
        attendance = conn.get_attendance()
        
        if attendance:
            print(f"📊 {len(attendance)} nouveaux pointages !")
            count_ok = 0
            
            for punch in attendance:
                punch_code = str(punch.punch)
                punch_type = "out" if punch_code == '2' else "in"
                
                payload = {
                    "user_id": punch.user_id,
                    "timestamp": str(punch.timestamp),
                    "punch_type": punch_type
                }
                
                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }
                
                try:
                    resp = requests.post(API_URL, json=payload, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        print(f"  ✅ User {punch.user_id} à {punch.timestamp} ({punch_type})")
                        count_ok += 1
                    else:
                        print(f"  ❌ Erreur {resp.status_code}")
                except Exception as e:
                    print(f"  ❌ {e}")
            
            print(f"✅ {count_ok}/{len(attendance)} envoyés")
        
        conn.enable_device()
        conn.disconnect()
        return True
        
    except Exception as e:
        # Erreur silencieuse (normal si pas de nouveaux pointages ou connexion temporaire échouée)
        return False


def main():
    print("=" * 60)
    print("🚀 SYNCHRONISATION CONTINUE POINTEUSE → ERP")
    print("=" * 60)
    print(f"⏰ Vérification toutes les {CHECK_INTERVAL} secondes")
    print(f"🌐 VPS: {API_URL}")
    print("=" * 60)
    print(f"▶️  Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{now}] Cycle #{cycle} - Vérification...")
            
            sync_once()
            
            # Attendre avant le prochain cycle
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt demandé (Ctrl+C)")
        print(f"   Total cycles: {cycle}")
        print(f"   Durée: {cycle * CHECK_INTERVAL // 60} minutes")


if __name__ == "__main__":
    main()



