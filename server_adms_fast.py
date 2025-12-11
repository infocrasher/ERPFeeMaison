#!/usr/bin/env python3
"""
Script de synchronisation pointeuse ZKTeco → ERP
Version RAPIDE avec scan multithread
"""

from zk import ZK
import requests
import time
import sys
import subprocess
import re
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= CONFIGURATION =================
POINTEUSE_MAC = "8C:AA:B5:D7:44:29"  # MAC de la pointeuse
ZK_IP_FALLBACK = "192.168.8.104"  # IP par défaut si détection échoue
ZK_PORT = 4370

# Config ERP
API_URL = "https://erp.declaimers.com/zkteco/api/attendance"
TOKEN = "TokenSecretFeeMaison2025"
# =================================================


def normalize_mac(mac):
    """Normalise une adresse MAC pour la comparaison"""
    if not mac:
        return ""
    return mac.upper().replace(":", "").replace("-", "")


def ping_ip(ip):
    """Ping une IP unique (pour multithreading)"""
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(['ping', '-n', '1', '-w', '100', ip], 
                          capture_output=True, timeout=0.3)
        else:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                          capture_output=True, timeout=0.3)
        return True
    except:
        return False


def detect_pointeuse_ip_fast():
    """
    Détecte l'IP de la pointeuse RAPIDEMENT avec scan multithread
    """
    print(f"🔍 Recherche rapide de la pointeuse (MAC: {POINTEUSE_MAC})...")
    
    try:
        system = platform.system()
        target_mac = normalize_mac(POINTEUSE_MAC)
        
        # 1. Vérifier cache ARP actuel
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
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
                    print(f"✅ Pointeuse trouvée en cache: {ip}")
                    return ip
        
        # 2. Scan multithread de la plage (RAPIDE !)
        print(f"   Scan rapide 192.168.8.100-200 (multithread)...")
        ips = [f"192.168.8.{i}" for i in range(100, 201)]
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(ping_ip, ip): ip for ip in ips}
            for future in as_completed(futures):
                pass  # On attend juste que tous les pings se terminent
        
        print(f"   Scan terminé, lecture table ARP...")
        
        # 3. Relire table ARP
        time.sleep(0.3)
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
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
                    print(f"✅ Pointeuse détectée: {ip}")
                    return ip
        
        print(f"⚠️  Pointeuse non trouvée, IP par défaut: {ZK_IP_FALLBACK}")
        return ZK_IP_FALLBACK
        
    except Exception as e:
        print(f"⚠️  Erreur: {e}")
        print(f"   IP par défaut: {ZK_IP_FALLBACK}")
        return ZK_IP_FALLBACK


def main():
    # Détection rapide
    ZK_IP = detect_pointeuse_ip_fast()
    
    print(f"🔌 Connexion au WL30 ({ZK_IP})...")
    
    zk = ZK(ZK_IP, port=ZK_PORT, timeout=10, password=0, force_udp=False, ommit_ping=False)
    conn = None

    try:
        conn = zk.connect()
        print("✅ Connecté à la pointeuse !")
        
        conn.disable_device()
        
        print("📥 Lecture des pointages...")
        try:
            attendance = conn.get_attendance()
            print(f"📊 {len(attendance)} pointages trouvés en mémoire.")
            
            if attendance:
                print("📤 Envoi vers l'ERP...")
                count_ok = 0
                for punch in attendance:
                    punch_code = str(punch.punch)
                    
                    if punch_code == '2':
                        punch_type = "out"
                    elif punch_code == '1':
                        punch_type = "in"
                    elif punch_code == '0':
                        punch_type = "in"
                    else:
                        punch_type = "in" 
                    
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
                            print(".", end="", flush=True)
                            count_ok += 1
                        else:
                            print(f"x({resp.status_code})", end="", flush=True)
                    except Exception as e:
                        print(f"![{e}]", end="", flush=True)

                print(f"\n✅ Terminé : {count_ok} envoyés sur {len(attendance)}.")
            else:
                print("💤 Aucun historique récent.")

        except Exception as e:
            print(f"⚠️ Erreur lecture logs : {e}")

        print("👤 Vérification des utilisateurs...")
        users_count = 0
        for uid in range(1, 10):
            try:
                if conn.get_user_template(uid, 0):
                    users_count += 1
            except: 
                pass
        print(f"   -> {users_count} utilisateurs détectés (Scan partiel).")

        conn.enable_device()
        print("🏁 Synchronisation finie avec succès.")

    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {e}")
        print("\n💡 VÉRIFICATIONS:")
        print("1. La pointeuse est-elle allumée ?")
        print("2. Même réseau (192.168.8.x) ?")
        print(f"3. Test: ping {ZK_IP}")
        
    finally:
        if conn:
            try:
                conn.disconnect()
                print("🔌 Déconnecté.")
            except: 
                pass


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SYNCHRONISATION POINTEUSE → ERP (VERSION RAPIDE)")
    print("=" * 60)
    print()
    
    start_time = time.time()
    main()
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Temps total: {elapsed:.1f}s")
    print("\n⏳ Fermeture dans 5 secondes...")
    time.sleep(5)



