"""
Formulaires pour le module d'inventaire
Module: app/inventory/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    DateField, BooleanField, TextAreaField, SubmitField, 
    FloatField, SelectField, HiddenField, IntegerField, FieldList, FormField
)
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from datetime import date, datetime
from app.inventory.models import AdjustmentReason, InventoryStatus, WasteReason

class CreateInventoryForm(FlaskForm):
    """Formulaire de création d'un nouvel inventaire"""
    
    inventory_date = DateField(
        'Date d\'inventaire', 
        validators=[DataRequired()],
        default=date.today,
        description="Date de fin de mois pour l'inventaire"
    )
    
    # Emplacements à inclure (comptoir exclu selon vos spécifications)
    include_ingredients_magasin = BooleanField(
        'Magasin (Labo A)', 
        default=True,
        description="Inclure le stock du magasin dans l'inventaire"
    )
    
    include_ingredients_local = BooleanField(
        'Local (Labo B)', 
        default=True,
        description="Inclure le stock du local dans l'inventaire"
    )
    
    include_consommables = BooleanField(
        'Consommables', 
        default=True,
        description="Inclure le stock de consommables dans l'inventaire"
    )
    
    notes = TextAreaField(
        'Notes',
        description="Notes ou commentaires sur cet inventaire"
    )
    
    submit = SubmitField('Créer l\'inventaire')
    
    def validate(self, extra_validators=None):
        """Validation personnalisée"""
        if not super().validate(extra_validators):
            return False
        
        # Au moins un emplacement doit être sélectionné
        if not (self.include_ingredients_magasin.data or 
                self.include_ingredients_local.data or 
                self.include_consommables.data):
            self.include_ingredients_magasin.errors.append(
                "Au moins un emplacement doit être sélectionné"
            )
            return False
        
        return True

class InventoryItemForm(FlaskForm):
    """Formulaire de saisie d'une ligne d'inventaire"""
    
    inventory_item_id = HiddenField()
    product_id = HiddenField()
    location_type = HiddenField()
    
    theoretical_stock = FloatField(
        'Stock théorique',
        render_kw={'readonly': True, 'class': 'form-control-plaintext'}
    )
    
    physical_stock = FloatField(
        'Stock physique',
        validators=[
            DataRequired(message="Le stock physique est obligatoire"),
            NumberRange(min=0, message="Le stock ne peut pas être négatif")
        ],
        description="Stock réellement compté"
    )
    
    adjustment_reason = SelectField(
        'Motif de l\'écart',
        choices=[
            ('', 'Sélectionner un motif...'),
            (AdjustmentReason.INVENDU_DONNE.value, 'Invendu donné gratuitement'),
            (AdjustmentReason.PEREMPTION.value, 'Produit périmé'),
            (AdjustmentReason.VOL_PERTE.value, 'Vol ou perte'),
            (AdjustmentReason.ERREUR_SAISIE.value, 'Erreur de saisie antérieure'),
            (AdjustmentReason.VENTE_NON_ENREGISTREE.value, 'Vente non enregistrée'),
            (AdjustmentReason.PRODUCTION_NON_DECLAREE.value, 'Production non déclarée'),
            (AdjustmentReason.AUTRE.value, 'Autre motif')
        ],
        validators=[Optional()]
    )
    
    notes = TextAreaField(
        'Commentaires',
        description="Commentaires sur cet écart"
    )
    
    submit = SubmitField('Enregistrer')

