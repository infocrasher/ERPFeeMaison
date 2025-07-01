from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Product, Order, OrderItem, DeliveryDebt
from datetime import datetime
from decimal import Decimal
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee
from decorators import require_open_cash_session, require_closed_cash_session

sales = Blueprint('sales', __name__, url_prefix='/sales')

def get_open_cash_session():
    """Récupérer la session de caisse ouverte actuelle"""
    return CashRegisterSession.query.filter_by(is_open=True).first()

@sales.route('/pos')
@login_required
@require_open_cash_session
def pos_interface():
    """Interface POS (Point of Sale) pour vente directe"""
    # Récupérer tous les produits finis disponibles en stock comptoir
    products = Product.query.filter(
        Product.product_type == 'finished',
        Product.stock_comptoir > 0
    ).all()
    
    # Préparer les données pour le JavaScript
    products_js = []
    for product in products:
        # Déterminer la catégorie
        category = 'autres'
        if product.category:
            category_name = product.category.name.lower()
            if 'gateau' in category_name or 'gâteau' in category_name:
                category = 'gateaux'
            elif 'msamen' in category_name:
                category = 'msamen'
            elif 'boisson' in category_name or 'thé' in category_name or 'café' in category_name:
                category = 'boissons'
        
        products_js.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price or 0),
            'category': category,
            'stock': int(product.stock_comptoir or 0)
        })
    
    return render_template('sales/pos_interface.html', 
                         products_js=products_js,
                         now=datetime.now())

@sales.route('/api/products')
@login_required
def get_products():
    """API pour récupérer les produits disponibles"""
    products = Product.query.filter(
        Product.product_type == 'finished',
        Product.stock_comptoir > 0
    ).all()
    
    products_data = []
    for product in products:
        # Déterminer la catégorie
        category = 'autres'
        if product.category:
            category_name = product.category.name.lower()
            if 'gateau' in category_name or 'gâteau' in category_name:
                category = 'gateaux'
            elif 'msamen' in category_name:
                category = 'msamen'
            elif 'boisson' in category_name or 'thé' in category_name or 'café' in category_name:
                category = 'boissons'
        
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price or 0),
            'stock': int(product.stock_comptoir or 0),
            'category': category,
            'unit': product.unit,
            'image_filename': product.image_filename
        })
    
    return jsonify(products_data)

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
        
        # Créer la commande de type 'in_store'
        order = Order(
            user_id=current_user.id,
            order_type='in_store',
            customer_name='Vente directe',
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
            
            total_amount += quantity * unit_price
            
            db.session.add(order_item)
            db.session.add(product)
        
        order.total_amount = total_amount
        
        # Créer le mouvement de caisse pour la vente
        cash_session = get_open_cash_session()
        if cash_session:
            cash_movement = CashMovement(
                session_id=cash_session.id,
                created_at=datetime.utcnow(),
                type='entrée',
                amount=total_amount,
                reason=f'Vente commande #{order.id}',
                notes=f'Commande client: {", ".join([f"{item.quantity}x {item.product.name}" for item in order.items])}',
                employee_id=current_user.id
            )
            db.session.add(cash_movement)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Vente finalisée avec succès',
            'order_id': order.id,
            'total': float(total_amount)
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
        
        db.session.commit()
        
        # Calculer le total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        return jsonify({
            'success': True,
            'message': 'Vente enregistrée avec succès',
            'total': total,
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
    if request.method == 'POST':
        initial_amount = float(request.form.get('initial_amount', 0))
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
    return render_template('sales/cash_open.html')

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
    from models import CashMovement, CashRegisterSession
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