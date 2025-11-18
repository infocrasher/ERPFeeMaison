"""
Formulaires pour la gestion des clients particuliers
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, DateField, 
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, Email, ValidationError
from datetime import date


class CustomerForm(FlaskForm):
    """Formulaire pour créer/modifier un client particulier"""
    
    # Informations personnelles
    first_name = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est obligatoire"),
        Length(min=2, max=100, message="Le prénom doit contenir entre 2 et 100 caractères")
    ])
    
    last_name = StringField('Nom de famille', validators=[
        DataRequired(message="Le nom de famille est obligatoire"),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères")
    ])
    
    phone = StringField('Téléphone', validators=[
        DataRequired(message="Le téléphone est obligatoire"),
        Length(min=10, max=20, message="Le téléphone doit contenir entre 10 et 20 caractères")
    ])
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message="Format d'email invalide"),
        Length(max=120, message="L'email ne peut pas dépasser 120 caractères")
    ])
    
    # Adresses
    address = TextAreaField('Adresse principale', validators=[
        Optional(),
        Length(max=500, message="L'adresse ne peut pas dépasser 500 caractères")
    ])
    
    delivery_address = TextAreaField('Adresse de livraison (si différente)', validators=[
        Optional(),
        Length(max=500, message="L'adresse de livraison ne peut pas dépasser 500 caractères")
    ])
    
    # Informations complémentaires
    birth_date = DateField('Date de naissance', validators=[Optional()])
    
    customer_type = SelectField('Type de client', choices=[
        ('regular', 'Régulier'),
        ('vip', 'VIP'),
        ('occasional', 'Occasionnel'),
        ('corporate', 'Entreprise (particulier)')
    ], default='regular')
    
    preferred_delivery = SelectField('Préférence de livraison', choices=[
        ('pickup', 'Retrait en magasin'),
        ('delivery', 'Livraison à domicile'),
        ('both', 'Les deux')
    ], default='pickup')
    
    # Historique et préférences
    notes = TextAreaField('Notes générales', validators=[
        Optional(),
        Length(max=1000, message="Les notes ne peuvent pas dépasser 1000 caractères")
    ])
    
    allergies = TextAreaField('Allergies alimentaires', validators=[
        Optional(),
        Length(max=500, message="Les allergies ne peuvent pas dépasser 500 caractères")
    ])
    
    preferences = TextAreaField('Préférences culinaires', validators=[
        Optional(),
        Length(max=500, message="Les préférences ne peuvent pas dépasser 500 caractères")
    ])
    
    # Statut
    is_active = BooleanField('Client actif', default=True)
    
    submit = SubmitField('Enregistrer')
    
    def validate_phone(self, field):
        """Validation personnalisée du téléphone"""
        phone = field.data.replace(' ', '').replace('-', '').replace('.', '')
        if not phone.isdigit():
            raise ValidationError('Le téléphone ne doit contenir que des chiffres.')
        if len(phone) < 10:
            raise ValidationError('Le téléphone doit contenir au moins 10 chiffres.')
    
    def validate_birth_date(self, field):
        """Validation de la date de naissance"""
        if field.data and field.data > date.today():
            raise ValidationError('La date de naissance ne peut pas être dans le futur.')


class CustomerSearchForm(FlaskForm):
    """Formulaire de recherche de clients"""
    
    search = StringField('Rechercher un client', validators=[
        Optional(),
        Length(max=200)
    ], render_kw={'placeholder': 'Nom, prénom, téléphone...'})
    
    customer_type = SelectField('Type', choices=[
        ('', 'Tous les types'),
        ('regular', 'Régulier'),
        ('vip', 'VIP'),
        ('occasional', 'Occasionnel'),
        ('corporate', 'Entreprise (particulier)')
    ], default='')
    
    preferred_delivery = SelectField('Préférence livraison', choices=[
        ('', 'Toutes'),
        ('pickup', 'Retrait en magasin'),
        ('delivery', 'Livraison à domicile'),
        ('both', 'Les deux')
    ], default='')
    
    is_active = SelectField('Statut', choices=[
        ('', 'Tous'),
        ('true', 'Actifs'),
        ('false', 'Inactifs')
    ], default='')
    
    submit = SubmitField('Rechercher')


class QuickCustomerForm(FlaskForm):
    """Formulaire rapide pour créer un client lors d'une commande"""
    
    first_name = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est obligatoire"),
        Length(min=2, max=100)
    ])
    
    last_name = StringField('Nom', validators=[
        DataRequired(message="Le nom est obligatoire"),
        Length(min=2, max=100)
    ])
    
    phone = StringField('Téléphone', validators=[
        DataRequired(message="Le téléphone est obligatoire"),
        Length(min=10, max=20)
    ])
    
    address = TextAreaField('Adresse', validators=[Optional()])
    
    submit = SubmitField('Créer client')









