from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, Recipe, RecipeIngredient
from .forms import OrderForm, OrderStatusForm, CustomerOrderForm, ProductionOrderForm
from decorators import admin_required, require_open_cash_session
from decimal import Decimal
from datetime import datetime, timezone
from app.sales.models import CashRegisterSession, CashMovement

orders = Blueprint('orders', __name__)


# ### DEBUT DU BLOC A AJOUTER ###
def check_stock_availability(form_items):
    """
    Vérifie la disponibilité des ingrédients pour une liste d'articles de commande.
    Retourne True si tout est disponible, False sinon, et flashe des messages d'erreur.
    """
    print("\n--- DEBUT DE LA VERIFICATION DE STOCK ---")
    is_sufficient = True
    for item_data in form_items:
        product_id = item_data.get('product')
        quantity_ordered = float(item_data.get('quantity', 0))

        if product_id and quantity_ordered > 0:
            product_fini = Product.query.get(int(product_id))
            print(f"\n[+] Vérification pour le produit fini : {product_fini.name} (Qté: {quantity_ordered})")

            if product_fini and product_fini.recipe_definition:
                recipe = product_fini.recipe_definition
                labo_key = recipe.production_location
                labo_name = "Labo A (Stock Magasin)" if labo_key == 'ingredients_magasin' else "Labo B (Stock Local)"
                print(f"    -> Recette trouvée: '{recipe.name}'. Doit être produit dans: {labo_name} (colonne: {labo_key})")

                for ingredient_in_recipe in recipe.ingredients.all():
                    # --- DEBUT DE LA CORRECTION ---
                    
                    # 1. Calcul de la quantité d'ingrédient nécessaire pour UNE SEULE unité de produit fini
                    # Ex: (4000g de semoule) / (12 galettes) = 333.33g de semoule par galette
                    qty_per_unit = float(ingredient_in_recipe.quantity_needed) / float(recipe.yield_quantity)
                    
                    # 2. Calcul du besoin total pour la commande actuelle
                    # Ex: (333.33g par galette) * (20 galettes commandées) = 6666.6g
                    needed_qty = qty_per_unit * quantity_ordered
                    
                    # --- FIN DE LA CORRECTION ---

                    ingredient_product = ingredient_in_recipe.product
                    
                    print(f"    - Ingrédient requis: {ingredient_product.name}")
                    print(f"      - Quantité par unité de recette: {qty_per_unit:.3f}g") # Log mis à jour
                    print(f"      - Quantité totale nécessaire pour la commande: {needed_qty:.3f}g") # Log mis à jour

                    # Correction du mapping pour le stock
                    location_map = {
                        "ingredients_magasin": "stock_ingredients_magasin",
                        "ingredients_local": "stock_ingredients_local"
                    }
                    stock_attr = location_map.get(labo_key, labo_key)
                    available_stock = ingredient_product.get_stock_by_location(stock_attr)
                    print(f"      - Stock disponible dans '{stock_attr}': {available_stock or 0:.3f}g")
                    
                    if not available_stock or available_stock < needed_qty:
                        is_sufficient = False
                        print(f"      - !!! STOCK INSUFFISANT !!!")
                        flash(f"Stock insuffisant pour '{ingredient_product.name}' dans {labo_name}. "
                              f"Besoin: {needed_qty:.3f}g, Dispo: {available_stock or 0:.3f}g", 'danger')
                    else:
                        print(f"      - Stock OK.")
            else:
                print(f"    -> Pas de recette trouvée pour ce produit. Vérification ignorée.")
    
    print(f"\n--- FIN DE LA VERIFICATION. Résultat final : {is_sufficient} ---")
    return is_sufficient
# ### FIN DU BLOC A AJOUTER ###


@orders.route('/customer/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_customer_order():
    form = CustomerOrderForm()
    
    if form.validate_on_submit():
        try:
            # On appelle notre nouvelle fonction de vérification
            stock_is_sufficient = check_stock_availability(form.items.data)
            initial_status = 'in_production' if stock_is_sufficient else 'pending'

            order = Order(
                user_id=current_user.id,
                order_type='customer_order',
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                customer_address=form.customer_address.data,
                delivery_option=form.delivery_option.data,
                due_date=form.due_date.data,
                delivery_cost=form.delivery_cost.data,
                notes=form.notes.data,
                status=initial_status # On utilise le statut calculé
            )

            db.session.add(order)
            db.session.flush()

            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item_data['quantity'],
                            unit_price=product.price or Decimal('0.00')
                        )
                        db.session.add(order_item)

            order.calculate_total_amount()
            db.session.commit()

            if not stock_is_sufficient:
                flash('Commande créée mais mise en attente en raison d\'un stock insuffisant.', 'warning')
            else:
                 flash('Commande créée et mise en production. Stock suffisant.', 'success')

            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création commande: {e}", exc_info=True)
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")

    return render_template(
        'orders/customer_order_form.html',
        form=form,
        title='Nouvelle Commande Client'
    )

