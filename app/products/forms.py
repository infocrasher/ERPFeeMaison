# Fichier: app/products/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Category
from flask_wtf.file import FileField, FileAllowed

def category_query_factory():
    return Category.query.order_by(Category.name)

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    show_in_pos = BooleanField('Afficher au Point de Vente (POV)', default=True, 
                                description="Cocher pour afficher cette catégorie dans l'interface de vente")
    submit = SubmitField('Enregistrer')

class ProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    sku = StringField('SKU / Référence', validators=[Optional(), Length(max=50)])
    
    product_type = SelectField(
        'Type de Produit', 
        choices=[
            ('ingredient', 'Ingrédient'), 
            ('finished', 'Produit Fini'),
            ('consommable', 'Consommable')
        ], 
        validators=[DataRequired()]
    )
    
    # ### DEBUT DE LA CORRECTION ###
    # Le champ "Unité" devient un SelectField pour choisir l'unité de BASE
    unit = SelectField(
        'Unité de Base (pour Stock et Recettes)', 
        choices=[
            ('g', 'Grammes (g)'),
            ('ml', 'Millilitres (ml)'),
            ('pièce', 'Pièce / Unité')
        ], 
        validators=[DataRequired()]
    )
    # ### FIN DE LA CORRECTION ###

    price = FloatField('Prix de vente (DA)', validators=[Optional(), NumberRange(min=0)])
    
    # On clarifie le label pour le coût
    cost_price = FloatField("Coût de Revient Initial / PMP (DA par unité de base)", 
                            validators=[Optional(), NumberRange(min=0)],
                            description="Sera mis à jour automatiquement par les achats (PMP).")
    
    # Seuils d'alerte de stock par localisation
    seuil_min_comptoir = FloatField('Seuil Min Comptoir', validators=[Optional(), NumberRange(min=0)],
                                   render_kw={"placeholder": "Seuil d'alerte pour stock comptoir"})
    
    seuil_min_ingredients_local = FloatField('Seuil Min Local (Production)', validators=[Optional(), NumberRange(min=0)],
                                            render_kw={"placeholder": "Seuil d'alerte pour stock local"})
    
    seuil_min_ingredients_magasin = FloatField('Seuil Min Magasin (Réserve)', validators=[Optional(), NumberRange(min=0)],
                                                render_kw={"placeholder": "Seuil d'alerte pour stock magasin"})
    
    seuil_min_consommables = FloatField('Seuil Min Consommables', validators=[Optional(), NumberRange(min=0)],
                                       render_kw={"placeholder": "Seuil d'alerte pour stock consommables"})
    
    # On retire le champ 'quantity_in_stock' qui était source de confusion.
    # Le stock initial sera géré par un "Ajustement de stock" ou un premier achat.
    
    category = QuerySelectField('Catégorie', query_factory=category_query_factory, get_label='name', allow_blank=False)
    image = FileField('Photo du produit', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images uniquement !')])
    submit = SubmitField('Enregistrer le produit')