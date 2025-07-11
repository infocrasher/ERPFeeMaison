# -*- coding: utf-8 -*-
"""
Status routes pour ERP Fée Maison
Routes spécialisées pour les changements de statut avec sélection employés
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import Order
from extensions import db
from app.employees.models import Employee
from decorators import admin_required

status_bp = Blueprint('status', __name__)

@status_bp.route('/<int:order_id>/change-status-to-ready', methods=['POST'])
@login_required
@admin_required
def change_status_to_ready(order_id):
    """
    Traite la finalisation de la production.
    Change le statut, décrémente la quantité ET la valeur des ingrédients, 
    et incrémente la quantité ET la valeur du stock du produit fini.
    """
    
    from models import Product, Recipe, RecipeIngredient

    order = Order.query.get_or_404(order_id)
    
    if not order.can_be_received_at_shop():
        flash(f"La commande #{order.id} ne peut pas être finalisée. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    employee_ids = request.form.getlist('employee_ids[]')
    
    if not employee_ids:
        return redirect(url_for('status.select_employees_for_status_change', 
                              order_id=order_id, 
                              new_status='ready_at_shop'))
    
    try:
        # ### DEBUT DE LA LOGIQUE CORRIGÉE ###
        
        for order_item in order.items:
            product_fini = order_item.product
            
            if product_fini and product_fini.recipe_definition:
                recipe = product_fini.recipe_definition
                labo_key = recipe.production_location
                
                # Correction du mapping pour la décrémentation
                location_map = {
                    "ingredients_magasin": "stock_ingredients_magasin",
                    "ingredients_local": "stock_ingredients_local"
                }
                stock_attr = location_map.get(labo_key, labo_key)

                for ingredient_in_recipe in recipe.ingredients.all():
                    ingredient_product = ingredient_in_recipe.product
                    
                    qty_per_unit = float(ingredient_in_recipe.quantity_needed) / float(recipe.yield_quantity)
                    quantity_to_decrement = qty_per_unit * float(order_item.quantity)
                    
                    # --- NOUVELLE LOGIQUE DE VALORISATION ---
                    # 1. On récupère le PMP (cost_price) de l'ingrédient
                    cost_per_base_unit = float(ingredient_product.cost_price or 0.0)
                    
                    # 2. On calcule la valeur du stock d'ingrédient qui a été consommé
                    value_to_decrement = quantity_to_decrement * cost_per_base_unit
                    
                    # 3. On met à jour la quantité ET la valeur du stock de l'ingrédient
                    ingredient_product.update_stock_by_location(stock_attr, -quantity_to_decrement)
                    ingredient_product.total_stock_value = float(ingredient_product.total_stock_value or 0.0) - value_to_decrement
                    
                    # Décrémenter la valeur du stock par emplacement
                    if stock_attr == "stock_ingredients_magasin":
                        ingredient_product.valeur_stock_ingredients_magasin = float(getattr(ingredient_product, "valeur_stock_ingredients_magasin", 0.0)) - value_to_decrement
                    elif stock_attr == "stock_ingredients_local":
                        ingredient_product.valeur_stock_ingredients_local = float(getattr(ingredient_product, "valeur_stock_ingredients_local", 0.0)) - value_to_decrement
                    
                    print(f"DECREMENT: {quantity_to_decrement:.2f}g de {ingredient_product.name} (Valeur: {value_to_decrement:.2f} DA)")
        
        # On appelle la méthode qui incrémente le stock ET la valeur du produit fini
        order._increment_shop_stock_with_value()

        # Décision sur le statut final
        if order.order_type == 'counter_production_request':
            order.status = 'completed'
            final_message = f'Ordre de production #{order.id} terminé. Stocks mis à jour.'
        else:
            # Commande client : décision basée sur delivery_option
            if order.delivery_option == 'pickup':
                order.status = 'waiting_for_pickup'
                final_message = f'Commande client #{order.id} en attente de retrait. Stocks mis à jour.'
            else:  # delivery_option == 'delivery'
                order.status = 'ready_at_shop'
                final_message = f'Commande client #{order.id} prête à livrer. Stocks mis à jour.'
        
        # Assignation des employés
        for employee_id in employee_ids:
            employee = Employee.query.get(employee_id)
            if employee and employee.is_active:
                order.assign_producer(employee)
        
        db.session.commit()
        
        producers_names = ", ".join([emp.name for emp in order.produced_by])
        flash(f'{final_message} Produit par: {producers_names}', 'success')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur critique lors de la finalisation de la commande #{order_id}: {str(e)}", exc_info=True)
        flash(f"Erreur critique lors de la mise à jour des stocks : {str(e)}", 'error')
    
    return redirect(url_for('dashboard.shop_dashboard'))


# ... (Le reste de ton fichier status_routes.py reste identique)

@status_bp.route('/<int:order_id>/change-status-to-delivered', methods=['POST'])
@login_required
@admin_required
def change_status_to_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    if order.order_type != 'customer_order':
        flash(f"Seules les commandes client peuvent être marquées comme livrées", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    if not order.can_be_delivered():
        flash(f"La commande #{order.id} ne peut pas être livrée. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    try:
        if order.mark_as_delivered():
            db.session.commit()
            flash(f'Commande #{order.id} marquée comme livrée ! Montant encaissé: {order.total_amount:.2f} DA', 'success')
        else:
            flash(f"Erreur lors du changement de statut de la commande #{order.id}", 'error')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la livraison: {str(e)}", 'error')
    return redirect(url_for('dashboard.shop_dashboard'))

@status_bp.route('/<int:order_id>/select-employees/<string:new_status>')
@login_required
@admin_required
def select_employees_for_status_change(order_id, new_status):
    order = Order.query.get_or_404(order_id)
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production'])
    ).order_by(Employee.name).all()
    return render_template('orders/change_status_form.html',
                         order=order,
                         employees=employees,
                         new_status=new_status,
                         title=f"Sélection Employés - Commande #{order_id}")
    
@status_bp.route('/<int:order_id>/manual-status-change', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_status_change(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        new_status = request.form.get('new_status')
        notes = request.form.get('notes', '')
        employee_ids = request.form.getlist('employee_ids[]')
        if not new_status:
            flash("Veuillez sélectionner un nouveau statut", 'error')
            return redirect(request.url)
        try:
            old_status = order.status
            order.status = new_status
            if employee_ids:
                order.produced_by.clear()
                for employee_id in employee_ids:
                    employee = Employee.query.get(employee_id)
                    if employee and employee.is_active:
                        order.assign_producer(employee)
            if notes:
                if order.notes:
                    order.notes += f"\n[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
                else:
                    order.notes = f"[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
            db.session.commit()
            producers_info = ""
            if order.produced_by:
                producers_names = ", ".join([emp.name for emp in order.produced_by])
                producers_info = f" (Employés: {producers_names})"
            flash(f'Statut de la commande #{order_id} changé de "{old_status}" à "{new_status}"{producers_info}', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors du changement de statut: {str(e)}", 'error')
    employees = Employee.query.filter(
        Employee.is_active == True
    ).order_by(Employee.name).all()
    return render_template('orders/manual_status_form.html',
                         order=order,
                         employees=employees,
                         title=f"Changement Statut - Commande #{order_id}")

@status_bp.route('/api/active-employees')
@login_required
@admin_required
def get_active_employees():
    employees = Employee.query.filter(Employee.is_active == True).order_by(Employee.name).all()
    return jsonify([{'id': emp.id,'name': emp.name,'role': emp.role} for emp in employees])

@status_bp.route('/<int:order_id>/test-employees/<string:new_status>')
def test_employees_no_decorators(order_id, new_status):
    return f"✅ TEST OK: order_id={order_id}, new_status={new_status}"

@status_bp.route('/<int:order_id>/test-login/<string:new_status>')
@login_required
def test_login_only(order_id, new_status):
    return f"✅ LOGIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

@status_bp.route('/<int:order_id>/test-admin/<string:new_status>')
@admin_required
def test_admin_only(order_id, new_status):
    return f"✅ ADMIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

@status_bp.route('/<int:order_id>/test-both/<string:new_status>')
@login_required
@admin_required
def test_both_decorators(order_id, new_status):
    return f"✅ BOTH OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

