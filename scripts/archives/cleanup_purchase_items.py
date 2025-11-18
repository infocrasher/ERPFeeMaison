#!/usr/bin/env python3
"""
Script pour nettoyer les purchase_items avec des références null
"""

from app import create_app, db
from app.purchases.models import PurchaseItem
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_purchase_items():
    """Nettoie les purchase_items avec des références null"""
    app = create_app()
    
    with app.app_context():
        # Trouver les purchase_items avec product_id null
        null_items = PurchaseItem.query.filter_by(product_id=None).all()
        
        if not null_items:
            logger.info("✅ Aucun purchase_item avec product_id null trouvé")
            return
        
        logger.info(f"🗑️  Suppression de {len(null_items)} purchase_items avec product_id null")
        
        for item in null_items:
            logger.info(f"  - Suppression de purchase_item ID {item.id}")
            db.session.delete(item)
        
        db.session.commit()
        logger.info("✅ Nettoyage terminé")

if __name__ == "__main__":
    cleanup_purchase_items() 