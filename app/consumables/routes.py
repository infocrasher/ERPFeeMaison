"""
Routes pour la gestion des consommables
Module: app/consumables/routes.py
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.consumables import consumables
from app.consumables.models import ConsumableUsage, ConsumableAdjustment, ConsumableRecipe, ConsumableCategory, ConsumableRange
from app.consumables.forms import ConsumableUsageForm, ConsumableAdjustmentForm, ConsumableRecipeForm, ConsumableSearchForm, ConsumableCategoryForm, ConsumableRangeForm
from models import Product, Category
from datetime import datetime, timedelta
from sqlalchemy import func, and_

def admin_required(f):
    """Décorateur pour vérifier les droits d'administrateur"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès non autorisé.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@consumables.route('/')
@login_required
@admin_required
def index():
    """Dashboard des consommables"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_
    
    # Statistiques générales
    total_consumables = Product.query.filter(Product.category.has(name='Boite Consomable')).count()
    low_stock_consumables = Product.query.filter(
        and_(
            Product.category.has(name='Boite Consomable'),
            Product.stock_consommables <= Product.seuil_min_consommables
        )
    ).count()
    
    # Consommables avec stock faible
    low_stock_products = Product.query.filter(
        and_(
            Product.category.has(name='Boite Consomable'),
            Product.stock_consommables <= Product.seuil_min_consommables
        )
    ).all()
    
    # Utilisation des 30 derniers jours
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    recent_usage = ConsumableUsage.query.filter(
        ConsumableUsage.usage_date >= thirty_days_ago
    ).all()
    
    total_usage_value = sum([float(u.actual_value or u.estimated_value or 0) for u in recent_usage])
    
    return render_template('consumables/index.html',
                         total_consumables=total_consumables,
                         low_stock_consumables=low_stock_consumables,
                         low_stock_products=low_stock_products,
                         total_usage_value=total_usage_value)

@consumables.route('/usage')
@login_required
@admin_required
def usage_index():
    """Liste des utilisations de consommables"""
    form = ConsumableSearchForm()
    
    # Remplir les choix de produits consommables
    form.product_id.choices = [(0, 'Tous les consommables')] + [
        (p.id, p.name) for p in Product.query.filter(Product.category.has(name='Boite Consomable')).order_by(Product.name).all()
    ]
    
    # Récupérer les utilisations avec filtres
    query = ConsumableUsage.query.join(Product, ConsumableUsage.product_id == Product.id).filter(Product.category.has(name='Boite Consomable'))
    
    if form.validate_on_submit():
        if form.start_date.data:
            query = query.filter(ConsumableUsage.usage_date >= form.start_date.data)
        if form.end_date.data:
            query = query.filter(ConsumableUsage.usage_date <= form.end_date.data)
        if form.product_id.data and form.product_id.data != 0:
            query = query.filter(ConsumableUsage.product_id == form.product_id.data)
    
    usages = query.order_by(ConsumableUsage.usage_date.desc()).limit(100).all()
    
    return render_template('consumables/usage_index.html',
                         usages=usages,
                         form=form)

@consumables.route('/usage/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_usage():
    """Créer une utilisation de consommable"""
    form = ConsumableUsageForm()
    
    # Remplir les choix de produits consommables
    form.product_id.choices = [
        (p.id, f"{p.name} - Stock: {p.format_quantity_display(p.stock_consommables)}")
        for p in Product.query.filter(Product.category.has(name='Boite Consomable')).order_by(Product.name).all()
    ]
    
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        
        # Calculer l'estimation basée sur les ventes récentes
        estimated_quantity = calculate_estimated_usage(product, form.usage_date.data)
        
        # Créer l'utilisation
        usage = ConsumableUsage(
            product_id=form.product_id.data,
            usage_date=form.usage_date.data,
            estimated_quantity_used=estimated_quantity,
            actual_quantity_used=form.actual_quantity_used.data,
            estimated_value=estimated_quantity * float(product.cost_price or 0),
            actual_value=form.actual_quantity_used.data * float(product.cost_price or 0),
            calculation_method='manual',
            notes=form.notes.data
        )
        
        db.session.add(usage)
        
        # Ajuster le stock
        product.stock_consommables = max(0, product.stock_consommables - form.actual_quantity_used.data)
        db.session.add(product)
        
        db.session.commit()
        
        flash(f'Utilisation enregistrée : {product.name} - {form.actual_quantity_used.data} {product.unit}', 'success')
        return redirect(url_for('consumables.usage_index'))
    
    return render_template('consumables/create_usage.html', form=form)

@consumables.route('/adjustments')
@login_required
@admin_required
def adjustments_index():
    """Liste des ajustements de consommables"""
    adjustments = ConsumableAdjustment.query.join(Product, ConsumableAdjustment.product_id == Product.id).filter(
        Product.category.has(name='Boite Consomable')
    ).order_by(ConsumableAdjustment.adjustment_date.desc()).limit(50).all()
    
    return render_template('consumables/adjustments_index.html', adjustments=adjustments)

@consumables.route('/adjustments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_adjustment():
    """Créer un ajustement de consommable"""
    form = ConsumableAdjustmentForm()
    
    # Remplir les choix de produits consommables
    form.product_id.choices = [
        (p.id, f"{p.name} - Stock: {p.format_quantity_display(p.stock_consommables)}")
        for p in Product.query.filter(Product.category.has(name='Boite Consomable')).order_by(Product.name).all()
    ]
    
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        
        # Créer l'ajustement
        adjustment = ConsumableAdjustment(
            product_id=form.product_id.data,
            adjustment_date=form.adjustment_date.data,
            adjustment_type=form.adjustment_type.data,
            quantity_adjusted=form.quantity_adjusted.data,
            reason=form.reason.data,
            notes=form.notes.data,
            adjusted_by_id=current_user.id
        )
        
        db.session.add(adjustment)
        
        # Ajuster le stock selon le type
        if form.adjustment_type.data == 'inventory':
            # Ajustement d'inventaire : remplacer le stock
            product.stock_consommables = form.quantity_adjusted.data
        else:
            # Autres ajustements : ajouter/soustraire
            product.stock_consommables = max(0, product.stock_consommables + form.quantity_adjusted.data)
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Ajustement enregistré : {product.name} - {form.quantity_adjusted.data} {product.unit}', 'success')
        return redirect(url_for('consumables.adjustments_index'))
    
    return render_template('consumables/create_adjustment.html', form=form)

@consumables.route('/recipes')
@login_required
@admin_required
def recipes_index():
    """Liste des recettes de consommables"""
    recipes = ConsumableRecipe.query.join(Product, ConsumableRecipe.finished_product_id == Product.id).filter(
        Product.category.has(name='Gateaux ')
    ).all()
    
    return render_template('consumables/recipes_index.html', recipes=recipes)

@consumables.route('/recipes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_recipe():
    """Créer une recette de consommable"""
    form = ConsumableRecipeForm()
    
    # Remplir les choix de produits finis
    form.finished_product_id.choices = [
        (p.id, p.name) for p in Product.query.filter(Product.category.has(name='Gateaux ')).order_by(Product.name).all()
    ]
    
    # Remplir les choix de consommables
    form.consumable_product_id.choices = [
        (p.id, p.name) for p in Product.query.filter(Product.category.has(name='Boite Consomable')).order_by(Product.name).all()
    ]
    
    if form.validate_on_submit():
        # Vérifier si la recette existe déjà
        existing = ConsumableRecipe.query.filter(
            ConsumableRecipe.finished_product_id == form.finished_product_id.data,
            ConsumableRecipe.consumable_product_id == form.consumable_product_id.data
        ).first()
        
        if existing:
            flash('Cette recette existe déjà.', 'warning')
            return redirect(url_for('consumables.create_recipe'))
        
        # Créer la recette
        recipe = ConsumableRecipe(
            finished_product_id=form.finished_product_id.data,
            consumable_product_id=form.consumable_product_id.data,
            quantity_per_unit=form.quantity_per_unit.data,
            notes=form.notes.data
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        flash('Recette créée avec succès.', 'success')
        return redirect(url_for('consumables.recipes_index'))
    
    return render_template('consumables/create_recipe.html', form=form)

def calculate_estimated_usage(product, usage_date):
    """Calcule l'utilisation estimée d'un consommable basée sur les ventes"""
    from datetime import datetime, timedelta
    from models import OrderItem
    from sqlalchemy import func
    
    # Récupérer les ventes des 7 derniers jours
    seven_days_ago = usage_date - timedelta(days=7)
    
    # Récupérer les recettes qui utilisent ce consommable
    recipes = ConsumableRecipe.query.filter(
        ConsumableRecipe.consumable_product_id == product.id
    ).all()
    
    if not recipes:
        return 0.0
    
    total_estimated = 0.0
    
    for recipe in recipes:
        # Calculer les ventes du produit fini
        from models import Order
        sales = OrderItem.query.join(Order, OrderItem.order_id == Order.id).filter(
            OrderItem.product_id == recipe.finished_product_id,
            Order.created_at >= seven_days_ago,
            Order.created_at < usage_date + timedelta(days=1)
        ).with_entities(func.sum(OrderItem.quantity)).scalar() or 0
        
        # Calculer l'utilisation estimée
        estimated_usage = sales * recipe.quantity_per_unit
        total_estimated += estimated_usage
    
    return total_estimated

@consumables.route('/api/products/search')
@login_required
@admin_required
def search_products():
    """API pour la recherche de produits avec autocomplétion"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    
    # Construire la requête de base
    if query and len(query) >= 2:
        base_query = Product.query.filter(Product.name.ilike(f'%{query}%'))
    else:
        # Si pas de query, retourner tous les produits de la catégorie demandée
        base_query = Product.query
    
    # Filtrer par catégorie si spécifiée
    if category == 'finished':
        # Inclure toutes les catégories de produits finis
        from sqlalchemy import or_
        base_query = base_query.filter(or_(
            Product.category.has(name='Gateaux '),
            Product.category.has(name='Salés'),
            Product.category.has(name='Les Plats '),
            Product.category.has(name='Pates Traditionnelles ')
        ))
    elif category == 'consumable':
        # Filtrer par product_type au lieu de category.name pour plus de fiabilité
        base_query = base_query.filter(Product.product_type == 'consommable')
    
    # Limiter les résultats
    products = base_query.limit(10).all()
    
    # Formater les résultats
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else '',
            'stock': product.format_quantity_display(product.stock_consommables) if category == 'consumable' else product.format_quantity_display(product.stock_comptoir)
        })
    
    return jsonify(results)