@orders.route('/production/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_production_order():
    form = ProductionOrderForm()
    
    if form.validate_on_submit():
        try:
            # On appelle notre nouvelle fonction de vérification
            stock_is_sufficient = check_stock_availability(form.items.data)
            initial_status = 'in_production' if stock_is_sufficient else 'pending'

            order = Order(
                user_id=current_user.id,
                order_type='counter_production_request',
                due_date=form.production_date.data,
                notes=form.production_notes.data,
                status=initial_status, # On utilise le statut calculé
                # Le reste des champs est None ou 0 par défaut
                delivery_cost=Decimal('0.00'),
                total_amount = Decimal('0.00')
            )

            db.session.add(order)
            db.session.flush()

            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item_data['quantity'],
                            unit_price=Decimal('0.00')
                        )
                        db.session.add(order_item)
            
            db.session.commit()

            if not stock_is_sufficient:
                flash('Ordre de production créé mais mis en attente en raison d\'un stock insuffisant.', 'warning')
            else:
                flash('Ordre de production créé et mis en production. Stock suffisant.', 'success')
                
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création ordre production: {e}", exc_info=True)
            flash(f"Une erreur est survenue lors de la création de l'ordre: {e}", "danger")

    return render_template(
        'orders/production_order_form.html',
        form=form,
        title='Nouvel Ordre de Production'
    )

# ... (Le reste du fichier reste identique, je l'omets pour la clarté mais il est dans ton presse-papier)
@orders.route('/')
@login_required
@admin_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.due_date.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    # Vérifier si une session de caisse est ouverte
    cash_session_open = CashRegisterSession.query.filter_by(is_open=True).first() is not None
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Gestion des Commandes', cash_session_open=cash_session_open)

