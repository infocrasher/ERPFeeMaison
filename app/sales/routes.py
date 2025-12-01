from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Product, Order, OrderItem, DeliveryDebt, Category
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, or_
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee
from decorators import require_open_cash_session, require_closed_cash_session

sales = Blueprint('sales', __name__, url_prefix='/sales')

def get_open_cash_session():
    """Récupérer la session de caisse ouverte actuelle"""
    return CashRegisterSession.query.filter_by(is_open=True).first()

def get_reserved_stock_by_product():
    """
    Calcule les quantités réservées par produit pour les commandes client en attente.
    Les produits des commandes 'waiting_for_pickup' ou 'ready_at_shop' sont réservés
    et ne doivent pas apparaître au PDV.
    """
    reserved = {}
    # Statuts où les produits sont réservés pour le client
    reserved_statuses = ['waiting_for_pickup', 'ready_at_shop', 'ready_to_deliver']
    
    # Requête pour récupérer les quantités réservées par produit
    reserved_items = db.session.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label('reserved_qty')
    ).join(Order).filter(
        Order.order_type == 'customer_order',
        Order.status.in_(reserved_statuses)
    ).group_by(OrderItem.product_id).all()
    
    for product_id, qty in reserved_items:
        reserved[product_id] = float(qty)
    
    return reserved

@sales.route('/pos')
@login_required
@require_open_cash_session
def pos_interface():
    """Interface POS (Point of Sale) pour vente directe"""
    # Récupérer les catégories visibles au POV
    pos_categories = Category.query.filter(Category.show_in_pos == True).order_by(Category.name).all()
    
    # Récupérer uniquement les produits finis avec stock_comptoir > 0
    # et appartenant à une catégorie visible au POV
    category_ids = [c.id for c in pos_categories]
    products = Product.query.filter(
        Product.product_type == 'finished',  # Uniquement produits finis
        Product.stock_comptoir > 0,  # Uniquement avec stock disponible
        Product.category_id.in_(category_ids) if category_ids else Product.category_id.isnot(None)
    ).all()
    
    # 🆕 Calculer les quantités réservées pour les commandes client en attente
    reserved_stock = get_reserved_stock_by_product()
    
    # Préparer les données pour le JavaScript
    products_js = []
    for product in products:
        # Calculer le stock disponible (stock réel - réservé pour commandes client)
        reserved_qty = reserved_stock.get(product.id, 0)
        stock_comptoir = float(product.stock_comptoir or 0)
        available_stock = max(0, stock_comptoir - reserved_qty)
        
        # Ne pas afficher les produits entièrement réservés
        if available_stock <= 0:
            continue
        
        # Utiliser le nom réel de la catégorie (slugifié pour le frontend)
        category_slug = 'autres'
        if product.category:
            # Créer un slug à partir du nom de la catégorie
            category_slug = product.category.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')
        
        products_js.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price or 0),
            'category': category_slug,
            'category_id': product.category_id,
            'stock': available_stock,  # Stock disponible (moins les réservations)
            'unit': product.display_sale_unit  # Utiliser l'unité de vente
        })
    
    # Préparer les catégories pour le frontend
    categories_js = [{'id': c.id, 'name': c.name, 'slug': c.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')} 
                     for c in pos_categories]
    
    return render_template('sales/pos_interface.html', 
                         products_js=products_js,
                         categories_js=categories_js,
                         now=datetime.now())

@sales.route('/api/products')
@login_required
def get_products():
    """API pour récupérer les produits disponibles avec leurs catégories"""
    # Récupérer les catégories visibles au POV
    pos_categories = Category.query.filter(Category.show_in_pos == True).order_by(Category.name).all()
    category_ids = [c.id for c in pos_categories]
    
    # Récupérer uniquement les produits finis avec stock_comptoir > 0
    products = Product.query.filter(
        Product.product_type == 'finished',  # Uniquement produits finis
        Product.stock_comptoir > 0,  # Uniquement avec stock disponible
        Product.category_id.in_(category_ids) if category_ids else Product.category_id.isnot(None)
    ).all()
    
    # 🆕 Calculer les quantités réservées pour les commandes client en attente
    reserved_stock = get_reserved_stock_by_product()
    
    products_data = []
    for product in products:
        # Calculer le stock disponible (stock réel - réservé pour commandes client)
        reserved_qty = reserved_stock.get(product.id, 0)
        stock_comptoir = float(product.stock_comptoir or 0)
        available_stock = max(0, stock_comptoir - reserved_qty)
        
        # Ne pas inclure les produits entièrement réservés
        if available_stock <= 0:
            continue
        
        # Utiliser le slug de la catégorie réelle
        category_slug = 'autres'
        if product.category:
            category_slug = product.category.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')
        
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price or 0),
            'stock': available_stock,  # Stock disponible (moins les réservations)
            'stock_comptoir': stock_comptoir,  # Stock réel (pour afficher rupture si = 0)
            'category': category_slug,
            'category_id': product.category_id,
            'unit': product.display_sale_unit,  # Utiliser l'unité de vente
            'image_filename': product.image_filename
        })
    
    # Inclure aussi les catégories dans la réponse
    categories_data = [{'id': c.id, 'name': c.name, 'slug': c.name.lower().replace(' ', '-').replace('é', 'e').replace('è', 'e')} 
                       for c in pos_categories]
    
    return jsonify({
        'products': products_data,
        'categories': categories_data
    })

