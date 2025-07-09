from flask import request, jsonify, current_app
from app.zkteco import zkteco
from datetime import datetime
from sqlalchemy import text
import json

@zkteco.route('/api/attendance', methods=['GET', 'POST'])
def receive_attendance():
    """
    Endpoint pour recevoir les données de pointage de la ZKTeco WL30
    """
    try:
        # Log de la requête reçue
        current_app.logger.info(f"Méthode: {request.method}, Données reçues: {request.get_data()}")
        
        # Si c'est une requête GET (test de connectivité)
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'message': 'Endpoint attendance accessible',
                'methods_supported': ['GET', 'POST'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Récupération des données JSON ou form-data pour POST
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Traitement des données de pointage
        if data:
            employee_id = data.get('user_id') or data.get('employee_id')
            timestamp = data.get('timestamp') or data.get('time')
            punch_type = data.get('punch_type', 'IN')  # IN/OUT
            
            # Import dynamique pour éviter les imports circulaires
            from app.models import Employee, db
            from app.employees.models import WorkHours
            
            # Recherche de l'employé
            employee = Employee.query.filter_by(id=employee_id).first()
            
            if employee:
                # Création d'un enregistrement de pointage
                work_hour = WorkHours(
                    employee_id=employee.id,
                    date=datetime.now().date(),
                    clock_in=datetime.fromisoformat(timestamp) if punch_type == 'IN' else None,
                    clock_out=datetime.fromisoformat(timestamp) if punch_type == 'OUT' else None,
                    created_at=datetime.now()
                )
                
                db.session.add(work_hour)
                db.session.commit()
                
                current_app.logger.info(f"Pointage enregistré pour {employee.first_name} {employee.last_name}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Pointage enregistré avec succès',
                    'employee': f"{employee.first_name} {employee.last_name}",
                    'timestamp': timestamp
                }), 200
            else:
                current_app.logger.warning(f"Employé non trouvé: ID {employee_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'Employé non trouvé'
                }), 404
        else:
            return jsonify({
                'status': 'error',
                'message': 'Aucune donnée reçue'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors du traitement du pointage: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Erreur serveur'
        }), 500

@zkteco.route('/api/ping', methods=['GET', 'POST'])
def ping():
    """
    Endpoint de test pour vérifier la connectivité avec la pointeuse
    """
    return jsonify({
        'status': 'success',
        'message': 'Serveur ERP accessible',
        'timestamp': datetime.now().isoformat()
    }), 200

@zkteco.route('/api/employees', methods=['GET'])
def get_employees():
    """
    Endpoint pour synchroniser la liste des employés avec la pointeuse
    """
    try:
        # Import dynamique pour éviter les imports circulaires
        from app import db
        
        # Requête SQL directe pour éviter les problèmes d'import
        result = db.session.execute(
            text("SELECT id, name, zk_user_id, role FROM employees WHERE is_active = true")
        )
        employees_data = []
        for row in result:
            employees_data.append({
                'id': row[0],
                'name': row[1],
                'employee_number': row[2] or row[0],  # zk_user_id ou id par défaut
                'department': row[3] or 'Production'
            })
        
        return jsonify({
            'status': 'success',
            'employees': employees_data,
            'count': len(employees_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des employés: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Erreur serveur'
        }), 500 