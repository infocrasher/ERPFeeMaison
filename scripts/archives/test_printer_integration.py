#!/usr/bin/env python3
"""
Script de test pour l'intégration imprimante/tiroir-caisse
ERP Fée Maison - Test complet du système POS
"""

import os
import sys
import time
from datetime import datetime

# Ajouter le répertoire de l'app au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_printer_service():
    """Test du service d'impression"""
    print("🖨️ Test du Service d'Impression ERP Fée Maison")
    print("=" * 50)
    
    try:
        # Importer le service
        from app.services.printer_service import get_printer_service
        
        printer_service = get_printer_service()
        
        # Afficher le statut
        status = printer_service.get_status()
        print(f"📊 Statut du service:")
        print(f"  - Activé: {status['enabled']}")
        print(f"  - En cours: {status['running']}")
        print(f"  - Connecté: {status['connected']}")
        print(f"  - Queue: {status['queue_size']} jobs")
        print(f"  - Config: {status['config']}")
        
        if not status['enabled']:
            print("\n⚠️ Service désactivé. Activez-le avec PRINTER_ENABLED=true")
            return False
        
        # Test d'impression
        print(f"\n🧪 Test d'impression...")
        success = printer_service.print_test()
        if success:
            print("✅ Test d'impression envoyé")
        else:
            print("❌ Échec test d'impression")
        
        # Attendre un peu
        time.sleep(2)
        
        # Test tiroir
        print(f"\n💰 Test ouverture tiroir...")
        success = printer_service.open_cash_drawer()
        if success:
            print("✅ Commande tiroir envoyée")
        else:
            print("❌ Échec ouverture tiroir")
        
        # Statut final
        time.sleep(1)
        final_status = printer_service.get_status()
        print(f"\n📊 Statut final:")
        print(f"  - Queue: {final_status['queue_size']} jobs")
        print(f"  - Connecté: {final_status['connected']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        print("💡 Assurez-vous que les dépendances sont installées:")
        print("   pip install python-escpos pyusb")
        return False
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_usb_detection():
    """Test de détection USB directe"""
    print("\n🔌 Test de Détection USB Directe")
    print("=" * 35)
    
    try:
        import usb.core
        
        # Rechercher l'imprimante
        dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)
        
        if dev is None:
            print("❌ Imprimante non détectée")
            print("💡 Vérifications:")
            print("  - Câble USB connecté")
            print("  - Imprimante allumée")
            print("  - Drivers installés (macOS/Linux)")
            
            # Lister tous les périphériques USB
            print("\n📋 Périphériques USB détectés:")
            devices = usb.core.find(find_all=True)
            for device in devices:
                try:
                    print(f"  - VID:0x{device.idVendor:04x} PID:0x{device.idProduct:04x}")
                except:
                    pass
            
            return False
        else:
            print(f"✅ Imprimante détectée")
            print(f"  - VID: 0x{dev.idVendor:04x}")
            print(f"  - PID: 0x{dev.idProduct:04x}")
            print(f"  - Manufacturer: {usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else 'N/A'}")
            print(f"  - Product: {usb.util.get_string(dev, dev.iProduct) if dev.iProduct else 'N/A'}")
            return True
            
    except ImportError:
        print("❌ Module pyusb non installé")
        print("💡 Installez avec: pip install pyusb")
        return False
    except Exception as e:
        print(f"❌ Erreur détection USB: {e}")
        return False

def test_flask_integration():
    """Test de l'intégration Flask"""
    print("\n🌐 Test Intégration Flask")
    print("=" * 25)
    
    try:
        # Créer un contexte d'application minimal
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            print("✅ Application Flask créée")
            
            # Tester l'import du service
            from app.services.printer_service import get_printer_service
            printer_service = get_printer_service()
            
            print("✅ Service d'impression accessible")
            
            # Tester les routes admin
            with app.test_client() as client:
                # Note: Ces tests nécessiteraient une authentification
                print("✅ Client de test créé")
                print("💡 Routes disponibles:")
                print("  - /admin/printer/ (Dashboard)")
                print("  - /admin/printer/status (API)")
                print("  - /admin/printer/test/print (Test)")
                print("  - /admin/printer/test/drawer (Test tiroir)")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur intégration Flask: {e}")
        return False

def main():
    """Fonction principale de test"""
    print(f"🎯 Test Complet Intégration Imprimante")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Tests séquentiels
    tests = [
        ("Détection USB", test_usb_detection),
        ("Service Impression", test_printer_service),
        ("Intégration Flask", test_flask_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHEC"
        print(f"{test_name:20} : {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'intégration est prête.")
        print("\n💡 Prochaines étapes:")
        print("  1. Démarrer l'ERP: python run.py")
        print("  2. Aller sur /admin/printer/ pour tester")
        print("  3. Effectuer une vente pour tester l'automatisation")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
        print("\n💡 Aide au dépannage:")
        print("  - Vérifiez que l'imprimante est connectée et allumée")
        print("  - Installez les dépendances: pip install python-escpos pyusb")
        print("  - Sur Linux: sudo usermod -a -G dialout $USER")
        print("  - Sur macOS: Vérifiez les permissions système")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





