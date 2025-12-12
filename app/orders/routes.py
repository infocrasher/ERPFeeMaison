from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, Recipe, RecipeIngredient
from .forms import OrderForm, OrderStatusForm, CustomerOrderForm, ProductionOrderForm
from decorators import admin_required, require_open_cash_session
from decimal import Decimal, InvalidOperation
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

            advance_payment = Decimal(str(form.advance_payment.data or 0))
            if advance_payment < 0:
                advance_payment = Decimal('0.00')
            total_amount = Decimal(order.total_amount or 0)
            if total_amount <= 0:
                advance_payment = Decimal('0.00')
            elif advance_payment > total_amount:
                advance_payment = total_amount
            advance_payment = advance_payment.quantize(Decimal('0.01'))
            order.amount_paid = advance_payment
            order.update_payment_status()

            if advance_payment > Decimal('0.00'):
                cash_session = CashRegisterSession.query.filter_by(is_open=True).first()
                if cash_session:
                    movement = CashMovement(
                        session_id=cash_session.id,
                        created_at=datetime.utcnow(),
                        type='entrée',
                        amount=float(advance_payment),
                        reason=f'Acompte commande #{order.id}',
                        notes=f'Acompte enregistré lors de la création - {order.customer_name or "-"}',
                        employee_id=current_user.id
                    )
                    db.session.add(movement)
                else:
                    flash("Acompte enregistré sans mouvement de caisse (aucune session ouverte). Pensez à encaisser l'acompte dès qu'une caisse est ouverte.", 'warning')

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
    from sqlalchemy import or_
    from models import OrderItem
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    
    # Requête de base : commandes client uniquement
    query = Order.query.filter_by(order_type='customer_order')
    
    # Recherche par nom client, téléphone ou produit
    if search_query:
        # Recherche dans les noms de clients
        name_filter = Order.customer_name.ilike(f'%{search_query}%')
        
        # Recherche dans les téléphones
        phone_filter = Order.customer_phone.ilike(f'%{search_query}%')
        
        # Recherche dans les produits (via OrderItem)
        product_ids = db.session.query(OrderItem.order_id).join(Product).filter(
            Product.name.ilike(f'%{search_query}%')
        ).subquery()
        product_filter = Order.id.in_(db.session.query(product_ids.c.order_id))
        
        # Combiner les filtres avec OR
        query = query.filter(or_(name_filter, phone_filter, product_filter))
    
    pagination = query.order_by(Order.due_date.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', 
                         orders_pagination=pagination, 
                         title='Commandes Client',
                         search_query=search_query)

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
    """
    Route legacy redirigée pour éviter la confusion.
    Utiliser désormais la création dédiée client.
    """
    flash("Cette page est redirigée vers la création d'une commande client.", "info")
    return redirect(url_for('orders.new_customer_order'))

@orders.route('/<int:order_id>')
@login_required
@admin_required
def view_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    cash_session_open = CashRegisterSession.query.filter_by(is_open=True).first() is not None
    return render_template(
        'orders/view_order.html',
        order=order,
        cash_session_open=cash_session_open,
        title=f'Détails Commande #{order.id}'
    )

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

