# -*- coding: utf-8 -*-
"""
app/employees/models.py
Modèles pour la gestion des employés et RH
"""

from datetime import datetime, date, time
from decimal import Decimal
from extensions import db
from sqlalchemy import UniqueConstraint, Index
import json

# Table d'association pour les commandes et employés (many-to-many)
order_employees = db.Table('order_employees',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True)
)

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    salaire_fixe = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    prime = db.Column(db.Numeric(10, 2), default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # 🆕 Nouveaux champs RH
    zk_user_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    work_schedule = db.Column(db.Text)  # JSON des horaires hebdomadaires
    is_insured = db.Column(db.Boolean, default=False)
    insurance_amount = db.Column(db.Numeric(10, 2), default=0.0)
    hourly_rate = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Relations
    orders_produced = db.relationship('Order', secondary=order_employees, back_populates='produced_by')
    attendance_records = db.relationship('AttendanceRecord', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    attendance_summaries = db.relationship('AttendanceSummary', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    payroll_entries = db.relationship('PayrollEntry', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    # 🆕 Nouvelles relations pour qualité et absences
    order_issues = db.relationship('OrderIssue', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    absence_records = db.relationship('AbsenceRecord', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    # Rôles disponibles
    ROLES = [
        ('production', 'Production'),
        ('chef_production', 'Chef de Production'),
        ('assistant_production', 'Assistant Production'),
        ('patissier', 'Pâtissier'),
        ('vendeuse', 'Vendeuse'),
        ('caissiere', 'Caissière'),
        ('femme_menage', 'Femme de Ménage'),
        ('livreur', 'Livreur'),
        ('admin', 'Administrateur')
    ]
    
    def get_role_display(self):
        roles_dict = dict(self.ROLES)
        return roles_dict.get(self.role, self.role.title())
    
    def get_monthly_salary_cost(self, year, month):
        """Calcul du coût mensuel total (salaire + prime + assurance)"""
        base_salary = float(self.salaire_fixe or 0)
        prime = float(self.prime or 0)
        insurance = float(self.insurance_amount or 0) if self.is_insured else 0
        return base_salary + prime + insurance
    
    def get_work_schedule(self):
        """Récupère les horaires de travail depuis JSON"""
        if self.work_schedule:
            try:
                return json.loads(self.work_schedule)
            except:
                return None
        return None
    
    def set_work_schedule(self, schedule_dict):
        """Sauvegarde les horaires de travail en JSON"""
        if schedule_dict:
            self.work_schedule = json.dumps(schedule_dict)
        else:
            self.work_schedule = None
    
    def get_weekly_hours(self):
        """Calcule le nombre d'heures hebdomadaires prévues"""
        schedule = self.get_work_schedule()
        if not schedule:
            return 0
        
        total_hours = 0
        for day, config in schedule.items():
            if config.get('active', False):
                start_time = config.get('start', '08:00')
                end_time = config.get('end', '17:00')
                try:
                    start_hour, start_min = map(int, start_time.split(':'))
                    end_hour, end_min = map(int, end_time.split(':'))
                    hours = (end_hour - start_hour) + (end_min - start_min) / 60
                    total_hours += hours
                except:
                    continue
        
        return total_hours
    
    # 🆕 Méthodes pour évaluation par rôle
    def is_production_role(self):
        """Vérifie si l'employé est en production"""
        return self.role in ['production', 'chef_production', 'assistant_production', 'patissier']
    
    def is_sales_role(self):
        """Vérifie si l'employé est en vente"""
        return self.role in ['vendeuse', 'caissiere']
    
    def is_support_role(self):
        """Vérifie si l'employé est en support (pas d'évaluation)"""
        return self.role in ['femme_menage', 'livreur']
    
    def can_be_evaluated(self):
        """Détermine si l'employé peut être évalué"""
        return not self.is_support_role()
    
    # Méthodes existantes de performance
    def get_monthly_revenue(self, year, month):
        """Calcule le CA mensuel généré"""
        try:
            from models import Order
            from datetime import datetime
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            orders = Order.query.join(Order.produced_by).filter(
                Employee.id == self.id,
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status.in_(['completed', 'delivered'])
            ).all()
            
            return sum(float(order.total_amount or 0) for order in orders)
        except:
            return 0.0
    
    def get_orders_count(self, year, month):
        """Compte les commandes du mois"""
        try:
            from models import Order
            from datetime import datetime
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            return Order.query.join(Order.produced_by).filter(
                Employee.id == self.id,
                Order.created_at >= start_date,
                Order.created_at < end_date
            ).count()
        except:
            return 0
    
    def get_productivity_score(self, year, month):
        """Score de productivité basique"""
        orders_count = self.get_orders_count(year, month)
        if orders_count == 0:
            return 0.0
        
        revenue = self.get_monthly_revenue(year, month)
        cost = self.get_monthly_salary_cost(year, month)
        
        if cost == 0:
            return 100.0
        
        return min(100.0, (revenue / cost) * 10)
    
    def get_formatted_salary(self):
        """Retourne le salaire formaté en DA"""
        total_salary = float(self.salaire_fixe or 0) + float(self.prime or 0)
        return f"{total_salary:,.2f} DA"
    
    # 🆕 Méthodes pour les pointages
    def get_today_attendance(self):
        """Récupère les pointages du jour pour cet employé"""
        from datetime import date
        today = date.today()
        return self.attendance_records.filter(
            db.func.date(AttendanceRecord.timestamp) == today
        ).order_by(AttendanceRecord.timestamp).all()
    
    def get_attendance_for_date(self, target_date):
        """Récupère les pointages pour une date donnée"""
        return self.attendance_records.filter(
            db.func.date(AttendanceRecord.timestamp) == target_date
        ).order_by(AttendanceRecord.timestamp).all()
    
    def get_attendance_for_period(self, start_date, end_date):
        """Récupère les pointages pour une période donnée"""
        return self.attendance_records.filter(
            db.func.date(AttendanceRecord.timestamp) >= start_date,
            db.func.date(AttendanceRecord.timestamp) <= end_date
        ).order_by(AttendanceRecord.timestamp).all()
    
    def get_current_status(self):
        """Détermine le statut actuel de l'employé (présent/absent)"""
        today_records = self.get_today_attendance()
        if not today_records:
            return 'absent'
        
        last_record = today_records[-1]
        return 'present' if last_record.punch_type == 'in' else 'absent'
    
    def get_work_hours_for_date(self, target_date):
        """Calcule les heures travaillées pour une date donnée"""
        records = self.get_attendance_for_date(target_date)
        total_hours = 0
        in_time = None
        
        for record in records:
            if record.punch_type == 'in':
                in_time = record.timestamp
            elif record.punch_type == 'out' and in_time:
                duration = record.timestamp - in_time
                total_hours += duration.total_seconds() / 3600
                in_time = None
        
        return round(total_hours, 2)
    
    def get_weekly_attendance_summary(self):
        """Résumé de présence de la semaine"""
        from datetime import date, timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        summary = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            records = self.get_attendance_for_date(day)
            hours = self.get_work_hours_for_date(day)
            
            summary.append({
                'date': day,
                'records_count': len(records),
                'hours_worked': hours,
                'status': 'present' if records else 'absent'
            })
        
        return summary
    
    def get_monthly_attendance_stats(self, year, month):
        """Statistiques de présence pour un mois"""
        from datetime import date, timedelta
        import calendar
        
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        
        total_days = (end_date - start_date).days + 1
        present_days = 0
        total_hours = 0
        
        current_date = start_date
        while current_date <= end_date:
            records = self.get_attendance_for_date(current_date)
            if records:
                present_days += 1
                total_hours += self.get_work_hours_for_date(current_date)
            current_date += timedelta(days=1)
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'attendance_rate': round((present_days / total_days) * 100, 1) if total_days > 0 else 0,
            'total_hours': round(total_hours, 2)
        }
    
    def __repr__(self):
        return f'<Employee {self.name} ({self.role})>'


class AttendanceRecord(db.Model):
    """Modèle pour les enregistrements de pointage de la pointeuse ZKTeco"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    punch_type = db.Column(db.String(10), nullable=False)  # 'in' ou 'out'
    device_id = db.Column(db.String(50))  # ID de la pointeuse
    verification_type = db.Column(db.String(20))  # 'fingerprint', 'card', 'password'
    
    # Données brutes de la pointeuse
    raw_data = db.Column(db.Text)  # JSON des données originales
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        db.Index('idx_employee_date', 'employee_id', 'timestamp'),
        db.Index('idx_date_punch', 'timestamp', 'punch_type'),
    )
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee.name} - {self.timestamp} - {self.punch_type}>'
    
    @property
    def formatted_time(self):
        """Retourne l'heure formatée"""
        return self.timestamp.strftime('%H:%M')
    
    @property
    def formatted_date(self):
        """Retourne la date formatée"""
        return self.timestamp.strftime('%d/%m/%Y')
    
    @property
    def formatted_datetime(self):
        """Retourne la date et l'heure formatées"""
        return self.timestamp.strftime('%d/%m/%Y %H:%M')
    
    def get_punch_type_display(self):
        """Retourne le type de pointage en français"""
        return 'Entrée' if self.punch_type == 'in' else 'Sortie'
    
    @staticmethod
    def create_from_zkteco_data(employee_id, timestamp, punch_type, raw_data=None):
        """Crée un enregistrement de pointage à partir des données ZKTeco"""
        record = AttendanceRecord(
            employee_id=employee_id,
            timestamp=timestamp,
            punch_type=punch_type,
            raw_data=raw_data
        )
        return record
    
    @staticmethod
    def get_daily_summary(target_date):
        """Récupère un résumé des pointages pour une date"""
        records = AttendanceRecord.query.filter(
            db.func.date(AttendanceRecord.timestamp) == target_date
        ).order_by(AttendanceRecord.timestamp).all()
        
        summary = {}
        for record in records:
            emp_id = record.employee_id
            if emp_id not in summary:
                summary[emp_id] = {
                    'employee': record.employee,
                    'records': [],
                    'total_hours': 0,
                    'status': 'absent'
                }
            
            summary[emp_id]['records'].append(record)
            
            # Calculer le statut actuel
            if record.punch_type == 'in':
                summary[emp_id]['status'] = 'present'
            else:
                summary[emp_id]['status'] = 'absent'
        
        # Calculer les heures travaillées
        for emp_id, data in summary.items():
            records = data['records']
            total_hours = 0
            in_time = None
            
            for record in records:
                if record.punch_type == 'in':
                    in_time = record.timestamp
                elif record.punch_type == 'out' and in_time:
                    duration = record.timestamp - in_time
                    total_hours += duration.total_seconds() / 3600
                    in_time = None
            
            data['total_hours'] = round(total_hours, 2)
        
        return summary


class AttendanceException(db.Model):
    """Système de quarantaine pour les données de pointage corrompues"""
    __tablename__ = 'attendance_exceptions'
    
    id = db.Column(db.Integer, primary_key=True)
    raw_data = db.Column(db.Text, nullable=False)
    error_type = db.Column(db.String(100), nullable=False)
    error_message = db.Column(db.Text)
    resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<AttendanceException {self.error_type} - {"Resolved" if self.resolved else "Pending"}>'


class AttendanceSummary(db.Model):
    """Résumés quotidiens de présence calculés"""
    __tablename__ = 'attendance_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)
    
    # Heures travaillées
    scheduled_hours = db.Column(db.Numeric(4, 2), default=0.0)
    worked_hours = db.Column(db.Numeric(4, 2), default=0.0)
    overtime_hours = db.Column(db.Numeric(4, 2), default=0.0)
    break_hours = db.Column(db.Numeric(4, 2), default=0.0)
    
    # Ponctualité
    arrived_at = db.Column(db.Time, nullable=True)
    left_at = db.Column(db.Time, nullable=True)
    is_late = db.Column(db.Boolean, default=False)
    late_minutes = db.Column(db.Integer, default=0)
    
    # Status
    is_present = db.Column(db.Boolean, default=True)
    is_absent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contrainte unique : un seul résumé par employé par jour
    __table_args__ = (
        UniqueConstraint('employee_id', 'work_date', name='uq_attendance_summary_employee_date'),
        Index('idx_attendance_summary_date', 'work_date'),
    )
    
    def __repr__(self):
        return f'<AttendanceSummary {self.employee_id} - {self.work_date}>'


class PayrollPeriod(db.Model):
    """Périodes de paie mensuelles"""
    __tablename__ = 'payroll_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Status
    is_closed = db.Column(db.Boolean, default=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Totaux
    total_employees = db.Column(db.Integer, default=0)
    total_base_salary = db.Column(db.Numeric(12, 2), default=0.0)
    total_overtime = db.Column(db.Numeric(12, 2), default=0.0)
    total_deductions = db.Column(db.Numeric(12, 2), default=0.0)
    total_net_salary = db.Column(db.Numeric(12, 2), default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    payroll_entries = db.relationship('PayrollEntry', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    
    # Contrainte unique : une seule période par mois/année
    __table_args__ = (
        UniqueConstraint('year', 'month', name='uq_payroll_period_year_month'),
    )
    
    def __repr__(self):
        return f'<PayrollPeriod {self.year}-{self.month:02d}>'


class PayrollEntry(db.Model):
    """Bulletins de paie individuels"""
    __tablename__ = 'payroll_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('payroll_periods.id'), nullable=False)
    
    # Salaire de base
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    prime = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Heures et suppléments
    regular_hours = db.Column(db.Numeric(6, 2), default=0.0)
    overtime_hours = db.Column(db.Numeric(6, 2), default=0.0)
    overtime_amount = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Déductions
    insurance_deduction = db.Column(db.Numeric(10, 2), default=0.0)
    other_deductions = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Total
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Métadonnées
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contrainte unique : un seul bulletin par employé par période
    __table_args__ = (
        UniqueConstraint('employee_id', 'period_id', name='uq_payroll_entry_employee_period'),
    )
    
    def __repr__(self):
        return f'<PayrollEntry {self.employee_id} - Period {self.period_id}>'


# 🆕 NOUVEAUX MODÈLES POUR QUALITÉ ET ABSENCES

class OrderIssue(db.Model):
    """Problèmes détectés sur les commandes"""
    __tablename__ = 'order_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Type de problème
    issue_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Métadonnées
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    detected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Résolution
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text)
    
    # Relations
    order = db.relationship('Order', backref='issues')
    
    # Types d'erreurs fréquentes
    ISSUE_TYPES = [
        ('cuisson_incorrecte', 'Cuisson insuffisante/excessive'),
        ('forme_incorrecte', 'Forme/présentation incorrecte'),
        ('quantite_incorrecte', 'Quantité incorrecte'),
        ('ingredient_manquant', 'Ingrédient manquant'),
        ('emballage_defaillant', 'Emballage défaillant'),
        ('autre', 'Autre')
    ]
    
    def get_issue_type_display(self):
        """Retourne le libellé du type d'erreur"""
        types_dict = dict(self.ISSUE_TYPES)
        return types_dict.get(self.issue_type, self.issue_type)
    
    def __repr__(self):
        return f'<OrderIssue Order:{self.order_id} Employee:{self.employee_id} ({self.issue_type})>'


class AbsenceRecord(db.Model):
    """Enregistrements des absences avec motifs"""
    __tablename__ = 'absence_records'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Période d'absence
    absence_date = db.Column(db.Date, nullable=False)
    is_full_day = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.Time, nullable=True)  # Si absence partielle
    end_time = db.Column(db.Time, nullable=True)    # Si absence partielle
    
    # Motif
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_justified = db.Column(db.Boolean, default=False)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Motifs d'absence fréquents
    ABSENCE_REASONS = [
        ('maladie', 'Maladie'),
        ('conge_autorise', 'Congé autorisé'),
        ('absence_personnelle', 'Absence personnelle'),
        ('retard', 'Retard'),
        ('autre', 'Autre')
    ]
    
    def get_reason_display(self):
        """Retourne le libellé du motif"""
        reasons_dict = dict(self.ABSENCE_REASONS)
        return reasons_dict.get(self.reason, self.reason)
    
    def __repr__(self):
        return f'<AbsenceRecord {self.employee_id} - {self.absence_date} ({self.reason})>'

# Import conditionnel pour éviter les imports circulaires
try:
    from models import Order
except ImportError:
    # Si Order n'est pas encore disponible, on l'importera plus tard
    pass

class WorkHours(db.Model):
    """Modèle pour enregistrer les heures de travail mensuelles"""
    __tablename__ = 'work_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    period_month = db.Column(db.Integer, nullable=False)  # 1-12
    period_year = db.Column(db.Integer, nullable=False)   # 2024, 2025, etc.
    
    # Heures de travail
    regular_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    overtime_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Absences (en jours)
    sick_days = db.Column(db.Integer, nullable=False, default=0)
    vacation_days = db.Column(db.Integer, nullable=False, default=0)
    other_absences = db.Column(db.Integer, nullable=False, default=0)
    
    # Primes et indemnités
    performance_bonus = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    transport_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    meal_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Déductions
    advance_deduction = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    other_deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Métadonnées
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relations
    employee = db.relationship('Employee', backref='work_hours_records')
    
    # Contrainte unique pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('employee_id', 'period_month', 'period_year', 
                                         name='unique_employee_period'),)
    
    def get_total_absences(self):
        """Retourne le total des jours d'absence"""
        return self.sick_days + self.vacation_days + self.other_absences
    
    def get_total_bonuses(self):
        """Retourne le total des primes et indemnités"""
        return float(self.performance_bonus or 0) + float(self.transport_allowance or 0) + float(self.meal_allowance or 0)
    
    def get_total_deductions(self):
        """Retourne le total des déductions"""
        return float(self.advance_deduction or 0) + float(self.other_deductions or 0)
    
    def __repr__(self):
        return f'<WorkHours {self.employee.name if self.employee else "Unknown"} {self.period_month}/{self.period_year}>'

class PayrollCalculation(db.Model):
    """Modèle pour les calculs de paie mensuels"""
    __tablename__ = 'payroll_calculations'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    work_hours_id = db.Column(db.Integer, db.ForeignKey('work_hours.id'), nullable=False)
    period_month = db.Column(db.Integer, nullable=False)
    period_year = db.Column(db.Integer, nullable=False)
    
    # Salaire de base
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    overtime_rate = db.Column(db.Numeric(10, 2), nullable=False)  # Taux majoré (ex: 1.5x)
    
    # Calculs
    regular_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    overtime_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_bonuses = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Salaire brut
    gross_salary = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Charges sociales (taux en pourcentage)
    social_security_rate = db.Column(db.Numeric(5, 2), nullable=False, default=9.0)
    unemployment_rate = db.Column(db.Numeric(5, 2), nullable=False, default=1.5)
    retirement_rate = db.Column(db.Numeric(5, 2), nullable=False, default=7.0)
    
    # Montants des charges
    social_security_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unemployment_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    retirement_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_charges = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Salaire net
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Validation
    is_validated = db.Column(db.Boolean, nullable=False, default=False)
    validated_at = db.Column(db.DateTime)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    validation_notes = db.Column(db.Text)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relations
    employee = db.relationship('Employee', backref='payroll_calculations')
    work_hours = db.relationship('WorkHours', backref='payroll_calculation')
    
    # Contrainte unique
    __table_args__ = (db.UniqueConstraint('employee_id', 'period_month', 'period_year', 
                                         name='unique_payroll_period'),)
    
    def calculate_all(self):
        """Calcule tous les montants automatiquement"""
        # Montant des heures normales
        self.regular_amount = float(self.work_hours.regular_hours) * float(self.hourly_rate)
        
        # Montant des heures supplémentaires
        self.overtime_amount = float(self.work_hours.overtime_hours) * float(self.overtime_rate)
        
        # Total des primes et déductions
        self.total_bonuses = self.work_hours.get_total_bonuses()
        self.total_deductions = self.work_hours.get_total_deductions()
        
        # Salaire brut
        self.gross_salary = self.regular_amount + self.overtime_amount + self.total_bonuses
        
        # Calcul des charges sociales
        self.social_security_amount = self.gross_salary * (float(self.social_security_rate) / 100)
        self.unemployment_amount = self.gross_salary * (float(self.unemployment_rate) / 100)
        self.retirement_amount = self.gross_salary * (float(self.retirement_rate) / 100)
        
        self.total_charges = self.social_security_amount + self.unemployment_amount + self.retirement_amount
        
        # Salaire net
        self.net_salary = self.gross_salary - self.total_charges - self.total_deductions
        
        return self.net_salary
    
    def get_payslip_data(self):
        """Retourne les données formatées pour le bulletin de paie"""
        return {
            'employee': self.employee,
            'period': f"{self.period_month:02d}/{self.period_year}",
            'work_hours': self.work_hours,
            'base_salary': f"{float(self.base_salary):,.2f} DA",
            'regular_amount': f"{float(self.regular_amount):,.2f} DA",
            'overtime_amount': f"{float(self.overtime_amount):,.2f} DA",
            'total_bonuses': f"{float(self.total_bonuses):,.2f} DA",
            'gross_salary': f"{float(self.gross_salary):,.2f} DA",
            'social_security': f"{float(self.social_security_amount):,.2f} DA",
            'unemployment': f"{float(self.unemployment_amount):,.2f} DA",
            'retirement': f"{float(self.retirement_amount):,.2f} DA",
            'total_charges': f"{float(self.total_charges):,.2f} DA",
            'total_deductions': f"{float(self.total_deductions):,.2f} DA",
            'net_salary': f"{float(self.net_salary):,.2f} DA",
            'is_validated': self.is_validated,
            'validation_notes': self.validation_notes
        }
    
    def __repr__(self):
        return f'<PayrollCalculation {self.employee.name if self.employee else "Unknown"} {self.period_month}/{self.period_year}>'

# Définir les fonctions avant de les assigner à la classe Employee
def employee_get_payroll_summary(self, year, month):
    """Retourne un résumé de la paie pour une période donnée"""
    payroll = PayrollCalculation.query.filter_by(
        employee_id=self.id,
        period_year=year,
        period_month=month
    ).first()
    
    if not payroll:
        return {
            'status': 'not_calculated',
            'message': 'Paie non calculée pour cette période'
        }
    
    return {
        'status': 'calculated' if payroll.is_validated else 'pending',
        'gross_salary': float(payroll.gross_salary),
        'net_salary': float(payroll.net_salary),
        'total_charges': float(payroll.total_charges),
        'is_validated': payroll.is_validated,
        'validation_date': payroll.validated_at
    }

def employee_get_annual_payroll_summary(self, year):
    """Retourne le résumé annuel de la paie"""
    payrolls = PayrollCalculation.query.filter_by(
        employee_id=self.id,
        period_year=year
    ).all()
    
    if not payrolls:
        return {
            'total_gross': 0,
            'total_net': 0,
            'total_charges': 0,
            'months_paid': 0
        }
    
    total_gross = sum(float(p.gross_salary) for p in payrolls)
    total_net = sum(float(p.net_salary) for p in payrolls)
    total_charges = sum(float(p.total_charges) for p in payrolls)
    
    return {
        'total_gross': total_gross,
        'total_net': total_net,
        'total_charges': total_charges,
        'months_paid': len(payrolls),
        'average_monthly_gross': total_gross / len(payrolls) if payrolls else 0,
        'average_monthly_net': total_net / len(payrolls) if payrolls else 0
    }

def employee_get_work_hours_for_period(self, year, month):
    """Retourne les heures de travail pour une période donnée"""
    work_hours = WorkHours.query.filter_by(
        employee_id=self.id,
        period_year=year,
        period_month=month
    ).first()
    
    return work_hours

# Ajouter les méthodes à la classe Employee
Employee.get_payroll_summary = employee_get_payroll_summary
Employee.get_annual_payroll_summary = employee_get_annual_payroll_summary
Employee.get_work_hours_for_period = employee_get_work_hours_for_period
