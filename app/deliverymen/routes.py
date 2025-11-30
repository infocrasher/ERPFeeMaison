from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.deliverymen.models import Deliveryman
from extensions import db
from models import Order
from datetime import datetime, date, timedelta
from sqlalchemy import func
from decorators import admin_required

deliverymen_bp = Blueprint('deliverymen', __name__)

@deliverymen_bp.route('/deliverymen')
@login_required
def list_deliverymen():
    """Liste tous les livreurs"""
    deliverymen = Deliveryman.query.all()
    return render_template('deliverymen/list_deliverymen.html', deliverymen=deliverymen)

@deliverymen_bp.route('/deliverymen/new', methods=['GET', 'POST'])
@login_required
def new_deliveryman():
    """Créer un nouveau livreur"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name:
            flash('Le nom du livreur est obligatoire', 'error')
            return render_template('deliverymen/deliveryman_form.html')
        
        deliveryman = Deliveryman(name=name, phone=phone)
        db.session.add(deliveryman)
        db.session.commit()
        
        flash('Livreur ajouté avec succès', 'success')
        return redirect(url_for('deliverymen.list_deliverymen'))
    
    return render_template('deliverymen/deliveryman_form.html')

@deliverymen_bp.route('/deliverymen/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_deliveryman(id):
    """Modifier un livreur"""
    deliveryman = Deliveryman.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name:
            flash('Le nom du livreur est obligatoire', 'error')
            return render_template('deliverymen/deliveryman_form.html', deliveryman=deliveryman)
        
        deliveryman.name = name
        deliveryman.phone = phone
        db.session.commit()
        
        flash('Livreur modifié avec succès', 'success')
        return redirect(url_for('deliverymen.list_deliverymen'))
    
    return render_template('deliverymen/deliveryman_form.html', deliveryman=deliveryman)

@deliverymen_bp.route('/deliverymen/<int:id>/delete', methods=['POST'])
@login_required
def delete_deliveryman(id):
    """Supprimer un livreur"""
    deliveryman = Deliveryman.query.get_or_404(id)
    
    # Vérifier s'il y a des commandes associées
    if deliveryman.orders:
        flash('Impossible de supprimer ce livreur car il a des commandes associées', 'error')
        return redirect(url_for('deliverymen.list_deliverymen'))
    
    db.session.delete(deliveryman)
    db.session.commit()
    
    flash('Livreur supprimé avec succès', 'success')
    return redirect(url_for('deliverymen.list_deliverymen'))


@deliverymen_bp.route('/deliverymen/dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def deliverymen_dashboard():
    """Dashboard de gestion complète des livreurs avec statistiques"""
    
    # Récupérer les paramètres de filtrage
    filter_date_start = request.args.get('date_start', None)
    filter_date_end = request.args.get('date_end', None)
    filter_deliveryman_id = request.args.get('deliveryman_id', None, type=int)
    
    # Valeurs par défaut : aujourd'hui si pas de dates spécifiées
    if filter_date_start:
        try:
            start_date = datetime.strptime(filter_date_start, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today()
    else:
        start_date = date.today()
    
    if filter_date_end:
        try:
            end_date = datetime.strptime(filter_date_end, '%Y-%m-%d').date()
        except ValueError:
            end_date = date.today()
    else:
        # Si pas de date de fin, utiliser la date de début (une seule journée)
        end_date = start_date
    
    # S'assurer que end_date >= start_date
    if end_date < start_date:
        end_date = start_date
    
    # Requête de base : commandes avec livreur assigné
    query = Order.query.filter(
        Order.deliveryman_id.isnot(None),
        Order.delivery_option == 'delivery'
    )
    
    # Filtrer par période (sur due_date qui est la date de livraison)
    query = query.filter(
        func.date(Order.due_date) >= start_date,
        func.date(Order.due_date) <= end_date
    )
    
    # Filtrer par livreur si spécifié
    if filter_deliveryman_id:
        query = query.filter(Order.deliveryman_id == filter_deliveryman_id)
    
    # Récupérer toutes les commandes
    orders = query.order_by(Order.due_date.desc()).all()
    
    # Grouper par livreur et calculer les statistiques
    stats_by_deliveryman = {}
    
    for order in orders:
        deliveryman_id = order.deliveryman_id
        if deliveryman_id not in stats_by_deliveryman:
            deliveryman = order.deliveryman
            stats_by_deliveryman[deliveryman_id] = {
                'deliveryman': deliveryman,
                'orders': [],
                'orders_count': 0,
                'total_ca': 0.0,
                'zones': set(),  # Utiliser un set pour éviter les doublons
                'delivery_costs': 0.0  # Frais de livraison totaux
            }
        
        stats = stats_by_deliveryman[deliveryman_id]
        stats['orders'].append(order)
        stats['orders_count'] += 1
        stats['total_ca'] += float(order.total_amount or 0)
        stats['delivery_costs'] += float(order.delivery_cost or 0)
        
        # Ajouter la zone de livraison si elle existe
        if order.delivery_zone:
            stats['zones'].add(order.delivery_zone)
        elif order.customer_address:
            # Extraire une zone approximative de l'adresse si possible
            address_parts = order.customer_address.split(',')
            if len(address_parts) > 0:
                stats['zones'].add(address_parts[-1].strip())
    
    # Convertir les sets en listes triées pour l'affichage
    for stats in stats_by_deliveryman.values():
        stats['zones'] = sorted(list(stats['zones']))
    
    # Calculer les totaux globaux
    total_orders = len(orders)
    total_ca = sum(float(order.total_amount or 0) for order in orders)
    total_delivery_costs = sum(float(order.delivery_cost or 0) for order in orders)
    
    # Récupérer tous les livreurs pour le filtre
    all_deliverymen = Deliveryman.query.order_by(Deliveryman.name).all()
    
    return render_template('deliverymen/dashboard.html',
                         stats_by_deliveryman=stats_by_deliveryman,
                         start_date=start_date,
                         end_date=end_date,
                         filter_deliveryman_id=filter_deliveryman_id,
                         all_deliverymen=all_deliverymen,
                         total_orders=total_orders,
                         total_ca=total_ca,
                         total_delivery_costs=total_delivery_costs,
                         title='Gestion Livreurs') 