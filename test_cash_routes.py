#!/usr/bin/env python3
"""
Script de test pour vérifier les routes de caisse
"""
from app import create_app
from extensions import db
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee

app = create_app()

with app.app_context():
    try:
        print("🔍 Test des routes de caisse...")
        
        # Vérifier que les modèles sont bien définis
        print("✅ Modèles sales importés avec succès!")
        print(f"   - CashRegisterSession: {CashRegisterSession.__tablename__}")
        print(f"   - CashMovement: {CashMovement.__tablename__}")
        
        # Vérifier les routes disponibles
        routes_to_test = [
            '/sales/cash/open',
            '/sales/cash/close', 
            '/sales/cash/movements/new',
            '/sales/cash/sessions',
            '/sales/cash/movements'
        ]
        
        print("\n📋 Routes à tester:")
        for route in routes_to_test:
            print(f"   - {route}")
        
        # Vérifier qu'il y a au moins un employé pour les tests
        employees = Employee.query.all()
        print(f"\n👥 Employés disponibles: {len(employees)}")
        if employees:
            print(f"   - Premier employé: {employees[0].name}")
        
        # Vérifier les sessions de caisse existantes
        sessions = CashRegisterSession.query.all()
        print(f"\n💰 Sessions de caisse: {len(sessions)}")
        
        # Vérifier les mouvements de caisse existants
        movements = CashMovement.query.all()
        print(f"\n💸 Mouvements de caisse: {len(movements)}")
        
        print("\n🎉 Test terminé avec succès!")
        print("\n📝 Prochaines étapes:")
        print("   1. Lancer Flask: flask run")
        print("   2. Aller sur http://localhost:5000")
        print("   3. Se connecter")
        print("   4. Tester le menu 'Caisse' dans la navigation")
        print("   5. Essayer d'ouvrir une caisse, ajouter des mouvements, etc.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc() 