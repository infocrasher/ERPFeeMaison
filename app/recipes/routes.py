from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import SubmitField
from extensions import db
from .forms import RecipeForm, ingredient_product_query_factory
from decorators import admin_required
from sqlalchemy import or_, and_ # Import or_ and and_
from app.stock.stock_manager import StockLocationManager

recipes = Blueprint('recipes', __name__, url_prefix='/admin/recipes')

class QuickActionForm(FlaskForm):
    delete = SubmitField('Supprimer')

@recipes.route('/')
@login_required
@admin_required
def list_recipes():
    from models import Recipe
    form = QuickActionForm()
    page = request.args.get('page', 1, type=int)
    pagination = Recipe.query.order_by(Recipe.name).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 10)
    )
    return render_template('recipes/list_recipes.html', 
                         recipes_pagination=pagination, 
                         form=form,
                         title='Gestion des Recettes')

@recipes.route('/<int:recipe_id>')
@login_required
@admin_required
def view_recipe(recipe_id):
    from models import Recipe
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = QuickActionForm()
    
    # Obtenir le label lisible pour le lieu de production
    production_location_label = None
    if recipe.production_location:
        production_choices = dict(StockLocationManager.get_production_choices())
        production_location_label = production_choices.get(recipe.production_location, recipe.production_location)
    
    return render_template('recipes/view_recipe.html', 
                         recipe=recipe, 
                         form=form,
                         production_location_label=production_location_label,
                         title=f"Recette : {recipe.name}")

@recipes.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_recipe():
    from models import Recipe, Product, RecipeIngredient
    form = RecipeForm()

    # LOG : Afficher le payload POST et le contenu de form.ingredients.data avant validation
    current_app.logger.warning(f"Payload POST : {request.form}")
    current_app.logger.warning(f"Form.ingredients.data avant validation : {form.ingredients.data}")

    if form.validate_on_submit():
        try:
            recipe = Recipe(
                name=form.name.data,
                description=form.description.data,
                yield_quantity=form.yield_quantity.data,
                yield_unit=form.yield_unit.data,
                product_id=form.finished_product.data if form.finished_product.data > 0 else None,
                production_location=form.production_location.data
            )
            db.session.add(recipe)
            db.session.flush()

            for item_data in form.ingredients.data:
                # On lit l'ID depuis le champ caché 'product_id'
                product_id = item_data.get('product_id')
                if product_id and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=product_id, # Utilisation de product_id
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'],
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"Recette '{recipe.name}' créée avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de la recette: {e}", exc_info=True)
            flash("Erreur inattendue lors de la création. Consulter les logs.", 'danger')
    
    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette (new): {form.errors}")

    # L'ancienne variable 'ingredients_json' est supprimée
    return render_template('recipes/recipe_form.html', form=form, title='Nouvelle Recette')

@recipes.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    from models import Recipe, Product, RecipeIngredient
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = RecipeForm(obj=recipe)

    if form.validate_on_submit():
        try:
            recipe.name = form.name.data
            recipe.description = form.description.data
            recipe.yield_quantity = form.yield_quantity.data
            recipe.yield_unit = form.yield_unit.data
            recipe.product_id = form.finished_product.data if form.finished_product.data > 0 else None
            recipe.production_location = form.production_location.data

            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            db.session.flush()

            for item_data in form.ingredients.data:
                # On lit l'ID depuis le champ caché 'product_id'
                product_id = item_data.get('product_id')
                if product_id and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=product_id, # Utilisation de product_id
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'],
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"Recette '{recipe.name}' mise à jour avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la mise à jour de la recette {recipe_id}: {e}", exc_info=True)
            flash("Erreur inattendue lors de la mise à jour. Consulter les logs.", 'danger')

    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette (edit {recipe_id}): {form.errors}")
    
    if request.method == 'GET':
        form.finished_product.data = recipe.product_id
        form.production_location.data = recipe.production_location
        
        while len(form.ingredients.entries) > 0:
            form.ingredients.pop_entry()
        for item in recipe.ingredients:
            # On peuple le formulaire avec les champs product_id et product_search
            form.ingredients.append_entry({
                'product_id': item.product_id,
                'product_search': item.product.name, # Pour l'affichage initial
                'quantity_needed': item.quantity_needed,
                'unit': item.unit,
                'notes': item.notes
            })

    # L'ancienne variable 'ingredients_json' est supprimée
    return render_template('recipes/recipe_form.html', 
                         form=form, 
                         title=f"Modifier Recette: {recipe.name}", 
                         edit_mode=True)

@recipes.route('/<int:recipe_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recipe(recipe_id):
    from models import Recipe
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    recipe_name = recipe.name
    try:
        db.session.delete(recipe)
        db.session.commit()
        flash(f"La recette '{recipe_name}' a été supprimée.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la recette {recipe_id}: {e}", exc_info=True)
        flash("Erreur lors de la suppression. Elle est peut-être liée à d'autres éléments.", 'danger')
    return redirect(url_for('recipes.list_recipes'))

# ### DEBUT DE LA MODIFICATION ###
@recipes.route('/api/ingredients/search')
@login_required
@admin_required
def api_ingredients_search():
    """
    API de recherche de produits de type 'ingrédient' pour l'auto-complétion.
    """
    from models import Product
    search_term = request.args.get('q', '')
    
    # On ne commence la recherche qu'après 2 caractères pour la performance
    if len(search_term) < 2:
        return jsonify([])
    
    # Requête pour trouver les ingrédients dont le nom contient le terme de recherche
    products = Product.query.filter(
        and_(
            Product.product_type == 'ingredient',
            Product.name.ilike(f'%{search_term}%')
        )
    ).limit(15).all() # On limite à 15 résultats

    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'unit': product.unit,
            # On s'assure que le PMP est formaté avec 4 décimales pour l'affichage
            'cost_price': f"{product.cost_price:.4f}" if product.cost_price is not None else "0.0000"
        })
    return jsonify(results)
# ### FIN DE LA MODIFICATION ###