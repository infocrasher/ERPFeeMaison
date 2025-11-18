#!/usr/bin/env python3
"""
Script de migration des données clients et fournisseurs
Migre les données existantes vers les nouveaux modèles Supplier et Customer
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire du projet au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_suppliers():
    """Migrer les fournisseurs depuis les achats existants"""
    print("🏭 MIGRATION DES FOURNISSEURS")
    print("=" * 40)
    
    try:
        from app import create_app
        from models import db, Supplier
        from app.purchases.models import Purchase
        
        app = create_app()
        
        with app.app_context():
            # Récupérer tous les achats avec des informations fournisseur
            purchases = Purchase.query.filter(
                Purchase.supplier_name.isnot(None),
                Purchase.supplier_name != ''
            ).all()
            
            print(f"📦 {len(purchases)} achats trouvés avec des fournisseurs")
            
            if not purchases:
                print("ℹ️ Aucun achat avec fournisseur trouvé")
                return True
            
            # Grouper par fournisseur unique (nom + contact)
            suppliers_data = {}
            
            for purchase in purchases:
                # Créer une clé unique basée sur le nom et le contact
                key = (
                    purchase.supplier_name.strip().lower(),
                    (purchase.supplier_contact or '').strip().lower()
                )
                
                if key not in suppliers_data:
                    suppliers_data[key] = {
                        'company_name': purchase.supplier_name.strip(),
                        'contact_person': purchase.supplier_contact,
                        'phone': purchase.supplier_phone,
                        'email': purchase.supplier_email,
                        'address': purchase.supplier_address,
                        'purchases': []
                    }
                
                suppliers_data[key]['purchases'].append(purchase)
                
                # Mettre à jour avec les informations les plus récentes
                if purchase.supplier_phone and not suppliers_data[key]['phone']:
                    suppliers_data[key]['phone'] = purchase.supplier_phone
                if purchase.supplier_email and not suppliers_data[key]['email']:
                    suppliers_data[key]['email'] = purchase.supplier_email
                if purchase.supplier_address and not suppliers_data[key]['address']:
                    suppliers_data[key]['address'] = purchase.supplier_address
            
            print(f"🔍 {len(suppliers_data)} fournisseurs uniques identifiés")
            
            # Créer les enregistrements Supplier
            created_count = 0
            updated_count = 0
            
            for supplier_data in suppliers_data.values():
                # Vérifier si le fournisseur existe déjà
                existing = Supplier.query.filter_by(
                    company_name=supplier_data['company_name']
                ).first()
                
                if existing:
                    print(f"⚠️ Fournisseur existant: {existing.company_name}")
                    # Mettre à jour les achats pour pointer vers ce fournisseur
                    for purchase in supplier_data['purchases']:
                        if not purchase.supplier_id:
                            purchase.supplier_id = existing.id
                            updated_count += 1
                else:
                    # Créer un nouveau fournisseur
                    supplier = Supplier(
                        company_name=supplier_data['company_name'],
                        contact_person=supplier_data['contact_person'],
                        phone=supplier_data['phone'],
                        email=supplier_data['email'],
                        address=supplier_data['address'],
                        supplier_type='general',  # Type par défaut
                        is_active=True
                    )
                    
                    db.session.add(supplier)
                    db.session.flush()  # Pour obtenir l'ID
                    
                    # Lier les achats à ce fournisseur
                    for purchase in supplier_data['purchases']:
                        purchase.supplier_id = supplier.id
                    
                    created_count += 1
                    print(f"✅ Créé: {supplier.company_name} (ID: {supplier.id})")
            
            # Sauvegarder les changements
            db.session.commit()
            
            print(f"\n📊 RÉSULTATS MIGRATION FOURNISSEURS:")
            print(f"   ✅ {created_count} nouveaux fournisseurs créés")
            print(f"   🔄 {updated_count} achats liés à des fournisseurs existants")
            print(f"   📦 {sum(len(data['purchases']) for data in suppliers_data.values())} achats traités")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration des fournisseurs: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_customers():
    """Migrer les clients depuis les commandes existantes"""
    print("\n👥 MIGRATION DES CLIENTS")
    print("=" * 40)
    
    try:
        from app import create_app
        from models import db, Customer, Order
        
        app = create_app()
        
        with app.app_context():
            # Récupérer toutes les commandes avec des informations client
            orders = Order.query.filter(
                Order.customer_name.isnot(None),
                Order.customer_name != '',
                Order.customer_phone.isnot(None),
                Order.customer_phone != ''
            ).all()
            
            print(f"📦 {len(orders)} commandes trouvées avec des clients")
            
            if not orders:
                print("ℹ️ Aucune commande avec client trouvée")
                return True
            
            # Grouper par client unique (téléphone comme clé principale)
            customers_data = {}
            
            for order in orders:
                # Nettoyer le téléphone pour la clé
                phone_key = order.customer_phone.replace(' ', '').replace('-', '').replace('.', '')
                
                if phone_key not in customers_data:
                    # Séparer le nom complet en prénom et nom
                    name_parts = order.customer_name.strip().split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    else:
                        first_name = name_parts[0] if name_parts else 'Client'
                        last_name = 'Inconnu'
                    
                    customers_data[phone_key] = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': order.customer_phone,
                        'address': order.customer_address,
                        'orders': []
                    }
                
                customers_data[phone_key]['orders'].append(order)
                
                # Mettre à jour avec les informations les plus récentes
                if order.customer_address and not customers_data[phone_key]['address']:
                    customers_data[phone_key]['address'] = order.customer_address
            
            print(f"🔍 {len(customers_data)} clients uniques identifiés")
            
            # Créer les enregistrements Customer
            created_count = 0
            updated_count = 0
            
            for customer_data in customers_data.values():
                # Vérifier si le client existe déjà (par téléphone)
                existing = Customer.query.filter_by(
                    phone=customer_data['phone']
                ).first()
                
                if existing:
                    print(f"⚠️ Client existant: {existing.full_name}")
                    # Mettre à jour les commandes pour pointer vers ce client
                    for order in customer_data['orders']:
                        if not order.customer_id:
                            order.customer_id = existing.id
                            updated_count += 1
                else:
                    # Créer un nouveau client
                    customer = Customer(
                        first_name=customer_data['first_name'],
                        last_name=customer_data['last_name'],
                        phone=customer_data['phone'],
                        address=customer_data['address'],
                        customer_type='regular',  # Type par défaut
                        preferred_delivery='pickup',  # Préférence par défaut
                        is_active=True
                    )
                    
                    db.session.add(customer)
                    db.session.flush()  # Pour obtenir l'ID
                    
                    # Lier les commandes à ce client
                    for order in customer_data['orders']:
                        order.customer_id = customer.id
                        # Mettre à jour la date de dernière commande
                        if not customer.last_order_date or order.created_at > customer.last_order_date:
                            customer.last_order_date = order.created_at
                    
                    created_count += 1
                    print(f"✅ Créé: {customer.full_name} (ID: {customer.id})")
            
            # Sauvegarder les changements
            db.session.commit()
            
            print(f"\n📊 RÉSULTATS MIGRATION CLIENTS:")
            print(f"   ✅ {created_count} nouveaux clients créés")
            print(f"   🔄 {updated_count} commandes liées à des clients existants")
            print(f"   📦 {sum(len(data['orders']) for data in customers_data.values())} commandes traitées")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration des clients: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Vérifier les résultats de la migration"""
    print("\n🔍 VÉRIFICATION DE LA MIGRATION")
    print("=" * 40)
    
    try:
        from app import create_app
        from models import db, Supplier, Customer
        from app.purchases.models import Purchase
        from models import Order
        
        app = create_app()
        
        with app.app_context():
            # Statistiques fournisseurs
            total_suppliers = Supplier.query.count()
            active_suppliers = Supplier.query.filter_by(is_active=True).count()
            purchases_with_supplier = Purchase.query.filter(Purchase.supplier_id.isnot(None)).count()
            purchases_without_supplier = Purchase.query.filter(Purchase.supplier_id.is_(None)).count()
            
            print(f"🏭 FOURNISSEURS:")
            print(f"   📊 Total: {total_suppliers}")
            print(f"   ✅ Actifs: {active_suppliers}")
            print(f"   🔗 Achats liés: {purchases_with_supplier}")
            print(f"   ⚠️ Achats non liés: {purchases_without_supplier}")
            
            # Statistiques clients
            total_customers = Customer.query.count()
            active_customers = Customer.query.filter_by(is_active=True).count()
            orders_with_customer = Order.query.filter(Order.customer_id.isnot(None)).count()
            orders_without_customer = Order.query.filter(Order.customer_id.is_(None)).count()
            
            print(f"\n👥 CLIENTS:")
            print(f"   📊 Total: {total_customers}")
            print(f"   ✅ Actifs: {active_customers}")
            print(f"   🔗 Commandes liées: {orders_with_customer}")
            print(f"   ⚠️ Commandes non liées: {orders_without_customer}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


def main():
    """Fonction principale"""
    print("🚀 MIGRATION CLIENTS ET FOURNISSEURS - ERP FÉE MAISON")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("")
    
    print("⚠️ ATTENTION: Cette migration va créer des enregistrements Supplier et Customer")
    print("   basés sur les données existantes dans Purchase et Order.")
    print("   Les données originales seront conservées pour compatibilité.")
    print("")
    
    response = input("Continuer la migration ? (oui/non): ").lower().strip()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("❌ Migration annulée par l'utilisateur")
        return False
    
    print("\n🚀 DÉBUT DE LA MIGRATION")
    print("=" * 30)
    
    # Migration des fournisseurs
    suppliers_success = migrate_suppliers()
    
    # Migration des clients
    customers_success = migrate_customers()
    
    # Vérification
    verification_success = verify_migration()
    
    print("\n" + "=" * 60)
    if suppliers_success and customers_success and verification_success:
        print("🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
        print("\n✅ Prochaines étapes:")
        print("   1. Vérifiez les données dans /admin/suppliers/ et /admin/customers/")
        print("   2. Testez la création de nouveaux achats et commandes")
        print("   3. Les anciens champs (supplier_name, customer_name) sont conservés")
        print("   4. Vous pouvez maintenant utiliser les sélecteurs dans les formulaires")
        return True
    else:
        print("❌ MIGRATION ÉCHOUÉE")
        print("   Vérifiez les erreurs ci-dessus et corrigez avant de relancer")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





