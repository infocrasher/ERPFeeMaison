"""
Routes d'administration pour le service d'impression
Gestion et test de l'imprimante et du tiroir-caisse
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from decorators import admin_required
from app.services.printer_service import get_printer_service
import logging

logger = logging.getLogger(__name__)

# Créer le blueprint
printer_admin = Blueprint('printer_admin', __name__, url_prefix='/admin/printer')

@printer_admin.route('/')
@login_required
@admin_required
def printer_dashboard():
    """Dashboard de gestion de l'imprimante"""
    printer_service = get_printer_service()
    status = printer_service.get_status()
    
    return render_template('admin/printer_dashboard.html', 
                         status=status,
                         title="Gestion Imprimante & Tiroir-Caisse")

@printer_admin.route('/status')
@login_required
@admin_required
def get_status():
    """API pour obtenir le statut en temps réel"""
    printer_service = get_printer_service()
    status = printer_service.get_status()
    return jsonify(status)

@printer_admin.route('/test/print', methods=['POST'])
@login_required
@admin_required
def test_print():
    """Tester l'impression"""
    try:
        printer_service = get_printer_service()
        success = printer_service.print_test()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test d\'impression envoyé avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Échec de l\'envoi du test d\'impression'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur test impression: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@printer_admin.route('/test/drawer', methods=['POST'])
@login_required
@admin_required
def test_drawer():
    """Tester l'ouverture du tiroir"""
    try:
        printer_service = get_printer_service()
        success = printer_service.open_cash_drawer()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Commande d\'ouverture tiroir envoyée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Échec de l\'envoi de la commande d\'ouverture'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur test tiroir: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@printer_admin.route('/test/ticket/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def test_ticket(order_id):
    """Tester l'impression d'un ticket pour une commande spécifique"""
    try:
        printer_service = get_printer_service()
        success = printer_service.print_ticket(order_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Impression du ticket pour la commande #{order_id} envoyée'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Échec de l\'impression du ticket pour la commande #{order_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur test ticket commande {order_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@printer_admin.route('/restart', methods=['POST'])
@login_required
@admin_required
def restart_service():
    """Redémarrer le service d'impression"""
    try:
        printer_service = get_printer_service()
        printer_service.stop_service()
        printer_service.start_service()
        
        return jsonify({
            'success': True,
            'message': 'Service d\'impression redémarré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur redémarrage service: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500









