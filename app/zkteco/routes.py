from flask import request, jsonify, current_app
from app.zkteco import zkteco
from datetime import datetime
from sqlalchemy import text
from extensions import db
from app.employees.models import Employee, AttendanceRecord
import json

@zkteco.route('/')
def root():
    """Endpoint racine pour la pointeuse - redirige vers attendance"""
    return attendance()

@zkteco.route('/api/ping')
def ping():
    """Test de connectivité pour la pointeuse"""
    try:
        current_app.logger.info("Test de connectivité ZKTeco reçu")
        
        return jsonify({
            'message': 'Serveur ERP accessible',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'server': 'Fee Maison ERP'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur ping ZKTeco: {str(e)}")
        return jsonify({
            'message': 'Erreur serveur',
            'status': 'error'
        }), 500

@zkteco.route('/api/attendance', methods=['GET', 'POST'])
def attendance():
    """Endpoint pour recevoir les données de pointage"""
    try:
        method = request.method
        data = request.get_data()
        
        current_app.logger.info(f"Méthode: {method}, Données reçues: {data}")
        
        if method == 'GET':
            # Réponse pour les tests de connectivité
            return jsonify({
                'message': 'Endpoint attendance accessible',
                'methods_supported': ['GET', 'POST'],
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        elif method == 'POST':
            # Traitement des données de pointage
            try:
                # Essayer de parser les données JSON
                if data:
                    try:
                        json_data = json.loads(data.decode('utf-8'))
                        current_app.logger.info(f"Données JSON parsées: {json_data}")
                        
                        # Traiter les données de pointage
                        result = process_attendance_data(json_data)
                        
                        return jsonify({
                            'message': 'Pointage enregistré avec succès',
                            'status': 'success',
                            'processed': result,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                    except json.JSONDecodeError:
                        # Si ce n'est pas du JSON, traiter comme données brutes
                        current_app.logger.info(f"Données brutes reçues: {data}")
                        
                        return jsonify({
                            'message': 'Données reçues (format non-JSON)',
                            'status': 'success',
                            'data_length': len(data),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                else:
                    # Aucune donnée reçue
                    return jsonify({
                        'message': 'Aucune donnée reçue',
                        'status': 'warning',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                current_app.logger.error(f"Erreur traitement POST: {str(e)}")
                return jsonify({
                    'message': 'Erreur lors du traitement des données',
                    'status': 'error',
                    'error': str(e)
                }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erreur endpoint attendance: {str(e)}")
        return jsonify({
            'message': 'Erreur serveur',
            'status': 'error'
        }), 500

def process_attendance_data(data):
    """Traite et sauvegarde les données de pointage"""
    try:
        # Format attendu des données ZKTeco
        # Exemple: {"user_id": 1, "timestamp": "2025-01-01 08:00:00", "punch_type": "in"}
        
        user_id = data.get('user_id') or data.get('zk_user_id')
        timestamp_str = data.get('timestamp') or data.get('time')
        punch_type = data.get('punch_type', 'in')  # 'in' ou 'out'
        
        if not user_id or not timestamp_str:
            raise ValueError("Données manquantes: user_id et timestamp requis")
        
        # Convertir le timestamp
        if isinstance(timestamp_str, str):
            # Essayer différents formats de date
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y %H:%M:%S']:
                try:
                    timestamp = datetime.strptime(timestamp_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Si aucun format ne fonctionne, utiliser l'heure actuelle
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
        
        # Trouver l'employé par zk_user_id ou par id
        employee = Employee.query.filter_by(zk_user_id=user_id, is_active=True).first()
        
        # Si pas trouvé par zk_user_id, essayer par id
        if not employee:
            employee = Employee.query.filter_by(id=user_id, is_active=True).first()
        
        if not employee:
            current_app.logger.warning(f"Employé non trouvé pour user_id: {user_id}")
            return {
                'success': False,
                'message': f'Employé non trouvé pour ID: {user_id}'
            }
        
        # Créer l'enregistrement de pointage
        attendance_record = AttendanceRecord(
            employee_id=employee.id,
            timestamp=timestamp,
            punch_type=punch_type,
            raw_data=json.dumps(data)
        )
        
        db.session.add(attendance_record)
        db.session.commit()
        
        current_app.logger.info(f"Pointage enregistré pour {employee.name}: {punch_type} à {timestamp}")
        
        return {
            'success': True,
            'employee_name': employee.name,
            'timestamp': timestamp.isoformat(),
            'punch_type': punch_type
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'enregistrement du pointage: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

@zkteco.route('/api/employees')
def employees():
    """Endpoint pour récupérer la liste des employés"""
    try:
        from extensions import db
        
        # Requête SQL directe pour éviter les problèmes d'import
        result = db.session.execute(
            text("SELECT id, name, zk_user_id, role FROM employees WHERE is_active = true")
        )
        employees_data = []
        for row in result:
            employees_data.append({
                'id': row[0],
                'name': row[1],
                'employee_number': row[2] or row[0],  # zk_user_id ou id
                'department': row[3] or 'Production'
            })
        
        current_app.logger.info(f"Liste d'employés fournie: {len(employees_data)} employés")
        
        return jsonify({
            'message': 'Liste des employés',
            'status': 'success',
            'count': len(employees_data),
            'employees': employees_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des employés: {str(e)}")
        return jsonify({
            'message': 'Erreur serveur',
            'status': 'error'
        }), 500

# Endpoint pour tester l'insertion manuelle de pointages
@zkteco.route('/api/test-attendance', methods=['GET', 'POST'])
def test_attendance():
    """Endpoint de test pour simuler un pointage"""
    try:
        if request.method == 'GET':
            # Réponse pour les tests de connectivité
            return jsonify({
                'message': 'Endpoint test-attendance accessible',
                'methods_supported': ['GET', 'POST'],
                'status': 'success',
                'usage': {
                    'POST': 'Envoyer des données JSON avec user_id, timestamp, punch_type',
                    'example': {
                        'user_id': 1,
                        'timestamp': '2025-01-01 08:00:00',
                        'punch_type': 'in'
                    }
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'message': 'Données JSON requises',
                    'status': 'error'
                }), 400
            
            result = process_attendance_data(data)
            
            return jsonify({
                'message': 'Test de pointage effectué',
                'status': 'success',
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        current_app.logger.error(f"Erreur test pointage: {str(e)}")
        return jsonify({
            'message': 'Erreur lors du test',
            'status': 'error',
            'error': str(e)
        }), 500 