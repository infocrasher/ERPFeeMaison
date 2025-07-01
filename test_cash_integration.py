#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration des ventes dans les mouvements de caisse
"""
from app import create_app
from extensions import db
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee
from models import Product
from datetime import datetime

app = create_app()

def test_cash_integration():
    """Test de l'intégration des ventes dans les mouvements de caisse"""
    
    with app.app_context():
        print("🔄 Test d'intégration des ventes dans les mouvements de caisse...")
        
        # Vérifier qu'il y a au moins un employé et des produits
        employees = Employee.query.all()
        products = Product.query.filter_by(product_type='finished').all()
        
        if not employees:
            print("❌ Aucun employé trouvé. Impossible de tester.")
            return
        
        if not products:
            print("❌ Aucun produit fini trouvé. Impossible de tester.")
            return
        
        employee = employees[0]
        product = products[0]
        print(f"✅ Employé de test: {employee.name}")
        print(f"✅ Produit de test: {product.name}")
        
        # 1. Nettoyer les sessions ouvertes
        print("\n📋 Test 1: Nettoyage des sessions")
        open_sessions = CashRegisterSession.query.filter_by(is_open=True).all()
        for session in open_sessions:
            session.is_open = False
            session.closed_at = datetime.utcnow()
        db.session.commit()
        print(f"   Sessions fermées: {len(open_sessions)}")
        
        # 2. Ouvrir une nouvelle session
        print("\n📋 Test 2: Ouverture d'une session")
        session = CashRegisterSession(
            opened_at=datetime.utcnow(),
            initial_amount=1000.0,
            opened_by_id=employee.id,
            is_open=True
        )
        db.session.add(session)
        db.session.commit()
        print(f"   ✅ Session ouverte (ID: {session.id})")
        
        # 3. Simuler une vente POS
        print("\n📋 Test 3: Simulation d'une vente POS")
        try:
            # Décrémenter le stock
            initial_stock = product.stock_comptoir
            product.stock_comptoir -= 2
            print(f"   Stock avant: {initial_stock}, après: {product.stock_comptoir}")
            
            # Créer le mouvement de caisse
            sale_amount = 2 * (product.price or 100)
            cash_movement = CashMovement(
                session_id=session.id,
                created_at=datetime.utcnow(),
                type='entrée',
                amount=sale_amount,
                reason=f'Vente POS - 2 article(s)',
                notes=f'Vente directe: 2x {product.name}',
                employee_id=employee.id
            )
            db.session.add(cash_movement)
            db.session.commit()
            print(f"   ✅ Mouvement de vente créé: {sale_amount} DA")
        except Exception as e:
            print(f"   ❌ Erreur lors de la vente: {e}")
            return
        
        # 4. Vérifier les mouvements
        print("\n📋 Test 4: Vérification des mouvements")
        movements = CashMovement.query.filter_by(session_id=session.id).all()
        print(f"   Mouvements dans la session: {len(movements)}")
        
        for movement in movements:
            print(f"   - {movement.type}: {movement.amount} DA ({movement.reason})")
        
        # 5. Vérifier le solde théorique
        print("\n📋 Test 5: Vérification du solde théorique")
        total_in = sum(m.amount for m in session.movements if m.type == 'entrée')
        total_out = sum(m.amount for m in session.movements if m.type == 'sortie')
        theoretical_balance = session.initial_amount + total_in - total_out
        
        print(f"   Montant initial: {session.initial_amount} DA")
        print(f"   Total entrées: {total_in} DA")
        print(f"   Total sorties: {total_out} DA")
        print(f"   Solde théorique: {theoretical_balance} DA")
        
        expected_balance = 1000 + float(sale_amount)
        if abs(float(theoretical_balance) - expected_balance) < 0.01:
            print("   ✅ Calcul correct")
        else:
            print(f"   ❌ Calcul incorrect (attendu: {expected_balance})")
        
        # 6. Simuler une vente commande
        print("\n📋 Test 6: Simulation d'une vente commande")
        try:
            order_amount = 150.0
            cash_movement_order = CashMovement(
                session_id=session.id,
                created_at=datetime.utcnow(),
                type='entrée',
                amount=order_amount,
                reason=f'Vente commande #123',
                notes=f'Commande client: 1x {product.name}',
                employee_id=employee.id
            )
            db.session.add(cash_movement_order)
            db.session.commit()
            print(f"   ✅ Mouvement de commande créé: {order_amount} DA")
        except Exception as e:
            print(f"   ❌ Erreur lors de la commande: {e}")
        
        # 7. Vérification finale
        print("\n📋 Test 7: Vérification finale")
        movements = CashMovement.query.filter_by(session_id=session.id).all()
        print(f"   Total mouvements: {len(movements)}")
        
        sales_movements = [m for m in movements if 'Vente POS' in m.reason]
        order_movements = [m for m in movements if 'Vente commande' in m.reason]
        
        print(f"   Mouvements de vente POS: {len(sales_movements)}")
        print(f"   Mouvements de commandes: {len(order_movements)}")
        
        # 8. Fermer la session
        print("\n📋 Test 8: Fermeture de session")
        session.closed_at = datetime.utcnow()
        session.closing_amount = theoretical_balance + order_amount
        session.closed_by_id = employee.id
        session.is_open = False
        db.session.commit()
        print("   ✅ Session fermée")
        
        print("\n🎉 Tests d'intégration terminés!")
        print("\n📝 Résumé:")
        print(f"   - Session créée: {session.id}")
        print(f"   - Ventes POS: {len(sales_movements)}")
        print(f"   - Commandes: {len(order_movements)}")
        print(f"   - Total mouvements: {len(movements)}")
        print(f"   - Solde final: {session.closing_amount} DA")

if __name__ == "__main__":
    test_cash_integration() 