@orders.route('/customer')
@login_required
@admin_required
def list_customer_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='customer_order').order_by(Order.due_date.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Commandes Client')

@orders.route('/production')
@login_required
@admin_required
def list_production_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='counter_production_request').order_by(Order.created_at.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Ordres de Production')

@orders.route('/api/products')
@login_required
@admin_required
def api_products():
    query = request.args.get('q', '')
    products = Product.query.filter(Product.product_type == 'finished', Product.name.ilike(f'%{query}%')).order_by(Product.name).limit(20).all()
    results = []
    for product in products:
        price = float(product.price or 0.0)
        results.append({'id': str(product.id), 'text': f"{product.name} ({price:.2f} DA / {product.unit})", 'name': product.name, 'price': price, 'unit': product.unit})
    return jsonify({'results': results})

@orders.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    form = OrderForm()
    if form.validate_on_submit():
        try:
            # Note: Cette route devrait aussi utiliser check_stock_availability si elle est utilisée.
            order = Order(user_id=current_user.id, order_type=form.order_type.data, customer_name=form.customer_name.data, customer_phone=form.customer_phone.data, customer_address=form.customer_address.data, delivery_option=form.delivery_option.data, due_date=form.due_date.data, delivery_cost=form.delivery_cost.data, notes=form.notes.data, status='pending')
            db.session.add(order)
            db.session.flush()
            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item_data['quantity'], unit_price=product.price or Decimal('0.00'))
                        db.session.add(order_item)
            order.calculate_total_amount()
            db.session.commit()
            flash('Nouvelle commande créée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")
    return render_template('orders/order_form_multifield.html', form=form, title='Nouvelle Commande')

@orders.route('/<int:order_id>')
@login_required
@admin_required
def view_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    return render_template('orders/view_order.html', order=order, title=f'Détails Commande #{order.id}')

@orders.route('/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    form = OrderForm(obj=order)
    if form.validate_on_submit():
        try:
            # Note: L'édition devrait aussi re-vérifier les stocks.
            for item in order.items:
                db.session.delete(item)
            db.session.flush()
            form.populate_obj(order)
            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item_data['quantity'], unit_price=product.price or Decimal('0.00'))
                        db.session.add(order_item)
            order.calculate_total_amount()
            db.session.commit()
            flash('Commande mise à jour avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la mise à jour: {e}", "danger")
    if request.method == 'GET':
        form.items.entries = []
        for item in order.items:
            form.items.append_entry({'product': str(item.product_id), 'quantity': item.quantity})
    return render_template('orders/order_form_multifield.html', form=form, title=f'Modifier Commande #{order.id}', edit_mode=True)

@orders.route('/<int:order_id>/edit_status', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order_status(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    form = OrderStatusForm(obj=order)
    if form.validate_on_submit():
        previous_status = order.status
        order.status = form.status.data
        if form.notes.data:
            order.notes = (order.notes or '') + f"\n---\nNote du {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}: {form.notes.data}"
        # PATCH : décrémentation du stock ingrédients lors du passage à 'ready_at_shop'
        if previous_status != 'ready_at_shop' and order.status == 'ready_at_shop':
            order.decrement_ingredients_stock_on_production()
            db.session.commit()
            flash('Stock des ingrédients décrémenté selon la recette et la quantité produite (réception au magasin).', 'info')
        else:
            db.session.commit()
        flash('Le statut de la commande a été mis à jour.', 'success')
        return redirect(url_for('orders.view_order', order_id=order.id))
    return render_template('orders/order_status_form.html', form=form, order=order, title='Modifier le Statut')

@orders.route('/calendar')
@login_required
@admin_required
def orders_calendar():
    orders = Order.query.filter(Order.due_date.isnot(None)).all()
    events = []
    for order in orders:
        if order.should_appear_in_calendar():
            events.append({'id': order.id, 'title': f"#{order.id} - {order.customer_name or 'Production'}", 'start': order.due_date.isoformat(), 'url': url_for('orders.view_order', order_id=order.id), 'backgroundColor': '#ffc107' if order.status == 'in_production' else '#6c757d'})
    return render_template('orders/orders_calendar.html', events=events, title="Calendrier des Commandes")

@orders.route('/<int:order_id>/pay', methods=['POST'])
@login_required
@admin_required
@require_open_cash_session
def pay_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Vérifier si déjà encaissée (mouvement de caisse existant pour cette commande)
    existing_movement = CashMovement.query.filter(
        CashMovement.reason.ilike(f'%commande #{order.id}%'),
        CashMovement.amount == order.total_amount
    ).first()
    if existing_movement:
        flash('Cette commande a déjà été encaissée.', 'info')
        return redirect(url_for('orders.view_order', order_id=order.id))
    session = CashRegisterSession.query.filter_by(is_open=True).first()
    if not session:
        flash('Aucune session de caisse ouverte.', 'warning')
        return redirect(url_for('orders.view_order', order_id=order.id))
    # Créer le mouvement de caisse
    movement = CashMovement(
        session_id=session.id,
        created_at=datetime.utcnow(),
        type='entrée',
        amount=order.total_amount,
        reason=f'Paiement commande #{order.id} ({order.delivery_option})',
        notes=f'Encaissement commande client: {order.customer_name or "-"}',
        employee_id=current_user.id
    )
    db.session.add(movement)
    db.session.flush()  # Pour obtenir l'ID du mouvement
    
    # Intégration comptable automatique
    try:
        from app.accounting.services import AccountingIntegrationService
        AccountingIntegrationService.create_sale_entry(
            order_id=order.id,
            sale_amount=float(order.total_amount),
            payment_method='cash',
            description=f'Vente commande #{order.id} - {order.customer_name or "Client"}'
        )
    except Exception as e:
        print(f"Erreur intégration comptable: {e}")
        # On continue même si l'intégration comptable échoue
    
    db.session.commit()
    flash(f'Commande #{order.id} encaissée avec succès ({order.total_amount:.2f} DA).', 'success')
    return redirect(url_for('orders.view_order', order_id=order.id))

@orders.route('/<int:order_id>/assign-deliveryman', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_deliveryman(order_id):
    """Assigner un livreur à une commande prête à livrer"""
    from app.orders.forms import AssignDeliverymanForm
    from app.deliverymen.models import Deliveryman
    from models import DeliveryDebt
    from app.sales.models import CashRegisterSession, CashMovement
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que la commande peut recevoir un livreur
    if order.status != 'ready_at_shop' or order.delivery_option != 'delivery':
        flash('Cette commande ne peut pas recevoir d\'assignation de livreur.', 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    form = AssignDeliverymanForm()
    
    if form.validate_on_submit():
        deliveryman_id = form.deliveryman_id.data
        is_paid = form.is_paid.data
        notes = form.notes.data
        
        if deliveryman_id == 0:
            flash('Veuillez sélectionner un livreur.', 'error')
            return render_template('orders/assign_deliveryman.html', order=order, form=form)
        
        # Assigner le livreur
        order.deliveryman_id = deliveryman_id
        
        if is_paid:
            # Le livreur a payé : marquer comme livrée et encaissée
            order.status = 'delivered'
            
            # Créer le mouvement de caisse si une session est ouverte
            session = CashRegisterSession.query.filter_by(is_open=True).first()
            if session:
                # Calculer le montant à encaisser (produits seulement, sans frais de livraison)
                products_amount = order.total_amount - (order.delivery_cost or 0)
                
                movement = CashMovement(
                    session_id=session.id,
                    created_at=datetime.utcnow(),
                    type='entrée',
                    amount=products_amount,
                    reason=f'Encaissement commande #{order.id} - Livraison payée (hors frais livraison)',
                    notes=f'Livreur: {Deliveryman.query.get(deliveryman_id).name} - Frais livraison: {order.delivery_cost or 0:.2f} DA' + (f' - {notes}' if notes else ''),
                    employee_id=current_user.id
                )
                db.session.add(movement)
                flash(f'Commande #{order.id} assignée à {Deliveryman.query.get(deliveryman_id).name} et encaissée ({products_amount:.2f} DA, frais livraison {order.delivery_cost or 0:.2f} DA pour le livreur).', 'success')
            else:
                flash(f'Commande #{order.id} assignée et livrée, mais aucune session de caisse ouverte pour l\'encaissement.', 'warning')
        else:
            # Le livreur n'a pas payé : marquer comme livrée non payée et créer une dette
            order.status = 'delivered_unpaid'
            
            # Créer une dette livreur (produits seulement, sans frais de livraison)
            products_amount = order.total_amount - (order.delivery_cost or 0)
            
            debt = DeliveryDebt(
                order_id=order.id,
                deliveryman_id=deliveryman_id,
                amount=products_amount,
                paid=False
            )
            db.session.add(debt)
            flash(f'Commande #{order.id} assignée à {Deliveryman.query.get(deliveryman_id).name}. Dette créée: {products_amount:.2f} DA (hors frais livraison {order.delivery_cost or 0:.2f} DA).', 'info')
        
        # Ajouter les notes à la commande si spécifiées
        if notes:
            if order.notes:
                order.notes += f'\n--- Livraison ---\n{notes}'
            else:
                order.notes = f'Livraison: {notes}'
        
        db.session.commit()
        return redirect(url_for('dashboard.shop_dashboard'))
    
    return render_template('orders/assign_deliveryman.html', order=order, form=form)

@orders.route('/<int:order_id>/report-issue', methods=['GET', 'POST'])
@login_required
@admin_required
def report_order_issue(order_id):
    """Signaler un problème de qualité sur une commande"""
    from app.employees.forms import OrderIssueForm
    from app.employees.models import OrderIssue, Employee
    
    order = Order.query.get_or_404(order_id)
    form = OrderIssueForm()
    
    # Récupérer la liste des employés actifs pour le formulaire
    employees = Employee.query.filter_by(is_active=True).all()
    employee_choices = [(str(emp.id), emp.name) for emp in employees]
    
    # Ajouter le champ employee_id au formulaire dynamiquement
    from wtforms import SelectField
    from wtforms.validators import DataRequired
    
    if not hasattr(form, 'employee_id'):
        form.employee_id = SelectField(
            'Employé concerné',
            choices=[('', '-- Sélectionner un employé --')] + employee_choices,
            validators=[DataRequired()]
        )
    else:
        form.employee_id.choices = [('', '-- Sélectionner un employé --')] + employee_choices
    
    if form.validate_on_submit():
        try:
            issue = OrderIssue(
                order_id=order.id,
                employee_id=int(form.employee_id.data),
                issue_type=form.issue_type.data,
                description=form.description.data,
                detected_by=current_user.id,
                is_resolved=False
            )
            
            db.session.add(issue)
            db.session.commit()
            
            flash(f'Problème signalé avec succès sur la commande #{order.id}', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur signalement problème: {e}", exc_info=True)
            flash(f"Erreur lors du signalement: {e}", "danger")
    
    return render_template(
        'orders/report_issue.html',
        form=form,
        order=order,
        title=f'Signaler un Problème - Commande #{order.id}'
    )

@orders.route('/<int:order_id>/resolve-issue/<int:issue_id>', methods=['POST'])
@login_required
@admin_required
def resolve_order_issue(order_id, issue_id):
    """Marquer un problème comme résolu"""
    from app.employees.models import OrderIssue
    from datetime import datetime
    
    order = Order.query.get_or_404(order_id)
    issue = OrderIssue.query.get_or_404(issue_id)
    
    if issue.order_id != order.id:
        flash('Problème non trouvé pour cette commande', 'error')
        return redirect(url_for('orders.view_order', order_id=order.id))
    
    try:
        issue.is_resolved = True
        issue.resolved_at = datetime.utcnow()
        issue.resolution_notes = request.form.get('resolution_notes', '')
        
        db.session.commit()
        flash('Problème marqué comme résolu', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la résolution: {e}', 'error')
    
    return redirect(url_for('orders.view_order', order_id=order.id))

