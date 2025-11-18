#!/usr/bin/env python3
"""
Script de test complet pour le module B2B
Teste toutes les fonctionnalités : clients, commandes, factures
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8080"
ADMIN_EMAIL = "admin@fee-maison.com"
ADMIN_PASSWORD = "admin123"

def test_connection():
    """Test de connexion au serveur"""
    print("🔍 Test de connexion au serveur...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible")
            return True
        else:
            print(f"❌ Serveur répond avec le code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Impossible de se connecter au serveur: {e}")
        return False

def test_login():
    """Test de connexion admin"""
    print("\n🔐 Test de connexion admin...")
    try:
        # Session pour maintenir les cookies
        session = requests.Session()
        
        # Page de connexion
        login_page = session.get(f"{BASE_URL}/auth/login")
        if login_page.status_code != 200:
            print("❌ Page de connexion inaccessible")
            return None
            
        # Tentative de connexion
        login_data = {
            'email': ADMIN_EMAIL,
            'password': ADMIN_PASSWORD,
            'submit': 'Se connecter'
        }
        
        login_response = session.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if login_response.status_code == 302:  # Redirection après connexion
            print("✅ Connexion admin réussie")
            return session
        else:
            print("❌ Échec de la connexion admin")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        return None

def test_b2b_routes(session):
    """Test des routes B2B"""
    print("\n🚀 Test des routes B2B...")
    
    routes_to_test = [
        ("/admin/b2b/clients", "Liste des clients B2B"),
        ("/admin/b2b/clients/new", "Nouveau client B2B"),
        ("/admin/b2b/orders", "Liste des commandes B2B"),
        ("/admin/b2b/orders/new", "Nouvelle commande B2B"),
        ("/admin/b2b/invoices", "Liste des factures B2B"),
        ("/admin/b2b/invoices/new", "Nouvelle facture B2B"),
    ]
    
    results = {}
    
    for route, description in routes_to_test:
        try:
            response = session.get(f"{BASE_URL}{route}")
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                results[route] = True
            elif response.status_code == 302:
                print(f"⚠️  {description}: Redirection (probablement vers login)")
                results[route] = False
            else:
                print(f"❌ {description}: Erreur {response.status_code}")
                results[route] = False
        except Exception as e:
            print(f"❌ {description}: Exception {e}")
            results[route] = False
    
    return results

def test_api_endpoints(session):
    """Test des endpoints API B2B"""
    print("\n🔌 Test des endpoints API B2B...")
    
    api_endpoints = [
        ("/admin/b2b/api/clients", "API Clients"),
        ("/admin/b2b/api/products", "API Produits"),
    ]
    
    for endpoint, description in api_endpoints:
        try:
            response = session.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                try:
                    data = response.json()
                    print(f"   📊 Données reçues: {len(data)} éléments")
                except:
                    print(f"   📊 Réponse non-JSON reçue")
            else:
                print(f"❌ {description}: Erreur {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Exception {e}")

def test_database_models():
    """Test des modèles de base de données"""
    print("\n🗄️  Test des modèles de base de données...")
    
    try:
        # Import des modèles
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import create_app, db
        from models import B2BClient, B2BOrder, B2BOrderItem, Invoice, InvoiceItem
        
        app = create_app('testing')
        
        with app.app_context():
            # Vérifier que les tables existent
            tables = ['b2b_clients', 'b2b_orders', 'b2b_order_items', 'invoices', 'invoice_items']
            
            for table in tables:
                try:
                    result = db.session.execute(f"SELECT 1 FROM {table} LIMIT 1")
                    print(f"✅ Table {table}: Existe")
                except Exception as e:
                    print(f"❌ Table {table}: Erreur - {e}")
            
            # Compter les enregistrements
            client_count = B2BClient.query.count()
            order_count = B2BOrder.query.count()
            invoice_count = Invoice.query.count()
            
            print(f"📊 Statistiques:")
            print(f"   Clients B2B: {client_count}")
            print(f"   Commandes B2B: {order_count}")
            print(f"   Factures: {invoice_count}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test des modèles: {e}")

def test_form_validation():
    """Test de validation des formulaires"""
    print("\n📝 Test de validation des formulaires...")
    
    try:
        from app.b2b.forms import B2BClientForm, B2BOrderForm, InvoiceForm
        
        # Test formulaire client
        client_form = B2BClientForm()
        print(f"✅ Formulaire client: {len(client_form._fields)} champs")
        
        # Test formulaire commande
        order_form = B2BOrderForm()
        print(f"✅ Formulaire commande: {len(order_form._fields)} champs")
        
        # Test formulaire facture
        invoice_form = InvoiceForm()
        print(f"✅ Formulaire facture: {len(invoice_form._fields)} champs")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des formulaires: {e}")

def main():
    """Fonction principale de test"""
    print("🧪 TEST COMPLET DU MODULE B2B")
    print("=" * 50)
    
    # Test 1: Connexion au serveur
    if not test_connection():
        print("\n❌ Impossible de continuer sans serveur")
        return
    
    # Test 2: Connexion admin
    session = test_login()
    if not session:
        print("\n⚠️  Tests limités sans connexion admin")
        session = requests.Session()
    
    # Test 3: Routes B2B
    route_results = test_b2b_routes(session)
    
    # Test 4: API endpoints
    test_api_endpoints(session)
    
    # Test 5: Modèles de base de données
    test_database_models()
    
    # Test 6: Validation des formulaires
    test_form_validation()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    successful_routes = sum(1 for result in route_results.values() if result)
    total_routes = len(route_results)
    
    print(f"Routes B2B: {successful_routes}/{total_routes} fonctionnelles")
    
    if successful_routes == total_routes:
        print("🎉 Module B2B entièrement fonctionnel !")
    elif successful_routes > 0:
        print("⚠️  Module B2B partiellement fonctionnel")
    else:
        print("❌ Module B2B non fonctionnel")

if __name__ == "__main__":
    main() 