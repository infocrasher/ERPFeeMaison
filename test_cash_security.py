#!/usr/bin/env python3
"""
Script de test pour vérifier la sécurisation du workflow de caisse
"""
from app import create_app
from extensions import db
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee
from datetime import datetime

app = create_app()

def test_cash_security():
    """Test de la sécurisation du workflow de caisse"""
    
    with app.app_context():
        print("🔒 Test de sécurisation du workflow de caisse...")
        
        # Vérifier qu'il y a au moins un employé
        employees = Employee.query.all()
        if not employees:
            print("❌ Aucun employé trouvé. Impossible de tester.")
            return
        
        employee = employees[0]
        print(f"✅ Employé de test: {employee.name}")
        
        # 1. Test: Aucune session ouverte au départ
        print("\n📋 Test 1: Vérification état initial")
        open_sessions = CashRegisterSession.query.filter_by(is_open=True).all()
        print(f"   Sessions ouvertes: {len(open_sessions)}")
        
        if len(open_sessions) > 0:
            print("   ⚠️  Il y a déjà des sessions ouvertes. Nettoyage...")
            for session in open_sessions:
                session.is_open = False
                session.closed_at = datetime.utcnow()
            db.session.commit()
            print("   ✅ Sessions fermées")
        
        # 2. Test: Ouverture d'une session
        print("\n📋 Test 2: Ouverture d'une session")
        try:
            session = CashRegisterSession(
                opened_at=datetime.utcnow(),
                initial_amount=1000.0,
                opened_by_id=employee.id,
                is_open=True
            )
            db.session.add(session)
            db.session.commit()
            print(f"   ✅ Session ouverte (ID: {session.id})")
        except Exception as e:
            print(f"   ❌ Erreur lors de l'ouverture: {e}")
            return
        
        # 3. Test: Tentative d'ouverture d'une deuxième session
        print("\n📋 Test 3: Tentative d'ouverture d'une deuxième session")
        try:
            session2 = CashRegisterSession(
                opened_at=datetime.utcnow(),
                initial_amount=500.0,
                opened_by_id=employee.id,
                is_open=True
            )
            db.session.add(session2)
            db.session.commit()
            print("   ❌ Deuxième session ouverte (ERREUR!)")
        except Exception as e:
            print(f"   ✅ Deuxième session bloquée (attendu): {e}")
        
        # 4. Test: Ajout de mouvements
        print("\n📋 Test 4: Ajout de mouvements")
        try:
            movement1 = CashMovement(
                session_id=session.id,
                created_at=datetime.utcnow(),
                type='entrée',
                amount=150.0,
                reason='Vente',
                employee_id=employee.id
            )
            db.session.add(movement1)
            
            movement2 = CashMovement(
                session_id=session.id,
                created_at=datetime.utcnow(),
                type='sortie',
                amount=50.0,
                reason='Achat fournitures',
                employee_id=employee.id
            )
            db.session.add(movement2)
            
            db.session.commit()
            print("   ✅ Mouvements ajoutés")
        except Exception as e:
            print(f"   ❌ Erreur lors de l'ajout de mouvements: {e}")
        
        # 5. Test: Calcul du solde théorique
        print("\n📋 Test 5: Calcul du solde théorique")
        total_in = sum(m.amount for m in session.movements if m.type == 'entrée')
        total_out = sum(m.amount for m in session.movements if m.type == 'sortie')
        theoretical_balance = session.initial_amount + total_in - total_out
        
        print(f"   Montant initial: {session.initial_amount} DA")
        print(f"   Total entrées: {total_in} DA")
        print(f"   Total sorties: {total_out} DA")
        print(f"   Solde théorique: {theoretical_balance} DA")
        
        expected_balance = 1000 + 150 - 50
        if theoretical_balance == expected_balance:
            print("   ✅ Calcul correct")
        else:
            print(f"   ❌ Calcul incorrect (attendu: {expected_balance})")
        
        # 6. Test: Fermeture de session
        print("\n📋 Test 6: Fermeture de session")
        try:
            session.closed_at = datetime.utcnow()
            session.closing_amount = theoretical_balance
            session.closed_by_id = employee.id
            session.is_open = False
            db.session.commit()
            print("   ✅ Session fermée")
        except Exception as e:
            print(f"   ❌ Erreur lors de la fermeture: {e}")
        
        # 7. Test: Vérification qu'aucune session n'est ouverte
        print("\n📋 Test 7: Vérification finale")
        open_sessions = CashRegisterSession.query.filter_by(is_open=True).all()
        print(f"   Sessions ouvertes: {len(open_sessions)}")
        
        if len(open_sessions) == 0:
            print("   ✅ Aucune session ouverte (correct)")
        else:
            print("   ❌ Sessions encore ouvertes (ERREUR!)")
        
        print("\n🎉 Tests de sécurisation terminés!")
        print("\n📝 Prochaines étapes:")
        print("   1. Lancer Flask: flask run")
        print("   2. Tester l'interface web")
        print("   3. Vérifier que les décorateurs bloquent les actions non autorisées")

if __name__ == "__main__":
    test_cash_security() 