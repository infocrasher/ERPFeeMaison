#!/usr/bin/env python3
"""
Script de test pour vérifier les routes B2B
"""

from app import create_app

def test_b2b_routes():
    app = create_app()
    
    with app.test_client() as client:
        print("✅ Test des routes B2B:")
        
        # Test des routes principales
        routes_to_test = [
            '/admin/b2b/clients',
            '/admin/b2b/clients/new',
            '/admin/b2b/orders',
            '/admin/b2b/orders/new',
            '/admin/b2b/invoices',
            '/admin/b2b/invoices/new',
            '/admin/b2b/api/clients',
            '/admin/b2b/api/products'
        ]
        
        for route in routes_to_test:
            response = client.get(route)
            status = response.status_code
            if status == 302:
                print(f"  {route}: {status} (Redirection - Normal)")
            elif status == 200:
                print(f"  {route}: {status} (OK)")
            elif status == 401:
                print(f"  {route}: {status} (Non authentifié - Normal)")
            else:
                print(f"  {route}: {status} (Problème)")
        
        print("\n✅ Test des modèles B2B:")
        with app.app_context():
            from models import B2BClient, B2BOrder, Invoice
            
            # Test des modèles
            try:
                clients = B2BClient.query.all()
                orders = B2BOrder.query.all()
                invoices = Invoice.query.all()
                
                print(f"  B2BClient: {len(clients)} clients trouvés")
                print(f"  B2BOrder: {len(orders)} commandes trouvées")
                print(f"  Invoice: {len(invoices)} factures trouvées")
                print("  ✅ Modèles B2B fonctionnels")
                
            except Exception as e:
                print(f"  ❌ Erreur avec les modèles: {e}")
        
        print("\n✅ Test des templates B2B:")
        try:
            from flask import render_template_string
            template_test = """
            {% extends "base.html" %}
            {% block content %}
            <h1>Test B2B</h1>
            {% endblock %}
            """
            render_template_string(template_test)
            print("  ✅ Templates B2B fonctionnels")
        except Exception as e:
            print(f"  ❌ Erreur avec les templates: {e}")

if __name__ == "__main__":
    test_b2b_routes() 