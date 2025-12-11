#!/usr/bin/env python3
"""
Script pour afficher tous les pointages de la journée
Le script demande la date de manière interactive
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.employees.models import AttendanceRecord, Employee
from datetime import datetime, date
from sqlalchemy import func

def afficher_pointages_jour():
    """Affiche tous les pointages d'une date donnée (demandée interactivement)"""
    app = create_app()
    
    with app.app_context():
        # Demander la date de manière interactive
        print("=" * 100)
        print("📅 AFFICHAGE DES POINTAGES")
        print("=" * 100)
        print()
        
        # Proposer aujourd'hui par défaut
        today = date.today()
        print(f"Date à consulter (format: YYYY-MM-DD)")
        print(f"Appuyez sur Entrée pour utiliser aujourd'hui ({today.strftime('%Y-%m-%d')})")
        print(f"Ou entrez une date (ex: 2025-12-10): ", end='')
        
        try:
            date_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Annulé par l'utilisateur")
            return
        
        # Déterminer la date cible
        if not date_input:
            target_date = today
            print(f"✅ Utilisation de la date d'aujourd'hui: {target_date.strftime('%d/%m/%Y')}")
        else:
            try:
                target_date = datetime.strptime(date_input, '%Y-%m-%d').date()
            except ValueError:
                # Essayer aussi le format DD/MM/YYYY
                try:
                    target_date = datetime.strptime(date_input, '%d/%m/%Y').date()
                except ValueError:
                    print(f"❌ Format de date invalide: {date_input}")
                    print("   Formats acceptés: YYYY-MM-DD (ex: 2025-12-10) ou DD/MM/YYYY (ex: 10/12/2025)")
                    return
        
        print("=" * 100)
        print(f"📅 POINTAGES DU {target_date.strftime('%d/%m/%Y')}")
        print("=" * 100)
        print()
        
        # Récupérer les pointages du jour
        records = AttendanceRecord.query.filter(
            func.date(AttendanceRecord.timestamp) == target_date
        ).order_by(AttendanceRecord.timestamp.asc()).all()
        
        if not records:
            print(f"⚠️  Aucun pointage trouvé pour le {target_date.strftime('%d/%m/%Y')}")
            print()
            return
        
        # Statistiques
        total = len(records)
        manual_count = sum(1 for r in records if 'manual' in (r.raw_data or '').lower())
        device_count = total - manual_count
        
        print(f"📊 STATISTIQUES")
        print("-" * 100)
        print(f"   Total pointages      : {total}")
        print(f"   Pointages pointeuse  : {device_count} ({device_count/total*100:.1f}%)")
        print(f"   Pointages manuels    : {manual_count} ({manual_count/total*100:.1f}%)")
        print()
        
        # Grouper par employé
        by_employee = {}
        for record in records:
            emp_id = record.employee_id
            if emp_id not in by_employee:
                employee = record.employee
                by_employee[emp_id] = {
                    'name': employee.name if employee else f'ID {emp_id}',
                    'records': []
                }
            by_employee[emp_id]['records'].append(record)
        
        # Afficher par employé avec nom et heure
        print(f"👥 POINTAGES PAR EMPLOYÉ")
        print("-" * 100)
        print(f"   {'Employé':<30} {'Heure':<12} {'Type':<10}")
        print("   " + "-" * 50)
        
        for emp_id in sorted(by_employee.keys()):
            data = by_employee[emp_id]
            employee_name = data['name']
            
            # Trier les pointages par heure
            sorted_records = sorted(data['records'], key=lambda r: r.timestamp)
            
            for i, record in enumerate(sorted_records):
                timestamp_str = record.timestamp.strftime('%H:%M:%S')
                punch_type = 'Entrée' if record.punch_type == 'in' else 'Sortie'
                
                # Afficher le nom de l'employé seulement pour le premier pointage
                if i == 0:
                    print(f"   {employee_name[:28]:<30} {timestamp_str:<12} {punch_type:<10}")
                else:
                    print(f"   {'':<30} {timestamp_str:<12} {punch_type:<10}")
            
            # Calculer les heures travaillées si possible
            if len(sorted_records) >= 2:
                # Essayer de calculer les heures (entrée/sortie)
                entries = [r for r in sorted_records if r.punch_type == 'in']
                exits = [r for r in sorted_records if r.punch_type == 'out']
                
                if entries and exits:
                    # Prendre la première entrée et la dernière sortie
                    first_entry = entries[0].timestamp
                    last_exit = exits[-1].timestamp
                    duration = last_exit - first_entry
                    hours = duration.total_seconds() / 3600
                    print(f"   {'':<30} {'':<12} ⏱️  Durée: {hours:.2f}h")
            
            print()
        
        # Résumé chronologique simple (nom et heure)
        print(f"⏰ CHRONOLOGIE COMPLÈTE")
        print("-" * 100)
        print(f"   {'Heure':<12} {'Employé':<30} {'Type':<10}")
        print("   " + "-" * 50)
        
        for record in records:
            employee_name = record.employee.name if record.employee else f'ID {record.employee_id}'
            timestamp_str = record.timestamp.strftime('%H:%M:%S')
            punch_type = 'Entrée' if record.punch_type == 'in' else 'Sortie'
            
            print(f"   {timestamp_str:<12} {employee_name[:28]:<30} {punch_type:<10}")
        
        print()
        print("=" * 100)

if __name__ == '__main__':
    afficher_pointages_jour()

