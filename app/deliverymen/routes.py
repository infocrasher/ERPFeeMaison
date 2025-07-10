from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.deliverymen.models import Deliveryman
from extensions import db

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