#!/usr/bin/env python3
"""
Script pour explorer les options de configuration du routeur Huawei
et voir si on peut configurer des IP statiques pour la pointeuse et le PC
"""

from huawei_lte_api.Client import Client
from huawei_lte_api.Connection import Connection
import json

print("🔧 EXPLORATION DU ROUTEUR HUAWEI")
print("=" * 80)
print()

# ⚠️ IMPORTANT: Remplacer 'admin' et 'votre_mot_de_passe' par les vrais identifiants
ROUTER_URL = 'http://192.168.8.1/'
USERNAME = 'admin'
PASSWORD = input("Entrez le mot de passe du routeur (ou laissez vide pour 'admin'): ").strip() or 'admin'

print()
print(f"Connexion au routeur: {ROUTER_URL}")
print()

try:
    with Connection(f'http://{USERNAME}:{PASSWORD}@192.168.8.1/') as connection:
        client = Client(connection)
        
        print("1️⃣  INFORMATIONS DU ROUTEUR")
        print("-" * 80)
        try:
            device_info = client.device.information()
            print(json.dumps(device_info, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erreur: {e}")
        print()
        
        print("2️⃣  INFORMATIONS RÉSEAU")
        print("-" * 80)
        try:
            net_info = client.net.net_mode()
            print(json.dumps(net_info, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erreur: {e}")
        print()
        
        print("3️⃣  CONFIGURATION DHCP")
        print("-" * 80)
        try:
            dhcp_info = client.dhcp.settings()
            print(json.dumps(dhcp_info, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erreur: {e}")
        print()
        
        print("4️⃣  LISTE DES CLIENTS CONNECTÉS (DHCP)")
        print("-" * 80)
        try:
            # Essayer différentes méthodes pour lister les clients
            try:
                hosts = client.dhcp.hosts()
                print(json.dumps(hosts, indent=2, ensure_ascii=False))
            except AttributeError:
                print("⚠️  client.dhcp.hosts() non disponible")
                
            try:
                lan_hosts = client.lan.hosts()
                print(json.dumps(lan_hosts, indent=2, ensure_ascii=False))
            except AttributeError:
                print("⚠️  client.lan.hosts() non disponible")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        print()
        
        print("5️⃣  CONFIGURATION LAN")
        print("-" * 80)
        try:
            lan_info = client.lan.settings()
            print(json.dumps(lan_info, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erreur: {e}")
        print()
        
        print("6️⃣  MÉTHODES DISPONIBLES SUR client.dhcp")
        print("-" * 80)
        dhcp_methods = [m for m in dir(client.dhcp) if not m.startswith('_')]
        print("Méthodes disponibles:")
        for method in dhcp_methods:
            print(f"  - client.dhcp.{method}()")
        print()
        
        print("7️⃣  MÉTHODES DISPONIBLES SUR client.lan")
        print("-" * 80)
        lan_methods = [m for m in dir(client.lan) if not m.startswith('_')]
        print("Méthodes disponibles:")
        for method in lan_methods:
            print(f"  - client.lan.{method}()")
        print()
        
        print("=" * 80)
        print("✅ Exploration terminée !")
        print()
        print("📋 PROCHAINES ÉTAPES:")
        print("1. Identifier l'adresse MAC de la pointeuse ZKTeco")
        print("2. Identifier l'adresse MAC du PC magasin")
        print("3. Chercher une méthode pour ajouter des baux DHCP statiques")
        print("   (ex: client.dhcp.static_address_add() ou similaire)")
        print()
        print("💡 OBJECTIF:")
        print("   - Pointeuse ZKTeco: 192.168.8.104 (fixe)")
        print("   - PC Magasin: 192.168.8.102 (fixe)")
        
except Exception as e:
    print(f"❌ ERREUR DE CONNEXION AU ROUTEUR: {e}")
    print()
    print("💡 VÉRIFICATIONS:")
    print("1. Le routeur est-il accessible à http://192.168.8.1/ ?")
    print("2. Les identifiants admin sont-ils corrects ?")
    print("3. Êtes-vous connecté au réseau du routeur (192.168.8.x) ?")
    print()
    print("⚠️  Si vous êtes en dehors du magasin (réseau 192.168.100.x),")
    print("    ce script ne fonctionnera pas. Il faut être sur le même réseau")
    print("    que le routeur Huawei.")

