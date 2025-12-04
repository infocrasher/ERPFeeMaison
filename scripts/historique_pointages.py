#!/usr/bin/env python3
"""
Script pour analyser l'historique complet des pointages
Identifie quand la pointeuse a arrêté de fonctionner
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.employees.models import AttendanceRecord
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_attendance_history():
    """Analyse l'historique des pointages"""
    app = create_app()
    
    with app.app_context():
        print("=" * 120)
        print("HISTORIQUE COMPLET DES POINTAGES")
        print("=" * 120)
        print()
        
        # Récupérer tous les pointages
        all_records = AttendanceRecord.query.order_by(AttendanceRecord.timestamp.desc()).all()
        
        if not all_records:
            print("❌ Aucun pointage trouvé dans la base de données")
            return
        
        # Statistiques globales
        total = len(all_records)
        manual_count = sum(1 for r in all_records if 'manual' in (r.raw_data or '').lower())
        device_count = total - manual_count
        
        print(f"📊 STATISTIQUES GLOBALES")
        print("-" * 120)
        print(f"   Total pointages      : {total}")
        print(f"   Pointages pointeuse  : {device_count} ({device_count/total*100:.1f}%)")
        print(f"   Pointages manuels    : {manual_count} ({manual_count/total*100:.1f}%)")
        print()
        
        # Grouper par jour
        by_day = defaultdict(lambda: {'device': 0, 'manual': 0})
        
        for record in all_records:
            day = record.timestamp.date()
            if 'manual' in (record.raw_data or '').lower():
                by_day[day]['manual'] += 1
            else:
                by_day[day]['device'] += 1
        
        # Afficher l'historique jour par jour
        print(f"📅 HISTORIQUE PAR JOUR")
        print("-" * 120)
        print(f"   {'Date':<15} {'Pointeuse':<15} {'Manuel':<15} {'Total':<10} {'Source principale':<20}")
        print("   " + "-" * 115)
        
        sorted_days = sorted(by_day.keys(), reverse=True)
        
        for day in sorted_days[:30]:  # 30 derniers jours
            stats = by_day[day]
            total_day = stats['device'] + stats['manual']
            main_source = '🤖 Pointeuse' if stats['device'] > stats['manual'] else '✋ Manuel'
            
            print(f"   {day.strftime('%Y-%m-%d'):<15} {stats['device']:<15} {stats['manual']:<15} {total_day:<10} {main_source:<20}")
        
        if len(sorted_days) > 30:
            print(f"   ... et {len(sorted_days) - 30} jours plus anciens")
        
        print()
        
        # Identifier le dernier pointage de la pointeuse
        print(f"🔍 DERNIER POINTAGE DE LA POINTEUSE")
        print("-" * 120)
        
        last_device_record = None
        for record in all_records:
            if 'manual' not in (record.raw_data or '').lower():
                last_device_record = record
                break
        
        if last_device_record:
            employee_name = last_device_record.employee.name if last_device_record.employee else 'Inconnu'
            punch_type = 'Entrée' if last_device_record.punch_type == 'in' else 'Sortie'
            
            print(f"   Date/Heure  : {last_device_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Employé     : {employee_name}")
            print(f"   Type        : {punch_type}")
            print(f"   Raw Data    : {last_device_record.raw_data}")
            
            days_ago = (datetime.now() - last_device_record.timestamp).days
            print(f"   Il y a      : {days_ago} jour(s)")
        else:
            print("   ⚠️  Aucun pointage de la pointeuse trouvé (tous manuels)")
        
        print()
        
        # Détails des 30 derniers pointages
        print(f"📋 DÉTAILS DES 30 DERNIERS POINTAGES")
        print("-" * 120)
        print(f"   {'Date/Heure':<20} {'Employé':<25} {'Type':<10} {'Source':<15} {'Raw Data':<40}")
        print("   " + "-" * 115)
        
        for record in all_records[:30]:
            employee_name = record.employee.name if record.employee else 'Inconnu'
            punch_type = 'Entrée' if record.punch_type == 'in' else 'Sortie'
            source = '✋ Manuel' if 'manual' in (record.raw_data or '').lower() else '🤖 Pointeuse'
            raw_data = (record.raw_data or 'N/A')[:38]
            
            print(f"   {record.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} {employee_name[:23]:<25} {punch_type:<10} {source:<15} {raw_data:<40}")
        
        print()
        print("=" * 120)

if __name__ == '__main__':
    analyze_attendance_history()

