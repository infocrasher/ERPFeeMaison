# -*- coding: utf-8 -*-
"""
app/employees/forms.py
Formulaires pour la gestion des employés
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, BooleanField, TextAreaField, TimeField, HiddenField, IntegerField, DateField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import datetime, date, timedelta

class EmployeeForm(FlaskForm):
    name = StringField('Nom complet', validators=[
        DataRequired(message="Le nom est obligatoire"),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères")
    ])
    
    role = SelectField('Rôle', choices=[
        ('production', 'Employé Production'),
        ('chef_production', 'Chef de Production'),
        ('assistant_production', 'Assistant Production'),
        ('patissier', 'Pâtissier'),
        ('apprenti', 'Apprenti'),
        ('manager', 'Manager'),
        ('vendeur', 'Vendeur')
    ], validators=[DataRequired(message="Veuillez sélectionner un rôle")])
    
    salaire_fixe = DecimalField('Salaire fixe (DA)', validators=[
        Optional(),
        NumberRange(min=0, max=999999, message="Le salaire doit être positif")
    ], places=2)
    
    prime = DecimalField('Prime (DA)', validators=[
        Optional(),
        NumberRange(min=0, max=999999, message="La prime doit être positive")
    ], places=2, default=0)
    
    is_active = BooleanField('Employé actif', default=True)
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message="Les notes ne doivent pas dépasser 500 caractères")
    ])
    
    # ===== NOUVEAUX CHAMPS RH =====
    zk_user_id = IntegerField('ID Pointeuse', validators=[
        Optional(),
        NumberRange(min=1, message="L'ID pointeuse doit être positif")
    ])
    
    # Cotisations sociales
    is_insured = BooleanField('Employé assuré', default=False)
    insurance_amount = DecimalField('Montant cotisation (DA)', validators=[
        Optional(),
        NumberRange(min=0, max=999999, message="Le montant doit être positif")
    ], places=2, default=0)
    
    # Taux horaire pour heures sup
    hourly_rate = DecimalField('Taux horaire (DA/h)', validators=[
        Optional(),
        NumberRange(min=0, max=9999, message="Le taux horaire doit être positif")
    ], places=2)

class EmployeeSearchForm(FlaskForm):
    search = StringField('Rechercher un employé', validators=[Optional()])
    
    role_filter = SelectField('Filtrer par rôle', choices=[
        ('', 'Tous les rôles'),
        ('production', 'Production'),
        ('chef_production', 'Chef de Production'),
        ('assistant_production', 'Assistant Production'),
        ('patissier', 'Pâtissier'),
        ('apprenti', 'Apprenti'),
        ('manager', 'Manager'),
        ('vendeur', 'Vendeur')
    ], validators=[Optional()])
    
    status_filter = SelectField('Filtrer par statut', choices=[
        ('', 'Tous'),
        ('active', 'Actifs seulement'),
        ('inactive', 'Inactifs seulement')
    ], validators=[Optional()])


class WorkScheduleForm(FlaskForm):
    """Formulaire pour définir les horaires de travail"""
    
    # Lundi
    monday_start = TimeField('Début', validators=[Optional()])
    monday_end = TimeField('Fin', validators=[Optional()])
    monday_active = BooleanField('Travaillé', default=True)
    
    # Mardi
    tuesday_start = TimeField('Début', validators=[Optional()])
    tuesday_end = TimeField('Fin', validators=[Optional()])
    tuesday_active = BooleanField('Travaillé', default=True)
    
    # Mercredi
    wednesday_start = TimeField('Début', validators=[Optional()])
    wednesday_end = TimeField('Fin', validators=[Optional()])
    wednesday_active = BooleanField('Travaillé', default=True)
    
    # Jeudi
    thursday_start = TimeField('Début', validators=[Optional()])
    thursday_end = TimeField('Fin', validators=[Optional()])
    thursday_active = BooleanField('Travaillé', default=True)
    
    # Vendredi
    friday_start = TimeField('Début', validators=[Optional()])
    friday_end = TimeField('Fin', validators=[Optional()])
    friday_active = BooleanField('Travaillé', default=True)
    
    # Samedi
    saturday_start = TimeField('Début', validators=[Optional()])
    saturday_end = TimeField('Fin', validators=[Optional()])
    saturday_active = BooleanField('Travaillé', default=False)
    
    # Dimanche
    sunday_start = TimeField('Début', validators=[Optional()])
    sunday_end = TimeField('Fin', validators=[Optional()])
    sunday_active = BooleanField('Travaillé', default=False)
    
    def populate_from_schedule(self, schedule_dict):
        """Remplit le formulaire depuis un dictionnaire d'horaires"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        
        for i, day in enumerate(days):
            day_name = day_names[i]
            if day_name in schedule_dict:
                day_schedule = schedule_dict[day_name]
                if day_schedule.get('active', False):
                    setattr(self, f'{day}_active', True)
                    if 'start' in day_schedule:
                        from datetime import time
                        start_time = time.fromisoformat(day_schedule['start'])
                        setattr(self, f'{day}_start', start_time)
                    if 'end' in day_schedule:
                        from datetime import time
                        end_time = time.fromisoformat(day_schedule['end'])
                        setattr(self, f'{day}_end', end_time)
    
    def get_schedule_dict(self):
        """Convertit le formulaire en dictionnaire d'horaires"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        
        schedule = {}
        for i, day in enumerate(days):
            day_name = day_names[i]
            active = getattr(self, f'{day}_active').data
            if active:
                start_time = getattr(self, f'{day}_start').data
                end_time = getattr(self, f'{day}_end').data
                if start_time and end_time:
                    schedule[day_name] = {
                        'active': True,
                        'start': start_time.strftime('%H:%M'),
                        'end': end_time.strftime('%H:%M')
                    }
        return schedule


# 🆕 NOUVEAU FORMULAIRE POUR ANALYTICS

class AnalyticsPeriodForm(FlaskForm):
    """Formulaire pour sélectionner la période d'analyse"""
    
    period_type = SelectField('Période d\'analyse', choices=[
        ('week', 'Semaine dernière'),
        ('month', 'Mois dernier'),
        ('quarter', 'Trimestre dernier'),
        ('semester', 'Semestre dernier'),
        ('year', 'Année dernière'),
        ('custom', 'Période personnalisée')
    ], default='quarter', validators=[DataRequired()])
    
    # Pour période personnalisée
    start_date = DateField('Date de début', validators=[Optional()])
    end_date = DateField('Date de fin', validators=[Optional()])
    
    def get_date_range(self):
        """Retourne les dates de début et fin selon le type de période"""
        today = date.today()
        
        if self.period_type.data == 'week':
            # Semaine dernière (lundi à dimanche)
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            return last_monday, last_sunday
            
        elif self.period_type.data == 'month':
            # Mois dernier
            if today.month == 1:
                start_date = date(today.year - 1, 12, 1)
                end_date = date(today.year, 1, 1) - timedelta(days=1)
            else:
                start_date = date(today.year, today.month - 1, 1)
                if today.month == 2:
                    end_date = date(today.year, today.month, 1) - timedelta(days=1)
                else:
                    end_date = date(today.year, today.month, 1) - timedelta(days=1)
            return start_date, end_date
            
        elif self.period_type.data == 'quarter':
            # Trimestre dernier (3 mois)
            end_date = today
            start_date = today - timedelta(days=90)
            return start_date, end_date
            
        elif self.period_type.data == 'semester':
            # Semestre dernier (6 mois)
            end_date = today
            start_date = today - timedelta(days=180)
            return start_date, end_date
            
        elif self.period_type.data == 'year':
            # Année dernière
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)
            return start_date, end_date
            
        elif self.period_type.data == 'custom':
            # Période personnalisée
            if self.start_date.data and self.end_date.data:
                return self.start_date.data, self.end_date.data
            else:
                # Par défaut : 3 derniers mois
                end_date = today
                start_date = today - timedelta(days=90)
                return start_date, end_date
        
        # Par défaut : 3 derniers mois
        end_date = today
        start_date = today - timedelta(days=90)
        return start_date, end_date


