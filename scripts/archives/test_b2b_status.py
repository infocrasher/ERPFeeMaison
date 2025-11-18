#!/usr/bin/env python3
"""
Test simple du statut des routes B2B
"""

from app import create_app

def test_b2b_status():
    app = create_app()
    
    with app.test_client() as client:
        print("🔍 Test du statut des routes B2B:")
        
        routes = [
            '/admin/b2b/clients',
            '/admin/b2b/orders',
            '/admin/b2b/invoices'
        ]
        
        for route in routes:
            response = client.get(route)
            print(f"  {route}: {response.status_code}")
            
        print("\n✅ Si tous les statuts sont 302 (redirection), c'est normal (authentification requise)")

if __name__ == "__main__":
    test_b2b_status() 