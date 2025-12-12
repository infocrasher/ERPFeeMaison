#!/usr/bin/env python3
"""
Script pour vérifier le calcul des heures travaillées
Compare le calcul actuel (Premier IN + Dernier OUT) avec un calcul correct (somme des périodes)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.employees.models import AttendanceRecord, Employee
from datetime import datetime, date, timedelta
from sqlalchemy import func

def normalize_punch_type(pt):
    """Normalise le type de pointage"""
    if pt in ('in', 0, '0'):
        return 'in'
    elif pt in ('out', 1, '1'):
        return 'out'
    return pt

def calcul_heures_correct(records):
    """
    Calcule les heures travaillées de manière correcte
    en sommant toutes les périodes IN->OUT
    """
    in_times = []
    out_times = []
    
    for record in records:
        punch = normalize_punch_type(record.punch_type)
        if punch == 'in':
            in_times.append(record.timestamp)
        elif punch == 'out':
            out_times.append(record.timestamp)
    
    if not in_times or not out_times:
        return 0.0
    
    # Trier les pointages
    in_times.sort()
    out_times.sort()
    
    total_seconds = 0
    
    # Parcourir les périodes IN->OUT
    i = 0  # Index pour les entrées
    j = 0  # Index pour les sorties
    
    while i < len(in_times) and j < len(out_times):
        entry = in_times[i]
        exit_time = out_times[j]
        
        # Si la sortie est après l'entrée, c'est une période valide
        if exit_time > entry:
            duration = (exit_time - entry).total_seconds()
            total_seconds += duration
            i += 1
            j += 1
        # Sinon, on avance l'index de sortie
        elif exit_time <= entry:
            j += 1
        else:
            i += 1
    
    return total_seconds / 3600

def calcul_heures_actuel(records):
    """
    Calcule les heures avec la méthode actuelle (Premier IN + Dernier OUT)
    """
    in_times = []
    out_times = []
    
    for record in records:
        punch = normalize_punch_type(record.punch_type)
        if punch == 'in':
            in_times.append(record.timestamp)
        elif punch == 'out':
            out_times.append(record.timestamp)
    
    if not in_times or not out_times:
        return 0.0
    
    first_in = min(in_times)
    last_out = max(out_times)
    
    if last_out > first_in:
        duration = (last_out - first_in).total_seconds() / 3600
        return duration
    
    return 0.0

def verifier_calcul_heures(target_date_str=None):
    """Vérifie le calcul des heures pour une date donnée"""
    app = create_app()
    
    with app.app_context():
        # Demander la date si non fournie
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                print(f"❌ Format de date invalide: {target_date_str}")
                print("   Format attendu: YYYY-MM-DD (ex: 2025-12-11)")
                return
        else:
            target_date = date.today()
            print(f"📅 Utilisation de la date d'aujourd'hui: {target_date.strftime('%d/%m/%Y')}")
        
        print("=" * 100)
        print(f"🔍 VÉRIFICATION DU CALCUL DES HEURES - {target_date.strftime('%d/%m/%Y')}")
        print("=" * 100)
        print()
        
        # Récupérer tous les pointages du jour
        records = AttendanceRecord.query.filter(
            func.date(AttendanceRecord.timestamp) == target_date
        ).order_by(AttendanceRecord.timestamp).all()
        
        if not records:
            print(f"⚠️  Aucun pointage trouvé pour le {target_date.strftime('%d/%m/%Y')}")
            return
        
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
        
        # Comparer les calculs
        print(f"{'Employé':<30} {'Entrée':<12} {'Sortie':<12} {'Actuel':<12} {'Correct':<12} {'Diff':<12} {'Pointages'}")
        print("-" * 100)
        
        problemes = []
        
        for emp_id in sorted(by_employee.keys()):
            data = by_employee[emp_id]
            employee_name = data['name']
            records = sorted(data['records'], key=lambda r: r.timestamp)
            
            # Calculs
            heures_actuel = calcul_heures_actuel(records)
            heures_correct = calcul_heures_correct(records)
            difference = abs(heures_actuel - heures_correct)
            
            # Trouver premier IN et dernier OUT pour affichage
            in_times = [r.timestamp for r in records if normalize_punch_type(r.punch_type) == 'in']
            out_times = [r.timestamp for r in records if normalize_punch_type(r.punch_type) == 'out']
            
            entry_str = in_times[0].strftime('%H:%M') if in_times else '-'
            exit_str = out_times[-1].strftime('%H:%M') if out_times else '-'
            
            # Formater les heures
            def format_hours(h):
                hours = int(h)
                minutes = int((h % 1) * 60)
                return f"{hours}h{minutes:02d}m"
            
            # Détecter les problèmes
            if difference > 0.01:  # Plus de 1 minute de différence
                problemes.append({
                    'name': employee_name,
                    'actuel': heures_actuel,
                    'correct': heures_correct,
                    'diff': difference,
                    'records': records
                })
            
            # Afficher tous les pointages pour les cas problématiques
            pointages_str = f"{len(records)}"
            if len(records) > 2:
                pointages_str += " ⚠️"
            
            print(f"{employee_name[:28]:<30} {entry_str:<12} {exit_str:<12} "
                  f"{format_hours(heures_actuel):<12} {format_hours(heures_correct):<12} "
                  f"{format_hours(difference):<12} {pointages_str}")
        
        print()
        print("=" * 100)
        
        if problemes:
            print(f"⚠️  {len(problemes)} EMPLOYÉ(S) AVEC CALCUL INCORRECT")
            print("=" * 100)
            print()
            
            for pb in problemes:
                print(f"📋 {pb['name']}")
                print(f"   Calcul actuel (Premier IN + Dernier OUT) : {format_hours(pb['actuel'])}")
                print(f"   Calcul correct (Somme des périodes)      : {format_hours(pb['correct'])}")
                print(f"   Différence                                : {format_hours(pb['diff'])}")
                print()
                print("   Pointages détaillés :")
                for record in pb['records']:
                    punch_type = normalize_punch_type(record.punch_type)
                    type_str = "ENTRÉE" if punch_type == 'in' else "SORTIE"
                    print(f"      {record.timestamp.strftime('%H:%M:%S')} - {type_str}")
                print()
        else:
            print("✅ Tous les calculs sont corrects !")
            print()
        
        print("=" * 100)
        print("💡 RECOMMANDATION")
        print("=" * 100)
        print("Si des différences sont détectées, il faut modifier la méthode")
        print("get_daily_summary() dans app/employees/models.py pour utiliser")
        print("la somme des périodes IN->OUT au lieu de Premier IN + Dernier OUT.")
        print()

if __name__ == '__main__':
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    verifier_calcul_heures(target_date)