# ========== NOUVELLES ROUTES POUR LES CATÉGORIES ==========

@consumables.route('/categories')
@login_required
@admin_required
def categories_index():
    """Liste des catégories de consommables"""
    categories = ConsumableCategory.query.order_by(ConsumableCategory.name).all()
    return render_template('consumables/categories_index.html', 
                         categories=categories,
                         title='Catégories de Consommables')

@consumables.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Créer une catégorie de consommables"""
    form = ConsumableCategoryForm()
    
    # Remplir les choix de catégories de produits
    form.product_category_id.choices = [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    
    if form.validate_on_submit():
        # Vérifier si la catégorie existe déjà pour cette catégorie de produit
        existing = ConsumableCategory.query.filter(
            ConsumableCategory.product_category_id == form.product_category_id.data
        ).first()
        
        if existing:
            flash('Une catégorie de consommables existe déjà pour cette catégorie de produits.', 'warning')
            return redirect(url_for('consumables.create_category'))
        
        # Créer la catégorie
        category = ConsumableCategory(
            name=form.name.data,
            description=form.description.data,
            product_category_id=form.product_category_id.data,
            is_active=form.is_active.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Catégorie créée avec succès. Configurez maintenant les plages de quantités.', 'success')
        return redirect(url_for('consumables.view_category', category_id=category.id))
    
    return render_template('consumables/create_category.html', 
                         form=form,
                         title='Nouvelle Catégorie de Consommables')

@consumables.route('/categories/<int:category_id>')
@login_required
@admin_required
def view_category(category_id):
    """Voir une catégorie de consommables et ses plages"""
    category = ConsumableCategory.query.get_or_404(category_id)
    
    # Récupérer les plages triées par quantités
    ranges = ConsumableRange.query.filter(
        ConsumableRange.category_id == category_id
    ).order_by(ConsumableRange.min_quantity).all()
    
    return render_template('consumables/view_category.html',
                         category=category,
                         ranges=ranges,
                         title=f'Catégorie : {category.name}')

@consumables.route('/categories/<int:category_id>/add-range', methods=['POST'])
@login_required
@admin_required
def add_range(category_id):
    """Ajouter une plage de quantités à une catégorie"""
    category = ConsumableCategory.query.get_or_404(category_id)
    
    data = request.json
    min_qty = int(data.get('min_quantity'))
    max_qty = int(data.get('max_quantity'))
    consumable_id = int(data.get('consumable_product_id'))
    qty_per_unit = float(data.get('quantity_per_unit', 1.0))
    
    # Vérifier les chevauchements
    overlapping = ConsumableRange.query.filter(
        ConsumableRange.category_id == category_id,
        ConsumableRange.min_quantity <= max_qty,
        ConsumableRange.max_quantity >= min_qty
    ).first()
    
    if overlapping:
        return jsonify({'success': False, 'message': f'Cette plage chevauche avec la plage {overlapping.min_quantity}-{overlapping.max_quantity}'})
    
    # Créer la plage
    range_obj = ConsumableRange(
        category_id=category_id,
        min_quantity=min_qty,
        max_quantity=max_qty,
        consumable_product_id=consumable_id,
        quantity_per_unit=qty_per_unit
    )
    
    db.session.add(range_obj)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Plage ajoutée avec succès'})

@consumables.route('/categories/<int:category_id>/delete-range/<int:range_id>', methods=['POST'])
@login_required
@admin_required
def delete_range(category_id, range_id):
    """Supprimer une plage de quantités"""
    range_obj = ConsumableRange.query.get_or_404(range_id)
    
    if range_obj.category_id != category_id:
        flash('Plage non trouvée.', 'error')
        return redirect(url_for('consumables.view_category', category_id=category_id))
    
    db.session.delete(range_obj)
    db.session.commit()
    
    flash('Plage supprimée avec succès.', 'success')
    return redirect(url_for('consumables.view_category', category_id=category_id))

@consumables.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Supprimer une catégorie de consommables"""
    category = ConsumableCategory.query.get_or_404(category_id)
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Catégorie supprimée avec succès.', 'success')
    return redirect(url_for('consumables.categories_index'))

@consumables.route('/categories/<int:category_id>/test')
@login_required
@admin_required
def test_category(category_id):
    """Tester une catégorie avec différentes quantités"""
    category = ConsumableCategory.query.get_or_404(category_id)
    
    # Quantités de test
    test_quantities = [1, 5, 10, 15, 25, 50, 75, 100]
    
    results = []
    for qty in test_quantities:
        consumables_needed = category.calculate_consumables_needed(qty)
        results.append({
            'quantity': qty,
            'consumables': [
                {'name': c.name if c else 'N/A', 'quantity': q} 
                for c, q in consumables_needed
            ]
        })
    
    return jsonify({'category': category.name, 'tests': results})
