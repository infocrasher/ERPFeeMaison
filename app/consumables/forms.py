"""
Formulaires pour la gestion des consommables
Module: app/consumables/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    DateField, FloatField, SelectField, TextAreaField, SubmitField,
    IntegerField, StringField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import date

class ConsumableUsageForm(FlaskForm):
    """Formulaire de saisie d'utilisation de consommable"""
    
    product_id = SelectField('Consommable', coerce=int, validators=[DataRequired()])
    usage_date = DateField('Date d\'utilisation', validators=[DataRequired()], default=date.today)
    actual_quantity_used = FloatField('Quantité réellement utilisée', validators=[DataRequired(), NumberRange(min=0.001)], render_kw={"step": "0.001"})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer l\'utilisation')

class ConsumableAdjustmentForm(FlaskForm):
    """Formulaire d'ajustement de consommable"""
    
    product_id = SelectField('Consommable', coerce=int, validators=[DataRequired()])
    adjustment_date = DateField('Date d\'ajustement', validators=[DataRequired()], default=date.today)
    adjustment_type = SelectField('Type d\'ajustement', choices=[
        ('inventory', 'Inventaire'),
        ('waste', 'Perte/Invendu'),
        ('correction', 'Correction d\'erreur')
    ], validators=[DataRequired()])
    quantity_adjusted = FloatField('Quantité ajustée', validators=[DataRequired()], render_kw={"step": "0.001"})
    reason = StringField('Raison', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer l\'ajustement')

class ConsumableRecipeForm(FlaskForm):
    """Formulaire de recette de consommable"""
    
    finished_product_id = SelectField('Produit fini', coerce=int, validators=[DataRequired()])
    consumable_product_id = SelectField('Consommable', coerce=int, validators=[DataRequired()])
    quantity_per_unit = FloatField('Quantité par unité', validators=[DataRequired(), NumberRange(min=0.001)], render_kw={"step": "0.001"})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer la recette')

class ConsumableSearchForm(FlaskForm):
    """Formulaire de recherche pour les consommables"""
    
    start_date = DateField('Date de début', validators=[Optional()])
    end_date = DateField('Date de fin', validators=[Optional()])
    product_id = SelectField('Consommable', coerce=int, validators=[Optional()])
    submit = SubmitField('Filtrer')

class ConsumableCategoryForm(FlaskForm):
    """Formulaire de catégorie de consommables"""
    
    name = StringField('Nom de la catégorie', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    product_category_id = SelectField('Catégorie de produits', coerce=int, validators=[DataRequired()])
    is_active = SelectField('Statut', choices=[(True, 'Active'), (False, 'Inactive')], coerce=bool, default=True)
    submit = SubmitField('Enregistrer')

class ConsumableRangeForm(FlaskForm):
    """Formulaire pour une plage de quantités"""
    
    min_quantity = IntegerField('Quantité min', validators=[DataRequired(), NumberRange(min=1)])
    max_quantity = IntegerField('Quantité max', validators=[DataRequired(), NumberRange(min=1)])
    consumable_product_id = SelectField('Consommable', coerce=int, validators=[DataRequired()])
    quantity_per_unit = FloatField('Quantité par unité', validators=[DataRequired(), NumberRange(min=0.001)], default=1.0, render_kw={"step": "0.001"})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Ajouter la plage')

