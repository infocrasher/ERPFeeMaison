"""
Formulaires pour le module comptabilité
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, DecimalField, 
                     DateField, BooleanField, SubmitField, FieldList, FormField, IntegerField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import date
from .models import AccountType, AccountNature, JournalType


class AccountForm(FlaskForm):
    """Formulaire pour créer/modifier un compte comptable"""
    code = StringField('Code compte', validators=[
        DataRequired(message="Le code est obligatoire"),
        Length(min=3, max=10, message="Le code doit faire entre 3 et 10 caractères")
    ])
    name = StringField('Libellé', validators=[
        DataRequired(message="Le libellé est obligatoire"),
        Length(max=200, message="Le libellé ne peut pas dépasser 200 caractères")
    ])
    account_type = SelectField('Type de compte', 
                              choices=[(t.value, f"Classe {t.value}") for t in AccountType],
                              validators=[DataRequired(message="Le type est obligatoire")])
    account_nature = SelectField('Nature', 
                                choices=[(n.value, n.value.title()) for n in AccountNature],
                                validators=[DataRequired(message="La nature est obligatoire")])
    parent_id = SelectField('Compte parent', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Actif', default=True)
    is_detail = BooleanField('Compte de détail', default=True)
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les comptes parents possibles
        from .models import Account
        accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
        self.parent_id.choices = [(0, 'Aucun')] + [(a.id, f"{a.code} - {a.name}") for a in accounts]


class JournalForm(FlaskForm):
    """Formulaire pour créer/modifier un journal"""
    code = StringField('Code journal', validators=[
        DataRequired(message="Le code est obligatoire"),
        Length(min=2, max=5, message="Le code doit faire entre 2 et 5 caractères")
    ])
    name = StringField('Libellé', validators=[
        DataRequired(message="Le libellé est obligatoire"),
        Length(max=100, message="Le libellé ne peut pas dépasser 100 caractères")
    ])
    journal_type = SelectField('Type de journal',
                              choices=[(t.value, t.name.replace('_', ' ').title()) for t in JournalType],
                              validators=[DataRequired(message="Le type est obligatoire")])
    default_debit_account_id = SelectField('Compte débit par défaut', coerce=int, validators=[Optional()])
    default_credit_account_id = SelectField('Compte crédit par défaut', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Actif', default=True)
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les comptes disponibles
        from .models import Account
        accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
        choices = [(0, 'Aucun')] + [(a.id, f"{a.code} - {a.name}") for a in accounts]
        self.default_debit_account_id.choices = choices
        self.default_credit_account_id.choices = choices


class JournalEntryLineForm(FlaskForm):
    """Formulaire pour une ligne d'écriture"""
    account_id = SelectField('Compte', coerce=int, validators=[DataRequired(message="Le compte est obligatoire")])
    debit_amount = DecimalField('Débit', validators=[Optional(), NumberRange(min=0)], places=2)
    credit_amount = DecimalField('Crédit', validators=[Optional(), NumberRange(min=0)], places=2)
    line_description = StringField('Libellé', validators=[Optional(), Length(max=255)])
    reference = StringField('Référence', validators=[Optional(), Length(max=100)])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les comptes de détail
        from .models import Account
        accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
        self.account_id.choices = [(a.id, f"{a.code} - {a.name}") for a in accounts]


class JournalEntryForm(FlaskForm):
    """Formulaire pour créer/modifier une écriture comptable"""
    journal_id = SelectField('Journal', coerce=int, validators=[DataRequired(message="Le journal est obligatoire")])
    entry_date = DateField('Date d\'écriture', default=date.today, validators=[DataRequired(message="La date est obligatoire")])
    accounting_date = DateField('Date comptable', default=date.today, validators=[DataRequired(message="La date comptable est obligatoire")])
    description = StringField('Description', validators=[
        DataRequired(message="La description est obligatoire"),
        Length(max=255, message="La description ne peut pas dépasser 255 caractères")
    ])
    reference_document = StringField('Référence document', validators=[Optional(), Length(max=100)])
    
    # Lignes d'écriture (dynamiques)
    lines = FieldList(FormField(JournalEntryLineForm), min_entries=2)
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les journaux actifs
        from .models import Journal
        journals = Journal.query.filter_by(is_active=True).order_by(Journal.code).all()
        self.journal_id.choices = [(j.id, f"{j.code} - {j.name}") for j in journals]
    
    def validate(self, extra_validators=None):
        """Validation personnalisée pour l'équilibre débit/crédit"""
        if not super().validate(extra_validators):
            return False
        
        total_debit = sum(float(line.debit_amount.data or 0) for line in self.lines)
        total_credit = sum(float(line.credit_amount.data or 0) for line in self.lines)
        
        if abs(total_debit - total_credit) > 0.01:
            self.lines.errors.append("L'écriture doit être équilibrée (total débit = total crédit)")
            return False
        
        # Vérifier qu'au moins une ligne a un montant
        has_amount = any(
            (line.debit_amount.data and line.debit_amount.data > 0) or 
            (line.credit_amount.data and line.credit_amount.data > 0)
            for line in self.lines
        )
        
        if not has_amount:
            self.lines.errors.append("Au moins une ligne doit avoir un montant")
            return False
        
        return True


class FiscalYearForm(FlaskForm):
    """Formulaire pour créer/modifier un exercice comptable"""
    name = StringField('Nom de l\'exercice', validators=[
        DataRequired(message="Le nom est obligatoire"),
        Length(max=50, message="Le nom ne peut pas dépasser 50 caractères")
    ])
    start_date = DateField('Date de début', validators=[DataRequired(message="La date de début est obligatoire")])
    end_date = DateField('Date de fin', validators=[DataRequired(message="La date de fin est obligatoire")])
    is_current = BooleanField('Exercice courant')
    submit = SubmitField('Enregistrer')
    
    def validate_end_date(self, field):
        """Valider que la date de fin est après la date de début"""
        if self.start_date.data and field.data:
            if field.data <= self.start_date.data:
                raise ValidationError("La date de fin doit être postérieure à la date de début")


