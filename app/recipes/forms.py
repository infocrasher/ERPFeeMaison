from flask_wtf import FlaskForm
from wtforms import (
    Form,
    StringField, 
    TextAreaField, 
    FieldList, 
    FormField, 
    SubmitField, 
    SelectField, 
    DecimalField, 
    IntegerField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import HiddenInput
from models import Product, Recipe
from sqlalchemy import or_

# On importe le manager pour les lieux de production
from app.stock.stock_manager import StockLocationManager


def ingredient_product_query_factory():
    """
    Retourne une requête pour obtenir tous les produits de type 'ingrédient'.
    """
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)

# ### DEBUT DE LA MODIFICATION ###
class IngredientForm(Form):
    """
    Sous-formulaire représentant une seule ligne d'ingrédient dans la recette.
    Adapté pour l'autocomplétion.
    """
    id = IntegerField(widget=HiddenInput(), validators=[Optional()])
    
    # Champ caché pour stocker l'ID du produit. La validation se fait sur ce champ.
    product_id = IntegerField(
        'Product ID',
        widget=HiddenInput(),
        filters=[lambda x: int(x) if x and str(x).isdigit() else None],
        validators=[DataRequired("Veuillez choisir un ingrédient valide.")]
    )
    
    # Champ visible pour la recherche par l'utilisateur.
    product_search = StringField('Ingrédient', render_kw={'placeholder': 'Tapez pour rechercher...'})
    
    quantity_needed = DecimalField('Quantité', validators=[DataRequired("La quantité est requise."), NumberRange(min=0.001)])
    unit = StringField('Unité', render_kw={'readonly': True}) # L'unité sera remplie par JS
    notes = StringField('Notes', validators=[Optional(), Length(max=200)])

    # L'ancien `__init__` qui peuplait le SelectField est supprimé.
# ### FIN DE LA MODIFICATION ###


class RecipeForm(FlaskForm):
    """
    Formulaire principal pour la création et l'édition d'une recette.
    """
    name = StringField('Nom de la recette', validators=[DataRequired("Le nom est requis."), Length(max=100)])
    description = TextAreaField('Description / Instructions', validators=[Optional(), Length(max=5000)])
    
    production_location = SelectField(
        'Lieu de Production (Source des Ingrédients)', 
        validators=[DataRequired()],
        choices=StockLocationManager.get_production_choices()
    )

    yield_quantity = IntegerField(
        'Quantité Produite', 
        validators=[DataRequired(), NumberRange(min=1)], 
        default=1,
        description="Combien d'unités cette recette produit-elle ? (ex: 112)"
    )
    yield_unit = StringField(
        'Unité Produite', 
        validators=[DataRequired(), Length(max=50)], 
        default='pièces',
        description="Quelle est l'unité ? (ex: pièces, portions, gâteaux)"
    )

    finished_product = SelectField('Produit Fini Associé', coerce=int, validators=[Optional()])
    
    ingredients = FieldList(FormField(IngredientForm), min_entries=1, label="Ingrédients")
    submit = SubmitField('Enregistrer la Recette')

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        
        recipe_obj = kwargs.get('obj')
        query = Product.query.filter_by(product_type='finished')
        
        if recipe_obj and recipe_obj.product_id:
            query = query.filter(or_(Product.recipe_definition == None, Product.id == recipe_obj.product_id))
        else:
            query = query.filter(Product.recipe_definition == None)
        
        self.finished_product.choices = [(p.id, p.name) for p in query.order_by(Product.name).all()]
        self.finished_product.choices.insert(0, (0, '-- Aucun --'))