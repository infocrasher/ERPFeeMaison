"""
Service d'impression et gestion du tiroir-caisse pour ERP Fée Maison
Intégration avec imprimante ZHU HAI SUNCSW Receipt Printer Co.,Ltd. Gprinter USB Printer
"""

import usb.core
import usb.util
import threading
import queue
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
import os
from flask import current_app
from extensions import db

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PrinterConfig:
    """Configuration de l'imprimante"""
    vendor_id: int = 0x0471
    product_id: int = 0x0055
    interface: int = 0
    timeout: int = 5000
    enabled: bool = True
    # Configuration réseau
    network_enabled: bool = False
    agent_host: str = 'localhost'
    agent_port: int = 8080
    agent_token: str = 'default_token_change_me'
    
    @classmethod
    def from_env(cls):
        """Créer la configuration depuis les variables d'environnement"""
        return cls(
            vendor_id=int(os.getenv('PRINTER_VENDOR_ID', '0x0471'), 16),
            product_id=int(os.getenv('PRINTER_PRODUCT_ID', '0x0055'), 16),
            interface=int(os.getenv('PRINTER_INTERFACE', '0')),
            timeout=int(os.getenv('PRINTER_TIMEOUT', '5000')),
            enabled=os.getenv('PRINTER_ENABLED', 'true').lower() == 'true',
            network_enabled=os.getenv('PRINTER_NETWORK_ENABLED', 'false').lower() == 'true',
            agent_host=os.getenv('PRINTER_AGENT_HOST', 'localhost'),
            agent_port=int(os.getenv('PRINTER_AGENT_PORT', '8080')),
            agent_token=os.getenv('PRINTER_AGENT_TOKEN', 'default_token_change_me')
        )

class PrinterError(Exception):
    """Exception personnalisée pour les erreurs d'imprimante"""
    pass

class PrintJob:
    """Représente un travail d'impression"""
    def __init__(self, job_type: str, data: Dict[Any, Any], priority: int = 1):
        self.job_type = job_type  # 'ticket', 'drawer', 'test'
        self.data = data
        self.priority = priority
        self.created_at = datetime.now()
        self.attempts = 0
        self.max_attempts = 3
    
    def __lt__(self, other):
        """Comparaison pour la PriorityQueue"""
        return self.created_at < other.created_at

