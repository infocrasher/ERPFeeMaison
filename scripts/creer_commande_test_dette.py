#!/usr/bin/env python3
"""
Script pour créer une commande de test avec une dette livreur à une date antérieure
Permet de tester le calcul du CA avec les dettes livreurs
"""
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Order, OrderItem, Product, DeliveryDebt
from app.deliverymen.models import Deliveryman

def creer_commande_test_dette():
    """Crée une commande de test avec une dette livreur à une date antérieure"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("CRÉATION COMMANDE TEST - DETTE LIVREUR")
        print("=" * 80)
        print()
        
        # Demander la date de livraison souhaitée
        print("📅 Date de livraison souhaitée (format: YYYY-MM-DD, ex: 2025-12-03):")
        date_input = input("> ").strip()
        
        # Si pas de date fournie, utiliser 03/12/2025 par défaut
        if not date_input:
            date_input = "2025-12-03"
            print(f"   → Utilisation de la date par défaut: {date_input}")
        
        try:
            target_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("❌ Format de date invalide. Utilisation de 2025-12-03 par défaut.")
            target_date = datetime(2025, 12, 3)
        
        print(f"📅 Date de livraison : {target_date.date()}")
        print()
        
        # Récupérer un produit fini pour la commande
        product = Product.query.filter_by(product_type='finished').first()
        if not product:
            print("❌ Aucun produit fini trouvé. Créez d'abord un produit fini.")
            return
        
        print(f"📦 Produit utilisé : {product.name} (ID: {product.id})")
        print()
        
        # Récupérer un livreur
        deliveryman = Deliveryman.query.first()
        if not deliveryman:
            print("❌ Aucun livreur trouvé. Créez d'abord un livreur.")
            return
        
        print(f"🚚 Livreur utilisé : {deliveryman.name} (ID: {deliveryman.id})")
        print()
        
        # Montant de la commande (300 DA comme demandé)
        quantity = 2
        unit_price = Decimal('150.00')
        total_amount = Decimal('300.00')  # Montant fixe de 300 DA
        
        print(f"💰 Montant commande : {total_amount} DA ({quantity} x {unit_price} DA)")
        print()
        
        # Créer la commande avec due_date à la date cible
        order = Order(
            user_id=1,  # Premier utilisateur
            order_type='customer_order',
            customer_name='Client Test Dette',
            customer_phone='0555123456',
            customer_address='Adresse test',
            delivery_option='delivery',
            due_date=target_date,  # Date prévue de livraison
            delivery_cost=Decimal('0.00'),
            status='delivered_unpaid',  # Statut livrée non payée
            total_amount=total_amount,
            payment_status='pending',
            created_at=target_date - timedelta(days=1)  # Créée 1 jour avant la livraison
        )
        
        db.session.add(order)
        db.session.flush()  # Pour obtenir l'ID de la commande
        
        # Créer l'article de commande
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price
        )
        db.session.add(order_item)
        
        # Créer la dette livreur à la date cible
        debt = DeliveryDebt(
            order_id=order.id,
            deliveryman_id=deliveryman.id,
            amount=total_amount,
            paid=False,
            created_at=target_date  # Date de livraison (où le livreur a été assigné)
        )
        db.session.add(debt)
        
        db.session.commit()
        
        print("=" * 80)
        print("✅ COMMANDE ET DETTE CRÉÉES AVEC SUCCÈS")
        print("=" * 80)
        print()
        print(f"📋 Commande créée :")
        print(f"   ID : #{order.id}")
        print(f"   Client : {order.customer_name}")
        print(f"   Date création : {order.created_at.date()}")
        print(f"   Date prévue livraison (due_date) : {order.due_date.date()}")
        print(f"   Montant : {total_amount} DA")
        print(f"   Statut : {order.status}")
        print()
        print(f"💳 Dette livreur créée :")
        print(f"   ID : #{debt.id}")
        print(f"   Commande : #{order.id}")
        print(f"   Livreur : {deliveryman.name}")
        print(f"   Montant : {debt.amount} DA")
        print(f"   Date création dette : {debt.created_at.date()}")
        print(f"   Statut : {'Payée' if debt.paid else 'Non payée'}")
        print()
        print("=" * 80)
        print("💡 PROCHAINES ÉTAPES")
        print("=" * 80)
        print()
        print(f"1. Vérifier le CA pour le {target_date.date()}:")
        print(f"   python3 scripts/test_calcul_ca_dette_livreur.py")
        print()
        print(f"2. Encaissez la dette dans l'interface ERP:")
        print(f"   /sales/cash/delivery_debts")
        print()
        print(f"3. Vérifier que le CA reste à la date de livraison après paiement:")
        print(f"   python3 scripts/test_calcul_ca_dette_livreur.py")
        print()

if __name__ == '__main__':
    creer_commande_test_dette()