@sales.route('/api/favorites')
@login_required
def get_favorite_products():
    """API pour récupérer les produits favoris (les plus vendus sur 30 jours)"""
    # Date limite : 30 jours en arrière
    date_limit = datetime.utcnow() - timedelta(days=30)
    
    # Récupérer les catégories visibles au POV
    pos_categories = Category.query.filter(Category.show_in_pos == True).all()
    category_ids = [c.id for c in pos_categories]
    
    # Requête pour obtenir les produits les plus vendus (top 20)
    top_products = db.session.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(Order).filter(
        Order.order_type == 'in_store',
        Order.created_at >= date_limit,
        OrderItem.product_id.in_(
            db.session.query(Product.id).filter(
                or_(
                    Product.product_type == 'finished',
                    Product.can_be_sold == True
                ),
                Product.category_id.in_(category_ids) if category_ids else Product.category_id.isnot(None)
            )
        )
    ).group_by(OrderItem.product_id).order_by(func.sum(OrderItem.quantity).desc()).limit(20).all()
    
    # Extraire les IDs des produits favoris
    favorite_product_ids = [row[0] for row in top_products]
    
    return jsonify({
        'favorite_product_ids': favorite_product_ids
    })

@sales.route('/api/complete-sale', methods=['POST'])
@login_required
@require_open_cash_session
def complete_sale():
    """Finaliser une vente et mettre à jour les stocks"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'success': False, 'message': 'Aucun article dans la vente'}), 400
        
        # Récupérer les informations client si disponibles
        customer_name = data.get('customer_name', 'Vente directe')
        customer_phone = data.get('customer_phone')
        customer_id = data.get('customer_id')
        
        # Créer la commande de type 'in_store'
        order = Order(
            user_id=current_user.id,
            order_type='in_store',
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_id=customer_id,
            due_date=datetime.utcnow(),
            status='completed',
            total_amount=0.0
        )
        
        # Ajouter l'order à la session et flusher pour obtenir l'ID
        db.session.add(order)
        db.session.flush()  # Ceci génère l'ID sans commiter
        
        total_amount = Decimal('0.0')
        
        # Ajouter les articles et décrémenter les stocks
        for item_data in items:
            product_id = item_data['product_id']
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data['unit_price']))
            
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'message': f'Produit {product_id} non trouvé'}), 400
            
            # Vérifier le stock
            if product.stock_comptoir < float(quantity):
                return jsonify({'success': False, 'message': f'Stock insuffisant pour {product.name}'}), 400
            
            # Créer l'article de commande (maintenant order.id existe)
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price
            )
            
            # Décrémenter le stock comptoir
            product.update_stock_by_location('stock_comptoir', -float(quantity))
            
            # Décrémenter la valeur du stock
            pmp = product.cost_price or Decimal('0.0')
            value_decrement = quantity * pmp
            product.total_stock_value = (product.total_stock_value or Decimal('0.0')) - value_decrement
            
            # DÉCRÉMENTER LES CONSOMMABLES selon la catégorie
            if product.category:
                from app.consumables.models import ConsumableCategory
                consumable_category = ConsumableCategory.query.filter(
                    ConsumableCategory.product_category_id == product.category.id,
                    ConsumableCategory.is_active == True
                ).first()
                
                if consumable_category:
                    # Calculer les consommables nécessaires
                    consumables_needed = consumable_category.calculate_consumables_needed(int(quantity))
                    
                    for consumable_product, qty in consumables_needed:
                        if consumable_product:
                            # Décrémenter le stock consommables
                            consumable_product.update_stock_by_location('stock_consommables', -float(qty))
                            print(f"Décrémentation consommable (PDV): {consumable_product.name} - {qty} {consumable_product.unit}")
            
            total_amount += quantity * unit_price
            
            db.session.add(order_item)
            db.session.add(product)
        
        order.total_amount = total_amount
        amount_received = Decimal(str(data.get('amount_received') or total_amount)).quantize(Decimal('0.01'))
        if amount_received < 0:
            amount_received = Decimal('0.00')
        if amount_received < total_amount:
            order.amount_paid = amount_received.quantize(Decimal('0.01'))
        else:
            order.amount_paid = total_amount
        order.update_payment_status()
        
        # Créer le mouvement de caisse pour la vente
        cash_session = get_open_cash_session()
        if cash_session:
            amount_for_cash = amount_received if amount_received <= total_amount else total_amount
            cash_movement = CashMovement(
                session_id=cash_session.id,
                created_at=datetime.utcnow(),
                type='entrée',
                amount=float(amount_for_cash),
                reason=f'Vente commande #{order.id}',
                notes=f'Commande client: {", ".join([f"{item.quantity}x {item.product.name}" for item in order.items])}',
                employee_id=current_user.id
            )
            db.session.add(cash_movement)
        
        db.session.commit()
        
        # Intégration POS : Impression ticket + ouverture tiroir pour vente complète
        try:
            from app.services.printer_service import get_printer_service
            printer_service = get_printer_service()
            
            # Calculer la monnaie à rendre
            change_amount = float(amount_received - total_amount) if amount_received > total_amount else 0
            
            # Imprimer le ticket avec les infos de paiement
            printer_service.print_ticket(
                order.id, 
                priority=1,
                employee_name=current_user.name if hasattr(current_user, 'name') else current_user.username,
                amount_received=float(amount_received),
                change_amount=change_amount
            )
            printer_service.open_cash_drawer(priority=1)
            
            print(f"🖨️ Impression ticket et ouverture tiroir déclenchées pour vente #{order.id}")
        except Exception as e:
            print(f"⚠️ Erreur intégration POS: {e}")
            # Ne pas faire échouer la vente si l'impression échoue
        
        return jsonify({
            'success': True, 
            'message': 'Vente finalisée avec succès',
            'order_id': order.id,
            'total': float(total_amount),
            'change': float(amount_received - total_amount) if amount_received > total_amount else 0
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la finalisation de la vente: {str(e)}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@sales.route('/history')
@login_required
def sales_history():
    """Historique des ventes"""
    # Récupérer les ventes directes
    sales_orders = Order.query.filter_by(order_type='in_store').order_by(Order.created_at.desc()).limit(50).all()
    
    return render_template('sales/history.html', sales_orders=sales_orders)

@sales.route('/reports')
@login_required
def sales_reports():
    """Rapports de vente"""
    # Statistiques de base
    total_sales = Order.query.filter_by(order_type='in_store').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(order_type='in_store').scalar() or 0
    
    # Ventes du jour
    today = datetime.utcnow().date()
    today_sales = Order.query.filter(
        Order.order_type == 'in_store',
        db.func.date(Order.created_at) == today
    ).count()
    
    today_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.order_type == 'in_store',
        db.func.date(Order.created_at) == today
    ).scalar() or 0
    
    return render_template('sales/reports.html',
                         total_sales=total_sales,
                         total_revenue=float(total_revenue),
                         today_sales=today_sales,
                         today_revenue=float(today_revenue))

@sales.route('/pos/checkout', methods=['POST'])
@login_required
@require_open_cash_session
def process_sale():
    """Traiter une vente et décrémenter le stock"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'success': False, 'error': 'Données invalides'}), 400
        
        items = data['items']
        if not items:
            return jsonify({'success': False, 'error': 'Panier vide'}), 400
        
        # Vérifier le stock avant de procéder
        for item in items:
            product = Product.query.get(item['id'])
            if not product:
                return jsonify({'success': False, 'error': f'Produit {item["id"]} non trouvé'}), 404
            
            if product.stock_comptoir < item['quantity']:
                return jsonify({
                    'success': False, 
                    'error': f'Stock insuffisant pour {product.name} (disponible: {product.stock_comptoir})'
                }), 400
        
        # Récupérer la session de caisse ouverte
        cash_session = get_open_cash_session()
        if not cash_session:
            return jsonify({'success': False, 'error': 'Aucune session de caisse ouverte'}), 400
        
        # Créer la vente et enregistrer le mouvement de caisse
        total_amount = 0
        for item in items:
            product = Product.query.get(item['id'])
            product.stock_comptoir -= item['quantity']
            total_amount += item['price'] * item['quantity']
            
            # Log de la décrémentation
            print(f"VENTE: {item['quantity']} x {product.name} (Stock comptoir: {product.stock_comptoir})")
        
        # Créer le mouvement de caisse pour la vente
        cash_movement = CashMovement(
            session_id=cash_session.id,
            created_at=datetime.utcnow(),
            type='entrée',
            amount=total_amount,
            reason=f'Vente POS - {len(items)} article(s)',
            notes=f'Vente directe: {", ".join([f"{item["quantity"]}x {Product.query.get(item["id"]).name}" for item in items])}',
            employee_id=current_user.id
        )
        db.session.add(cash_movement)
        db.session.flush()  # Pour obtenir l'ID du mouvement
        
        # Intégration comptable automatique
        try:
            from app.accounting.services import AccountingIntegrationService
            AccountingIntegrationService.create_cash_movement_entry(
                cash_movement_id=cash_movement.id,
                amount=total_amount,
                movement_type='in',
                description=f'Vente POS - {len(items)} article(s)'
            )
        except Exception as e:
            print(f"Erreur intégration comptable: {e}")
            # On continue même si l'intégration comptable échoue
        
        # Créer une commande temporaire pour l'impression du ticket
        temp_order = Order(
            user_id=current_user.id,
            order_type='pos_direct',
            customer_name='Vente POS',
            due_date=datetime.utcnow(),
            status='completed',
            total_amount=total_amount
        )
        db.session.add(temp_order)
        db.session.flush()  # Pour obtenir l'ID
        
        # Ajouter les articles à la commande temporaire
        for item in items:
            product = Product.query.get(item['id'])
            order_item = OrderItem(
                order_id=temp_order.id,
                product_id=item['id'],
                quantity=item['quantity'],
                unit_price=item['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Calculer le total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # Récupérer les infos de paiement si disponibles
        amount_received = float(data.get('amount_received', total))
        change_amount = max(0, amount_received - total)
        
        # Intégration POS : Impression ticket + ouverture tiroir pour vente POS
        try:
            from app.services.printer_service import get_printer_service
            printer_service = get_printer_service()
            
            # Imprimer le ticket avec les infos de paiement
            printer_service.print_ticket(
                temp_order.id, 
                priority=1,
                employee_name=current_user.name if hasattr(current_user, 'name') else current_user.username,
                amount_received=amount_received,
                change_amount=change_amount
            )
            printer_service.open_cash_drawer(priority=1)
            
            print(f"🖨️ Impression ticket et ouverture tiroir déclenchées pour vente POS #{temp_order.id}")
        except Exception as e:
            print(f"⚠️ Erreur intégration POS: {e}")
            # Ne pas faire échouer la vente si l'impression échoue
        
        return jsonify({
            'success': True,
            'message': 'Vente enregistrée avec succès',
            'total': total,
            'change': change_amount,
            'items_count': len(items)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la vente: {e}")
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500

# --- ROUTES DE CAISSE ---

@sales.route('/cash/open', methods=['GET', 'POST'])
@login_required
@require_closed_cash_session
def open_cash_register():
    last_closed_session = (
        CashRegisterSession.query
        .filter(CashRegisterSession.is_open == False)
        .order_by(CashRegisterSession.closed_at.desc())
        .first()
    )

    default_initial_amount = 0.0
    if last_closed_session:
        if last_closed_session.closing_amount is not None:
            default_initial_amount = float(last_closed_session.closing_amount)
        elif last_closed_session.initial_amount is not None:
            default_initial_amount = float(last_closed_session.initial_amount)

    if request.method == 'POST':
        raw_amount = request.form.get('initial_amount', '').strip()
        try:
            initial_amount = float(raw_amount) if raw_amount else default_initial_amount
        except ValueError:
            initial_amount = default_initial_amount

        session = CashRegisterSession(
            opened_at=datetime.utcnow(),
            initial_amount=initial_amount,
            opened_by_id=current_user.id,
            is_open=True
        )
        db.session.add(session)
        db.session.commit()
        flash('Caisse ouverte avec succès.', 'success')
        return redirect(url_for('sales.list_cash_sessions'))

    return render_template('sales/cash_open.html', default_initial_amount=default_initial_amount)

@sales.route('/cash/close', methods=['GET', 'POST'])
@login_required
@require_open_cash_session
def close_cash_register():
    session = get_open_cash_session()
    if request.method == 'POST':
        closing_amount = float(request.form.get('closing_amount', 0))
        session.closed_at = datetime.utcnow()
        session.closing_amount = closing_amount
        session.closed_by_id = current_user.id
        session.is_open = False
        db.session.commit()
        flash('Caisse clôturée avec succès.', 'success')
        return redirect(url_for('sales.list_cash_sessions'))
    
    # Calculer les totaux pour l'affichage
    total_cash_in = sum(m.amount for m in session.movements if m.type == 'entrée')
    total_cash_out = sum(m.amount for m in session.movements if m.type == 'sortie')
    
    return render_template('sales/cash_close.html', 
                         session=session,
                         total_cash_in=total_cash_in,
                         total_cash_out=total_cash_out)

@sales.route('/api/open-drawer', methods=['POST'])
@login_required
def open_drawer():
    """API pour ouvrir le tiroir-caisse (utilisé lors du comptage/fermeture)"""
    try:
        from app.services.printer_service import get_printer_service
        printer_service = get_printer_service()
        
        success = printer_service.open_cash_drawer(priority=1)
        
        if success:
            print(f"💰 Ouverture tiroir-caisse demandée par {current_user.username}")
            return jsonify({'success': True, 'message': 'Tiroir-caisse ouvert'})
        else:
            return jsonify({'success': False, 'message': 'Impossible d\'ouvrir le tiroir-caisse'}), 500
    except Exception as e:
        print(f"⚠️ Erreur ouverture tiroir: {e}")
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@sales.route('/cash/movements/new', methods=['GET', 'POST'])
@login_required
@require_open_cash_session
def new_cash_movement():
    session = get_open_cash_session()
    if request.method == 'POST':
        movement_type = request.form.get('type')
        amount = float(request.form.get('amount', 0))
        reason = request.form.get('reason', '')
        notes = request.form.get('notes', '')
        movement = CashMovement(
            session_id=session.id,
            created_at=datetime.utcnow(),
            type=movement_type,
            amount=amount,
            reason=reason,
            notes=notes,
            employee_id=current_user.id
        )
        db.session.add(movement)
        db.session.flush()  # Pour obtenir l'ID du mouvement
        
        # Intégration comptable automatique
        try:
            from app.accounting.services import AccountingIntegrationService
            AccountingIntegrationService.create_cash_movement_entry(
                cash_movement_id=movement.id,
                amount=amount,
                movement_type='in' if movement_type == 'entrée' else 'out',
                description=f'{reason} - {notes}'
            )
        except Exception as e:
            print(f"Erreur intégration comptable: {e}")
            # On continue même si l'intégration comptable échoue
        
        db.session.commit()
        flash('Mouvement de caisse ajouté.', 'success')
        return redirect(url_for('sales.list_cash_movements'))
    return render_template('sales/cash_movement_form.html', session=session)

@sales.route('/cash/sessions')
@login_required
def list_cash_sessions():
    sessions = CashRegisterSession.query.order_by(CashRegisterSession.opened_at.desc()).all()
    return render_template('sales/cash_sessions.html', sessions=sessions)

@sales.route('/cash/movements')
@login_required
def list_cash_movements():
    session_id = request.args.get('session_id')
    query = CashMovement.query.order_by(CashMovement.created_at.desc())
    if session_id:
        query = query.filter_by(session_id=session_id)
    movements = query.all()
    return render_template('sales/cash_movements.html', movements=movements)

@sales.route('/cash/status')
@login_required
def cash_status():
    """Afficher l'état actuel de la caisse"""
    session = get_open_cash_session()
    if session:
        # Calculer les totaux
        total_cash_in = sum(m.amount for m in session.movements if m.type == 'entrée')
        total_cash_out = sum(m.amount for m in session.movements if m.type == 'sortie')
        theoretical_balance = session.initial_amount + total_cash_in - total_cash_out
        
        return render_template('sales/cash_status.html', 
                             session=session,
                             total_cash_in=total_cash_in,
                             total_cash_out=total_cash_out,
                             theoretical_balance=theoretical_balance)
    else:
        flash('Aucune session de caisse ouverte.', 'info')
        return redirect(url_for('sales.open_cash_register'))

@sales.route('/cash/delivery_debts')
@login_required
def list_delivery_debts():
    """Affiche la liste des dettes livreurs (total par livreur, détail par commande)"""
    # Récupérer toutes les dettes non payées, groupées par livreur
    dettes = DeliveryDebt.query.filter_by(paid=False).all()
    # Regrouper par livreur
    dettes_par_livreur = {}
    for dette in dettes:
        livreur = dette.deliveryman
        if livreur.id not in dettes_par_livreur:
            dettes_par_livreur[livreur.id] = {
                'livreur': livreur,
                'total': 0,
                'dettes': []
            }
        dettes_par_livreur[livreur.id]['total'] += float(dette.amount)
        dettes_par_livreur[livreur.id]['dettes'].append(dette)
    # Trier par montant dû décroissant
    dettes_liste = sorted(dettes_par_livreur.values(), key=lambda x: x['total'], reverse=True)
    return render_template('sales/delivery_debts.html', dettes_liste=dettes_liste, title='Dettes Livreurs')

@sales.route('/cash/delivery_debts/<int:debt_id>/pay', methods=['POST'])
@login_required
@require_open_cash_session
def pay_delivery_debt(debt_id):
    """Encaisse une dette livreur, crée le mouvement de caisse, solde la dette"""
    from .models import CashMovement, CashRegisterSession
    debt = DeliveryDebt.query.get_or_404(debt_id)
    if debt.paid:
        flash('Cette dette a déjà été réglée.', 'info')
        return redirect(url_for('sales.list_delivery_debts'))
    session = CashRegisterSession.query.filter_by(is_open=True).first()
    if not session:
        flash('Aucune session de caisse ouverte.', 'warning')
        return redirect(url_for('sales.list_delivery_debts'))
    # Créer le mouvement de caisse
    movement = CashMovement(
        session_id=session.id,
        created_at=datetime.utcnow(),
        type='entrée',
        amount=debt.amount,
        reason=f'Paiement dette commande #{debt.order_id} par livreur {debt.deliveryman.name}',
        notes=f'Encaissement dette livreur (commande #{debt.order_id})',
        employee_id=current_user.id
    )
    db.session.add(movement)
    # Marquer la dette comme payée
    debt.paid = True
    debt.paid_at = datetime.utcnow()
    debt.session_id = session.id
    db.session.commit()
    flash(f'Dette de {debt.amount:.2f} DA pour la commande #{debt.order_id} réglée par {debt.deliveryman.name}.', 'success')
    return redirect(url_for('sales.list_delivery_debts'))

@sales.route('/cash/cashout', methods=['GET', 'POST'])
@login_required
@require_open_cash_session
def cashout():
    """Dépôt de caisse vers banque (Cashout)"""
    session = get_open_cash_session()
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        notes = request.form.get('notes', '')
        
        if amount <= 0:
            flash('Le montant doit être supérieur à 0.', 'error')
            return redirect(url_for('sales.cashout'))
        
        # Calculer le solde théorique actuel de la caisse
        total_cash_in = sum(m.amount for m in session.movements if m.type == 'entrée')
        total_cash_out = sum(m.amount for m in session.movements if m.type == 'sortie')
        theoretical_balance = session.initial_amount + total_cash_in - total_cash_out
        
        if amount > theoretical_balance:
            flash(f'Montant insuffisant en caisse. Solde disponible: {theoretical_balance:.2f} DZD', 'error')
            return redirect(url_for('sales.cashout'))
        
        # Créer le mouvement de caisse (sortie)
        cash_movement = CashMovement(
            session_id=session.id,
            created_at=datetime.utcnow(),
            type='sortie',
            amount=amount,
            reason='Dépôt en banque (Cashout)',
            notes=f'Dépôt bancaire - {notes}' if notes else 'Dépôt bancaire',
            employee_id=current_user.id
        )
        db.session.add(cash_movement)
        db.session.flush()  # Pour obtenir l'ID du mouvement
        
        # Intégration comptable automatique (Caisse → Banque)
        try:
            from app.accounting.services import AccountingIntegrationService
            AccountingIntegrationService.create_bank_deposit_entry(
                cash_movement_id=cash_movement.id,
                amount=amount,
                description=f'Dépôt caisse vers banque - {notes}' if notes else 'Dépôt caisse vers banque'
            )
        except Exception as e:
            print(f"Erreur intégration comptable cashout: {e}")
            # On continue même si l'intégration comptable échoue
        
        db.session.commit()
        
        # Intégration POS : Impression reçu + ouverture tiroir pour cashout
        try:
            from app.services.printer_service import get_printer_service
            printer_service = get_printer_service()
            
            # Imprimer le reçu de cashout et ouvrir le tiroir
            printer_service.print_cashout_receipt(
                amount=amount,
                notes=notes,
                employee_name=current_user.username,
                priority=1
            )
            printer_service.open_cash_drawer(priority=1)
            
            print(f"🖨️ Impression reçu et ouverture tiroir déclenchées pour cashout de {amount:.2f} DA")
        except Exception as e:
            print(f"⚠️ Erreur intégration POS: {e}")
            # Ne pas faire échouer le cashout si l'impression échoue
        
        flash(f'Dépôt de {amount:.2f} DZD effectué avec succès vers la banque.', 'success')
        return redirect(url_for('sales.cash_status'))
    
    # Calculer les totaux pour l'affichage
    total_cash_in = sum(m.amount for m in session.movements if m.type == 'entrée')
    total_cash_out = sum(m.amount for m in session.movements if m.type == 'sortie')
    theoretical_balance = session.initial_amount + total_cash_in - total_cash_out
    
    return render_template('sales/cashout.html', 
                         session=session,
                         theoretical_balance=theoretical_balance) 