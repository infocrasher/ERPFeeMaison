"""
Décorateurs et utilitaires pour l'intégration POS/PDV
Gestion automatique de l'impression et du tiroir-caisse
"""

import functools
import logging
from flask import request, current_app
from .printer_service import get_printer_service

logger = logging.getLogger(__name__)

def auto_print_and_drawer(order_id_param='order_id', trigger_drawer=True, trigger_print=True):
    """
    Décorateur pour automatiser l'impression et l'ouverture du tiroir
    
    Args:
        order_id_param: Nom du paramètre contenant l'ID de commande
        trigger_drawer: Si True, ouvre le tiroir-caisse
        trigger_print: Si True, imprime le ticket
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Exécuter la fonction originale
            result = func(*args, **kwargs)
            
            try:
                # Récupérer le service d'impression
                printer_service = get_printer_service()
                
                # Récupérer l'ID de commande
                order_id = None
                
                # Essayer de récupérer depuis les kwargs
                if order_id_param in kwargs:
                    order_id = kwargs[order_id_param]
                # Essayer depuis les args (pour les routes Flask)
                elif args and len(args) > 0:
                    order_id = args[0]  # Premier argument souvent l'ID
                
                if order_id and trigger_print:
                    printer_service.print_ticket(order_id, priority=1)
                    logger.info(f"🖨️ Impression automatique déclenchée pour commande #{order_id}")
                
                if trigger_drawer:
                    printer_service.open_cash_drawer(priority=1)
                    logger.info("💰 Ouverture tiroir automatique déclenchée")
                    
            except Exception as e:
                logger.error(f"❌ Erreur intégration POS: {e}")
                # Ne pas faire échouer la fonction principale
            
            return result
        return wrapper
    return decorator

def auto_drawer_only():
    """Décorateur pour ouvrir uniquement le tiroir-caisse"""
    return auto_print_and_drawer(trigger_print=False, trigger_drawer=True)

def pos_sale_complete(order_id_param='order_id'):
    """Décorateur spécialisé pour la finalisation d'une vente POS"""
    return auto_print_and_drawer(order_id_param=order_id_param, trigger_drawer=True, trigger_print=True)

def cashout_complete():
    """Décorateur spécialisé pour les cashouts (retrait d'espèces)"""
    return auto_print_and_drawer(trigger_print=False, trigger_drawer=True)