@orders.route('/customer/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer_order(order_id):
    """Modifier une commande client (produits, date, etc.)"""
    order = db.session.get(Order, order_id) or abort(404)
    
    # Vérifier que c'est bien une commande client
    if order.order_type != 'customer_order':
        flash('Cette route est uniquement pour les commandes client.', 'error')
        return redirect(url_for('orders.view_order', order_id=order.id))
    
    form = CustomerOrderForm(obj=order)
    
    if form.validate_on_submit():
        try:
            # Vérifier les stocks avant de modifier
            stock_is_sufficient = check_stock_availability(form.items.data)
            
            # Supprimer les anciens items
            for item in order.items:
                db.session.delete(item)
            db.session.flush()
            
            # Mettre à jour les informations de base
            order.customer_name = form.customer_name.data
            order.customer_phone = form.customer_phone.data
            order.customer_address = form.customer_address.data
            order.delivery_zone = form.delivery_zone.data
            order.delivery_option = form.delivery_option.data
            order.due_date = form.due_date.data  # Modifier la date
            order.delivery_cost = form.delivery_cost.data or Decimal('0.00')
            order.notes = form.notes.data

            # 🔄 SYNCHRONISATION AUTOMATIQUE STATUT <-> LIVRAISON
            if order.delivery_option == 'delivery' and order.status == 'waiting_for_pickup':
                order.status = 'ready_at_shop'
                flash('Statut mis à jour : En attente -> Prêt (Livraison)', 'info')
            elif order.delivery_option == 'pickup' and order.status == 'ready_at_shop':
                order.status = 'waiting_for_pickup'
                flash('Statut mis à jour : Prêt -> En attente (Retrait)', 'info')
            
            # Ajouter les nouveaux items
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
            
            # Recalculer le total
            order.calculate_total_amount()
            
            # Mettre à jour le statut si stock insuffisant
            if not stock_is_sufficient and order.status != 'pending':
                order.status = 'pending'
                flash('Stock insuffisant. La commande a été mise en attente.', 'warning')
            
            db.session.commit()
            flash('Commande modifiée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la modification de la commande: {str(e)}")
            flash(f"Une erreur est survenue lors de la modification: {str(e)}", "danger")
    
    # Pré-remplir le formulaire avec les données existantes
    if request.method == 'GET':
        # S'assurer que les champs de base sont pré-remplis
        form.customer_name.data = order.customer_name
        form.customer_phone.data = order.customer_phone
        form.customer_address.data = order.customer_address
        form.delivery_zone.data = order.delivery_zone
        form.delivery_option.data = order.delivery_option
        form.due_date.data = order.due_date
        form.delivery_cost.data = order.delivery_cost or Decimal('0.00')
        form.notes.data = order.notes
        
        # Pré-remplir les items - IMPORTANT: vider d'abord puis reconstruire
        form.items.entries = []
        
        # Récupérer les choix de produits une seule fois
        from .forms import get_sellable_products
        products = get_sellable_products()
        product_choices = [('', '-- Choisir un produit --')]
        for product in products:
            price = product.price or 0.0
            label = f"{product.name} ({price:.2f} DA / {product.unit})"
            product_choices.append((str(product.id), label))
        
        # Ajouter chaque item de la commande
        for item in order.items:
            item_entry = form.items.append_entry()
            # Définir les valeurs après avoir créé l'entrée
            item_entry.product.data = str(item.product_id)
            item_entry.quantity.data = item.quantity
            # Réinitialiser les choix de produits pour cet item
            item_entry.product.choices = product_choices
    
    return render_template('orders/customer_order_form.html', 
                         form=form, 
                         order=order,
                         title=f'Modifier Commande #{order.id}',
                         edit_mode=True)

@orders.route('/production/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_production_order(order_id):
    """Modifier un ordre de production (produits, date, etc.)"""
    order = db.session.get(Order, order_id) or abort(404)
    
    # Vérifier que c'est bien un ordre de production
    if order.order_type != 'counter_production_request':
        flash('Cette route est uniquement pour les ordres de production.', 'error')
        return redirect(url_for('orders.view_order', order_id=order.id))
    
    form = ProductionOrderForm()
    
    if form.validate_on_submit():
        try:
            # Vérifier les stocks avant de modifier
            stock_is_sufficient = check_stock_availability(form.items.data)
            
            # Supprimer les anciens items
            for item in order.items:
                db.session.delete(item)
            db.session.flush()
            
            # Mettre à jour les informations de base
            order.due_date = form.production_date.data  # Modifier la date
            order.notes = form.production_notes.data
            
            # Ajouter les nouveaux items
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
            
            # Mettre à jour le statut si stock insuffisant
            if not stock_is_sufficient and order.status != 'pending':
                order.status = 'pending'
                flash('Stock insuffisant. L\'ordre a été mis en attente.', 'warning')
            
            db.session.commit()
            flash('Ordre de production modifié avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la modification de l'ordre de production: {str(e)}")
            flash(f"Une erreur est survenue lors de la modification: {str(e)}", "danger")
    
    # Pré-remplir le formulaire avec les données existantes
    if request.method == 'GET':
        form.production_date.data = order.due_date
        form.production_notes.data = order.notes
        
        # Pré-remplir les items avec les choix de produits
        form.items.entries = []
        # Récupérer les choix de produits une seule fois
        from .forms import get_sellable_products
        products = get_sellable_products()
        product_choices = [('', '-- Choisir un produit --')]
        for product in products:
            label = f"{product.name} (Unité: {product.unit})"
            product_choices.append((str(product.id), label))
        
        # Ajouter chaque item de l'ordre
        for item in order.items:
            item_entry = form.items.append_entry()
            # Définir les valeurs après avoir créé l'entrée
            item_entry.product.data = str(item.product_id)
            item_entry.quantity.data = item.quantity
            # Réinitialiser les choix de produits pour cet item
            item_entry.product.choices = product_choices
    
    return render_template('orders/production_order_form.html', 
                         form=form, 
                         order=order,
                         title=f'Modifier Ordre de Production #{order.id}',
                         edit_mode=True)

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
    outstanding = order.balance_due
    if outstanding <= 0:
        flash('Cette commande est déjà totalement réglée.', 'info')
        return redirect(url_for('orders.view_order', order_id=order.id))

    amount_raw = request.form.get('amount_received')
    if not amount_raw or not amount_raw.strip():
        if Decimal(order.amount_paid or 0) == 0:
            amount_received = outstanding
        else:
            flash('Veuillez saisir le montant à encaisser.', 'warning')
            return redirect(url_for('orders.view_order', order_id=order.id))
    else:
        amount_raw = amount_raw.strip().replace(',', '.')
        try:
            amount_received = Decimal(amount_raw)
        except InvalidOperation:
            flash('Montant invalide.', 'danger')
            return redirect(url_for('orders.view_order', order_id=order.id))
        if amount_received <= 0:
            flash('Le montant saisi doit être supérieur à zéro.', 'warning')
            return redirect(url_for('orders.view_order', order_id=order.id))

    amount_received = amount_received.quantize(Decimal('0.01'))
    outstanding = order.balance_due
    if outstanding <= 0:
        flash('Cette commande est déjà totalement réglée.', 'info')
        return redirect(url_for('orders.view_order', order_id=order.id))

    amount_to_record = amount_received if amount_received <= outstanding else outstanding
    amount_to_record = amount_to_record.quantize(Decimal('0.01'))
    change_amount = (amount_received - amount_to_record).quantize(Decimal('0.01')) if amount_received > outstanding else Decimal('0.00')

    session = CashRegisterSession.query.filter_by(is_open=True).first()
    if not session:
        flash('Aucune session de caisse ouverte.', 'warning')
        return redirect(url_for('orders.view_order', order_id=order.id))

    # Créer le mouvement de caisse
    movement = CashMovement(
        session_id=session.id,
        created_at=datetime.utcnow(),
        type='entrée',
        amount=float(amount_to_record),
        reason=f'Encaissement commande #{order.id}',
        notes=f'Paiement {"partiel" if amount_to_record < outstanding else "final"} - {order.customer_name or "-"}',
        employee_id=current_user.id
    )
    db.session.add(movement)

    previous_payment_status = order.payment_status
    order.amount_paid = (Decimal(order.amount_paid or 0) + amount_to_record).quantize(Decimal('0.01'))
    order.update_payment_status()

    # ✅ CORRECTION : Changer le statut de la commande après encaissement
    status_changed = False
    previous_status = None
    if order.status in ['waiting_for_pickup', 'delivered_unpaid'] and order.payment_status == 'paid':
        previous_status = order.status
        order.status = 'delivered'
        status_changed = True
        print(f"✅ Statut commande #{order.id} changé de '{previous_status}' à 'delivered' après encaissement")

    db.session.commit()

    if order.payment_status == 'paid' and previous_payment_status != 'paid':
        try:
            from app.accounting.services import AccountingIntegrationService
            AccountingIntegrationService.create_sale_entry(
                order_id=order.id,
                sale_amount=float(order.total_amount),
                payment_method='cash',
                description=f'Vente commande #{order.id} - {order.customer_name or "Client"}'
            )
        except Exception as e:
            current_app.logger.error(f"Erreur intégration comptable paiement commande (order_id={order.id}): {e}", exc_info=True)

    # Intégration POS : Impression ticket + ouverture tiroir
    try:
        from app.services.printer_service import get_printer_service
        printer_service = get_printer_service()
        
        # Calculer la monnaie à rendre
        change_amount = float(amount_received - amount_to_record) if amount_received > amount_to_record else 0
        
        # Imprimer le ticket avec les infos de paiement et ouvrir le tiroir
        printer_service.print_ticket(
            order.id, 
            priority=1,
            employee_name=current_user.name if hasattr(current_user, 'name') else current_user.username,
            amount_received=float(amount_received),
            change_amount=change_amount
        )
        printer_service.open_cash_drawer(priority=1)
        
        print(f"🖨️ Impression ticket et ouverture tiroir déclenchées pour commande #{order.id}")
    except Exception as e:
        print(f"⚠️ Erreur intégration POS: {e}")
        # Ne pas faire échouer le paiement si l'impression échoue
    
    # Message de confirmation avec info sur le changement de statut
    message = f'Paiement enregistré ({float(amount_to_record):.2f} DA).'
    if change_amount > 0:
        message += f' Monnaie à rendre : {float(change_amount):.2f} DA.'
    if status_changed:
        message += ' Statut mis à jour sur "Livrée".'
    remaining_after = order.balance_due
    if remaining_after > Decimal('0.00'):
        message += f' Solde restant : {float(remaining_after):.2f} DA.'
    else:
        message += ' Solde totalement réglé.'
    flash(message, 'success')
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
    # Accepter les commandes customer_order ET in_store avec statut ready_at_shop et delivery_option='delivery'
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
            
            # Calculer le montant à encaisser (produits seulement, sans frais de livraison)
            # Pour les commandes in_store créées depuis PDV, total_amount = produits seulement
            # Pour les commandes customer_order, total_amount peut inclure les frais de livraison
            if order.order_type == 'in_store':
                # Pour les commandes PDV, total_amount est déjà le montant produits seulement
                products_amount = order.total_amount
            else:
                # Pour les commandes customer_order, soustraire les frais de livraison
                products_amount = order.total_amount - (order.delivery_cost or 0)
            
            # Créer le mouvement de caisse si une session est ouverte
            session = CashRegisterSession.query.filter_by(is_open=True).first()
            if session:
                movement = CashMovement(
                    session_id=session.id,
                    created_at=datetime.utcnow(),
                    type='entrée',
                    amount=float(products_amount),
                    reason=f'Encaissement commande #{order.id} - Livraison payée (hors frais livraison)',
                    notes=f'Livreur: {Deliveryman.query.get(deliveryman_id).name} - Frais livraison: {order.delivery_cost or 0:.2f} DA' + (f' - {notes}' if notes else ''),
                    employee_id=current_user.id
                )
                db.session.add(movement)
                
                # ✅ CORRECTION : Impression ticket + ouverture tiroir-caisse
                try:
                    from app.services.printer_service import get_printer_service
                    printer_service = get_printer_service()
                    
                    change_amount = 0.0  # Pas de monnaie à rendre pour livraison
                    
                    # Récupérer les informations du livreur
                    deliveryman = Deliveryman.query.get(deliveryman_id)
                    deliveryman_name = deliveryman.name if deliveryman else ''
                    deliveryman_phone = deliveryman.phone if deliveryman and deliveryman.phone else ''
                    
                    printer_service.print_ticket(
                        order.id,
                        priority=1,
                        employee_name=current_user.name if hasattr(current_user, 'name') else current_user.username,
                        amount_received=float(products_amount),
                        change_amount=change_amount,
                        customer_phone=order.customer_phone,
                        customer_address=order.customer_address,
                        delivery_cost=float(order.delivery_cost) if order.delivery_cost else 0,
                        deliveryman_name=deliveryman_name,
                        deliveryman_phone=deliveryman_phone
                    )
                    printer_service.open_cash_drawer(priority=1)
                except Exception as e:
                    current_app.logger.error(f"Erreur impression/tiroir (assign_deliveryman): {e}")
                
                flash(f'Commande #{order.id} assignée à {Deliveryman.query.get(deliveryman_id).name} et encaissée ({products_amount:.2f} DA, frais livraison {order.delivery_cost or 0:.2f} DA pour le livreur).', 'success')
            else:
                flash(f'Commande #{order.id} assignée et livrée, mais aucune session de caisse ouverte pour l\'encaissement.', 'warning')

            previous_payment_status = order.payment_status
            incremental_payment = (order.total_amount - (order.delivery_cost or 0)) or Decimal('0.00')
            order.amount_paid = (Decimal(order.amount_paid or 0) + Decimal(incremental_payment)).quantize(Decimal('0.01'))
            order.update_payment_status()

            if order.payment_status == 'paid' and previous_payment_status != 'paid':
                # ✅ CORRECTION : Décrémenter le stock des produits finis (livraison = vente)
                # Seulement pour les commandes qui ont été dans le stock_comptoir (in_store)
                # Les commandes client n'ont jamais été dans le stock_comptoir (réservées)
                if order.order_type == 'in_store':
                    order._decrement_stock_with_value_on_delivery()
                # Pour les commandes client, le stock était déjà réservé, pas besoin de décrémenter
                
                # ✅ CORRECTION : Décrémenter les consommables lors de l'encaissement
                for order_item in order.items:
                    product_fini = order_item.product
                    if product_fini and product_fini.category:
                        from app.consumables.models import ConsumableCategory
                        consumable_category = ConsumableCategory.query.filter(
                            ConsumableCategory.product_category_id == product_fini.category.id,
                            ConsumableCategory.is_active == True
                        ).first()
                        
                        if consumable_category:
                            consumables_needed = consumable_category.calculate_consumables_needed(int(order_item.quantity))
                            for consumable_product, qty in consumables_needed:
                                if consumable_product:
                                    consumable_product.update_stock_by_location('stock_consommables', -float(qty))
                                    current_app.logger.info(f"Décrémentation consommable (livraison payée): {consumable_product.name} - {qty} {consumable_product.unit}")
                
                try:
                    from app.accounting.services import AccountingIntegrationService
                    AccountingIntegrationService.create_sale_entry(
                        order_id=order.id,
                        sale_amount=float(order.total_amount),
                        payment_method='cash',
                        description=f'Vente commande #{order.id} - {order.customer_name or "Client"}'
                    )
                except Exception as e:
                    current_app.logger.warning(f"Erreur intégration comptable (assign_deliveryman) : {e}")
        else:
            # Le livreur n'a pas payé : marquer comme livrée non payée et créer une dette
            order.status = 'delivered_unpaid'
            
            # Calculer le montant produits (sans frais de livraison)
            # Pour les commandes in_store créées depuis PDV, total_amount = produits seulement
            # Pour les commandes customer_order, total_amount peut inclure les frais de livraison
            if order.order_type == 'in_store':
                # Pour les commandes PDV, total_amount est déjà le montant produits seulement
                products_amount = order.total_amount
            else:
                # Pour les commandes customer_order, soustraire les frais de livraison
                products_amount = order.total_amount - (order.delivery_cost or 0)
            
            debt = DeliveryDebt(
                order_id=order.id,
                deliveryman_id=deliveryman_id,
                amount=products_amount,
                paid=False
            )
            db.session.add(debt)
            
            # Impression ticket même si le livreur ne paie pas
            try:
                from app.services.printer_service import get_printer_service
                printer_service = get_printer_service()
                
                # Récupérer les informations du livreur
                deliveryman = Deliveryman.query.get(deliveryman_id)
                deliveryman_name = deliveryman.name if deliveryman else ''
                deliveryman_phone = deliveryman.phone if deliveryman and deliveryman.phone else ''
                
                printer_service.print_ticket(
                    order.id,
                    priority=1,
                    employee_name=current_user.name if hasattr(current_user, 'name') else current_user.username,
                    amount_received=0.0,  # Pas de paiement
                    change_amount=0.0,
                    customer_phone=order.customer_phone,
                    customer_address=order.customer_address,
                    delivery_cost=float(order.delivery_cost) if order.delivery_cost else 0,
                    deliveryman_name=deliveryman_name,
                    deliveryman_phone=deliveryman_phone
                )
                printer_service.open_cash_drawer(priority=1)
            except Exception as e:
                current_app.logger.error(f"Erreur impression/tiroir (assign_deliveryman non payé): {e}")
            
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

@orders.route('/<int:order_id>/cancel-delivery-order', methods=['POST'])
@login_required
@admin_required
def cancel_delivery_order(order_id):
    """Annuler une commande de livraison PDV et restaurer le stock"""
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que c'est une commande de livraison PDV qui peut être annulée
    if order.order_type != 'in_store' or order.delivery_option != 'delivery' or order.status != 'ready_at_shop':
        flash('Cette commande ne peut pas être annulée.', 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    try:
        # Restaurer le stock
        order.restore_stock_on_cancellation()
        
        # Changer le statut
        order.status = 'cancelled'
        order.notes = (order.notes or '') + f'\n--- Annulée le {datetime.utcnow().strftime("%d/%m/%Y %H:%M")} ---'
        
        db.session.commit()
        flash(f'Commande #{order.id} annulée. Stock restauré.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'annulation de la commande {order_id}: {e}", exc_info=True)
        flash('Erreur lors de l\'annulation de la commande.', 'error')
    
    return redirect(url_for('dashboard.shop_dashboard'))

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

