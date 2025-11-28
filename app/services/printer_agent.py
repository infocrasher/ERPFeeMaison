"""
Agent réseau pour l'impression à distance
Permet au serveur ERP (VPS) de communiquer avec l'imprimante locale (PDV)
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
import requests
from .printer_service import PrinterService, PrinterConfig

logger = logging.getLogger(__name__)

class PrinterAgent:
    """Agent local qui écoute les requêtes d'impression du serveur ERP"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080, token: str = None):
        self.host = host
        self.port = port
        self.token = token or "default_token_change_me"
        self.printer_service = PrinterService()
        
        # Créer l'app Flask pour l'agent
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Statistiques
        self.stats = {
            'started_at': datetime.now(),
            'requests_received': 0,
            'print_jobs': 0,
            'drawer_jobs': 0,
            'errors': 0
        }
    
    def setup_routes(self):
        """Configurer les routes de l'agent"""
        
        @self.app.before_request
        def authenticate():
            """Vérifier le token d'authentification"""
            if request.endpoint in ['health']:  # Exclure la route de santé
                return
            
            auth_token = request.headers.get('Authorization')
            if not auth_token or auth_token != f"Bearer {self.token}":
                return jsonify({'error': 'Token d\'authentification invalide'}), 401
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Endpoint de santé"""
            return jsonify({
                'status': 'healthy',
                'service': 'printer_agent',
                'timestamp': datetime.now().isoformat(),
                'printer_connected': self.printer_service.device is not None
            })
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Statut détaillé de l'agent"""
            self.stats['requests_received'] += 1
            
            printer_status = self.printer_service.get_status()
            
            return jsonify({
                'agent': {
                    'host': self.host,
                    'port': self.port,
                    'uptime': str(datetime.now() - self.stats['started_at']),
                    'stats': self.stats
                },
                'printer': printer_status
            })
        
        @self.app.route('/print/ticket', methods=['POST'])
        def print_ticket():
            """Imprimer un ticket"""
            try:
                self.stats['requests_received'] += 1
                
                data = request.get_json()
                if not data or 'order_id' not in data:
                    return jsonify({'error': 'order_id requis'}), 400
                
                order_id = data['order_id']
                priority = data.get('priority', 1)
                
                success = self.printer_service.print_ticket(order_id, priority)
                
                if success:
                    self.stats['print_jobs'] += 1
                    return jsonify({
                        'success': True,
                        'message': f'Impression ticket commande #{order_id} programmée'
                    })
                else:
                    self.stats['errors'] += 1
                    return jsonify({
                        'success': False,
                        'message': 'Échec programmation impression'
                    }), 500
                    
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Erreur impression ticket: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/drawer/open', methods=['POST'])
        def open_drawer():
            """Ouvrir le tiroir-caisse"""
            try:
                self.stats['requests_received'] += 1
                
                data = request.get_json() or {}
                priority = data.get('priority', 1)
                
                success = self.printer_service.open_cash_drawer(priority)
                
                if success:
                    self.stats['drawer_jobs'] += 1
                    return jsonify({
                        'success': True,
                        'message': 'Ouverture tiroir programmée'
                    })
                else:
                    self.stats['errors'] += 1
                    return jsonify({
                        'success': False,
                        'message': 'Échec programmation ouverture tiroir'
                    }), 500
                    
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Erreur ouverture tiroir: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/test/print', methods=['POST'])
        def test_print():
            """Test d'impression"""
            try:
                self.stats['requests_received'] += 1
                
                success = self.printer_service.print_test()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Test d\'impression programmé'
                    })
                else:
                    self.stats['errors'] += 1
                    return jsonify({
                        'success': False,
                        'message': 'Échec test impression'
                    }), 500
                    
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Erreur test impression: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/print/cashout', methods=['POST'])
        def print_cashout():
            """Imprimer un reçu de cashout (dépôt banque)"""
            try:
                self.stats['requests_received'] += 1
                
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Données JSON requises'}), 400
                
                amount = data.get('amount', 0)
                notes = data.get('notes', '')
                employee_name = data.get('employee_name', 'Employé')
                priority = data.get('priority', 1)
                
                if amount <= 0:
                    return jsonify({'error': 'Montant invalide'}), 400
                
                success = self.printer_service.print_cashout_receipt(
                    amount=float(amount),
                    notes=notes,
                    employee_name=employee_name,
                    priority=priority
                )
                
                if success:
                    self.stats['print_jobs'] += 1
                    return jsonify({
                        'success': True,
                        'message': f'Impression reçu cashout de {amount:.2f} DA programmée'
                    })
                else:
                    self.stats['errors'] += 1
                    return jsonify({
                        'success': False,
                        'message': 'Échec programmation impression cashout'
                    }), 500
                    
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Erreur impression cashout: {e}")
                return jsonify({'error': str(e)}), 500
    
    def run(self, debug: bool = False):
        """Démarrer l'agent"""
        logger.info(f"🖨️ Démarrage agent imprimante sur {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)

class RemotePrinterService:
    """Service pour communiquer avec un agent d'impression distant"""
    
    def __init__(self, agent_host: str, agent_port: int = 8080, token: str = None):
        # Détecter le protocole : si l'host contient déjà http:// ou https://, l'utiliser
        # Sinon, détecter automatiquement pour Ngrok (HTTPS) ou utiliser HTTP par défaut
        if agent_host.startswith('http://') or agent_host.startswith('https://'):
            # URL complète fournie
            if ':' in agent_host.split('://')[1]:
                # Port déjà dans l'URL
                self.agent_url = agent_host
            else:
                # Ajouter le port
                self.agent_url = f"{agent_host}:{agent_port}"
        elif '.ngrok-free.dev' in agent_host or '.ngrok.io' in agent_host or '.ngrok.app' in agent_host:
            # Domaine Ngrok : utiliser HTTPS (Ngrok utilise HTTPS par défaut)
            self.agent_url = f"https://{agent_host}:{agent_port}"
        else:
            # Par défaut : HTTP
            self.agent_url = f"http://{agent_host}:{agent_port}"
        
        self.token = token or "default_token_change_me"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })
        
        # Timeout pour les requêtes
        self.timeout = 10
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Faire une requête à l'agent"""
        try:
            url = f"{self.agent_url}{endpoint}"
            
            if method == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur requête agent {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur communication agent: {e}")
            return None
    
    def print_ticket(self, order_id: int, priority: int = 1) -> bool:
        """Imprimer un ticket via l'agent distant (deprecated - utiliser print_ticket_with_data)"""
        result = self._make_request('/print/ticket', 'POST', {
            'order_id': order_id,
            'priority': priority
        })
        
        return result is not None and result.get('success', False)
    
    def print_ticket_with_data(self, order_data: Dict, priority: int = 1) -> bool:
        """Imprimer un ticket via l'agent distant avec les données complètes"""
        # Construire le payload avec toutes les données nécessaires
        payload = {
            'order_id': order_data.get('order_id'),
            'customer_name': order_data.get('customer_name', ''),
            'total': order_data.get('total_amount', 0),
            'total_amount': order_data.get('total_amount', 0),
            'items': order_data.get('items', []),
            'employee_name': order_data.get('employee_name', ''),
            'amount_received': order_data.get('amount_received', 0),
            'change_amount': order_data.get('change_amount', 0),
            'priority': priority
        }
        
        result = self._make_request('/print/ticket', 'POST', payload)
        
        return result is not None and result.get('success', False)
    
    def open_cash_drawer(self, priority: int = 1) -> bool:
        """Ouvrir le tiroir via l'agent distant"""
        result = self._make_request('/drawer/open', 'POST', {
            'priority': priority
        })
        
        return result is not None and result.get('success', False)
    
    def print_cashout_receipt(self, amount: float, notes: str = '', employee_name: str = '', priority: int = 1) -> bool:
        """Imprimer un reçu de cashout via l'agent distant"""
        result = self._make_request('/print/cashout', 'POST', {
            'amount': amount,
            'notes': notes,
            'employee_name': employee_name,
            'priority': priority
        })
        
        return result is not None and result.get('success', False)
    
    def print_test(self) -> bool:
        """Test d'impression via l'agent distant"""
        result = self._make_request('/test/print', 'POST')
        
        return result is not None and result.get('success', False)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtenir le statut de l'agent distant"""
        result = self._make_request('/status')
        
        if result:
            return result
        else:
            return {
                'enabled': False,
                'running': False,
                'connected': False,
                'queue_size': 0,
                'error': 'Agent non accessible'
            }
    
    def is_healthy(self) -> bool:
        """Vérifier si l'agent est accessible"""
        result = self._make_request('/health')
        return result is not None and result.get('status') == 'healthy'

def create_agent_app(config: Dict[str, Any] = None) -> Flask:
    """Créer une application Flask pour l'agent d'impression"""
    config = config or {}
    
    agent = PrinterAgent(
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8080),
        token=config.get('token', 'default_token_change_me')
    )
    
    return agent.app

if __name__ == "__main__":
    # Démarrage standalone de l'agent
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent d\'impression ERP Fée Maison')
    parser.add_argument('--host', default='0.0.0.0', help='Adresse d\'écoute')
    parser.add_argument('--port', type=int, default=8080, help='Port d\'écoute')
    parser.add_argument('--token', default='default_token_change_me', help='Token d\'authentification')
    parser.add_argument('--debug', action='store_true', help='Mode debug')
    
    args = parser.parse_args()
    
    agent = PrinterAgent(args.host, args.port, args.token)
    agent.run(debug=args.debug)











