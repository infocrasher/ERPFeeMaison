#!/usr/bin/env python3
"""
Script de debug pour analyser le problème d'impression lors des ventes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_vente_impression():
    """Debug du processus de vente et impression"""
    print("🔍 DEBUG VENTE ET IMPRESSION")
    print("=" * 40)
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            from app.services.printer_service import get_printer_service
            from models import Order, OrderItem, Product
            from flask_login import current_user
            
            printer_service = get_printer_service()
            
            print("✅ Application et service d'impression initialisés")
            
            # Simuler une vente comme dans la route
            print("\n🛒 Simulation d'une vente POS...")
            
            # Créer une commande temporaire comme dans process_sale
            from datetime import datetime
            from extensions import db
            
            temp_order = Order(
                user_id=1,  # ID utilisateur de test
                order_type='pos_direct',
                customer_name='Vente POS',
                due_date=datetime.utcnow(),
                status='completed',
                total_amount=300.0
            )
            
            db.session.add(temp_order)
            db.session.flush()  # Pour obtenir l'ID
            
            print(f"📦 Commande temporaire créée: #{temp_order.id}")
            
            # Ajouter un article de test
            # Récupérer le premier produit disponible
            product = Product.query.first()
            if product:
                order_item = OrderItem(
                    order_id=temp_order.id,
                    product_id=product.id,
                    quantity=2,
                    unit_price=150.0
                )
                db.session.add(order_item)
                print(f"📄 Article ajouté: {product.name} x2")
            else:
                print("⚠️ Aucun produit trouvé en base")
            
            db.session.commit()
            print("💾 Commande sauvegardée en base")
            
            # Test d'impression comme dans la route
            print("\n🖨️ Test d'impression depuis contexte de vente...")
            
            try:
                # Récupérer la commande fraîchement créée
                fresh_order = Order.query.get(temp_order.id)
                if fresh_order:
                    print(f"✅ Commande récupérée: #{fresh_order.id}")
                    print(f"   - Client: {fresh_order.customer_name}")
                    print(f"   - Total: {fresh_order.total_amount}")
                    print(f"   - Articles: {fresh_order.items.count()}")
                    
                    # Test d'impression
                    success = printer_service.print_ticket(fresh_order.id, priority=1)
                    
                    if success:
                        print("✅ Appel print_ticket réussi")
                    else:
                        print("❌ Échec appel print_ticket")
                        
                    # Test ouverture tiroir
                    drawer_success = printer_service.open_cash_drawer(priority=1)
                    
                    if drawer_success:
                        print("✅ Appel open_cash_drawer réussi")
                    else:
                        print("❌ Échec appel open_cash_drawer")
                        
                else:
                    print("❌ Impossible de récupérer la commande")
                    
            except Exception as e:
                print(f"❌ Erreur lors du test d'impression: {e}")
                import traceback
                traceback.print_exc()
            
            # Nettoyer la commande de test
            try:
                db.session.delete(temp_order)
                db.session.commit()
                print("\n🧹 Commande de test supprimée")
            except:
                pass
                
            return True
            
    except Exception as e:
        print(f"❌ Erreur debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🎯 Debug Vente et Impression - ERP Fée Maison")
    print("=" * 50)
    
    success = debug_vente_impression()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 DEBUG TERMINÉ")
        print("\n💡 Vérifiez les logs ci-dessus pour identifier:")
        print("  - Si l'appel print_ticket réussit")
        print("  - Si les données de commande sont correctes")
        print("  - Si des erreurs apparaissent dans le processus")
    else:
        print("❌ ERREUR DURANT LE DEBUG")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
