#!/usr/bin/env python3
"""
Script pour identifier les appareils connectés au réseau
et leurs adresses MAC pour configurer des IP statiques
"""

from huawei_lte_api.Client import Client
from huawei_lte_api.Connection import Connection
import json
from datetime import datetime

print("🔍 IDENTIFICATION DES APPAREILS RÉSEAU")
print("=" * 80)
print()

ROUTER_URL = 'http://192.168.8.1/'
USERNAME = 'admin'
PASSWORD = input("Entrez le mot de passe du routeur: ").strip() or 'admin'

print()
print(f"⏰ Scan effectué le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    with Connection(f'http://{USERNAME}:{PASSWORD}@192.168.8.1/') as connection:
        client = Client(connection)
        
        print("📡 APPAREILS CONNECTÉS AU ROUTEUR")
        print("-" * 80)
        
        # Essayer de récupérer la liste des clients DHCP
        try:
            # Méthode 1: via DHCP
            dhcp_info = client.dhcp.settings()
            print("Configuration DHCP:")
            print(json.dumps(dhcp_info, indent=2, ensure_ascii=False))
            print()
        except Exception as e:
            print(f"⚠️  DHCP settings: {e}")
        
        # Essayer d'autres méthodes
        print("\n🔎 Tentative de récupération des clients via différentes API...")
        print()
        
        # Liste de toutes les méthodes à essayer
        methods_to_try = [
            ('client.monitoring.traffic_statistics()', lambda: client.monitoring.traffic_statistics()),
            ('client.monitoring.month_statistics()', lambda: client.monitoring.month_statistics()),
            ('client.monitoring.status()', lambda: client.monitoring.status()),
        ]
        
        for method_name, method_func in methods_to_try:
            try:
                print(f"📊 {method_name}")
                print("-" * 40)
                result = method_func()
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print()
            except Exception as e:
                print(f"   ❌ {e}")
                print()
        
        print("=" * 80)
        print()
        print("💡 INFORMATIONS NÉCESSAIRES POUR IP STATIQUE:")
        print()
        print("Pour configurer une IP statique via DHCP, il nous faut:")
        print("1. ✅ IP souhaitée: 192.168.8.104 (Pointeuse)")
        print("2. ✅ IP souhaitée: 192.168.8.102 (PC)")
        print("3. ❓ Adresse MAC de la pointeuse ZKTeco")
        print("4. ❓ Adresse MAC du PC magasin")
        print()
        print("🔧 COMMENT TROUVER L'ADRESSE MAC:")
        print()
        print("📱 Sur la pointeuse ZKTeco:")
        print("   Menu → Comm → Ethernet → Voir MAC Address")
        print()
        print("💻 Sur le PC Windows (magasin):")
        print("   cmd → ipconfig /all → chercher 'Adresse physique'")
        print()
        print("💻 Sur le PC Mac:")
        print("   Préférences Système → Réseau → Avancé → Matériel → Adresse MAC")
        print()
        print("💻 Sur Linux:")
        print("   ip link show")
        print()
        print("=" * 80)
        print()
        print("📝 UNE FOIS LES ADRESSES MAC IDENTIFIÉES:")
        print()
        print("Vous pourrez soit:")
        print("A) Configurer via l'interface web du routeur (192.168.8.1)")
        print("   → DHCP → Static IP Address / IP Reservation")
        print()
        print("B) Utiliser un script Python pour automatiser la configuration")
        print("   (si l'API Huawei l'autorise)")
        
except Exception as e:
    print(f"❌ ERREUR: {e}")
    print()
    print("⚠️  ATTENTION:")
    print("Ce script doit être exécuté depuis un appareil connecté")
    print("au réseau du routeur Huawei (192.168.8.x)")
    print()
    print("Actuellement, vous êtes probablement sur le réseau 192.168.100.x")
    print("(réseau de test local).")
    print()
    print("Pour exécuter ce script:")
    print("1. Connectez-vous au WiFi/réseau du routeur Huawei au magasin")
    print("2. Relancez ce script")

