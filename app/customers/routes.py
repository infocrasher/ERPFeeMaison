"""
Routes pour la gestion des clients particuliers
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime

from . import customers
from .forms import CustomerForm, CustomerSearchForm, QuickCustomerForm
from models import db, Customer, Order
from decorators import admin_required


@customers.route('/')
@login_required
@admin_required
def list_customers():
    """Liste des clients avec recherche"""
    search_form = CustomerSearchForm()
    
    # Construire la requête de base
    query = Customer.query
    
    # Appliquer les filtres de recherche
    if request.method == 'GET' and request.args.get('search'):
        search_term = request.args.get('search', '').strip()
        customer_type = request.args.get('customer_type', '')
        preferred_delivery = request.args.get('preferred_delivery', '')
        is_active = request.args.get('is_active', '')
        
        # Pré-remplir le formulaire
        search_form.search.data = search_term
        search_form.customer_type.data = customer_type
        search_form.preferred_delivery.data = preferred_delivery
        search_form.is_active.data = is_active
        
        # Filtrer par terme de recherche
        if search_term:
            query = query.filter(
                or_(
                    Customer.first_name.ilike(f'%{search_term}%'),
                    Customer.last_name.ilike(f'%{search_term}%'),
                    Customer.phone.ilike(f'%{search_term}%'),
                    Customer.email.ilike(f'%{search_term}%')
                )
            )
        
        # Filtrer par type
        if customer_type:
            query = query.filter(Customer.customer_type == customer_type)
        
        # Filtrer par préférence de livraison
        if preferred_delivery:
            query = query.filter(Customer.preferred_delivery == preferred_delivery)
        
        # Filtrer par statut
        if is_active:
            query = query.filter(Customer.is_active == (is_active == 'true'))
    
    # Ordonner et paginer
    customers_list = query.order_by(Customer.last_name, Customer.first_name).all()
    
    return render_template('customers/list.html', 
                         customers=customers_list, 
                         search_form=search_form)


@customers.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_customer():
    """Créer un nouveau client"""
    form = CustomerForm()
    
    if form.validate_on_submit():
        try:
            customer = Customer(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                delivery_address=form.delivery_address.data,
                birth_date=form.birth_date.data,
                customer_type=form.customer_type.data,
                preferred_delivery=form.preferred_delivery.data,
                notes=form.notes.data,
                allergies=form.allergies.data,
                preferences=form.preferences.data,
                is_active=form.is_active.data
            )
            
            db.session.add(customer)
            db.session.commit()
            
            flash(f'Client "{customer.full_name}" créé avec succès.', 'success')
            return redirect(url_for('customers.view_customer', customer_id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du client: {str(e)}', 'danger')
    
    return render_template('customers/form.html', form=form, title='Nouveau Client')


@customers.route('/<int:customer_id>')
@login_required
@admin_required
def view_customer(customer_id):
    """Voir les détails d'un client"""
    customer = Customer.query.get_or_404(customer_id)
    
    # Récupérer les commandes récentes
    recent_orders = customer.orders.order_by(
        db.text('created_at DESC')
    ).limit(10).all()
    
    return render_template('customers/view.html', 
                         customer=customer, 
                         recent_orders=recent_orders)


@customers.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_customer(customer_id):
    """Modifier un client"""
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(customer)
            db.session.commit()
            
            flash(f'Client "{customer.full_name}" modifié avec succès.', 'success')
            return redirect(url_for('customers.view_customer', customer_id=customer.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'danger')
    
    return render_template('customers/form.html', 
                         form=form, 
                         customer=customer,
                         title=f'Modifier {customer.full_name}')


@customers.route('/<int:customer_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_customer_status(customer_id):
    """Activer/désactiver un client"""
    customer = Customer.query.get_or_404(customer_id)
    
    try:
        customer.is_active = not customer.is_active
        db.session.commit()
        
        status = "activé" if customer.is_active else "désactivé"
        flash(f'Client "{customer.full_name}" {status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut: {str(e)}', 'danger')
    
    return redirect(url_for('customers.view_customer', customer_id=customer.id))


@customers.route('/api/search')
@login_required
def api_search_customers():
    """API pour recherche de clients (auto-complétion)"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if not query or len(query) < 2:
        return jsonify([])
    
    customers_list = Customer.query.filter(
        Customer.is_active == True,
        or_(
            Customer.first_name.ilike(f'%{query}%'),
            Customer.last_name.ilike(f'%{query}%'),
            Customer.phone.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = []
    for customer in customers_list:
        results.append({
            'id': customer.id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'email': customer.email,
            'full_name': customer.full_name,
            'display_phone': customer.display_phone,
            'text': f"{customer.full_name} ({customer.display_phone})"
        })
    
    return jsonify(results)


@customers.route('/api/details/<int:customer_id>')
@login_required
def api_customer_details(customer_id):
    """API pour récupérer les détails d'un client"""
    customer = Customer.query.get_or_404(customer_id)
    
    return jsonify({
        'id': customer.id,
        'first_name': customer.first_name,
        'last_name': customer.last_name,
        'full_name': customer.full_name,
        'phone': customer.phone,
        'display_phone': customer.display_phone,
        'email': customer.email,
        'address': customer.address,
        'delivery_address': customer.delivery_address,
        'customer_type': customer.customer_type,
        'preferred_delivery': customer.preferred_delivery,
        'is_active': customer.is_active,
        'total_orders': customer.total_orders,
        'total_spent': float(customer.total_spent) if customer.total_spent else 0
    })


@customers.route('/api/quick-create', methods=['POST'])
@login_required
def api_quick_create_customer():
    """API pour création rapide d'un client lors d'une commande"""
    form = QuickCustomerForm()
    
    if form.validate_on_submit():
        try:
            # Vérifier si le client existe déjà (par téléphone)
            existing = Customer.query.filter_by(phone=form.phone.data).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Un client avec ce téléphone existe déjà: {existing.full_name}'
                }), 400
            
            customer = Customer(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
                customer_type='regular',
                is_active=True
            )
            
            db.session.add(customer)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'full_name': customer.full_name,
                    'phone': customer.phone,
                    'address': customer.address
                },
                'message': f'Client "{customer.full_name}" créé avec succès.'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Erreur lors de la création: {str(e)}'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Données invalides',
        'errors': form.errors
    }), 400