class BulkInventoryForm(FlaskForm):
    """Formulaire de saisie en lot pour l'inventaire"""
    
    location_type = SelectField(
        'Emplacement',
        choices=[
            ('ingredients_magasin', 'Magasin (Labo A)'),
            ('ingredients_local', 'Local (Labo B)'),
            ('consommables', 'Consommables')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Charger les produits')

class ValidateInventoryForm(FlaskForm):
    """Formulaire de validation d'un inventaire"""
    
    validation_notes = TextAreaField(
        'Notes de validation',
        description="Commentaires sur la validation de cet inventaire"
    )
    
    apply_adjustments = BooleanField(
        'Appliquer les ajustements',
        default=True,
        description="Appliquer automatiquement les ajustements de stock"
    )
    
    submit = SubmitField('Valider l\'inventaire')

class InventorySearchForm(FlaskForm):
    """Formulaire de recherche d'inventaires"""
    
    year = SelectField(
        'Année',
        choices=[],  # Sera rempli dynamiquement
        validators=[Optional()]
    )
    
    month = SelectField(
        'Mois',
        choices=[
            ('', 'Tous les mois'),
            ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
            ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
            ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
            ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
        ],
        validators=[Optional()]
    )
    
    status = SelectField(
        'Statut',
        choices=[
            ('', 'Tous les statuts'),
            (InventoryStatus.EN_COURS.value, 'En cours'),
            (InventoryStatus.COMPLETE.value, 'Terminé'),
            (InventoryStatus.VALIDE.value, 'Validé'),
            (InventoryStatus.CLOTURE.value, 'Clôturé')
        ],
        validators=[Optional()]
    )
    
    submit = SubmitField('Rechercher')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Générer les choix d'années (5 dernières années + année courante + 1 année future)
        current_year = datetime.now().year
        years = [('', 'Toutes les années')]
        for year in range(current_year - 4, current_year + 2):
            years.append((str(year), str(year)))
        self.year.choices = years

class QuickCountForm(FlaskForm):
    """Formulaire de saisie rapide pour mobile"""
    
    product_search = HiddenField()  # Pour la recherche de produit
    physical_stock = FloatField(
        'Quantité comptée',
        validators=[
            DataRequired(message="La quantité est obligatoire"),
            NumberRange(min=0, message="La quantité ne peut pas être négative")
        ]
    )
    
    has_variance = BooleanField('Écart détecté')
    
    quick_reason = SelectField(
        'Motif rapide',
        choices=[
            ('', 'Pas d\'écart'),
            (AdjustmentReason.INVENDU_DONNE.value, 'Invendu donné'),
            (AdjustmentReason.PEREMPTION.value, 'Périmé'),
            (AdjustmentReason.VOL_PERTE.value, 'Perte'),
            (AdjustmentReason.AUTRE.value, 'Autre')
        ],
        validators=[Optional()]
    )
    
    submit = SubmitField('Suivant')

class InventoryReportForm(FlaskForm):
    """Formulaire de génération de rapports d'inventaire"""
    
    inventory_id = SelectField(
        'Inventaire',
        choices=[],  # Sera rempli dynamiquement
        validators=[DataRequired()]
    )
    
    report_type = SelectField(
        'Type de rapport',
        choices=[
            ('summary', 'Résumé des écarts'),
            ('detailed', 'Rapport détaillé'),
            ('variance_only', 'Écarts uniquement'),
            ('critical_only', 'Écarts critiques uniquement'),
            ('by_location', 'Par emplacement'),
            ('valuation', 'Valorisation des écarts')
        ],
        validators=[DataRequired()]
    )
    
    format_type = SelectField(
        'Format',
        choices=[
            ('html', 'Affichage web'),
            ('pdf', 'PDF'),
            ('excel', 'Excel')
        ],
        default='html',
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Générer le rapport')

# Formulaires pour la gestion des invendus et inventaire hebdomadaire

def coerce_int_or_none(value):
    """Convertir en int ou None si vide"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class DailyWasteLineForm(FlaskForm):
    """Formulaire pour une ligne d'invendu"""
    product_id = SelectField('Produit', coerce=coerce_int_or_none, validators=[Optional()])
    quantity = FloatField('Quantité', validators=[Optional(), NumberRange(min=0.001)], render_kw={"step": "0.001"})
    reason = SelectField('Raison', choices=[
        ('', '-- Sélectionner --'),
        ('peremption', 'Péremption'),
        ('invendu', 'Invendu'),
        ('casse', 'Casse'),
        ('don', 'Don gratuit')
    ], validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])

class DailyWasteForm(FlaskForm):
    """Formulaire de déclaration quotidienne des invendus (multi-produits)"""
    
    waste_date = DateField('Date de l\'invendu', validators=[DataRequired()], default=date.today)
    lines = FieldList(FormField(DailyWasteLineForm), min_entries=1)
    global_notes = TextAreaField('Notes générales', validators=[Optional()])
    submit = SubmitField('Déclarer les invendus')
    
    def validate_lines(self, field):
        """Valider qu'au moins une ligne est remplie"""
        valid_lines = 0
        for line in field.entries:
            product_id = line.product_id.data
            quantity = line.quantity.data
            reason = line.reason.data
            
            # Vérifier que tous les champs sont remplis et non vides
            if product_id and quantity and reason and reason != '':
                valid_lines += 1
        
        if valid_lines == 0:
            raise ValidationError('Vous devez déclarer au moins un produit invendu.')

class WeeklyComptoirInventoryForm(FlaskForm):
    """Formulaire de création d'inventaire hebdomadaire du comptoir"""
    
    inventory_date = DateField('Date de l\'inventaire', validators=[DataRequired()], default=date.today)
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Créer l\'inventaire hebdomadaire')

class WeeklyComptoirItemForm(FlaskForm):
    """Formulaire de saisie d'une ligne d'inventaire hebdomadaire"""
    
    physical_stock = FloatField('Stock Physique', validators=[DataRequired(), NumberRange(min=0)], render_kw={"step": "0.001"})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class WeeklyComptoirSearchForm(FlaskForm):
    """Formulaire de recherche pour les inventaires hebdomadaires"""
    
    year = SelectField('Année', choices=[], validators=[Optional()])
    week = SelectField('Semaine', choices=[], validators=[Optional()])
    status = SelectField('Statut', choices=[
        ('EN_COURS', 'En cours'),
        ('COMPLETE', 'Complète'),
        ('VALIDE', 'Validée'),
        ('CLOTURE', 'Clôturée'),
        ('', 'Tous')
    ], validators=[Optional()], default='')
    submit = SubmitField('Filtrer')
