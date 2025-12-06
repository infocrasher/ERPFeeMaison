#!/usr/bin/env python3
"""
Script de synchronisation pointeuse ZKTeco → ERP
Version améliorée avec détection automatique d'IP
"""

from zk import ZK
import requests
import time
import sys
import subprocess
import re
import platform

# ================= CONFIGURATION =================
# 🔧 AMÉLIORATION : Détection automatique de l'IP par MAC
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


def detect_pointeuse_ip():
    """
    Détecte automatiquement l'IP de la pointeuse par sa MAC
    Retourne l'IP détectée ou l'IP par défaut si non trouvée
    """
    print(f"🔍 Recherche de la pointeuse (MAC: {POINTEUSE_MAC})...")
    
    try:
        # Ping broadcast pour peupler la table ARP
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
                # Format Windows: 192.168.8.100     8c-aa-b5-d7-44-29     dynamique
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\w\-:]+)', line)
            else:
                # Format Unix: ? (192.168.8.100) at 8c:aa:b5:d7:44:29 on en0
                match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\w:]+)', line)
            
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                if normalize_mac(mac) == target_mac:
                    print(f"✅ Pointeuse détectée à l'IP: {ip}")
                    return ip
        
        print(f"⚠️  Pointeuse non trouvée, utilisation IP par défaut: {ZK_IP_FALLBACK}")
        return ZK_IP_FALLBACK
        
    except Exception as e:
        print(f"⚠️  Erreur détection IP: {e}")
        print(f"   Utilisation IP par défaut: {ZK_IP_FALLBACK}")
        return ZK_IP_FALLBACK


def main():
    # 🔧 AMÉLIORATION : Détecter l'IP automatiquement
    ZK_IP = detect_pointeuse_ip()
    
    print(f"🔌 Connexion au WL30 ({ZK_IP})...")
    
    # Configuration pour WL30 (TCP sans password)
    zk = ZK(ZK_IP, port=ZK_PORT, timeout=10, password=0, force_udp=False, ommit_ping=False)
    conn = None

    try:
        conn = zk.connect()
        print("✅ Connecté à la pointeuse !")
        
        # Désactiver pour éviter les conflits pendant la lecture
        conn.disable_device()
        
        # 1. RECUPERER LES LOGS
        print("📥 Lecture des pointages...")
        try:
            attendance = conn.get_attendance()
            print(f"📊 {len(attendance)} pointages trouvés en mémoire.")
            
            if attendance:
                print("📤 Envoi vers l'ERP...")
                count_ok = 0
                for punch in attendance:
                    # ---------------------------------------------------------
                    # 🔧 CORRECTION MAJEURE ICI (Selon votre photo)
                    # Code 1 = Entrée (Check-In)
                    # Code 2 = Sortie (Check-Out)
                    # Code 0 = Entrée par défaut (souvent)
                    # ---------------------------------------------------------
                    punch_code = str(punch.punch)
                    
                    if punch_code == '2':
                        punch_type = "out"
                    elif punch_code == '1':
                        punch_type = "in"
                    elif punch_code == '0':
                        punch_type = "in" # Par défaut
                    else:
                        # Autres codes (Pauses, etc.) -> On traite comme IN par défaut ou on ignore
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
                            print(".", end="", flush=True) # Petit point = Succès
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

        # 2. WORKAROUND WL30 (Scan Utilisateurs - Optionnel)
        print("👤 Vérification des utilisateurs...")
        users_count = 0
        for uid in range(1, 10): # Scan partiel rapide
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
        print("1. La pointeuse est-elle allumée et connectée au réseau ?")
        print("2. Êtes-vous sur le même réseau (192.168.8.x) ?")
        print(f"3. Pouvez-vous pinguer l'IP: {ZK_IP} ?")
        print(f"   Commande: ping {ZK_IP}")
        
    finally:
        if conn:
            try:
                conn.disconnect()
                print("🔌 Déconnecté.")
            except: 
                pass


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SYNCHRONISATION POINTEUSE → ERP")
    print("   Version avec détection automatique d'IP")
    print("=" * 60)
    print()
    
    main()
    
    # On laisse la fenêtre ouverte 5 secondes pour lire
    print("\n⏳ Fermeture dans 5 secondes...")
    time.sleep(5)

