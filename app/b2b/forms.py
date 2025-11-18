"""
Formulaires pour le module B2B
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, DecimalField, 
                     DateField, BooleanField, SubmitField, FieldList, FormField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import date, datetime, timedelta
from models import Product


class B2BClientForm(FlaskForm):
    """Formulaire pour créer/modifier un client B2B"""
    company_name = StringField('Nom de l\'entreprise', validators=[
        DataRequired(message="Le nom de l'entreprise est obligatoire"),
        Length(max=200, message="Le nom ne peut pas dépasser 200 caractères")
    ])
    contact_person = StringField('Personne de contact', validators=[
        Optional(),
        Length(max=100, message="Le nom ne peut pas dépasser 100 caractères")
    ])
    email = StringField('Email', validators=[
        Optional(),
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
    tax_number = StringField('NIF', validators=[
        Optional(),
        Length(max=50, message="Le NIF ne peut pas dépasser 50 caractères")
    ])
    payment_terms = SelectField('Conditions de paiement', choices=[
        (30, '30 jours'),
        (45, '45 jours'),
        (60, '60 jours'),
        (0, 'Comptant')
    ], coerce=int, default=30)
    credit_limit = DecimalField('Limite de crédit (DA)', validators=[
        Optional(),
        NumberRange(min=0, message="La limite doit être positive")
    ], places=2, default=0.0)
    is_active = BooleanField('Client actif', default=True)
    submit = SubmitField('Enregistrer')


class B2BOrderItemForm(FlaskForm):
    """Formulaire pour une ligne de commande B2B"""
    class Meta:
        csrf = False
    
    product = SelectField(
        'Produit',
        choices=[('', '-- Choisir un produit --')],
        validators=[DataRequired("Veuillez sélectionner un produit.")]
    )
    
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired("La quantité est requise."), NumberRange(min=0.001)],
        default=1
    )
    
    unit_price = DecimalField(
        'Prix unitaire (DA)',
        validators=[DataRequired("Le prix est requis."), NumberRange(min=0)],
        places=2
    )
    
    description = StringField(
        'Description personnalisée',
        validators=[Optional(), Length(max=255)]
    )


class B2BOrderForm(FlaskForm):
    """Formulaire pour créer/modifier une commande B2B"""
    b2b_client_id = SelectField('Client B2B', coerce=int, validators=[
        DataRequired(message="Le client est obligatoire")
    ])
    
    delivery_date = DateField('Date de livraison', validators=[
        DataRequired(message="La date de livraison est obligatoire")
    ])
    
    is_multi_day = BooleanField('Commande sur plusieurs jours')
    period_start = DateField('Début de période', validators=[Optional()])
    period_end = DateField('Fin de période', validators=[Optional()])
    
    items = FieldList(FormField(B2BOrderItemForm), min_entries=0)
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Enregistrer la commande')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les clients B2B actifs
        from models import B2BClient
        clients = B2BClient.query.filter_by(is_active=True).order_by(B2BClient.company_name).all()
        self.b2b_client_id.choices = [(c.id, c.company_name) for c in clients]

        # Charger les produits finis + option produit composé
        products = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
        product_choices = [('', '-- Choisir un produit --')]
        
        # Ajouter option pour produits composés
        product_choices.append(('composite', '🧩 Produit composé'))
        
        for product in products:
            price = product.price or 0.0
            label = f"{product.name} ({price:.2f} DA / {product.unit})"
            product_choices.append((str(product.id), label))

        for item_form in self.items:
            item_form.product.choices = product_choices
    
    def validate(self, extra_validators=None):
        """Validation personnalisée"""
        if not super().validate(extra_validators):
            return False

        # Validation de la période multi-jours
        if self.is_multi_day.data:
            if not self.period_start.data or not self.period_end.data:
                self.period_start.errors.append("Les dates de période sont obligatoires pour une commande multi-jours")
                return False
            if self.period_start.data >= self.period_end.data:
                self.period_end.errors.append("La date de fin doit être postérieure à la date de début")
                return False

        # Validation des items (modifiée pour gérer les produits composés)
        if not self.items.data:
            self.items.errors.append("Au moins un produit doit être sélectionné")
            return False
        
        # Vérifier qu'il y a au moins un item valide (produit normal ou composé)
        has_valid_items = False
        for item in self.items.data:
            product_value = item.get('product', '').strip()
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            
            # Item valide si : produit sélectionné OU produit composé, avec quantité et prix > 0
            if product_value and quantity > 0 and unit_price > 0:
                if product_value == 'composite' or product_value.isdigit():
                    has_valid_items = True
                    break
        
        if not has_valid_items:
            self.items.errors.append("Au moins un produit valide doit être ajouté avec quantité et prix")
            return False

        return True


class InvoiceItemForm(FlaskForm):
    """Formulaire pour une ligne de facture"""
    class Meta:
        csrf = False
    
    description = StringField(
        'Description',
        validators=[DataRequired("La description est requise."), Length(max=255)]
    )
    
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired("La quantité est requise."), NumberRange(min=0.001)],
        default=1
    )
    
    unit_price = DecimalField(
        'Prix unitaire (DA)',
        validators=[DataRequired("Le prix est requis."), NumberRange(min=0)],
        places=2
    )


class InvoiceForm(FlaskForm):
    """Formulaire pour créer une facture"""
    b2b_client_id = SelectField('Client B2B', coerce=int, validators=[
        DataRequired(message="Le client est obligatoire")
    ])
    
    invoice_type = SelectField('Type de facture', choices=[
        ('proforma', 'Facture Proforma (Devis)'),
        ('final', 'Facture Définitive')
    ], validators=[DataRequired()])
    
    invoice_date = DateField('Date de facture', default=date.today, validators=[
        DataRequired(message="La date de facture est obligatoire")
    ])
    
    due_date = DateField('Date d\'échéance', validators=[
        DataRequired(message="La date d'échéance est obligatoire")
    ])
    
    payment_method = SelectField('Mode de paiement', choices=[
        ('cheque', 'Par chèque'),
        ('espece', 'En espèces'),
        ('virement', 'Par virement'),
        ('traite', 'Par traite')
    ], default='cheque', validators=[DataRequired(message="Le mode de paiement est obligatoire")])
    
    invoice_items = FieldList(FormField(InvoiceItemForm), min_entries=1)
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Créer la facture')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les clients B2B actifs
        from models import B2BClient
        clients = B2BClient.query.filter_by(is_active=True).order_by(B2BClient.company_name).all()
        self.b2b_client_id.choices = [(c.id, c.company_name) for c in clients]
    
    def validate(self, extra_validators=None):
        """Validation personnalisée"""
        if not super().validate(extra_validators):
            return False
        
        # La date d'échéance doit être postérieure à la date de facture
        if self.invoice_date.data and self.due_date.data:
            if self.due_date.data <= self.invoice_date.data:
                self.due_date.errors.append("La date d'échéance doit être postérieure à la date de facture")
                return False
        
        return True


class InvoiceFromOrderForm(FlaskForm):
    """Formulaire pour créer une facture depuis une commande"""
    invoice_type = SelectField(
        'Type de facture',
        choices=[('proforma', 'Proforma'), ('final', 'Définitive')],
        validators=[DataRequired()]
    )
    invoice_date = DateField('Date facture', default=date.today, validators=[DataRequired()])
    due_date = DateField('Échéance', default=lambda: date.today() + timedelta(days=30), validators=[DataRequired()])
    payment_method = SelectField('Mode de paiement', choices=[
        ('cheque', 'Par chèque'),
        ('espece', 'En espèces'),
        ('virement', 'Par virement'),
        ('traite', 'Par traite')
    ], default='cheque', validators=[DataRequired(message="Le mode de paiement est obligatoire")])
    notes = TextAreaField('Notes')
    submit = SubmitField('Créer la facture')


class EmailTemplateForm(FlaskForm):
    """Formulaire pour l'envoi d'email"""
    subject = StringField('Objet', validators=[
        DataRequired(message="L'objet est obligatoire"),
        Length(max=200, message="L'objet ne peut pas dépasser 200 caractères")
    ])
    
    message = TextAreaField('Message', validators=[
        DataRequired(message="Le message est obligatoire"),
        Length(max=5000, message="Le message ne peut pas dépasser 5000 caractères")
    ])
    
    send_copy = BooleanField('Envoyer une copie à Fée Maison', default=True)
    submit = SubmitField('Envoyer l\'email') 