class AccountSearchForm(FlaskForm):
    """Formulaire de recherche de comptes"""
    search = StringField('Rechercher', validators=[Optional()])
    account_type = SelectField('Type', choices=[('', 'Tous')] + [(t.value, f"Classe {t.value}") for t in AccountType], validators=[Optional()])
    is_active = SelectField('Statut', choices=[('', 'Tous'), ('1', 'Actifs'), ('0', 'Inactifs')], validators=[Optional()])
    submit = SubmitField('Filtrer')


class JournalEntrySearchForm(FlaskForm):
    """Formulaire de recherche d'écritures"""
    search = StringField('Rechercher', validators=[Optional()])
    journal_id = SelectField('Journal', coerce=int, validators=[Optional()])
    date_from = DateField('Du', validators=[Optional()])
    date_to = DateField('Au', validators=[Optional()])
    is_validated = SelectField('Statut', choices=[('', 'Tous'), ('1', 'Validées'), ('0', 'Brouillons')], validators=[Optional()])
    submit = SubmitField('Filtrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les journaux
        from .models import Journal
        journals = Journal.query.filter_by(is_active=True).order_by(Journal.code).all()
        self.journal_id.choices = [(0, 'Tous')] + [(j.id, f"{j.code} - {j.name}") for j in journals]


class ExpenseForm(FlaskForm):
    """Formulaire pour enregistrer une dépense courante"""
    date = DateField('Date', default=date.today, validators=[DataRequired(message="La date est obligatoire")])
    description = StringField('Description', validators=[
        DataRequired(message="La description est obligatoire"),
        Length(max=255, message="La description ne peut pas dépasser 255 caractères")
    ])
    amount = DecimalField('Montant', validators=[
        DataRequired(message="Le montant est obligatoire"),
        NumberRange(min=0.01, message="Le montant doit être positif")
    ], places=2)
    category = SelectField('Catégorie', validators=[DataRequired(message="La catégorie est obligatoire")])
    other_category = StringField('Précision (optionnel)', validators=[Optional(), Length(max=100)])
    payment_method = SelectField('Mode de paiement', choices=[
        ('bank', 'Banque'),
        ('cash', 'Caisse')
    ], default='bank', validators=[DataRequired(message="Le mode de paiement est obligatoire")])
    supplier = StringField('Fournisseur/Bénéficiaire', validators=[Optional(), Length(max=100)])
    reference = StringField('Référence (facture, reçu...)', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_paid = BooleanField('Payé automatiquement', default=True)
    submit = SubmitField('Enregistrer et Déduire de la Banque')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Catégories de charges basées sur les comptes comptables existants
        self.category.choices = [
            ('613', 'Loyer (613 - Locations)'),
            ('615', 'Réparations (615 - Entretien et réparations)'),
            ('616', 'Assurance (616 - Primes d\'assurance)'),
            ('621', 'Personnel extérieur (621)'),
            ('625', 'Déplacements (625)'),
            ('626', 'Frais postaux et téléphone (626)'),
            ('627', 'Services bancaires (627)'),
            ('628', 'Divers (628)'),
            ('641', 'Salaires (641 - Rémunérations du personnel)'),
            ('645', 'Charges sociales (645)'),
            ('658', 'Charges diverses (658)'),
            ('661', 'Charges financières (661)'),
            ('681', 'Amortissements (681)')
        ]
    
    def validate(self, extra_validators=None):
        """Validation personnalisée"""
        if not super().validate(extra_validators):
            return False
        
        # Si la catégorie est "628" (Divers), le champ other_category peut être utilisé pour préciser
        # Mais ce n'est pas obligatoire
        
        return True


class BusinessConfigForm(FlaskForm):
    """Formulaire de configuration des objectifs métier"""
    
    # Objectifs financiers
    monthly_objective = DecimalField('Objectif mensuel (DZD)', validators=[
        DataRequired(message="L'objectif mensuel est obligatoire"),
        NumberRange(min=1, message="L'objectif doit être positif")
    ], places=2)
    
    daily_objective = DecimalField('Objectif journalier (DZD)', validators=[
        DataRequired(message="L'objectif journalier est obligatoire"),
        NumberRange(min=1, message="L'objectif doit être positif")
    ], places=2)
    
    yearly_objective = DecimalField('Objectif annuel (DZD)', validators=[
        DataRequired(message="L'objectif annuel est obligatoire"),
        NumberRange(min=1, message="L'objectif doit être positif")
    ], places=2)
    
    # Paramètres stock
    stock_rotation_days = IntegerField('Période rotation stock (jours)', validators=[
        DataRequired(message="La période est obligatoire"),
        NumberRange(min=1, max=365, message="Entre 1 et 365 jours")
    ], default=30)
    
    # Paramètres qualité
    quality_target_percent = DecimalField('Objectif qualité (%)', validators=[
        DataRequired(message="L'objectif qualité est obligatoire"),
        NumberRange(min=50, max=100, message="Entre 50% et 100%")
    ], places=1, default=95.0)
    
    # Paramètres RH
    standard_work_hours_per_day = DecimalField('Heures standard/jour', validators=[
        DataRequired(message="Les heures standard sont obligatoires"),
        NumberRange(min=1, max=12, message="Entre 1 et 12 heures")
    ], places=1, default=8.0)
    
    submit = SubmitField('Enregistrer la Configuration') 