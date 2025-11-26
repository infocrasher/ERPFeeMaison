from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required
from extensions import db
from models import Product, Category
from .forms import ProductForm, CategoryForm # Import local depuis le même dossier
from decorators import admin_required
import os
from werkzeug.utils import secure_filename

# Création du Blueprint 'products'
products = Blueprint('products', __name__)

UPLOAD_FOLDER = os.path.join('app', 'static', 'img', 'products')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- ROUTES POUR LES CATÉGORIES ---

@products.route('/categories')
@login_required
@admin_required
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    # Le chemin du template est maintenant relatif au dossier 'templates' de l'app
    return render_template('products/list_categories.html', categories=categories, title='Catégories')

@products.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    form = CategoryForm() # On crée une instance du formulaire
    if form.validate_on_submit():
        category = Category(name=form.name.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash('Nouvelle catégorie ajoutée.', 'success')
        return redirect(url_for('products.list_categories'))
    # On passe le formulaire au template
    return render_template('products/category_form.html', form=form, title='Nouvelle Catégorie')

@products.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = db.session.get(Category, category_id) or abort(404)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('Catégorie mise à jour.', 'success')
        return redirect(url_for('products.list_categories'))
    return render_template('products/category_form.html', form=form, title=f'Modifier: {category.name}')

@products.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = db.session.get(Category, category_id) or abort(404)
    if category.products.first():
        flash('Impossible de supprimer une catégorie contenant des produits.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Catégorie supprimée.', 'success')
    return redirect(url_for('products.list_categories'))


# --- ROUTES POUR LES PRODUITS ---

@products.route('/')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    type_param = request.args.get('type', 'all')
    query = Product.query
    if type_param != 'all':
        query = query.filter(Product.product_type == type_param)
    pagination = query.order_by(Product.name).paginate(page=page, per_page=current_app.config['PRODUCTS_PER_PAGE'])
    return render_template('products/list_products.html', products_pagination=pagination, title='Produits')

@products.route('/<int:product_id>')
@login_required
def view_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    return render_template('products/view_product.html', product=product, title=product.name)

@products.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Validation : si can_be_sold est coché, le prix doit être renseigné
        if form.can_be_sold.data and (not form.price.data or form.price.data <= 0):
            flash('Si "Peut être vendu" est coché, le prix de vente doit être renseigné et supérieur à 0.', 'danger')
            return render_template('products/product_form.html', form=form, title='Nouveau Produit', product=None)
        
        product = Product()
        form.populate_obj(product)
        product.category = form.category.data
        
        # ✅ CORRECTION : Convertir SKU vide en None pour éviter les doublons
        if product.sku == '':
            product.sku = None
        
        # Convertir sale_unit vide en None (pour utiliser l'unité de base par défaut)
        if hasattr(product, 'sale_unit') and product.sale_unit == '':
            product.sale_unit = None
        
        # Gestion de l'image
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            form.image.data.save(filepath)
            product.image_filename = filename
        db.session.add(product)
        db.session.commit()
        flash(f'Le produit "{product.name}" a été créé.', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/product_form.html', form=form, title='Nouveau Produit', product=None)

@products.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        # Validation : si can_be_sold est coché, le prix doit être renseigné
        if form.can_be_sold.data and (not form.price.data or form.price.data <= 0):
            flash('Si "Peut être vendu" est coché, le prix de vente doit être renseigné et supérieur à 0.', 'danger')
            return render_template('products/product_form.html', form=form, title=f'Modifier: {product.name}', product=product)
        
        form.populate_obj(product)
        product.category = form.category.data
        
        # ✅ CORRECTION : Convertir SKU vide en None pour éviter les doublons
        if product.sku == '':
            product.sku = None
        
        # Convertir sale_unit vide en None (pour utiliser l'unité de base par défaut)
        if hasattr(product, 'sale_unit') and product.sale_unit == '':
            product.sale_unit = None
        
        # Gestion de l'image
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            form.image.data.save(filepath)
            product.image_filename = filename
        db.session.commit()
        flash(f'Le produit "{product.name}" a été mis à jour.', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/product_form.html', form=form, title=f'Modifier: {product.name}', product=product)

@products.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    
    # Vérifier toutes les relations qui empêchent la suppression
    blocking_reasons = []
    
    # Vérifier recipe_uses (relation one-to-many, retourne une liste)
    if hasattr(product, 'recipe_uses') and len(list(product.recipe_uses)) > 0:
        blocking_reasons.append("utilisé dans des recettes")
    
    # Vérifier order_items (relation lazy='dynamic')
    if product.order_items.first():
        blocking_reasons.append("utilisé dans des commandes")
    
    # Vérifier recipe_definition (relation one-to-one)
    if product.recipe_definition:
        blocking_reasons.append("défini comme produit fini d'une recette")
    
    # Vérifier purchase_items (relation lazy=True, retourne une liste)
    if hasattr(product, 'purchase_items') and len(list(product.purchase_items)) > 0:
        blocking_reasons.append("utilisé dans des bons d'achat")
    
    # Vérifier stock_movements (relation lazy='dynamic' ou liste)
    if hasattr(product, 'stock_movements'):
        if hasattr(product.stock_movements, 'first'):
            if product.stock_movements.first():
                blocking_reasons.append("présent dans des mouvements de stock")
        elif len(list(product.stock_movements)) > 0:
            blocking_reasons.append("présent dans des mouvements de stock")
    
    # Vérifier inventory_items (relation backref, retourne une liste)
    if hasattr(product, 'inventory_items') and len(list(product.inventory_items)) > 0:
        blocking_reasons.append("présent dans des inventaires")
    
    # Vérifier waste_declarations (relation backref, retourne une liste)
    if hasattr(product, 'waste_declarations') and len(list(product.waste_declarations)) > 0:
        blocking_reasons.append("présent dans des déclarations de pertes")
    
    # Vérifier consumable_usage (relation backref, retourne une liste)
    if hasattr(product, 'consumable_usage') and len(list(product.consumable_usage)) > 0:
        blocking_reasons.append("utilisé comme consommable")
    
    # Vérifier consumable_adjustments (relation backref, retourne une liste)
    if hasattr(product, 'consumable_adjustments') and len(list(product.consumable_adjustments)) > 0:
        blocking_reasons.append("présent dans des ajustements de consommables")
    
    # Vérifier les relations B2B
    from models import B2BOrderItem, InvoiceItem
    if B2BOrderItem.query.filter_by(product_id=product_id).first():
        blocking_reasons.append("utilisé dans des commandes B2B")
    if InvoiceItem.query.filter_by(product_id=product_id).first():
        blocking_reasons.append("utilisé dans des factures")
    
    if blocking_reasons:
        reasons_str = ", ".join(blocking_reasons)
        flash(f"Impossible de supprimer '{product.name}' car il est {reasons_str}.", 'danger')
    else:
        try:
            db.session.delete(product)
            db.session.commit()
            flash(f'Produit "{product.name}" supprimé avec succès.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('products.list_products'))

@products.route('/autocomplete')
@login_required
def autocomplete_products():
    term = request.args.get('q', '').strip()
    results = []
    if len(term) >= 2:
        products = Product.query.filter(Product.name.ilike(f'%{term}%')).order_by(Product.name).limit(10).all()
        for p in products:
            results.append({
                'id': p.id,
                'name': p.name,
                'type': p.product_type,
                'sku': p.sku
            })
    return {'results': results}