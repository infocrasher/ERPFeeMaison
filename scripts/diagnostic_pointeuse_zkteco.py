#!/usr/bin/env python3
"""
Script de diagnostic pour la pointeuse ZKTeco
Vérifie la connectivité, la configuration et les derniers pointages
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.employees.models import AttendanceRecord, Employee
from extensions import db
from datetime import datetime, timedelta
import requests

def diagnostic_pointeuse():
    """Diagnostic complet de la pointeuse ZKTeco"""
    app = create_app()
    
    with app.app_context():
        print("=" * 100)
        print("DIAGNOSTIC POINTEUSE ZKTECO")
        print("=" * 100)
        print()
        
        # 1. Vérifier la configuration
        print("1️⃣  CONFIGURATION")
        print("-" * 100)
        
        zkteco_ip = app.config.get('ZKTECO_IP', 'Non configuré')
        zkteco_port = app.config.get('ZKTECO_PORT', 'Non configuré')
        
        print(f"   IP Pointeuse    : {zkteco_ip}")
        print(f"   Port           : {zkteco_port}")
        print()
        
        # 2. Vérifier les routes API
        print("2️⃣  ROUTES API DISPONIBLES")
        print("-" * 100)
        
        with app.test_request_context():
            from flask import url_for
            
            routes = [
                ('zkteco.attendance', 'Endpoint principal pour recevoir les pointages'),
                ('zkteco.ping', 'Test de connectivité'),
                ('zkteco.employees', 'Liste des employés'),
                ('zkteco.test_attendance', 'Test de pointage'),
            ]
            
            for route_name, description in routes:
                try:
                    url = url_for(route_name, _external=False)
                    print(f"   ✅ {route_name:<30} → {url:<40} ({description})")
                except Exception as e:
                    print(f"   ❌ {route_name:<30} → Erreur: {str(e)}")
        print()
        
        # 3. Statistiques des pointages
        print("3️⃣  STATISTIQUES DES POINTAGES")
        print("-" * 100)
        
        total_records = AttendanceRecord.query.count()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = AttendanceRecord.query.filter(AttendanceRecord.timestamp >= today).count()
        
        last_7_days = datetime.now() - timedelta(days=7)
        week_records = AttendanceRecord.query.filter(AttendanceRecord.timestamp >= last_7_days).count()
        
        print(f"   Total pointages (historique)  : {total_records}")
        print(f"   Pointages aujourd'hui          : {today_records}")
        print(f"   Pointages derniers 7 jours     : {week_records}")
        print()
        
        # 4. Derniers pointages
        print("4️⃣  10 DERNIERS POINTAGES")
        print("-" * 100)
        
        last_records = AttendanceRecord.query.order_by(AttendanceRecord.timestamp.desc()).limit(10).all()
        
        if last_records:
            print(f"   {'Date/Heure':<20} {'Employé':<30} {'Type':<10} {'Source':<15}")
            print("   " + "-" * 95)
            
            for record in last_records:
                employee_name = record.employee.name if record.employee else 'Inconnu'
                punch_type = 'Entrée' if record.punch_type == 'in' else 'Sortie'
                source = 'Manuel' if 'manual' in (record.raw_data or '') else 'Pointeuse'
                timestamp_str = record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"   {timestamp_str:<20} {employee_name[:28]:<30} {punch_type:<10} {source:<15}")
        else:
            print("   ⚠️  Aucun pointage enregistré")
        
        print()
        
        # 5. Employés configurés
        print("5️⃣  EMPLOYÉS CONFIGURÉS")
        print("-" * 100)
        
        active_employees = Employee.query.filter(Employee.is_active == True).all()
        inactive_employees = Employee.query.filter(Employee.is_active == False).count()
        
        print(f"   Employés actifs   : {len(active_employees)}")
        print(f"   Employés inactifs : {inactive_employees}")
        
        if active_employees:
            print()
            print(f"   {'ID':<6} {'Nom':<30} {'Rôle':<20} {'Device User ID':<15}")
            print("   " + "-" * 95)
            
            for emp in active_employees[:10]:  # Afficher les 10 premiers
                device_user_id = getattr(emp, 'device_user_id', 'N/A')
                print(f"   {emp.id:<6} {emp.name[:28]:<30} {emp.get_role_display()[:18]:<20} {device_user_id:<15}")
            
            if len(active_employees) > 10:
                print(f"   ... et {len(active_employees) - 10} autres employés")
        
        print()
        
        # 6. Test de connectivité (si configuration présente)
        print("6️⃣  TEST DE CONNECTIVITÉ")
        print("-" * 100)
        
        if zkteco_ip != 'Non configuré':
            try:
                # Tenter une connexion à la pointeuse
                url = f"http://{zkteco_ip}"
                print(f"   Test de connexion à {url}...")
                
                response = requests.get(url, timeout=5)
                print(f"   ✅ Connexion réussie (Status: {response.status_code})")
            except requests.exceptions.Timeout:
                print(f"   ⚠️  Timeout - La pointeuse ne répond pas")
            except requests.exceptions.ConnectionError:
                print(f"   ❌ Erreur de connexion - Vérifier l'IP et le réseau")
            except Exception as e:
                print(f"   ❌ Erreur: {str(e)}")
        else:
            print("   ⚠️  Configuration manquante - Impossible de tester")
        
        print()
        
        # 7. Recommandations
        print("7️⃣  RECOMMANDATIONS")
        print("-" * 100)
        
        recommendations = []
        
        if zkteco_ip == 'Non configuré':
            recommendations.append("⚠️  Configurer ZKTECO_IP dans config.py")
        
        if total_records == 0:
            recommendations.append("⚠️  Aucun pointage enregistré - Vérifier la connexion pointeuse → ERP")
        
        if today_records == 0:
            recommendations.append("⚠️  Aucun pointage aujourd'hui - Vérifier que la pointeuse envoie bien les données")
        
        if len(active_employees) == 0:
            recommendations.append("⚠️  Aucun employé actif - Créer des employés dans le système")
        
        if not recommendations:
            print("   ✅ Tout semble fonctionner correctement !")
        else:
            for rec in recommendations:
                print(f"   {rec}")
        
        print()
        print("=" * 100)
        print()
        print("💡 INSTRUCTIONS POUR CONFIGURER LA POINTEUSE:")
        print()
        print("1. Dans config.py, ajouter:")
        print("   ZKTECO_IP = '192.168.1.XXX'  # IP de votre pointeuse")
        print("   ZKTECO_PORT = 4370")
        print()
        print("2. Configurer la pointeuse pour envoyer les pointages à:")
        print(f"   http://VOTRE_SERVEUR_IP:5000/zkteco/api/attendance")
        print()
        print("3. Tester avec:")
        print("   curl -X POST http://localhost:5000/zkteco/api/test-attendance \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"user_id\": 1, \"timestamp\": \"2025-01-01 08:00:00\", \"punch_type\": \"in\"}'")
        print()
        print("=" * 100)

if __name__ == '__main__':
    diagnostic_pointeuse()

