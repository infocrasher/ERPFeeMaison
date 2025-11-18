#!/usr/bin/env python3
"""
Script de test avec authentification pour vérifier les routes B2B
"""

from app import create_app
from models import User

def test_b2b_authenticated():
    app = create_app()
    
    with app.test_client() as client:
        print("✅ Test des routes B2B avec authentification:")
        
        # Créer un utilisateur de test
        with app.app_context():
            # Vérifier si l'utilisateur admin existe
            admin = User.query.filter_by(email='admin@fee-maison.com').first()
            if not admin:
                print("  ⚠️  Utilisateur admin non trouvé, création d'un utilisateur de test...")
                admin = User(
                    email='admin@fee-maison.com',
                    username='admin',
                    role='admin'
                )
                admin.set_password('admin123')
                from models import db
                db.session.add(admin)
                db.session.commit()
                print("  ✅ Utilisateur admin créé")
            else:
                print("  ✅ Utilisateur admin trouvé")
        
        # Se connecter
        print("\n🔐 Connexion...")
        response = client.post('/auth/login', data={
            'email': 'admin@fee-maison.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        if response.status_code == 200:
            print("  ✅ Connexion réussie")
            
            # Test des routes principales avec authentification
            routes_to_test = [
                '/admin/b2b/clients',
                '/admin/b2b/clients/new',
                '/admin/b2b/orders',
                '/admin/b2b/orders/new',
                '/admin/b2b/invoices',
                '/admin/b2b/invoices/new'
            ]
            
            print("\n📋 Test des pages principales:")
            for route in routes_to_test:
                response = client.get(route)
                status = response.status_code
                if status == 200:
                    print(f"  {route}: {status} ✅")
                elif status == 302:
                    print(f"  {route}: {status} ⚠️ (Redirection)")
                else:
                    print(f"  {route}: {status} ❌")
            
            # Test des API endpoints
            print("\n🔌 Test des API endpoints:")
            api_routes = [
                '/admin/b2b/api/clients',
                '/admin/b2b/api/products'
            ]
            
            for route in api_routes:
                response = client.get(route)
                status = response.status_code
                if status == 200:
                    print(f"  {route}: {status} ✅")
                    try:
                        import json
                        data = json.loads(response.data)
                        print(f"    Données: {len(data)} éléments")
                    except:
                        print(f"    Données: Format non-JSON")
                elif status == 302:
                    print(f"  {route}: {status} ⚠️ (Redirection)")
                else:
                    print(f"  {route}: {status} ❌")
            
            # Test de création d'un client B2B
            print("\n➕ Test de création d'un client B2B:")
            response = client.post('/admin/b2b/clients/new', data={
                'company_name': 'Test Company',
                'contact_person': 'Test Contact',
                'email': 'test@company.com',
                'phone': '0123456789',
                'payment_terms': '30',
                'credit_limit': '10000.00',
                'is_active': 'y'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("  ✅ Création de client réussie")
            else:
                print(f"  ❌ Erreur création client: {response.status_code}")
        
        else:
            print("  ❌ Échec de la connexion")

if __name__ == "__main__":
    test_b2b_authenticated() 