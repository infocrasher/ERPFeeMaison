"""
Routes Flask pour le module AI
===============================

Ce module expose les endpoints Flask pour l'analyse AI.

Endpoints :
- POST /ai/train : Entraîne les modèles Prophet
- GET /ai/predict : Génère des prédictions
- GET /ai/analyze : Analyse un rapport via LLM
- GET /ai/status : Statut du module AI

Usage :
    from app.ai import ai
    app.register_blueprint(ai)
"""

import logging
from datetime import date, datetime, timedelta
from flask import jsonify, request

from app.ai import ai
from app.ai.ai_manager import AIManager
from app.ai.model_trainer import train_model, train_all_reports

# Configuration du logger
logger = logging.getLogger(__name__)


@ai.route('/status', methods=['GET'])
def status():
    """
    Retourne le statut du module AI
    
    GET /ai/status
    
    Réponse :
    {
        "status": "ok",
        "prophet": {...},
        "llm": {...},
        "context_builder": {...}
    }
    """
    try:
        ai_manager = AIManager()
        status_info = ai_manager.get_status()
        
        return jsonify({
            'status': 'ok',
            **status_info
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@ai.route('/train', methods=['POST'])
def train():
    """
    Entraîne les modèles Prophet
    
    POST /ai/train
    
    Body (JSON):
    {
        "report_name": "daily_sales",  # optionnel, si omis entraîne tous
        "days_history": 90              # optionnel, défaut 90
    }
    
    Réponse :
    {
        "success": true,
        "results": [...]
    }
    """
    try:
        data = request.get_json() or {}
        
        report_name = data.get('report_name')
        days_history = data.get('days_history', 90)
        
        if report_name:
            # Entraîner un seul rapport
            logger.info(f"Entraînement du rapport {report_name}")
            result = train_model(report_name, days_history)
            
            return jsonify({
                'success': result['success'],
                'result': result
            }), 200 if result['success'] else 400
        
        else:
            # Entraîner tous les rapports
            logger.info("Entraînement de tous les rapports")
            results = train_all_reports(days_history)
            
            success_count = sum(1 for r in results if r['success'])
            
            return jsonify({
                'success': success_count > 0,
                'total': len(results),
                'success_count': success_count,
                'results': results
            }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai.route('/predict', methods=['GET'])
def predict():
    """
    Génère des prédictions Prophet pour un rapport
    
    GET /ai/predict?report=daily_sales&days=7&date=2025-01-15
    
    Paramètres :
    - report : Nom du rapport (requis)
    - days : Nombre de jours à prédire (optionnel, défaut 7)
    - date : Date de référence YYYY-MM-DD (optionnel, défaut aujourd'hui)
    
    Réponse :
    {
        "success": true,
        "forecast": [...]
    }
    """
    try:
        report_name = request.args.get('report')
        days = int(request.args.get('days', 7))
        date_str = request.args.get('date')
        
        if not report_name:
            return jsonify({
                'success': False,
                'error': 'Paramètre "report" requis'
            }), 400
        
        # Parser la date
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Format de date invalide (attendu: YYYY-MM-DD)'
                }), 400
        else:
            report_date = date.today()
        
        # Générer les prédictions
        logger.info(f"Prédiction pour {report_name} à {days} jours depuis {report_date}")
        
        ai_manager = AIManager()
        forecast = ai_manager.generate_forecasts(
            report_name=report_name,
            days=days,
            report_date=report_date
        )
        
        return jsonify(forecast), 200 if forecast.get('success') else 400
    
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """
    Analyse un rapport via LLM
    
    GET /ai/analyze?report=daily_sales&date=2025-01-15&prompt_type=daily_analysis&include_forecast=true
    
    POST /ai/analyze
    Body: {
        "report_name": "daily_sales",
        "date": "2025-01-15",
        "prompt_type": "daily_analysis",
        "include_forecast": true
    }
    
    Paramètres :
    - report : Nom du rapport (requis)
    - date : Date YYYY-MM-DD (optionnel, défaut aujourd'hui)
    - prompt_type : Type de prompt (optionnel, défaut daily_analysis)
    - include_forecast : Inclure prédictions Prophet (optionnel, défaut false)
    
    Réponse :
    {
        "success": true,
        "analysis": "...",
        "provider": "groq",
        "model": "llama-3.1-70b-versatile"
    }
    """
    try:
        # Récupérer les paramètres (GET ou POST)
        if request.method == 'POST':
            data = request.get_json() or {}
            report_name = data.get('report_name') or data.get('report')
            date_str = data.get('date')
            prompt_type = data.get('prompt_type', 'daily_analysis')
            include_forecast = data.get('include_forecast', False)
        else:
            report_name = request.args.get('report')
            date_str = request.args.get('date')
            prompt_type = request.args.get('prompt_type', 'daily_analysis')
            include_forecast = request.args.get('include_forecast', 'false').lower() == 'true'
        
        if not report_name:
            return jsonify({
                'success': False,
                'error': 'Paramètre "report" requis'
            }), 400
        
        # Parser la date
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Format de date invalide (attendu: YYYY-MM-DD)'
                }), 400
        else:
            report_date = date.today()
        
        # Analyser le rapport
        logger.info(f"Analyse du rapport {report_name} pour {report_date}")
        
        ai_manager = AIManager()
        analysis = ai_manager.analyze_reports(
            report_name=report_name,
            report_date=report_date,
            prompt_type=prompt_type,
            include_forecast=include_forecast
        )
        
        return jsonify(analysis), 200 if analysis.get('success') else 400
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai.route('/anomalies', methods=['GET'])
def anomalies():
    """
    Détecte les anomalies dans un rapport
    
    GET /ai/anomalies?report=daily_sales&date=2025-01-15
    
    Paramètres :
    - report : Nom du rapport (requis)
    - date : Date YYYY-MM-DD (optionnel, défaut aujourd'hui)
    
    Réponse :
    {
        "success": true,
        "analysis": "...",
        "statistics": {...}
    }
    """
    try:
        report_name = request.args.get('report')
        date_str = request.args.get('date')
        
        if not report_name:
            return jsonify({
                'success': False,
                'error': 'Paramètre "report" requis'
            }), 400
        
        # Parser la date
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Format de date invalide (attendu: YYYY-MM-DD)'
                }), 400
        else:
            report_date = date.today()
        
        # Détecter les anomalies
        logger.info(f"Détection d'anomalies pour {report_name} le {report_date}")
        
        ai_manager = AIManager()
        result = ai_manager.detect_anomalies(
            report_name=report_name,
            report_date=report_date
        )
        
        return jsonify(result), 200 if result.get('success') else 400
    
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'anomalies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai.route('/summary', methods=['GET'])
def summary():
    """
    Génère un résumé AI global
    
    GET /ai/summary?type=daily&date=2025-01-15
    
    Paramètres :
    - type : Type de résumé (daily/weekly/monthly, défaut daily)
    - date : Date de référence YYYY-MM-DD (optionnel, défaut aujourd'hui)
    
    Réponse :
    {
        "success": true,
        "analysis": "...",
        "summary_type": "daily"
    }
    """
    try:
        summary_type = request.args.get('type', 'daily')
        date_str = request.args.get('date')
        
        # Valider le type
        if summary_type not in ['daily', 'weekly', 'monthly']:
            return jsonify({
                'success': False,
                'error': 'Type invalide. Options: daily, weekly, monthly'
            }), 400
        
        # Parser la date
        if date_str:
            try:
                reference_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Format de date invalide (attendu: YYYY-MM-DD)'
                }), 400
        else:
            reference_date = date.today()
        
        # Générer le résumé
        logger.info(f"Génération du résumé {summary_type} pour {reference_date}")
        
        ai_manager = AIManager()
        result = ai_manager.get_ai_summary(
            summary_type=summary_type,
            reference_date=reference_date
        )
        
        return jsonify(result), 200 if result.get('success') else 400
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Export des routes
__all__ = ['ai']

