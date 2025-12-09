#!/usr/bin/env python3
"""
Script d'analyse des logs pour identifier les erreurs de finalisation de vente PDV
Analyse les logs à des heures précises pour trouver la cause des erreurs
"""

import sys
import os
import re
from datetime import datetime, timedelta

def analyse_logs_vente_pdv(date_str=None, heures=None):
    """
    Analyse les logs pour trouver les erreurs de finalisation de vente
    
    Args:
        date_str: Date au format YYYY-MM-DD (si None, utilise aujourd'hui)
        heures: Liste des heures à analyser (ex: ['21:46', '13:00'])
    """
    
    # Déterminer la date
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        target_date = datetime.now()
    
    # Heures par défaut si non spécifiées
    if not heures:
        heures = ['21:46', '13:00']
    
    print("=" * 80)
    print("ANALYSE DES LOGS - ERREURS FINALISATION VENTE PDV")
    print("=" * 80)
    print()
    print(f"Date cible : {target_date.strftime('%Y-%m-%d')}")
    print(f"Heures à analyser : {', '.join(heures)}")
    print()
    
    # Chemins possibles des logs
    log_paths = [
        '/var/log/erp/app.log',
        '/opt/erp/app/logs/app.log',
        '/var/log/gunicorn/erp.log',
        '/var/log/nginx/error.log',
        'logs/app.log',
        'app.log'
    ]
    
    # Chercher le fichier de log
    log_file = None
    for path in log_paths:
        if os.path.exists(path):
            log_file = path
            break
    
    if not log_file:
        print("❌ Aucun fichier de log trouvé dans les emplacements standards")
        print()
        print("Emplacements vérifiés :")
        for path in log_paths:
            print(f"   - {path}")
        print()
        print("💡 Pour trouver les logs :")
        print("   sudo journalctl -u erp > /tmp/erp_logs.txt")
        print("   python3 scripts/analyse_logs_vente_pdv.py --file /tmp/erp_logs.txt")
        return
    
    print(f"📄 Fichier de log trouvé : {log_file}")
    print()
    
    # Lire les logs
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier : {e}")
        return
    
    print(f"📊 Total de lignes dans le log : {len(lines)}")
    print()
    
    # Analyser chaque heure
    for heure_str in heures:
        print("=" * 80)
        print(f"ANALYSE POUR {heure_str}")
        print("=" * 80)
        print()
        
        # Parser l'heure
        try:
            heure_parts = heure_str.split(':')
            target_hour = int(heure_parts[0])
            target_minute = int(heure_parts[1]) if len(heure_parts) > 1 else 0
        except:
            print(f"⚠️  Format d'heure invalide : {heure_str}")
            continue
        
        # Fenêtre de temps à analyser (±5 minutes)
        window_start = target_date.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) - timedelta(minutes=5)
        window_end = target_date.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) + timedelta(minutes=5)
        
        print(f"Fenêtre d'analyse : {window_start.strftime('%Y-%m-%d %H:%M:%S')} → {window_end.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Chercher les erreurs dans cette fenêtre
        errors_found = []
        warnings_found = []
        complete_sale_logs = []
        
        for i, line in enumerate(lines):
            # Essayer de parser la date/heure de la ligne
            # Formats possibles : 2025-12-09 21:46:12,123 ou [2025-12-09 21:46:12]
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})', line)
            if date_match:
                try:
                    log_date = datetime.strptime(f"{date_match.group(1)} {date_match.group(2)}:{date_match.group(3)}:{date_match.group(4)}", '%Y-%m-%d %H:%M:%S')
                    
                    # Vérifier si dans la fenêtre
                    if window_start <= log_date <= window_end:
                        # Chercher les erreurs de finalisation
                        if 'finalisation de la vente' in line.lower() or 'complete-sale' in line.lower():
                            complete_sale_logs.append((i+1, log_date, line))
                        
                        # Chercher les erreurs
                        if 'error' in line.lower() or 'erreur' in line.lower() or 'exception' in line.lower():
                            errors_found.append((i+1, log_date, line))
                        
                        # Chercher les warnings
                        if 'warning' in line.lower() or 'avertissement' in line.lower():
                            warnings_found.append((i+1, log_date, line))
                except:
                    pass
        
        # Afficher les résultats
        print(f"📋 Logs de finalisation de vente trouvés : {len(complete_sale_logs)}")
        if complete_sale_logs:
            print()
            for line_num, log_date, line in complete_sale_logs:
                print(f"   Ligne {line_num} [{log_date.strftime('%H:%M:%S')}]: {line.strip()[:200]}")
            print()
        
        print(f"⚠️  Warnings trouvés : {len(warnings_found)}")
        if warnings_found:
            print()
            for line_num, log_date, line in warnings_found[:10]:  # Limiter à 10
                print(f"   Ligne {line_num} [{log_date.strftime('%H:%M:%S')}]: {line.strip()[:200]}")
            print()
        
        print(f"❌ Erreurs trouvées : {len(errors_found)}")
        if errors_found:
            print()
            for line_num, log_date, line in errors_found[:20]:  # Limiter à 20
                print(f"   Ligne {line_num} [{log_date.strftime('%H:%M:%S')}]: {line.strip()[:200]}")
            
            # Chercher les tracebacks complets
            print()
            print("🔍 Recherche des tracebacks complets...")
            print()
            
            for line_num, log_date, line in errors_found:
                # Si c'est une ligne d'erreur, chercher le traceback suivant
                if 'traceback' in line.lower() or 'file "' in line.lower():
                    # Afficher les lignes suivantes (traceback)
                    traceback_lines = []
                    for j in range(line_num, min(line_num + 30, len(lines))):
                        traceback_lines.append(lines[j])
                        if 'error' in lines[j].lower() and j > line_num:
                            break
                    
                    print(f"   Traceback (ligne {line_num}):")
                    for tb_line in traceback_lines[:15]:
                        print(f"      {tb_line.rstrip()}")
                    print()
        else:
            print("   Aucune erreur trouvée dans cette fenêtre")
        
        print()
    
    # Résumé final
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print()
    print("💡 Pour voir les logs en temps réel :")
    print("   sudo journalctl -u erp -f")
    print()
    print("💡 Pour exporter les logs :")
    print("   sudo journalctl -u erp --since '2025-12-09 00:00:00' > /tmp/erp_logs.txt")
    print()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyser les logs pour les erreurs de vente PDV')
    parser.add_argument('--date', type=str, help='Date au format YYYY-MM-DD (défaut: aujourd\'hui)')
    parser.add_argument('--heures', type=str, nargs='+', help='Heures à analyser (ex: 21:46 13:00)')
    parser.add_argument('--file', type=str, help='Chemin vers le fichier de log')
    
    args = parser.parse_args()
    
    if args.file:
        # Utiliser le fichier spécifié
        log_paths = [args.file]
    
    if args.heures:
        heures = args.heures
    else:
        heures = ['21:46', '13:00']
    
    analyse_logs_vente_pdv(date_str=args.date, heures=heures)