class PrinterService:
    """Service centralisé pour l'impression et le tiroir-caisse"""
    
    def __init__(self):
        self.config = PrinterConfig.from_env()
        self.device = None
        self.endpoint_out = None
        self.print_queue = queue.PriorityQueue()
        self.worker_thread = None
        self.running = False
        self._lock = threading.Lock()
        
        # Service réseau (si activé)
        self.remote_service = None
        if self.config.network_enabled:
            try:
                from .printer_agent import RemotePrinterService
                self.remote_service = RemotePrinterService(
                    self.config.agent_host,
                    self.config.agent_port,
                    self.config.agent_token
                )
                logger.info(f"🌐 Service réseau activé: {self.config.agent_host}:{self.config.agent_port}")
            except ImportError:
                logger.warning("⚠️ Module printer_agent non disponible pour le mode réseau")
                self.config.network_enabled = False
        
        # Commandes ESC/POS
        self.ESC_INIT = b'\x1b@'  # Initialiser l'imprimante
        self.ESC_CUT = b'\x1dVA'  # Couper le papier
        self.ESC_DRAWER = b'\x1bp\x00\x19\xfa'  # Ouvrir le tiroir-caisse
        self.ESC_ALIGN_CENTER = b'\x1ba\x01'  # Centrer le texte
        self.ESC_ALIGN_LEFT = b'\x1ba\x00'  # Aligner à gauche
        self.ESC_BOLD_ON = b'\x1bE\x01'  # Gras ON
        self.ESC_BOLD_OFF = b'\x1bE\x00'  # Gras OFF
        self.ESC_DOUBLE_HEIGHT = b'\x1b!\x10'  # Double hauteur
        self.ESC_NORMAL = b'\x1b!\x00'  # Taille normale
        
        if self.config.enabled:
            self.start_service()
    
    def start_service(self):
        """Démarrer le service d'impression"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("🖨️ Service d'impression démarré")
    
    def stop_service(self):
        """Arrêter le service d'impression"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        self._disconnect_printer()
        logger.info("🖨️ Service d'impression arrêté")
    
    def _connect_printer(self) -> bool:
        """Connecter à l'imprimante USB"""
        # Si USB n'est pas disponible (VPS en mode réseau), ne pas essayer de se connecter
        if not USB_AVAILABLE:
            logger.warning("⚠️ USB non disponible - mode réseau requis")
            return False
            
        try:
            with self._lock:
                if self.device is not None:
                    return True
                
                # Rechercher l'imprimante
                self.device = usb.core.find(
                    idVendor=self.config.vendor_id,
                    idProduct=self.config.product_id
                )
                
                if self.device is None:
                    raise PrinterError("Imprimante non détectée sur le port USB")
                
                # Détacher le driver système si nécessaire (Linux/macOS)
                try:
                    if self.device.is_kernel_driver_active(self.config.interface):
                        self.device.detach_kernel_driver(self.config.interface)
                except (usb.core.USBError, NotImplementedError):
                    # Sur certains systèmes, cette fonction n'est pas implémentée
                    pass
                
                # Configurer l'imprimante
                self.device.set_configuration()
                cfg = self.device.get_active_configuration()
                intf = cfg[(self.config.interface, 0)]
                
                # Trouver l'endpoint de sortie
                self.endpoint_out = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                )
                
                if self.endpoint_out is None:
                    raise PrinterError("Endpoint de sortie non trouvé")
                
                logger.info(f"🖨️ Imprimante connectée (VID:{self.config.vendor_id:04x}, PID:{self.config.product_id:04x})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion imprimante: {e}")
            self.device = None
            self.endpoint_out = None
            return False
    
    def _disconnect_printer(self):
        """Déconnecter l'imprimante"""
        with self._lock:
            if self.device is not None:
                try:
                    usb.util.dispose_resources(self.device)
                except:
                    pass
                self.device = None
                self.endpoint_out = None
                logger.info("🖨️ Imprimante déconnectée")
    
    def _send_raw_data(self, data: bytes) -> bool:
        """Envoyer des données brutes à l'imprimante"""
        try:
            if not self._connect_printer():
                return False
            
            with self._lock:
                self.endpoint_out.write(data, timeout=self.config.timeout)
                return True
                
        except usb.core.USBTimeoutError:
            logger.error("❌ Timeout lors de l'envoi à l'imprimante")
            return False
        except usb.core.USBError as e:
            logger.error(f"❌ Erreur USB: {e}")
            self._disconnect_printer()  # Forcer la reconnexion
            return False
        except Exception as e:
            logger.error(f"❌ Erreur envoi données: {e}")
            return False
    
    def _worker(self):
        """Thread worker pour traiter la queue d'impression"""
        logger.info("🔄 Worker d'impression démarré")
        
        while self.running:
            try:
                # Attendre un job avec timeout
                try:
                    priority, job = self.print_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Traiter le job
                success = self._process_job(job)
                
                if not success and job.attempts < job.max_attempts:
                    job.attempts += 1
                    logger.warning(f"⚠️ Nouvelle tentative {job.attempts}/{job.max_attempts} pour {job.job_type}")
                    time.sleep(2)  # Attendre avant de réessayer
                    self.print_queue.put((priority, job))
                elif not success:
                    logger.error(f"❌ Échec définitif pour {job.job_type} après {job.max_attempts} tentatives")
                
                self.print_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Erreur dans le worker: {e}")
                time.sleep(1)
        
        logger.info("🔄 Worker d'impression arrêté")
    
    def _process_job(self, job: PrintJob) -> bool:
        """Traiter un job d'impression"""
        try:
            if job.job_type == 'ticket':
                return self._print_ticket_internal(job.data)
            elif job.job_type == 'drawer':
                return self._open_drawer_internal()
            elif job.job_type == 'test':
                return self._print_test_internal()
            elif job.job_type == 'cashout_receipt':
                return self._print_cashout_receipt_internal(job.data)
            else:
                logger.error(f"❌ Type de job inconnu: {job.job_type}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur traitement job {job.job_type}: {e}")
            return False
    
    def _format_currency(self, amount: float) -> str:
        """Formater un montant en devise"""
        return f"{amount:,.2f} DA".replace(',', ' ')
    
    def _format_line(self, left: str, right: str, width: int = 32) -> str:
        """Formater une ligne avec alignement gauche/droite"""
        available_space = width - len(right)
        left_truncated = left[:available_space-1] if len(left) >= available_space else left
        spaces = width - len(left_truncated) - len(right)
        return left_truncated + ' ' * spaces + right
    
    def _print_ticket_internal(self, data: Dict[Any, Any]) -> bool:
        """Imprimer un ticket de caisse (méthode interne)"""
        try:
            # Récupérer les données de la commande depuis les données passées
            order_id = data.get('order_id')
            customer_name = data.get('customer_name', '')
            delivery_option = data.get('delivery_option', '')
            total_amount = data.get('total_amount', 0)
            items = data.get('items', [])
            
            if not order_id:
                logger.error("❌ ID de commande manquant")
                return False
            
            # Construire le ticket ESC/POS
            ticket = bytearray()
            
            # Initialiser l'imprimante
            ticket.extend(self.ESC_INIT)
            
            # En-tête centré avec nouvelles informations
            ticket.extend(self.ESC_ALIGN_CENTER)
            ticket.extend(self.ESC_DOUBLE_HEIGHT)
            ticket.extend(self.ESC_BOLD_ON)
            ticket.extend(b"FEE MAISON\n")
            ticket.extend(self.ESC_NORMAL)
            ticket.extend(self.ESC_BOLD_OFF)
            ticket.extend(b"Patisserie Traditionnelle\n")
            ticket.extend(b"183 cooperative ERRAHMA\n")
            ticket.extend(b"Dely Brahim Alger\n")
            ticket.extend(b"TEL: 0556250370\n")
            ticket.extend(b"--------------------------------\n")
            
            # Informations de la commande
            ticket.extend(self.ESC_ALIGN_LEFT)
            ticket.extend(f"Ticket N°: {order_id}\n".encode('utf-8'))
            ticket.extend(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('utf-8'))
            
            if customer_name and customer_name not in ['Vente directe', 'Vente POS']:
                ticket.extend(f"Client: {customer_name}\n".encode('utf-8'))
            
            if delivery_option:
                ticket.extend(f"Type: {delivery_option}\n".encode('utf-8'))
            
            ticket.extend(b"--------------------------------\n")
            
            # Articles
            total = 0
            if items:
                for item in items:
                    product_name = item.get('product_name', 'Article')
                    quantity = item.get('quantity', 0)
                    unit_price = item.get('unit_price', 0)
                    line_total = quantity * unit_price
                    total += line_total
                    
                    # Ligne produit
                    ticket.extend(f"{product_name}\n".encode('utf-8'))
                    
                    # Ligne quantité x prix = total
                    qty_display = int(quantity) if quantity == int(quantity) else quantity
                    qty_price_line = self._format_line(
                        f"  {qty_display} x {self._format_currency(unit_price)}",
                        self._format_currency(line_total)
                    )
                    ticket.extend(f"{qty_price_line}\n".encode('utf-8'))
            else:
                # Si pas d'items, utiliser le total de la commande
                total = total_amount
                ticket.extend(b"Vente directe\n")
                ticket.extend(f"Montant: {self._format_currency(total)}\n".encode('utf-8'))
            
            ticket.extend(b"--------------------------------\n")
            
            # Total
            ticket.extend(self.ESC_BOLD_ON)
            total_line = self._format_line("TOTAL:", self._format_currency(total))
            ticket.extend(f"{total_line}\n".encode('utf-8'))
            ticket.extend(self.ESC_BOLD_OFF)
            
            # Paiement
            ticket.extend(b"--------------------------------\n")
            ticket.extend(b"Mode de paiement: ESPECES\n")
            
            # Pied de page
            ticket.extend(b"\n")
            ticket.extend(self.ESC_ALIGN_CENTER)
            ticket.extend(b"Merci de votre visite !\n")
            ticket.extend(b"A bientot chez Fee Maison\n")
            ticket.extend(b"\n")
            
            # Couper le papier
            ticket.extend(self.ESC_CUT)
            ticket.extend(b"\n\n\n")
            
            # Envoyer à l'imprimante
            success = self._send_raw_data(bytes(ticket))
            
            if success:
                logger.info(f"✅ Ticket imprimé pour commande #{order_id}")
            else:
                logger.error(f"❌ Échec impression ticket commande #{order_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"❌ Erreur impression ticket: {e}")
            return False
    
    def _open_drawer_internal(self) -> bool:
        """Ouvrir le tiroir-caisse (méthode interne)"""
        try:
            # Séquence d'ouverture du tiroir
            drawer_command = bytearray()
            drawer_command.extend(self.ESC_DRAWER)
            
            success = self._send_raw_data(bytes(drawer_command))
            
            if success:
                logger.info("✅ Tiroir-caisse ouvert")
            else:
                logger.error("❌ Échec ouverture tiroir-caisse")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur ouverture tiroir: {e}")
            return False
    
    def _print_test_internal(self) -> bool:
        """Imprimer un ticket de test (méthode interne)"""
        try:
            test_ticket = bytearray()
            
            # Initialiser
            test_ticket.extend(self.ESC_INIT)
            
            # Contenu du test
            test_ticket.extend(self.ESC_ALIGN_CENTER)
            test_ticket.extend(self.ESC_BOLD_ON)
            test_ticket.extend(b"TEST IMPRIMANTE\n")
            test_ticket.extend(self.ESC_BOLD_OFF)
            test_ticket.extend(b"Fee Maison ERP\n")
            test_ticket.extend(b"183 cooperative ERRAHMA\n")
            test_ticket.extend(b"Dely Brahim Alger\n")
            test_ticket.extend(b"TEL: 0556250370\n")
            test_ticket.extend(b"--------------------------------\n")
            test_ticket.extend(self.ESC_ALIGN_LEFT)
            test_ticket.extend(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n".encode('utf-8'))
            test_ticket.extend(b"Status: Imprimante OK\n")
            test_ticket.extend(b"Tiroir: Fonctionnel\n")
            test_ticket.extend(b"--------------------------------\n")
            test_ticket.extend(self.ESC_ALIGN_CENTER)
            test_ticket.extend(b"Test reussi !\n\n")
            
            # Couper
            test_ticket.extend(self.ESC_CUT)
            test_ticket.extend(b"\n\n")
            
            success = self._send_raw_data(bytes(test_ticket))
            
            if success:
                logger.info("✅ Ticket de test imprimé")
            else:
                logger.error("❌ Échec impression test")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur impression test: {e}")
            return False
    
    def _print_cashout_receipt_internal(self, data: Dict[Any, Any]) -> bool:
        """Imprimer un reçu de cashout (méthode interne)"""
        try:
            amount = data.get('amount', 0)
            notes = data.get('notes', '')
            employee_name = data.get('employee_name', 'Employé')
            
            # Construire le reçu ESC/POS
            receipt = bytearray()
            
            # Initialiser l'imprimante
            receipt.extend(self.ESC_INIT)
            
            # En-tête centré avec nouvelles informations
            receipt.extend(self.ESC_ALIGN_CENTER)
            receipt.extend(self.ESC_DOUBLE_HEIGHT)
            receipt.extend(self.ESC_BOLD_ON)
            receipt.extend(b"FEE MAISON\n")
            receipt.extend(self.ESC_NORMAL)
            receipt.extend(self.ESC_BOLD_OFF)
            receipt.extend(b"Patisserie Traditionnelle\n")
            receipt.extend(b"183 cooperative ERRAHMA\n")
            receipt.extend(b"Dely Brahim Alger\n")
            receipt.extend(b"TEL: 0556250370\n")
            receipt.extend(b"--------------------------------\n")
            
            # Titre du reçu
            receipt.extend(self.ESC_BOLD_ON)
            receipt.extend(b"RECU DE DEPOT BANCAIRE\n")
            receipt.extend(self.ESC_BOLD_OFF)
            receipt.extend(b"--------------------------------\n")
            
            # Informations du cashout
            receipt.extend(self.ESC_ALIGN_LEFT)
            receipt.extend(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('utf-8'))
            receipt.extend(f"Employe: {employee_name}\n".encode('utf-8'))
            receipt.extend(b"Operation: Depot en banque\n")
            receipt.extend(b"--------------------------------\n")
            
            # Montant
            receipt.extend(self.ESC_BOLD_ON)
            amount_line = self._format_line("MONTANT DEPOSE:", self._format_currency(amount))
            receipt.extend(f"{amount_line}\n".encode('utf-8'))
            receipt.extend(self.ESC_BOLD_OFF)
            
            # Notes si présentes
            if notes:
                receipt.extend(b"--------------------------------\n")
                receipt.extend(f"Notes: {notes}\n".encode('utf-8'))
            
            receipt.extend(b"--------------------------------\n")
            
            # Pied de page
            receipt.extend(b"\n")
            receipt.extend(self.ESC_ALIGN_CENTER)
            receipt.extend(b"Depot effectue avec succes\n")
            receipt.extend(b"Conservez ce recu\n")
            receipt.extend(b"\n")
            
            # Informations légales
            receipt.extend(b"Tel: +213 XXX XXX XXX\n")
            receipt.extend(b"www.feemaison.dz\n")
            receipt.extend(b"\n")
            
            # Couper le papier
            receipt.extend(self.ESC_CUT)
            receipt.extend(b"\n\n\n")
            
            # Envoyer à l'imprimante
            success = self._send_raw_data(bytes(receipt))
            
            if success:
                logger.info(f"✅ Reçu de cashout imprimé pour {self._format_currency(amount)}")
            else:
                logger.error(f"❌ Échec impression reçu cashout")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur impression reçu cashout: {e}")
            return False
    
    # API publique
    def print_ticket(self, order_id: int, priority: int = 1) -> bool:
        """
        Imprimer un ticket de caisse (non bloquant)
        
        Args:
            order_id: ID de la commande
            priority: Priorité du job (1=haute, 2=normale, 3=basse)
        
        Returns:
            bool: True si le job a été ajouté à la queue
        """
        if not self.config.enabled:
            logger.info("🖨️ Impression désactivée par configuration")
            return True
        
        # Mode réseau : déléguer à l'agent distant
        if self.config.network_enabled and self.remote_service:
            try:
                success = self.remote_service.print_ticket(order_id, priority)
                if success:
                    logger.info(f"📄 Impression ticket #{order_id} envoyée à l'agent distant")
                else:
                    logger.error(f"❌ Échec impression ticket #{order_id} via agent distant")
                return success
            except Exception as e:
                logger.error(f"❌ Erreur communication agent distant: {e}")
                return False
        
        # Mode local : récupérer les données dans le contexte actuel
        try:
            from models import Order
            from flask import current_app
            
            if current_app:
                order = Order.query.get(order_id)
                if not order:
                    logger.error(f"❌ Commande {order_id} non trouvée")
                    return False
                
                # Préparer les données pour le thread d'impression
                order_data = {
                    'order_id': order.id,
                    'customer_name': order.customer_name,
                    'delivery_option': getattr(order, 'delivery_option', None),
                    'total_amount': float(order.total_amount) if order.total_amount else 0,
                    'items': []
                }
                
                # Récupérer les items (forcer l'évaluation de la relation)
                items_list = order.items.all()  # Convertir AppenderQuery en liste
                for item in items_list:
                    # OrderItem n'a pas d'attribut description, contrairement à B2BOrderItem
                    product_name = item.product.name if item.product else "Article"
                    item_data = {
                        'product_name': product_name,
                        'quantity': float(item.quantity),
                        'unit_price': float(item.unit_price),
                        'description': getattr(item, 'description', None)  # Sécurisé pour les deux types
                    }
                    order_data['items'].append(item_data)
                
                job = PrintJob('ticket', order_data, priority)
                self.print_queue.put((priority, job))
                logger.info(f"📄 Job d'impression ajouté pour commande #{order_id}")
                return True
            else:
                logger.error("❌ Contexte d'application non disponible")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout job impression: {e}")
            return False
    
    def open_cash_drawer(self, priority: int = 1) -> bool:
        """
        Ouvrir le tiroir-caisse (non bloquant)
        
        Args:
            priority: Priorité du job (1=haute, 2=normale, 3=basse)
        
        Returns:
            bool: True si le job a été ajouté à la queue
        """
        if not self.config.enabled:
            logger.info("💰 Ouverture tiroir désactivée par configuration")
            return True
        
        # Mode réseau : déléguer à l'agent distant
        if self.config.network_enabled and self.remote_service:
            try:
                success = self.remote_service.open_cash_drawer(priority)
                if success:
                    logger.info("💰 Ouverture tiroir envoyée à l'agent distant")
                else:
                    logger.error("❌ Échec ouverture tiroir via agent distant")
                return success
            except Exception as e:
                logger.error(f"❌ Erreur communication agent distant: {e}")
                return False
        
        # Mode local : ajouter à la queue
        try:
            job = PrintJob('drawer', {}, priority)
            self.print_queue.put((priority, job))
            logger.info("💰 Job d'ouverture tiroir ajouté")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur ajout job tiroir: {e}")
            return False
    
    def print_test(self) -> bool:
        """
        Imprimer un ticket de test (non bloquant)
        
        Returns:
            bool: True si le job a été ajouté à la queue
        """
        if not self.config.enabled:
            logger.info("🖨️ Test impression désactivé par configuration")
            return True
        
        try:
            job = PrintJob('test', {}, 1)  # Haute priorité pour les tests
            self.print_queue.put((1, job))
            logger.info("🧪 Job de test d'impression ajouté")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur ajout job test: {e}")
            return False
    
    def print_cashout_receipt(self, amount: float, notes: str = '', employee_name: str = '', priority: int = 1) -> bool:
        """
        Imprimer un reçu de cashout (non bloquant)
        
        Args:
            amount: Montant du cashout
            notes: Notes optionnelles
            employee_name: Nom de l'employé
            priority: Priorité du job (1=haute, 2=normale, 3=basse)
        
        Returns:
            bool: True si le job a été ajouté à la queue
        """
        if not self.config.enabled:
            logger.info("🖨️ Impression reçu cashout désactivée par configuration")
            return True
        
        # Mode réseau : déléguer à l'agent distant
        if self.config.network_enabled and self.remote_service:
            try:
                # Pour le mode réseau, on pourrait étendre l'agent pour supporter les cashouts
                logger.info("🌐 Impression reçu cashout via agent distant non implémentée")
                return True
            except Exception as e:
                logger.error(f"❌ Erreur communication agent distant: {e}")
                return False
        
        # Mode local : ajouter à la queue
        try:
            job = PrintJob('cashout_receipt', {
                'amount': amount,
                'notes': notes,
                'employee_name': employee_name
            }, priority)
            self.print_queue.put((priority, job))
            logger.info(f"🧾 Job d'impression reçu cashout ajouté ({amount:.2f} DA)")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur ajout job reçu cashout: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtenir le statut du service d'impression
        
        Returns:
            Dict contenant les informations de statut
        """
        return {
            'enabled': self.config.enabled,
            'running': self.running,
            'connected': self.device is not None,
            'queue_size': self.print_queue.qsize(),
            'config': {
                'vendor_id': f"0x{self.config.vendor_id:04x}",
                'product_id': f"0x{self.config.product_id:04x}",
                'timeout': self.config.timeout
            }
        }

# Instance globale du service
printer_service = PrinterService()

def get_printer_service() -> PrinterService:
    """Obtenir l'instance du service d'impression"""
    return printer_service
