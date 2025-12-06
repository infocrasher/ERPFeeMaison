#!/usr/bin/env python3
"""
Script pour détecter automatiquement l'IP de la pointeuse ZKTeco
en scannant le réseau local par adresse MAC
"""

import subprocess
import re
import platform
import sys

# Adresse MAC de la pointeuse ZKTeco
POINTEUSE_MAC = "8C:AA:B5:D7:44:29"
POINTEUSE_MAC_NORMALIZED = POINTEUSE_MAC.upper().replace(":", "").replace("-", "")

def normalize_mac(mac):
    """Normalise une adresse MAC pour la comparaison"""
    return mac.upper().replace(":", "").replace("-", "")

def scan_network_windows():
    """Scan réseau sur Windows via arp -a"""
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            # Format: 192.168.8.100     8c-aa-b5-d7-44-29     dynamique
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\w\-:]+)', line)
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                if normalize_mac(mac) == POINTEUSE_MAC_NORMALIZED:
                    return ip
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur scan Windows: {e}")
        return None

def scan_network_unix():
    """Scan réseau sur Mac/Linux via arp -a"""
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            # Format: ? (192.168.8.100) at 8c:aa:b5:d7:44:29 on en0 ifscope [ethernet]
            match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\w:]+)', line)
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                if normalize_mac(mac) == POINTEUSE_MAC_NORMALIZED:
                    return ip
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur scan Unix: {e}")
        return None

def ping_broadcast():
    """Envoie un ping broadcast pour peupler la table ARP"""
    system = platform.system()
    
    try:
        if system == "Windows":
            # Ping broadcast Windows
            subprocess.run(['ping', '-n', '1', '192.168.8.255'], 
                          capture_output=True, timeout=2)
        else:
            # Ping broadcast Mac/Linux
            subprocess.run(['ping', '-c', '1', '192.168.8.255'], 
                          capture_output=True, timeout=2)
    except:
        pass

def detect_pointeuse_ip():
    """Détecte l'IP actuelle de la pointeuse"""
    print("🔍 Détection de l'IP de la pointeuse ZKTeco...")
    print(f"   MAC recherchée: {POINTEUSE_MAC}")
    print()
    
    # Peupler la table ARP
    print("📡 Scan du réseau local...")
    ping_broadcast()
    
    # Attendre un peu
    import time
    time.sleep(1)
    
    # Détecter le système
    system = platform.system()
    
    if system == "Windows":
        ip = scan_network_windows()
    else:
        ip = scan_network_unix()
    
    if ip:
        print(f"✅ Pointeuse trouvée: {ip}")
        print(f"   MAC: {POINTEUSE_MAC}")
        return ip
    else:
        print(f"❌ Pointeuse non trouvée sur le réseau")
        print()
        print("💡 Vérifications:")
        print("1. La pointeuse est-elle allumée ?")
        print("2. Est-elle connectée au réseau ?")
        print("3. Êtes-vous sur le même réseau (192.168.8.x) ?")
        return None

if __name__ == "__main__":
    ip = detect_pointeuse_ip()
    
    if ip:
        sys.exit(0)
    else:
        sys.exit(1)

