"""
Formulaires pour la gestion des fournisseurs
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, IntegerField, 
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, Email, NumberRange


class SupplierForm(FlaskForm):
    """Formulaire pour créer/modifier un fournisseur"""
    
    # Informations principales
    company_name = StringField('Nom de l\'entreprise', validators=[
        DataRequired(message="Le nom de l'entreprise est obligatoire"),
        Length(min=2, max=200, message="Le nom doit contenir entre 2 et 200 caractères")
    ])
    
    contact_person = StringField('Personne de contact', validators=[
        Optional(),
        Length(max=100, message="Le nom ne peut pas dépasser 100 caractères")
    ])
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message="Format d'email invalide"),
        Length(max=120, message="L'email ne peut pas dépasser 120 caractères")
    ])
    
    phone = StringField('Téléphone', validators=[
        Optional(),
        Length(max=20, message="Le téléphone ne peut pas dépasser 20 caractères")
    ])
    
    address = TextAreaField('Adresse', validators=[
        Optional(),
        Length(max=500, message="L'adresse ne peut pas dépasser 500 caractères")
    ])
    
    # Informations commerciales
    tax_number = StringField('NIF/RC', validators=[
        Optional(),
        Length(max=50, message="Le NIF ne peut pas dépasser 50 caractères")
    ])
    
    payment_terms = IntegerField('Délai de paiement (jours)', validators=[
        Optional(),
        NumberRange(min=0, max=365, message="Le délai doit être entre 0 et 365 jours")
    ], default=30)
    
    bank_details = TextAreaField('Coordonnées bancaires (RIB)', validators=[
        Optional(),
        Length(max=500, message="Les coordonnées bancaires ne peuvent pas dépasser 500 caractères")
    ])
    
    # Catégorisation
    supplier_type = SelectField('Type de fournisseur', choices=[
        ('general', 'Général'),
        ('ingredients', 'Ingrédients'),
        ('equipment', 'Équipements'),
        ('services', 'Services'),
        ('packaging', 'Emballages'),
        ('maintenance', 'Maintenance')
    ], default='general')
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=1000, message="Les notes ne peuvent pas dépasser 1000 caractères")
    ])
    
    # Statut
    is_active = BooleanField('Fournisseur actif', default=True)
    
    submit = SubmitField('Enregistrer')
    
    def validate_company_name(self, field):
        """Validation personnalisée du nom de l'entreprise"""
        if len(field.data.strip()) < 2:
            raise ValidationError('Le nom de l\'entreprise doit contenir au moins 2 caractères.')


class SupplierSearchForm(FlaskForm):
    """Formulaire de recherche de fournisseurs"""
    
    search = StringField('Rechercher un fournisseur', validators=[
        Optional(),
        Length(max=200)
    ], render_kw={'placeholder': 'Nom, contact, téléphone...'})
    
    supplier_type = SelectField('Type', choices=[
        ('', 'Tous les types'),
        ('general', 'Général'),
        ('ingredients', 'Ingrédients'),
        ('equipment', 'Équipements'),
        ('services', 'Services'),
        ('packaging', 'Emballages'),
        ('maintenance', 'Maintenance')
    ], default='')
    
    is_active = SelectField('Statut', choices=[
        ('', 'Tous'),
        ('true', 'Actifs'),
        ('false', 'Inactifs')
    ], default='')
    
    submit = SubmitField('Rechercher')


# Import nécessaire pour ValidationError
from wtforms.validators import ValidationError











