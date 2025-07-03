"""
Formulaires pour le module comptabilité
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, DecimalField, 
                     DateField, BooleanField, SubmitField, FieldList, FormField)
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
    description = StringField('Libellé', validators=[Optional(), Length(max=255)])
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