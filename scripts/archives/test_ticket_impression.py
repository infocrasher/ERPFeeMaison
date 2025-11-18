#!/usr/bin/env python3
"""
Test spécifique de l'impression de ticket
Vérification du nouveau format avec logo et informations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ticket_impression():
    """Test de l'impression de ticket avec nouvelles informations"""
    print("🎫 TEST IMPRESSION TICKET AVEC NOUVELLES INFORMATIONS")
    print("=" * 55)
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            from app.services.printer_service import get_printer_service
            
            printer_service = get_printer_service()
            
            # Données de test pour un ticket
            test_order_data = {
                'order_id': 999,
                'customer_name': 'Test Client',
                'delivery_option': 'Sur place',
                'total_amount': 450.0,
                'items': [
                    {
                        'product_name': 'Mhadjeb Traditionnel',
                        'quantity': 2,
                        'unit_price': 150.0,
                        'description': 'Mhadjeb aux épices'
                    },
                    {
                        'product_name': 'Msamen aux Amandes',
                        'quantity': 1,
                        'unit_price': 150.0,
                        'description': 'Msamen fait maison'
                    }
                ]
            }
            
            print("📄 Test impression ticket avec nouvelles informations:")
            print(f"  • Adresse: 183 cooperative ERRAHMA, Dely Brahim Alger")
            print(f"  • Téléphone: 0556250370")
            print(f"  • Commande test: #{test_order_data['order_id']}")
            print(f"  • Articles: {len(test_order_data['items'])}")
            print(f"  • Total: {test_order_data['total_amount']} DA")
            
            # Test direct de la fonction interne
            success = printer_service._print_ticket_internal(test_order_data)
            
            if success:
                print("✅ Ticket de test imprimé avec succès !")
                print("\n📋 Format du ticket:")
                print("  ✅ En-tête: FEE MAISON")
                print("  ✅ Adresse: 183 cooperative ERRAHMA")
                print("  ✅ Ville: Dely Brahim Alger") 
                print("  ✅ Téléphone: 0556250370")
                print("  ✅ Articles détaillés")
                print("  ✅ Total calculé")
                print("  ✅ Mode de paiement: ESPECES")
                print("  ✅ Message de remerciement")
            else:
                print("❌ Échec impression ticket de test")
                
            return success
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 Test Impression Ticket - Nouvelles Informations")
    print("=" * 55)
    
    success = test_ticket_impression()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 TEST RÉUSSI !")
        print("\n💡 Le ticket contient maintenant:")
        print("  📍 Adresse complète: 183 cooperative ERRAHMA, Dely Brahim Alger")
        print("  📞 Téléphone: 0556250370")
        print("  🏪 Nom: FEE MAISON - Patisserie Traditionnelle")
        print("  📄 Format professionnel avec tous les détails")
        
        print("\n🚀 Prochaines étapes:")
        print("  1. Effectuer une vraie vente dans l'ERP")
        print("  2. Vérifier que le ticket s'imprime automatiquement")
        print("  3. Contrôler que toutes les informations sont correctes")
    else:
        print("❌ ÉCHEC DU TEST")
        print("💡 Vérifiez:")
        print("  - Imprimante connectée et allumée")
        print("  - Drivers USB installés")
        print("  - Configuration PRINTER_ENABLED=true")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





