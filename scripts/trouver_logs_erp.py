#!/usr/bin/env python3
"""
Script pour trouver où sont les logs de l'ERP
"""

import os
import subprocess

def trouver_logs_erp():
    """Trouve tous les emplacements possibles des logs"""
    
    print("=" * 80)
    print("RECHERCHE DES LOGS ERP")
    print("=" * 80)
    print()
    
    # Emplacements possibles
    emplacements = [
        '/var/log/erp/',
        '/var/log/gunicorn/',
        '/opt/erp/app/logs/',
        '/opt/erp/logs/',
        '/var/log/nginx/',
        '/tmp/',
        '/home/erp-admin/',
    ]
    
    print("📁 Recherche dans les emplacements standards...")
    print()
    
    fichiers_trouves = []
    
    for emplacement in emplacements:
        if os.path.exists(emplacement):
            print(f"✅ {emplacement} existe")
            try:
                fichiers = os.listdir(emplacement)
                for fichier in fichiers:
                    chemin_complet = os.path.join(emplacement, fichier)
                    if os.path.isfile(chemin_complet):
                        # Vérifier si c'est un fichier de log
                        if any(ext in fichier.lower() for ext in ['.log', 'log', 'error', 'access']):
                            taille = os.path.getsize(chemin_complet)
                            fichiers_trouves.append((chemin_complet, taille))
                            print(f"   📄 {fichier} ({taille:,} octets)")
            except PermissionError:
                print(f"   ⚠️  Permission refusée")
            except Exception as e:
                print(f"   ⚠️  Erreur : {e}")
        else:
            print(f"❌ {emplacement} n'existe pas")
    
    print()
    print("=" * 80)
    print("FICHIERS DE LOG TROUVÉS")
    print("=" * 80)
    print()
    
    if fichiers_trouves:
        for chemin, taille in fichiers_trouves:
            print(f"📄 {chemin}")
            print(f"   Taille : {taille:,} octets")
            # Afficher les 5 dernières lignes
            try:
                with open(chemin, 'r', encoding='utf-8', errors='ignore') as f:
                    lignes = f.readlines()
                    if lignes:
                        print(f"   Dernières lignes ({len(lignes)} lignes total) :")
                        for ligne in lignes[-3:]:
                            print(f"      {ligne.strip()[:150]}")
            except Exception as e:
                print(f"   ⚠️  Impossible de lire : {e}")
            print()
    else:
        print("❌ Aucun fichier de log trouvé")
    
    print("=" * 80)
    print("VÉRIFICATION SERVICE SYSTEMD")
    print("=" * 80)
    print()
    
    # Vérifier le service systemd
    try:
        result = subprocess.run(['systemctl', 'status', 'erp'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Service 'erp' trouvé")
            # Extraire les infos de log
            for ligne in result.stdout.split('\n'):
                if 'Main PID' in ligne or 'Active:' in ligne:
                    print(f"   {ligne.strip()}")
        else:
            print("⚠️  Service 'erp' non trouvé ou erreur")
    except Exception as e:
        print(f"⚠️  Impossible de vérifier le service : {e}")
    
    print()
    print("=" * 80)
    print("COMMANDES UTILES")
    print("=" * 80)
    print()
    print("Pour voir les logs journalctl :")
    print("   sudo journalctl -u erp -n 100")
    print()
    print("Pour exporter les logs :")
    print("   sudo journalctl -u erp --since '2025-12-09 00:00:00' --no-pager > /tmp/erp_logs_complet.txt")
    print()
    print("Pour voir les logs en temps réel :")
    print("   sudo journalctl -u erp -f")
    print()
    print("Pour vérifier la configuration du service :")
    print("   sudo systemctl cat erp")
    print()

if __name__ == '__main__':
    trouver_logs_erp()