# 🆕 FORMULAIRES POUR QUALITÉ ET ABSENCES

class OrderIssueForm(FlaskForm):
    """Formulaire pour signaler un problème sur une commande"""
    
    employee_id = SelectField('Employé concerné', choices=[], validators=[DataRequired()])
    
    issue_type = SelectField('Type de problème', choices=[
        ('cuisson_incorrecte', 'Cuisson insuffisante/excessive'),
        ('forme_incorrecte', 'Forme/présentation incorrecte'),
        ('quantite_incorrecte', 'Quantité incorrecte'),
        ('ingredient_manquant', 'Ingrédient manquant'),
        ('emballage_defaillant', 'Emballage défaillant'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Description du problème', validators=[Optional()])
    submit = SubmitField('Signaler le Problème')


class AbsenceRecordForm(FlaskForm):
    """Formulaire pour enregistrer une absence"""
    
    absence_date = DateField('Date d\'absence', validators=[DataRequired()])
    
    is_full_day = BooleanField('Journée complète', default=True)
    start_time = StringField('Heure de début', validators=[Optional()], default='08:00')
    end_time = StringField('Heure de fin', validators=[Optional()], default='17:00')
    
    reason = SelectField('Motif', choices=[
        ('maladie', 'Maladie'),
        ('conge_autorise', 'Congé autorisé'),
        ('absence_personnelle', 'Absence personnelle'),
        ('retard', 'Retard'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Description/Justification', validators=[Optional()])
    is_justified = BooleanField('Absence justifiée', default=False)

class PayrollPeriodForm(FlaskForm):
    """Formulaire pour sélectionner une période de paie"""
    
    month = SelectField('Mois', choices=[
        ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'), ('4', 'Avril'),
        ('5', 'Mai'), ('6', 'Juin'), ('7', 'Juillet'), ('8', 'Août'),
        ('9', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
    ], validators=[DataRequired()])
    
    year = SelectField('Année', choices=[], validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer les années (année actuelle ± 2 ans)
        from datetime import datetime
        current_year = datetime.now().year
        year_choices = [(str(year), str(year)) for year in range(current_year - 2, current_year + 3)]
        self.year.choices = year_choices
        
        # Valeurs par défaut
        if not self.month.data:
            self.month.data = str(datetime.now().month)
        if not self.year.data:
            self.year.data = str(current_year)

class WorkHoursForm(FlaskForm):
    """Formulaire pour saisir les heures de travail d'un employé"""
    
    employee_id = SelectField('Employé', choices=[], validators=[DataRequired()])
    period_month = IntegerField('Mois', validators=[DataRequired(), NumberRange(min=1, max=12)])
    period_year = IntegerField('Année', validators=[DataRequired(), NumberRange(min=2020, max=2030)])
    
    # Heures de travail
    regular_hours = DecimalField('Heures normales', validators=[DataRequired(), NumberRange(min=0, max=300)], 
                                places=2, default=0)
    overtime_hours = DecimalField('Heures supplémentaires', validators=[Optional(), NumberRange(min=0, max=100)], 
                                 places=2, default=0)
    
    # Absences
    sick_days = IntegerField('Jours maladie', validators=[Optional(), NumberRange(min=0, max=31)], default=0)
    vacation_days = IntegerField('Jours congé', validators=[Optional(), NumberRange(min=0, max=31)], default=0)
    other_absences = IntegerField('Autres absences', validators=[Optional(), NumberRange(min=0, max=31)], default=0)
    
    # Primes et déductions
    performance_bonus = DecimalField('Prime performance', validators=[Optional(), NumberRange(min=0)], 
                                    places=2, default=0)
    transport_allowance = DecimalField('Indemnité transport', validators=[Optional(), NumberRange(min=0)], 
                                      places=2, default=0)
    meal_allowance = DecimalField('Indemnité repas', validators=[Optional(), NumberRange(min=0)], 
                                 places=2, default=0)
    
    # Déductions
    advance_deduction = DecimalField('Avance sur salaire', validators=[Optional(), NumberRange(min=0)], 
                                    places=2, default=0)
    other_deductions = DecimalField('Autres déductions', validators=[Optional(), NumberRange(min=0)], 
                                   places=2, default=0)
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Enregistrer les Heures')

class PayrollCalculationForm(FlaskForm):
    """Formulaire pour calculer et valider la paie"""
    
    employee_id = SelectField('Employé', choices=[], validators=[DataRequired()])
    period_month = IntegerField('Mois', validators=[DataRequired()])
    period_year = IntegerField('Année', validators=[DataRequired()])
    
    # Calculs automatiques (affichage seulement)
    base_salary = DecimalField('Salaire de base', validators=[DataRequired()], places=2)
    overtime_amount = DecimalField('Montant heures sup.', validators=[Optional()], places=2, default=0)
    total_bonuses = DecimalField('Total primes', validators=[Optional()], places=2, default=0)
    total_deductions = DecimalField('Total déductions', validators=[Optional()], places=2, default=0)
    
    # Charges sociales
    social_security_rate = DecimalField('Taux sécu. sociale (%)', validators=[DataRequired()], 
                                       places=2, default=9.0)
    unemployment_rate = DecimalField('Taux chômage (%)', validators=[DataRequired()], 
                                    places=2, default=1.5)
    retirement_rate = DecimalField('Taux retraite (%)', validators=[DataRequired()], 
                                  places=2, default=7.0)
    
    # Résultats
    gross_salary = DecimalField('Salaire brut', validators=[DataRequired()], places=2)
    total_charges = DecimalField('Total charges', validators=[DataRequired()], places=2)
    net_salary = DecimalField('Salaire net', validators=[DataRequired()], places=2)
    
    # Validation
    is_validated = BooleanField('Valider cette paie')
    validation_notes = TextAreaField('Notes de validation', validators=[Optional()])
    
    submit = SubmitField('Calculer et Valider')

class PayslipGenerationForm(FlaskForm):
    """Formulaire pour générer les bulletins de paie"""
    
    period_month = SelectField('Mois', choices=[
        ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'), ('4', 'Avril'),
        ('5', 'Mai'), ('6', 'Juin'), ('7', 'Juillet'), ('8', 'Août'),
        ('9', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
    ], validators=[DataRequired()])
    
    period_year = SelectField('Année', choices=[], validators=[DataRequired()])
    
    # Options de génération
    employee_ids = SelectMultipleField('Employés (laisser vide pour tous)', choices=[])
    include_inactive = BooleanField('Inclure employés inactifs', default=False)
    
    # Format de sortie
    output_format = SelectField('Format', choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('both', 'PDF + Excel')
    ], validators=[DataRequired()], default='pdf')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer les années
        from datetime import datetime
        current_year = datetime.now().year
        year_choices = [(str(year), str(year)) for year in range(current_year - 2, current_year + 3)]
        self.period_year.choices = year_choices
        
        # Valeurs par défaut
        if not self.period_month.data:
            self.period_month.data = str(datetime.now().month)
        if not self.period_year.data:
            self.period_year.data = str(current_year)
    
    submit = SubmitField('Générer les Bulletins')
