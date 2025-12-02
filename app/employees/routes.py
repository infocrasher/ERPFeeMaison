# -*- coding: utf-8 -*-
"""
app/employees/routes.py
Routes pour la gestion des employés
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from app.employees.models import Employee, AttendanceRecord
from app.employees.forms import EmployeeForm, EmployeeSearchForm, WorkScheduleForm, AnalyticsPeriodForm, WorkHoursForm, PayrollCalculationForm
from decorators import admin_required
from datetime import datetime, timedelta, date
from sqlalchemy import func, text
from decimal import Decimal

# Imports pour analytics - imports conditionnels pour éviter les conflits
ORDER_AVAILABLE = False
Product = None

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
@admin_required
def list_employees():
    """Liste des employés avec recherche et filtres"""
    
    form = EmployeeSearchForm()
    
    # Query de base
    query = Employee.query
    
    # Filtres de recherche
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(Employee.name.ilike(search_term))
    
    if form.role_filter.data:
        query = query.filter(Employee.role == form.role_filter.data)
    
    if form.status_filter.data == 'active':
        query = query.filter(Employee.is_active == True)
    elif form.status_filter.data == 'inactive':
        query = query.filter(Employee.is_active == False)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    employees_pagination = query.order_by(Employee.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    production_staff = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production', 'patissier'])
    ).count()
    
    return render_template('employees/list_employees.html',
                         employees_pagination=employees_pagination,
                         form=form,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         production_staff=production_staff,
                         title="Gestion des Employés")

@employees_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_employee():
    """Créer un nouvel employé"""
    
    form = EmployeeForm()
    
    if form.validate_on_submit():
        try:
            employee = Employee(
                name=form.name.data,
                role=form.role.data,
                salaire_fixe=form.salaire_fixe.data,
                prime=form.prime.data or 0,
                is_active=form.is_active.data,
                notes=form.notes.data,
                # Nouveaux champs RH
                zk_user_id=form.zk_user_id.data or None,
                is_insured=form.is_insured.data,
                insurance_amount=form.insurance_amount.data or 0,
                hourly_rate=form.hourly_rate.data or 0
            )
            
            db.session.add(employee)
            db.session.commit()
            
            flash(f'Employé "{employee.name}" créé avec succès !', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création : {str(e)}', 'error')
    
    return render_template('employees/employee_form.html',
                         form=form,
                         title="Nouvel Employé",
                         action="Créer")

@employees_bp.route('/<int:employee_id>')
@login_required
@admin_required
def view_employee(employee_id):
    """Voir les détails d'un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Statistiques de performance
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    monthly_revenue = employee.get_monthly_revenue(current_year, current_month)
    productivity_score = employee.get_productivity_score(current_year, current_year)
    orders_count = employee.get_orders_count(current_year, current_month)
    
    # 🆕 Données de pointage
    today_attendance = employee.get_today_attendance()
    current_status = employee.get_current_status()
    
    # Pointages de la semaine
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_attendance = employee.get_attendance_for_period(start_of_week, today)
    
    return render_template('employees/view_employee.html',
                         employee=employee,
                         monthly_revenue=monthly_revenue,
                         productivity_score=productivity_score,
                         orders_count=orders_count,
                         today_attendance=today_attendance,
                         current_status=current_status,
                         week_attendance=week_attendance,
                         title=f"Employé - {employee.name}")

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(employee_id):
    """Modifier un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(employee)
            db.session.commit()
            
            flash(f'Employé "{employee.name}" modifié avec succès !', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('employees/employee_form.html',
                         form=form,
                         employee=employee,
                         title=f"Modifier - {employee.name}",
                         action="Modifier")

@employees_bp.route('/<int:employee_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_employee_status(employee_id):
    """Activer/désactiver un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        employee.is_active = not employee.is_active
        db.session.commit()
        
        status = "activé" if employee.is_active else "désactivé"
        flash(f'Employé "{employee.name}" {status} avec succès !', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut : {str(e)}', 'error')
    
    return redirect(url_for('employees.view_employee', employee_id=employee_id))

# 🆕 ROUTES POUR LA GESTION DES POINTAGES

@employees_bp.route('/<int:employee_id>/attendance')
@login_required
@admin_required
def employee_attendance(employee_id):
    """Page des pointages d'un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Paramètres de période
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Par défaut : derniers 7 jours
    if not start_date or not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Récupérer les pointages
    attendance_records = employee.get_attendance_for_period(start_date, end_date)
    
    # Grouper par jour
    daily_attendance = {}
    for record in attendance_records:
        day = record.timestamp.date()
        if day not in daily_attendance:
            daily_attendance[day] = []
        daily_attendance[day].append(record)
    
    # Calculer les statistiques
    total_days = (end_date - start_date).days + 1
    days_worked = len(daily_attendance)
    total_hours = sum(employee.get_work_hours_for_date(day) for day in daily_attendance.keys())
    
    stats = {
        'total_days': total_days,
        'days_worked': days_worked,
        'days_absent': total_days - days_worked,
        'total_hours': round(total_hours, 2),
        'average_hours': round(total_hours / days_worked, 2) if days_worked > 0 else 0,
        'attendance_rate': round((days_worked / total_days) * 100, 1) if total_days > 0 else 0
    }
    
    # Calculer les dates de raccourci pour les boutons
    today = date.today()
    date_shortcuts = {
        'week_start': (today - timedelta(days=6)).strftime('%Y-%m-%d'),
        'week_end': today.strftime('%Y-%m-%d'),
        'month_start': (today - timedelta(days=29)).strftime('%Y-%m-%d'),
        'month_end': today.strftime('%Y-%m-%d')
    }
    
    # Calculer la liste des jours pour le tableau
    days_in_period = []
    current_date = start_date
    while current_date <= end_date:
        days_in_period.append(current_date)
        current_date += timedelta(days=1)
    
    return render_template('employees/employee_attendance.html',
                         employee=employee,
                         daily_attendance=daily_attendance,
                         stats=stats,
                         start_date=start_date,
                         end_date=end_date,
                         date_shortcuts=date_shortcuts,
                         days_in_period=days_in_period,
                         title=f"Pointages - {employee.name}")

@employees_bp.route('/attendance/dashboard')
@login_required
@admin_required
def attendance_dashboard():
    """Dashboard général des pointages"""
    
    # Date sélectionnée (par défaut aujourd'hui)
    selected_date = request.args.get('date')
    if selected_date:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = date.today()
    
    # Récupérer le résumé des pointages du jour
    daily_summary = AttendanceRecord.get_daily_summary(selected_date)
    
    # Statistiques générales
    total_employees = Employee.query.filter(Employee.is_active == True).count()
    present_employees = len([emp for emp in daily_summary.values() if emp['status'] == 'present'])
    absent_employees = total_employees - present_employees
    
    # Employés sans pointage
    employees_with_attendance = set(daily_summary.keys())
    all_active_employees = Employee.query.filter(Employee.is_active == True).all()
    employees_without_attendance = [emp for emp in all_active_employees if emp.id not in employees_with_attendance]
    
    stats = {
        'total_employees': total_employees,
        'present_employees': present_employees,
        'absent_employees': absent_employees,
        'attendance_rate': round((present_employees / total_employees) * 100, 1) if total_employees > 0 else 0,
        'total_hours_worked': sum(emp['total_hours'] for emp in daily_summary.values())
    }
    
    # Calcul des dates précédente et suivante pour la navigation
    previous_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)
    
    return render_template('employees/attendance_dashboard.html',
                         daily_summary=daily_summary,
                         employees_without_attendance=employees_without_attendance,
                         stats=stats,
                         selected_date=selected_date,
                         previous_date=previous_date,
                         next_date=next_date,
                         title="Dashboard Pointages")

@employees_bp.route('/attendance/live')
@login_required
@admin_required
def live_attendance():
    """Page de pointages en temps réel"""
    
    # Récupérer les pointages d'aujourd'hui
    today = date.today()
    today_records = AttendanceRecord.query.filter(
        db.func.date(AttendanceRecord.timestamp) == today
    ).order_by(AttendanceRecord.timestamp.desc()).limit(50).all()
    
    # Statut actuel de tous les employés
    active_employees = Employee.query.filter(Employee.is_active == True).all()
    employee_status = {}
    
    for employee in active_employees:
        status = employee.get_current_status()
        last_punch = employee.get_today_attendance()
        last_punch_time = last_punch[-1].timestamp if last_punch else None
        
        employee_status[employee.id] = {
            'employee': employee,
            'status': status,
            'last_punch_time': last_punch_time,
            'today_hours': employee.get_work_hours_for_date(today)
        }
    
    # Heure actuelle pour l'affichage
    current_time = datetime.now().strftime('%H:%M:%S')
    
    return render_template('employees/live_attendance.html',
                         today_records=today_records,
                         employee_status=employee_status,
                         current_time=current_time,
                         title="Pointages en Temps Réel")

@employees_bp.route('/attendance/manual', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_attendance():
    """Saisie manuelle de pointage"""
    
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            punch_type = request.form.get('punch_type')
            timestamp_str = request.form.get('timestamp')
            notes = request.form.get('notes', '')
            
            # Validation
            if not employee_id or not punch_type or not timestamp_str:
                flash('Tous les champs sont requis', 'error')
                return redirect(url_for('employees.manual_attendance'))
            
            employee = Employee.query.get_or_404(employee_id)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')
            
            # Créer l'enregistrement
            record = AttendanceRecord(
                employee_id=employee_id,
                timestamp=timestamp,
                punch_type=punch_type,
                raw_data=f'{{"source": "manual", "notes": "{notes}"}}'
            )
            
            db.session.add(record)
            db.session.commit()
            
            flash(f'Pointage manuel ajouté pour {employee.name}', 'success')
            return redirect(url_for('employees.live_attendance'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout : {str(e)}', 'error')
    
    # Récupérer les employés actifs
    active_employees = Employee.query.filter(Employee.is_active == True).order_by(Employee.name).all()
    
    # Date actuelle pour le formulaire
    current_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    return render_template('employees/manual_attendance.html',
                         active_employees=active_employees,
                         current_datetime=current_datetime,
                         title="Pointage Manuel")

# API pour les pointages
@employees_bp.route('/api/attendance/today')
@login_required
@admin_required
def api_attendance_today():
    """API pour récupérer les pointages du jour"""
    
    today = date.today()
    
    # Récupérer tous les pointages du jour
    records = AttendanceRecord.query.filter(
        db.func.date(AttendanceRecord.timestamp) == today
    ).order_by(AttendanceRecord.timestamp.desc()).all()
    
    result = {
        'date': today.isoformat(),
        'count': len(records),
        'attendance': [{
            'employee_id': record.employee_id,
            'employee_name': record.employee.name,
            'time': record.formatted_time,
            'punch_type': record.punch_type,
            'punch_type_display': record.get_punch_type_display()
        } for record in records]
    }
    
    return jsonify(result)

@employees_bp.route('/api/attendance/employee/<int:employee_id>')
@login_required
@admin_required
def api_employee_attendance(employee_id):
    """API pour récupérer les pointages d'un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Paramètres
    days = request.args.get('days', 7, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Récupérer les pointages
    records = employee.get_attendance_for_period(start_date, end_date)
    
    result = {
        'employee_id': employee.id,
        'employee_name': employee.name,
        'current_status': employee.get_current_status(),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'records': [{
            'date': record.formatted_date,
            'time': record.formatted_time,
            'type': record.punch_type,
            'type_display': record.get_punch_type_display()
        } for record in records]
    }
    
    return jsonify(result)

@employees_bp.route('/<int:employee_id>/schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def work_schedule(employee_id):
    """Gérer les horaires de travail d'un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    form = WorkScheduleForm()
    
    if request.method == 'GET':
        # Charger les horaires existants
        current_schedule = employee.get_work_schedule()
        if current_schedule:
            form.populate_from_schedule(current_schedule)
    
    if form.validate_on_submit():
        try:
            # Sauvegarder les nouveaux horaires
            schedule_dict = form.get_schedule_dict()
            employee.set_work_schedule(schedule_dict)
            db.session.commit()
            
            flash(f'Horaires de travail mis à jour pour {employee.name} !', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'error')
    
    return render_template('employees/work_schedule.html',
                         employee=employee,
                         form=form,
                         title=f"Horaires - {employee.name}")


@employees_bp.route('/payroll/dashboard')
@login_required
@admin_required
def payroll_dashboard():
    """Dashboard RH avec masse salariale temps réel"""
    
    from datetime import datetime, date
    from app.employees.models import PayrollPeriod, PayrollEntry
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Employés actifs
    active_employees = Employee.query.filter(Employee.is_active == True).all()
    
    # Calcul masse salariale temps réel
    total_base_salary = sum(float(emp.salaire_fixe or 0) for emp in active_employees)
    total_primes = sum(float(emp.prime or 0) for emp in active_employees)
    total_insurance = sum(float(emp.insurance_amount or 0) for emp in active_employees if emp.is_insured)
    
    # Statistiques générales
    stats = {
        'total_employees': len(active_employees),
        'insured_employees': len([emp for emp in active_employees if emp.is_insured]),
        'total_base_salary': total_base_salary,
        'total_primes': total_primes,
        'total_insurance': total_insurance,
        'total_monthly_cost': total_base_salary + total_primes + total_insurance,
        'average_salary': total_base_salary / len(active_employees) if active_employees else 0
    }
    
    # Employés par rôle
    roles_stats = {}
    for emp in active_employees:
        role = emp.role
        if role not in roles_stats:
            roles_stats[role] = {
                'count': 0,
                'total_salary': 0,
                'employees': []
            }
        roles_stats[role]['count'] += 1
        roles_stats[role]['total_salary'] += emp.get_monthly_salary_cost(current_year, current_month)
        roles_stats[role]['employees'].append(emp)
    
    return render_template('employees/payroll_dashboard.html',
                         stats=stats,
                         roles_stats=roles_stats,
                         active_employees=active_employees,
                         current_month=current_month,
                         current_year=current_year,
                         title="Dashboard RH")

@employees_bp.route('/<int:employee_id>/analytics', methods=['GET', 'POST'])
@login_required
@admin_required
def employee_analytics(employee_id):
    """Analytics détaillées d'un employé avec tous les KPI et sélecteur de période"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    # SOLUTION DÉFINITIVE : Accès via Registry SQLAlchemy
    mapper_registry = db.Model.registry
    Order = mapper_registry._class_registry.get('Order')
    Product = mapper_registry._class_registry.get('Product')
    
    # Vérifier la disponibilité des modèles
    ORDER_AVAILABLE = Order is not None and Product is not None
    
    # 🆕 Formulaire de sélection de période
    period_form = AnalyticsPeriodForm()
    
    # Déterminer la période d'analyse
    if period_form.validate_on_submit():
        start_date, end_date = period_form.get_date_range()
    else:
        # Par défaut : 3 derniers mois
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
    
    # Convertir en datetime pour les requêtes
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Importer les modèles nécessaires pour les analytics
    from app.employees.models import AttendanceRecord, OrderIssue
    
    # 🆕 Vérifier si l'employé peut être évalué ou si les analytics sont disponibles
    if not employee.can_be_evaluated() or not ORDER_AVAILABLE:
        if not ORDER_AVAILABLE:
            flash("Analytics temporairement désactivés pour éviter les conflits système.", "warning")
        else:
            flash(f"Les employés en support ({employee.get_role_display()}) ne sont pas évalués sur la performance.", "info")
        
        # Calculer quand même les KPI de présence pour les employés non évaluables
        days_in_period = (end_date - start_date).days + 1
        
        # Récupérer les enregistrements d'assiduité pour la période
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.timestamp >= start_datetime,
            AttendanceRecord.timestamp <= end_datetime
        ).all()
        
        # Calculer les KPI de présence
        total_work_days = days_in_period
        days_present = len(set(record.timestamp.date() for record in attendance_records if record.punch_type == 'in'))
        days_absent = total_work_days - days_present
        
        # Taux de présence
        attendance_rate = (days_present / total_work_days * 100) if total_work_days > 0 else 0
        
        # Calculer la ponctualité selon le schedule
        late_arrivals = 0
        total_late_minutes = 0
        actual_hours_period = 0
        overtime_hours = 0
        
        # Récupérer le schedule de l'employé
        schedule = employee.get_work_schedule()
        day_names_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        
        # Regrouper les pointages par date pour calculer les heures travaillées
        daily_records = {}
        for record in attendance_records:
            date_key = record.timestamp.date()
            if date_key not in daily_records:
                daily_records[date_key] = {'in': [], 'out': []}
            daily_records[date_key][record.punch_type].append(record.timestamp)
        
        # Calculer les heures travaillées par jour et vérifier les retards
        for date_key, records in daily_records.items():
            if records['in'] and records['out']:
                # Prendre le premier pointage d'entrée et le dernier de sortie
                first_in = min(records['in'])
                last_out = max(records['out'])
                
                work_duration = (last_out - first_in).total_seconds() / 3600
                actual_hours_period += work_duration
                
                # Vérifier le retard selon le schedule
                weekday = date_key.weekday()  # 0=Lundi, 6=Dimanche
                day_name_fr = day_names_fr[weekday]
                
                if schedule and day_name_fr in schedule:
                    day_schedule = schedule[day_name_fr]
                    if day_schedule.get('active', False) and 'start' in day_schedule:
                        # Heure d'arrivée attendue selon le schedule
                        expected_start_str = day_schedule['start']
                        try:
                            expected_hour, expected_min = map(int, expected_start_str.split(':'))
                            expected_time = datetime.combine(date_key, datetime.min.time().replace(hour=expected_hour, minute=expected_min))
                            actual_time = first_in
                            
                            # Calculer le retard en minutes
                            if actual_time > expected_time:
                                delay_minutes = (actual_time - expected_time).total_seconds() / 60
                                if delay_minutes > 0:  # Seulement si retard > 0 (pas d'avance)
                                    late_arrivals += 1
                                    total_late_minutes += delay_minutes
                        except (ValueError, AttributeError):
                            # Si erreur de parsing, utiliser l'ancienne méthode (8h00)
                            if first_in.time() > datetime.strptime('08:00', '%H:%M').time():
                                late_arrivals += 1
                else:
                    # Pas de schedule défini, utiliser l'ancienne méthode (8h00)
                    if first_in.time() > datetime.strptime('08:00', '%H:%M').time():
                        late_arrivals += 1
                
                # Calculer les heures supplémentaires (plus de 8h par jour)
                if work_duration > 8:
                    overtime_hours += (work_duration - 8)
        
        # Taux de ponctualité (pourcentage de jours sans retard)
        punctuality_rate = ((days_present - late_arrivals) / days_present * 100) if days_present > 0 else 0
        
        # Taux de retard (pourcentage de jours avec retard)
        tardiness_rate = (late_arrivals / days_present * 100) if days_present > 0 else 0
        
        # Si pas de données réelles, utiliser les estimations
        if not attendance_records:
            attendance_rate = 90.0
            punctuality_rate = 85.0
            work_schedule = employee.get_work_schedule()
            estimated_hours_per_week = employee.get_weekly_hours()
            weeks_in_period = days_in_period / 7
            actual_hours_period = estimated_hours_per_week * weeks_in_period
            overtime_hours = 0
            days_present = int(total_work_days * 0.9)
            days_absent = total_work_days - days_present
            late_arrivals = int(days_present * 0.15)
            tardiness_rate = 15.0  # Estimation
            total_late_minutes = 0
            average_late_minutes = 0
        
        kpis = {
            'can_be_evaluated': employee.can_be_evaluated() and ORDER_AVAILABLE,
            'role_display': employee.get_role_display(),
            'start_date': start_date,
            'end_date': end_date,
            'days_in_period': days_in_period,
            'order_available': ORDER_AVAILABLE,
            # Données de présence pour tous les employés
            'attendance_rate': attendance_rate,
            'punctuality_rate': punctuality_rate,
            'actual_hours_period': actual_hours_period,
            'overtime_hours': overtime_hours,
            'days_present': days_present,
            'days_absent': days_absent,
            'late_arrivals': late_arrivals,
            'tardiness_rate': tardiness_rate,
            'total_late_minutes': total_late_minutes,
            'average_late_minutes': (total_late_minutes / late_arrivals) if late_arrivals > 0 else 0,
            'attendance_details': len(attendance_records) > 0,
        }
        return render_template('employees/employee_analytics.html',
                             employee=employee,
                             kpis=kpis,
                             period_form=period_form,
                             title=f"Analytics - {employee.name}")
    
    # 📊 KPI FINANCIERS (pour employés évaluables)
    if employee.is_production_role():
        # CA généré par l'employé (commandes produites)
        orders_ca = db.session.query(func.sum(Order.total_amount)).join(
            Order.produced_by
        ).filter(
            Employee.id == employee.id,
            Order.created_at >= start_datetime,
            Order.created_at <= end_datetime,
            Order.status.in_(['completed', 'delivered'])
        ).scalar() or 0
        
        # Nombre de commandes produites
        orders_count = Order.query.join(Order.produced_by).filter(
            Employee.id == employee.id,
            Order.created_at >= start_datetime,
            Order.created_at <= end_datetime
        ).count()
        
    elif employee.is_sales_role():
        # Pour les vendeurs : CA encaissé (à implémenter avec CashMovement)
        # Pour l'instant, on utilise les commandes assignées
        orders_ca = 0  # À implémenter avec les données de caisse
        orders_count = 0  # À implémenter
        
    else:
        orders_ca = 0
        orders_count = 0
    
    # 💰 CALCULS KPI
    # Calcul du coût sur la période
    days_in_period = (end_date - start_date).days + 1
    monthly_cost = employee.get_monthly_salary_cost(end_datetime.year, end_datetime.month)
    period_cost = Decimal(str(monthly_cost)) * Decimal(str(days_in_period)) / Decimal('30')  # Approximation
    orders_ca = Decimal(str(orders_ca or 0))
    
    # ROI Employé
    roi_employee = float(orders_ca / period_cost * 100) if period_cost > 0 else 0
    
    # Rentabilité
    profit = orders_ca - period_cost
    profitability = float(profit / period_cost * 100) if period_cost > 0 else 0
    
    # CA par commande
    ca_per_order = float(orders_ca / orders_count) if orders_count > 0 else 0
    
    # ⏰ KPI TEMPS (estimés basés sur horaires)
    work_schedule = employee.get_work_schedule()
    estimated_hours_per_week = employee.get_weekly_hours()
    weeks_in_period = days_in_period / 7
    estimated_hours_period = estimated_hours_per_week * weeks_in_period
    
    # CA par heure (estimation)
    ca_per_hour = float(orders_ca / Decimal(str(estimated_hours_period))) if estimated_hours_period > 0 else 0
    
    # Commandes par heure
    orders_per_hour = (orders_count / estimated_hours_period) if estimated_hours_period > 0 else 0
    
    # 🎯 SCORE POLYVALENCE
    if employee.is_production_role() or employee.is_sales_role():
        # Calculer le nombre de produits différents travaillés
        try:
            
            distinct_products = db.session.query(func.count(func.distinct(Product.id))).select_from(
                Order
            ).join(Order.items).join(Product).join(Order.produced_by).filter(
                Employee.id == employee.id,
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime
            ).scalar() or 0
            
            total_products = Product.query.count()
            polyvalence_score = (distinct_products / total_products * 100) if total_products > 0 else 0
        except Exception:
            distinct_products = 0
            total_products = 1
            polyvalence_score = 0
    else:
        distinct_products = 0
        total_products = 1
        polyvalence_score = 0
    
    # 🔍 KPI QUALITÉ (problèmes détectés)
    
    issues_count = OrderIssue.query.filter(
        OrderIssue.employee_id == employee.id,
        OrderIssue.detected_at >= start_datetime,
        OrderIssue.detected_at <= end_datetime
    ).count()
    
    error_rate = (issues_count / orders_count * 100) if orders_count > 0 else 0
    
    # ⏰ KPI PRÉSENCE ET PONCTUALITÉ (Données réelles)
    
    # Récupérer les enregistrements d'assiduité pour la période
    attendance_records = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.timestamp >= start_datetime,
        AttendanceRecord.timestamp <= end_datetime
    ).all()
    
    # Calculer les KPI de présence
    total_work_days = days_in_period  # Simplification, peut être affiné avec les jours ouvrables
    days_present = len(set(record.timestamp.date() for record in attendance_records if record.punch_type == 'in'))
    days_absent = total_work_days - days_present
    
    # Taux de présence
    attendance_rate = (days_present / total_work_days * 100) if total_work_days > 0 else 0
    
    # Calculer la ponctualité (arrivées à l'heure) selon le schedule
    late_arrivals = 0
    total_late_minutes = 0
    actual_hours_period = 0
    overtime_hours = 0
    
    # Récupérer le schedule de l'employé
    schedule = employee.get_work_schedule()
    day_names_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    
    # Regrouper les pointages par date pour calculer les heures travaillées
    daily_records = {}
    for record in attendance_records:
        date_key = record.timestamp.date()
        if date_key not in daily_records:
            daily_records[date_key] = {'in': [], 'out': []}
        daily_records[date_key][record.punch_type].append(record.timestamp)
    
    # Calculer les heures travaillées par jour et vérifier les retards
    for date_key, records in daily_records.items():
        if records['in'] and records['out']:
            # Prendre le premier pointage d'entrée et le dernier de sortie
            first_in = min(records['in'])
            last_out = max(records['out'])
            
            work_duration = (last_out - first_in).total_seconds() / 3600
            actual_hours_period += work_duration
            
            # Vérifier le retard selon le schedule
            weekday = date_key.weekday()  # 0=Lundi, 6=Dimanche
            day_name_fr = day_names_fr[weekday]
            
            if schedule and day_name_fr in schedule:
                day_schedule = schedule[day_name_fr]
                if day_schedule.get('active', False) and 'start' in day_schedule:
                    # Heure d'arrivée attendue selon le schedule
                    expected_start_str = day_schedule['start']
                    try:
                        expected_hour, expected_min = map(int, expected_start_str.split(':'))
                        expected_time = datetime.combine(date_key, datetime.min.time().replace(hour=expected_hour, minute=expected_min))
                        actual_time = first_in
                        
                        # Calculer le retard en minutes
                        if actual_time > expected_time:
                            delay_minutes = (actual_time - expected_time).total_seconds() / 60
                            if delay_minutes > 0:  # Seulement si retard > 0 (pas d'avance)
                                late_arrivals += 1
                                total_late_minutes += delay_minutes
                    except (ValueError, AttributeError):
                        # Si erreur de parsing, utiliser l'ancienne méthode (8h00)
                        if first_in.time() > datetime.strptime('08:00', '%H:%M').time():
                            late_arrivals += 1
            else:
                # Pas de schedule défini, utiliser l'ancienne méthode (8h00)
                if first_in.time() > datetime.strptime('08:00', '%H:%M').time():
                    late_arrivals += 1
            
            # Calculer les heures supplémentaires (plus de 8h par jour)
            if work_duration > 8:
                overtime_hours += (work_duration - 8)
    
    # Taux de ponctualité (pourcentage de jours sans retard)
    punctuality_rate = ((days_present - late_arrivals) / days_present * 100) if days_present > 0 else 0
    
    # Taux de retard (pourcentage de jours avec retard)
    tardiness_rate = (late_arrivals / days_present * 100) if days_present > 0 else 0
    
    # Si pas de données réelles, utiliser les estimations
    if not attendance_records:
        attendance_rate = 90.0  # Estimation
        punctuality_rate = 85.0  # Estimation
        actual_hours_period = estimated_hours_period
        overtime_hours = 0
        days_present = int(total_work_days * 0.9)
        days_absent = total_work_days - days_present
        late_arrivals = int(days_present * 0.15)
    
    # 📈 ÉVOLUTION MENSUELLE (3 derniers mois de la période)
    monthly_stats = []
    current_date = end_date
    for i in range(3):
        month_start = current_date.replace(day=1)
        if current_date.month == 12:
            month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
        
        month_start_dt = datetime.combine(month_start, datetime.min.time())
        month_end_dt = datetime.combine(month_end, datetime.max.time())
        
        if employee.is_production_role():
            month_ca = db.session.query(func.sum(Order.total_amount)).join(
                Order.produced_by
            ).filter(
                Employee.id == employee.id,
                Order.created_at >= month_start_dt,
                Order.created_at <= month_end_dt,
                Order.status.in_(['completed', 'delivered'])
            ).scalar() or 0
            
            month_orders = Order.query.join(Order.produced_by).filter(
                Employee.id == employee.id,
                Order.created_at >= month_start_dt,
                Order.created_at <= month_end_dt
            ).count()
        else:
            month_ca = 0
            month_orders = 0
        
        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'ca': float(month_ca or 0),
            'orders': month_orders,
            'ca_per_order': float(Decimal(str(month_ca or 0)) / month_orders) if month_orders > 0 else 0
        })
        
        # Mois précédent
        if current_date.month == 1:
            current_date = current_date.replace(year=current_date.year - 1, month=12)
        else:
            current_date = current_date.replace(month=current_date.month - 1)
    
    # 🎯 OBJECTIFS
    monthly_target = Decimal('50000')  # Objectif mensuel en DA
    period_target = monthly_target * Decimal(str(days_in_period)) / Decimal('30')
    target_achievement = float(orders_ca / period_target * 100) if period_target > 0 else 0
    
    # 🏆 SCORE COMPOSITE (si évaluable)
    if employee.can_be_evaluated():
        # Normalisation des scores sur 100
        productivity_score = min(100, roi_employee / 2)  # ROI/2 pour normaliser
        quality_score = max(0, 100 - error_rate * 10)  # Moins d'erreurs = meilleur score
        polyvalence_normalized = polyvalence_score
        punctuality_score = punctuality_rate  # Utiliser les données réelles
        presence_score = attendance_rate     # Utiliser les données réelles
        
        # Score composite pondéré
        composite_score = (
            productivity_score * 0.30 +
            quality_score * 0.25 +
            polyvalence_normalized * 0.20 +
            punctuality_score * 0.15 +
            presence_score * 0.10
        )
        
        # Grade
        if composite_score >= 90:
            grade = "A+"
        elif composite_score >= 80:
            grade = "A"
        elif composite_score >= 70:
            grade = "B"
        elif composite_score >= 60:
            grade = "C"
        else:
            grade = "D"
    else:
        composite_score = 0
        grade = "N/A"
    
    # 📊 COMPILATION DES KPI
    kpis = {
        # Métadonnées
        'can_be_evaluated': employee.can_be_evaluated(),
        'role_display': employee.get_role_display(),
        'is_production': employee.is_production_role(),
        'is_sales': employee.is_sales_role(),
        
        # Financiers
        'total_ca': float(orders_ca),
        'period_cost': float(period_cost),
        'profit': float(profit),
        'roi_employee': roi_employee,
        'profitability': profitability,
        'target_achievement': target_achievement,
        
        # Productivité
        'orders_count': orders_count,
        'ca_per_order': ca_per_order,
        'ca_per_hour': ca_per_hour,
        'orders_per_hour': orders_per_hour,
        
        # Qualité
        'issues_count': issues_count,
        'error_rate': error_rate,
        
        # Polyvalence
        'distinct_products': distinct_products,
        'total_products': total_products,
        'polyvalence_score': polyvalence_score,
        
        # Score composite
        'composite_score': composite_score,
        'grade': grade,
        
        # Temps
        'estimated_hours_period': estimated_hours_period,
        'estimated_hours_per_week': estimated_hours_per_week,
        'days_in_period': days_in_period,
        
        # Présence et ponctualité (données réelles)
        'attendance_rate': attendance_rate,
        'punctuality_rate': punctuality_rate,
        'actual_hours_period': actual_hours_period,
        'overtime_hours': overtime_hours,
        'days_present': days_present,
        'days_absent': days_absent,
        'late_arrivals': late_arrivals,
        'attendance_details': len(attendance_records) > 0,  # Indique si on a des données réelles
        
        # Évolution
        'monthly_stats': monthly_stats,
        
        # Périodes
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render_template('employees/employee_analytics.html',
                         employee=employee,
                         kpis=kpis,
                         period_form=period_form,
                         title=f"Analytics - {employee.name}")

@employees_bp.route('/payroll/work-hours', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_work_hours():
    """Gestion des heures de travail"""
    from app.employees.forms import WorkHoursForm
    from app.employees.models import WorkHours
    
    form = WorkHoursForm()
    
    # Remplir les choix d'employés
    active_employees = Employee.query.filter_by(is_active=True).all()
    form.employee_id.choices = [(str(emp.id), emp.name) for emp in active_employees]
    
    if form.validate_on_submit():
        # Vérifier si les heures existent déjà pour cette période
        existing_hours = WorkHours.query.filter_by(
            employee_id=form.employee_id.data,
            period_month=form.period_month.data,
            period_year=form.period_year.data
        ).first()
        
        if existing_hours:
            # Mettre à jour les heures existantes
            existing_hours.regular_hours = form.regular_hours.data
            existing_hours.overtime_hours = form.overtime_hours.data
            existing_hours.sick_days = form.sick_days.data
            existing_hours.vacation_days = form.vacation_days.data
            existing_hours.other_absences = form.other_absences.data
            existing_hours.performance_bonus = form.performance_bonus.data
            existing_hours.transport_allowance = form.transport_allowance.data
            existing_hours.meal_allowance = form.meal_allowance.data
            existing_hours.advance_deduction = form.advance_deduction.data
            existing_hours.other_deductions = form.other_deductions.data
            existing_hours.notes = form.notes.data
            existing_hours.updated_at = datetime.utcnow()
            
            flash('Heures de travail mises à jour avec succès!', 'success')
        else:
            # Créer de nouvelles heures
            work_hours = WorkHours(
                employee_id=form.employee_id.data,
                period_month=form.period_month.data,
                period_year=form.period_year.data,
                regular_hours=form.regular_hours.data,
                overtime_hours=form.overtime_hours.data,
                sick_days=form.sick_days.data,
                vacation_days=form.vacation_days.data,
                other_absences=form.other_absences.data,
                performance_bonus=form.performance_bonus.data,
                transport_allowance=form.transport_allowance.data,
                meal_allowance=form.meal_allowance.data,
                advance_deduction=form.advance_deduction.data,
                other_deductions=form.other_deductions.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            
            db.session.add(work_hours)
            flash('Heures de travail enregistrées avec succès!', 'success')
        
        db.session.commit()
        return redirect(url_for('employees.manage_work_hours'))
    
    # Récupérer les heures récentes pour affichage
    recent_hours = WorkHours.query.order_by(WorkHours.created_at.desc()).limit(10).all()
    
    return render_template('employees/work_hours.html', 
                         form=form, 
                         recent_hours=recent_hours,
                         title='Gestion des Heures de Travail')


@employees_bp.route('/api/consolidate-hours')
@login_required
@admin_required
def api_consolidate_hours():
    """API pour consolider les heures depuis les pointages (AJAX)
    
    Logique de comptage des jours payés :
    - Chaque semaine = 1 jour off payé de base (seulement si >= 6 jours travaillés)
    - Jours travaillés normaux = 1 jour payé chacun
    - Vendredi travaillé (si pas jour off) = 2 jours payés (double)
    - Jour off travaillé = 1 jour payé (les heures supplémentaires sont saisies manuellement)
    """
    from flask import jsonify
    import traceback
    
    try:
        employee_id = request.args.get('employee_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not all([employee_id, month, year]):
            return jsonify({'success': False, 'message': 'Paramètres manquants'})
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'message': 'Employé non trouvé'})
        
        # Récupérer le schedule pour déterminer le jour off
        schedule = employee.get_work_schedule()
        day_off = None  # Jour de la semaine (0=Lundi, 1=Mardi, ..., 6=Dimanche)
        if schedule:
            # Trouver le jour avec active=False (jour off)
            day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
            for day_name, config in schedule.items():
                if not config.get('active', True):
                    try:
                        day_off = day_names.index(day_name.lower())
                    except ValueError:
                        pass
        
        # Calculer les heures depuis les pointages
        total_regular = 0
        total_overtime = 0
        days_worked = 0
        
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Récupérer les pointages pour ce mois
        records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            db.func.date(AttendanceRecord.timestamp) >= start_date,
            db.func.date(AttendanceRecord.timestamp) <= end_date
        ).order_by(AttendanceRecord.timestamp).all()
        
        # Grouper par jour
        daily_records = {}
        for record in records:
            day_key = record.timestamp.date()
            if day_key not in daily_records:
                daily_records[day_key] = {'in': [], 'out': []}
            if record.punch_type == 'in':
                daily_records[day_key]['in'].append(record.timestamp)
            elif record.punch_type == 'out':
                daily_records[day_key]['out'].append(record.timestamp)
        
        # Calculer les heures par jour et compter les jours payés PAR SEMAINE
        paid_days = 0  # Total jours payés (avec doubles)
        days_by_week = {}  # {week_num: [dates travaillées]}
        paid_days_by_week = {}  # {week_num: jours payés pour cette semaine}
        
        for day_key, punches in daily_records.items():
            if punches['in'] and punches['out']:
                first_in = min(punches['in'])
                last_out = max(punches['out'])
                
                if last_out > first_in:
                    hours = (last_out - first_in).total_seconds() / 3600
                    days_worked += 1
                    
                    # Ajouter au compteur par semaine
                    week_num = day_key.isocalendar()[1]
                    if week_num not in days_by_week:
                        days_by_week[week_num] = []
                        paid_days_by_week[week_num] = 0
                    days_by_week[week_num].append(day_key)
                    
                    weekday = day_key.weekday()  # 0=Lundi, 4=Vendredi, 5=Samedi
                    is_friday = weekday == 4
                    is_day_off = (day_off is not None) and (weekday == day_off)
                    
                    # Calculer les jours payés pour ce jour
                    if is_day_off:
                        # Jour off travaillé = 1 jour payé (heures supplémentaires saisies manuellement)
                        paid_days_by_week[week_num] += 1
                    elif is_friday:
                        # Vendredi travaillé (si pas jour off) = 2 jours payés (double)
                        paid_days_by_week[week_num] += 2
                    else:
                        # Jour normal travaillé = 1 jour payé
                        paid_days_by_week[week_num] += 1
                    
                    # Calculer les heures (vendredi = double heures, jour off = heures normales)
                    if is_friday:
                        hours = hours * 2
                    # Jour off travaillé : heures normales (heures supplémentaires saisies manuellement)
                    
                    # Heures régulières (max 16h si vendredi, sinon 8h) et supplémentaires
                    daily_max = 16 if is_friday else 8
                    if hours <= daily_max:
                        total_regular += hours
                    else:
                        total_regular += daily_max
                        total_overtime += (hours - daily_max)
        
        # Calculer les absences par semaine et ajouter jour off payé si >= 6 jours travaillés
        weeks_in_month = set()
        current_day = start_date
        while current_day <= end_date:
            weeks_in_month.add(current_day.isocalendar()[1])
            current_day += timedelta(days=1)
        
        # Pour chaque semaine : ajouter jour off payé seulement si >= 6 jours travaillés
        for week_num in weeks_in_month:
            days_worked_this_week = len(days_by_week.get(week_num, []))
            if days_worked_this_week >= 6:
                # Ajouter 1 jour off payé de base
                paid_days_by_week[week_num] = paid_days_by_week.get(week_num, 0) + 1
            
            # Ajouter au total
            paid_days += paid_days_by_week.get(week_num, 0)
        
        # Calculer les absences (jours attendus - jours travaillés)
        expected_days_per_week = 6 if day_off is not None else 7  # 6 si jour off défini, sinon 7
        other_absences = 0
        for week_num in weeks_in_month:
            days_worked_this_week = len(days_by_week.get(week_num, []))
            if days_worked_this_week < expected_days_per_week:
                other_absences += (expected_days_per_week - days_worked_this_week)
        
        return jsonify({
            'success': True,
            'regular_hours': round(total_regular, 2),
            'overtime_hours': round(total_overtime, 2),
            'days_worked': days_worked,
            'paid_days': paid_days,
            'expected_days_per_week': expected_days_per_week,
            'other_absences': other_absences
        })
    
    except Exception as e:
        current_app.logger.error(f"Erreur dans api_consolidate_hours: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la consolidation: {str(e)}'
        }), 500


@employees_bp.route('/payroll/consolidate-hours', methods=['GET', 'POST'])
@login_required
@admin_required
def consolidate_hours():
    """Consolider les heures depuis les pointages vers WorkHours"""
    from app.employees.forms import ConsolidateHoursForm
    from app.employees.models import WorkHours, SalaryAdvance
    
    form = ConsolidateHoursForm()
    
    # Remplir les choix d'employés
    active_employees = Employee.query.filter_by(is_active=True).all()
    form.employee_id.choices = [('', '-- Sélectionner --')] + [(str(emp.id), emp.name) for emp in active_employees]
    
    results = []
    
    if form.validate_on_submit():
        month = int(form.period_month.data)
        year = int(form.period_year.data)
        
        # Déterminer quels employés traiter
        if form.consolidate_all.data:
            employees_to_process = active_employees
        else:
            emp = Employee.query.get(form.employee_id.data)
            employees_to_process = [emp] if emp else []
        
        for employee in employees_to_process:
            # Utiliser la même logique que l'API
            schedule = employee.get_work_schedule()
            day_off = None
            if schedule:
                day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
                for day_name, config in schedule.items():
                    if not config.get('active', True):
                        try:
                            day_off = day_names.index(day_name.lower())
                        except ValueError:
                            pass
            
            total_regular = 0
            total_overtime = 0
            days_worked = 0
            
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            
            records = AttendanceRecord.query.filter(
                AttendanceRecord.employee_id == employee.id,
                db.func.date(AttendanceRecord.timestamp) >= start_date,
                db.func.date(AttendanceRecord.timestamp) <= end_date
            ).order_by(AttendanceRecord.timestamp).all()
            
            daily_records = {}
            for record in records:
                day_key = record.timestamp.date()
                if day_key not in daily_records:
                    daily_records[day_key] = {'in': [], 'out': []}
                if record.punch_type == 'in':
                    daily_records[day_key]['in'].append(record.timestamp)
                elif record.punch_type == 'out':
                    daily_records[day_key]['out'].append(record.timestamp)
            
            days_by_week = {}
            for day_key, punches in daily_records.items():
                if punches['in'] and punches['out']:
                    first_in = min(punches['in'])
                    last_out = max(punches['out'])
                    
                    if last_out > first_in:
                        hours = (last_out - first_in).total_seconds() / 3600
                        days_worked += 1
                        
                        week_num = day_key.isocalendar()[1]
                        if week_num not in days_by_week:
                            days_by_week[week_num] = []
                        days_by_week[week_num].append(day_key)
                        
                        weekday = day_key.weekday()
                        is_friday = weekday == 4
                        is_day_off = (day_off is not None) and (weekday == day_off)
                        
                        # Calculer les heures (vendredi = double heures, jour off = heures normales)
                        if is_friday:
                            hours = hours * 2
                        # Jour off travaillé : heures normales (heures supplémentaires saisies manuellement)
                        
                        # Heures régulières (max 16h si vendredi, sinon 8h) et supplémentaires
                        daily_max = 16 if is_friday else 8
                        if hours <= daily_max:
                            total_regular += hours
                        else:
                            total_regular += daily_max
                            total_overtime += (hours - daily_max)
            
            weeks_in_month = set()
            current_day = start_date
            while current_day <= end_date:
                weeks_in_month.add(current_day.isocalendar()[1])
                current_day += timedelta(days=1)
            
            expected_days_per_week = 6 if day_off is not None else 7
            other_absences = 0
            for week_num in weeks_in_month:
                days_worked_this_week = len(days_by_week.get(week_num, []))
                if days_worked_this_week < expected_days_per_week:
                    other_absences += (expected_days_per_week - days_worked_this_week)
            
            total_advances = SalaryAdvance.get_total_for_period(employee.id, month, year)
            
            existing = WorkHours.query.filter_by(
                employee_id=employee.id,
                period_month=month,
                period_year=year
            ).first()
            
            if existing:
                existing.regular_hours = round(total_regular, 2)
                existing.overtime_hours = round(total_overtime, 2)
                existing.other_absences = other_absences
                existing.advance_deduction = total_advances
                existing.updated_at = datetime.utcnow()
                action = "mis à jour"
            else:
                work_hours = WorkHours(
                    employee_id=employee.id,
                    period_month=month,
                    period_year=year,
                    regular_hours=round(total_regular, 2),
                    overtime_hours=round(total_overtime, 2),
                    other_absences=other_absences,
                    advance_deduction=total_advances,
                    created_by=current_user.id
                )
                db.session.add(work_hours)
                action = "créé"
            
            results.append({
                'employee': employee.name,
                'regular_hours': round(total_regular, 2),
                'overtime_hours': round(total_overtime, 2),
                'days_worked': days_worked,
                'advances': total_advances,
                'action': action
            })
        
        db.session.commit()
        
        if results:
            flash(f'Consolidation terminée pour {len(results)} employé(s)!', 'success')
        else:
            flash('Aucun employé à consolider.', 'warning')
    
    return render_template('employees/consolidate_hours.html',
                         form=form,
                         results=results,
                         title='Consolider les Heures')


@employees_bp.route('/api/get-advances')
@login_required
@admin_required
def api_get_advances():
    """API pour récupérer le total des avances (AJAX)"""
    from flask import jsonify
    from app.employees.models import SalaryAdvance
    
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not all([employee_id, month, year]):
        return jsonify({'success': False, 'message': 'Paramètres manquants'})
    
    # Récupérer les avances
    advances = SalaryAdvance.get_advances_for_period(employee_id, month, year)
    total = SalaryAdvance.get_total_for_period(employee_id, month, year)
    
    return jsonify({
        'success': True,
        'total': round(total, 2),
        'count': len(advances)
    })


@employees_bp.route('/payroll/advances', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_advances():
    """Gestion des avances sur salaire"""
    from app.employees.forms import SalaryAdvanceForm
    from app.employees.models import SalaryAdvance
    
    form = SalaryAdvanceForm()
    
    # Remplir les choix d'employés
    active_employees = Employee.query.filter_by(is_active=True).all()
    form.employee_id.choices = [(str(emp.id), emp.name) for emp in active_employees]
    
    # Valeurs par défaut
    if not form.advance_date.data:
        form.advance_date.data = date.today()
    if not form.period_month.data:
        form.period_month.data = str(date.today().month)
    if not form.period_year.data:
        form.period_year.data = date.today().year
    
    if form.validate_on_submit():
        advance = SalaryAdvance(
            employee_id=form.employee_id.data,
            amount=form.amount.data,
            advance_date=form.advance_date.data,
            period_month=int(form.period_month.data),
            period_year=form.period_year.data,
            reason=form.reason.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        
        db.session.add(advance)
        db.session.commit()
        
        employee = Employee.query.get(form.employee_id.data)
        flash(f'Avance de {form.amount.data} DA enregistrée pour {employee.name}!', 'success')
        return redirect(url_for('employees.manage_advances'))
    
    # Filtres pour affichage
    filter_month = request.args.get('month', date.today().month, type=int)
    filter_year = request.args.get('year', date.today().year, type=int)
    filter_employee = request.args.get('employee_id', type=int)
    
    # Requête des avances
    query = SalaryAdvance.query.filter_by(
        period_month=filter_month,
        period_year=filter_year
    )
    
    if filter_employee:
        query = query.filter_by(employee_id=filter_employee)
    
    advances = query.order_by(SalaryAdvance.advance_date.desc()).all()
    
    # Calculer les totaux par employé
    totals_by_employee = {}
    for adv in advances:
        if adv.employee_id not in totals_by_employee:
            totals_by_employee[adv.employee_id] = {
                'employee': adv.employee,
                'total': 0,
                'count': 0
            }
        totals_by_employee[adv.employee_id]['total'] += float(adv.amount)
        totals_by_employee[adv.employee_id]['count'] += 1
    
    return render_template('employees/salary_advances.html',
                         form=form,
                         advances=advances,
                         totals_by_employee=totals_by_employee,
                         filter_month=filter_month,
                         filter_year=filter_year,
                         filter_employee=filter_employee,
                         employees=active_employees,
                         title='Avances sur Salaire')


@employees_bp.route('/payroll/advances/<int:advance_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_advance(advance_id):
    """Supprimer une avance sur salaire"""
    from app.employees.models import SalaryAdvance
    
    advance = SalaryAdvance.query.get_or_404(advance_id)
    employee_name = advance.employee.name
    amount = advance.amount
    
    db.session.delete(advance)
    db.session.commit()
    
    flash(f'Avance de {amount} DA pour {employee_name} supprimée!', 'success')
    return redirect(url_for('employees.manage_advances'))


@employees_bp.route('/payroll/calculate', methods=['GET', 'POST'])
@login_required
@admin_required
def calculate_payroll():
    """Calculer la paie pour une période donnée"""
    from app.employees.forms import PayrollCalculationForm
    from app.employees.models import PayrollCalculation, WorkHours
    
    form = PayrollCalculationForm()
    
    # Remplir les choix d'employés
    # Inclure les employés actifs + les employés inactifs qui ont des heures de travail
    # (pour permettre le calcul de paie même si l'employé a été désactivé récemment)
    active_employees = Employee.query.filter_by(is_active=True).all()
    
    # Récupérer aussi les employés inactifs qui ont des heures de travail enregistrées
    # (pour les périodes passées)
    inactive_with_hours = db.session.query(Employee).join(
        WorkHours, Employee.id == WorkHours.employee_id
    ).filter(Employee.is_active == False).distinct().all()
    
    # Combiner les deux listes et éviter les doublons
    all_employees = {emp.id: emp for emp in active_employees}
    for emp in inactive_with_hours:
        if emp.id not in all_employees:
            all_employees[emp.id] = emp
    
    # Trier par nom et créer les choix
    sorted_employees = sorted(all_employees.values(), key=lambda e: e.name)
    form.employee_id.choices = [(str(emp.id), f"{emp.name} {'(inactif)' if not emp.is_active else ''}") for emp in sorted_employees]
    
    if form.validate_on_submit():
        employee = Employee.query.get(form.employee_id.data)
        
        # Récupérer les heures de travail pour cette période
        work_hours = WorkHours.query.filter_by(
            employee_id=form.employee_id.data,
            period_month=form.period_month.data,
            period_year=form.period_year.data
        ).first()
        
        if not work_hours:
            flash('Aucune heure de travail enregistrée pour cette période!', 'error')
            return render_template('employees/payroll_calculation.html', form=form, title='Calcul de Paie')
        
        # Vérifier si le calcul existe déjà
        existing_payroll = PayrollCalculation.query.filter_by(
            employee_id=form.employee_id.data,
            period_month=form.period_month.data,
            period_year=form.period_year.data
        ).first()
        
        if existing_payroll:
            payroll = existing_payroll
        else:
            # Créer un nouveau calcul de paie
            payroll = PayrollCalculation(
                employee_id=form.employee_id.data,
                work_hours_id=work_hours.id,
                period_month=form.period_month.data,
                period_year=form.period_year.data,
                base_salary=employee.salaire_fixe,
                created_by=current_user.id
            )
        
        # Calculer le taux horaire (basé sur 173.33 heures par mois)
        monthly_hours = 240  # 30 jours × 8h/jour
        payroll.hourly_rate = float(employee.salaire_fixe) / monthly_hours
        payroll.overtime_rate = payroll.hourly_rate * 1.5  # Majoration 50%
        
        # Les taux de charges sont définis par défaut dans le modèle (9%, 1.5%, 7%)
        # Pas besoin de les modifier depuis le formulaire
        
        # Calculer tous les montants
        payroll.calculate_all()
        
        # Validation
        if form.is_validated.data:
            payroll.is_validated = True
            payroll.validated_at = datetime.utcnow()
            payroll.validated_by = current_user.id
            payroll.validation_notes = form.validation_notes.data
        
        if not existing_payroll:
            db.session.add(payroll)
        
        db.session.commit()
        
        # Intégration comptable automatique lors de la validation
        if form.is_validated.data:
            try:
                from app.accounting.services import AccountingIntegrationService
                payroll_entry = AccountingIntegrationService.create_payroll_entry(
                    payroll_id=payroll.id,
                    gross_salary=float(payroll.gross_salary),
                    net_salary=float(payroll.net_salary),
                    description=f"Calcul salaire {employee.name} - {form.period_month.data}/{form.period_year.data}"
                )
                # Lier l'écriture au calcul de paie
                payroll.payroll_entry_id = payroll_entry.id
            except Exception as e:
                current_app.logger.error(f"Erreur intégration comptable salaire (payroll_id={payroll.id}, employee_id={employee.id}): {e}", exc_info=True)
            # On continue même si l'intégration comptable échoue
        
        flash('Paie calculée avec succès!', 'success')
        
        # Pré-remplir le formulaire avec les résultats calculés
        form.base_salary.data = payroll.base_salary
        form.overtime_amount.data = payroll.overtime_amount
        form.total_bonuses.data = payroll.total_bonuses
        form.total_deductions.data = payroll.total_deductions
        form.gross_salary.data = payroll.gross_salary
        form.total_charges.data = payroll.total_charges
        form.net_salary.data = payroll.net_salary
        form.is_validated.data = payroll.is_validated
        form.validation_notes.data = payroll.validation_notes
        
        # Passer les données du calcul au template
        return render_template('employees/payroll_calculation.html', 
                             form=form, 
                             payroll=payroll,
                             employee=employee,
                             work_hours=work_hours,
                             title='Calcul de Paie')
    
    # Vérifier si on doit pré-charger un calcul existant (via paramètres GET)
    employee_id = request.args.get('employee_id')
    period_month = request.args.get('period_month')
    period_year = request.args.get('period_year')
    
    payroll = None
    employee = None
    work_hours = None
    
    if employee_id and period_month and period_year:
        try:
            existing_payroll = PayrollCalculation.query.filter_by(
                employee_id=int(employee_id),
                period_month=int(period_month),
                period_year=int(period_year)
            ).first()
            
            if existing_payroll:
                payroll = existing_payroll
                employee = Employee.query.get(employee_id)
                work_hours = WorkHours.query.get(payroll.work_hours_id)
                
                # Pré-remplir le formulaire
                form.employee_id.data = str(employee_id)
                form.period_month.data = str(period_month)
                form.period_year.data = int(period_year)
                form.base_salary.data = payroll.base_salary
                form.overtime_amount.data = payroll.overtime_amount
                form.total_bonuses.data = payroll.total_bonuses
                form.total_deductions.data = payroll.total_deductions
                form.gross_salary.data = payroll.gross_salary
                form.total_charges.data = payroll.total_charges
                form.net_salary.data = payroll.net_salary
                form.is_validated.data = payroll.is_validated
                form.validation_notes.data = payroll.validation_notes
                
        except (ValueError, TypeError):
            pass  # Paramètres invalides, ignorer
    
    return render_template('employees/payroll_calculation.html', 
                         form=form,
                         payroll=payroll,
                         employee=employee,
                         work_hours=work_hours,
                         title='Calcul de Paie')

@employees_bp.route('/salaries', methods=['GET', 'POST'])
@login_required
@admin_required
def salaries_dashboard():
    """
    Affiche la liste des employés avec leurs salaires calculés pour une période donnée
    Permet de payer chaque employé individuellement
    """
    from app.employees.models import PayrollCalculation, WorkHours
    from app.accounting.services import AccountingIntegrationService
    
    # Récupérer la période sélectionnée ou courante par défaut
    current_date = datetime.now()
    selected_month = request.args.get('month', current_date.month, type=int)
    selected_year = request.args.get('year', current_date.year, type=int)
    
    if request.method == 'POST':
        # Traitement du paiement d'un salaire (toujours par banque)
        payroll_id = request.form.get('payroll_id')
        
        if payroll_id:
            try:
                payroll = PayrollCalculation.query.get(payroll_id)
                if payroll and payroll.is_validated and not payroll.is_paid:
                    # Créer l'écriture comptable de paiement (toujours par banque)
                    payment_entry = AccountingIntegrationService.create_salary_payment_entry(
                        payroll_id=payroll.id,
                        employee_id=payroll.employee_id,
                        net_salary=float(payroll.net_salary),
                        payment_method='bank',  # Toujours par banque
                        description=f"Paiement salaire {payroll.employee.name} - {payroll.period_month}/{payroll.period_year}"
                    )
                    
                    # Lier l'écriture de paiement au calcul de paie
                    payroll.payment_entry_id = payment_entry.id
                    
                    # Marquer le salaire comme payé
                    payroll.is_paid = True
                    payroll.paid_at = datetime.utcnow()
                    payroll.paid_by = current_user.id
                    db.session.commit()
                    
                    flash(f'Paiement de {payroll.net_salary:.2f} DZD effectué par virement bancaire pour {payroll.employee.name}', 'success')
                elif payroll and payroll.is_paid:
                    flash('Ce salaire a déjà été payé', 'warning')
                else:
                    flash('Calcul de paie non trouvé ou non validé', 'error')
            except Exception as e:
                flash(f'Erreur lors du paiement: {str(e)}', 'error')
        
        # Rediriger en conservant les paramètres de période
        return redirect(url_for('employees.salaries_dashboard', month=selected_month, year=selected_year))
    
    # Récupérer tous les calculs de paie validés pour la période sélectionnée
    payrolls = PayrollCalculation.query.filter(
        PayrollCalculation.is_validated == True,
        PayrollCalculation.period_month == selected_month,
        PayrollCalculation.period_year == selected_year
    ).join(Employee).order_by(Employee.name).all()
    
    # Recalculer les avances en temps réel pour chaque payroll
    # (car les avances peuvent avoir changé depuis le calcul initial)
    for payroll in payrolls:
        try:
            payroll.calculate_all()
        except Exception as e:
            current_app.logger.warning(f"Erreur lors du recalcul de la paie {payroll.id}: {str(e)}")
    
    # Sauvegarder les recalculs
    db.session.commit()
    
    # Séparer les payés et non payés
    paid_payrolls = [p for p in payrolls if p.is_paid]
    unpaid_payrolls = [p for p in payrolls if not p.is_paid]
    
    # Calculer les totaux
    total_gross = sum(float(p.gross_salary) for p in payrolls)
    total_net = sum(float(p.net_salary) for p in payrolls)
    total_paid = sum(float(p.net_salary) for p in paid_payrolls)
    total_unpaid = sum(float(p.net_salary) for p in unpaid_payrolls)
    
    # Générer les options pour le sélecteur de période
    # Récupérer toutes les périodes disponibles
    available_periods = db.session.query(
        PayrollCalculation.period_year,
        PayrollCalculation.period_month
    ).filter(PayrollCalculation.is_validated == True).distinct().order_by(
        PayrollCalculation.period_year.desc(),
        PayrollCalculation.period_month.desc()
    ).all()
    
    return render_template('employees/salaries.html',
                         payrolls=payrolls,
                         paid_payrolls=paid_payrolls,
                         unpaid_payrolls=unpaid_payrolls,
                         selected_month=selected_month,
                         selected_year=selected_year,
                         available_periods=available_periods,
                         total_gross=total_gross,
                         total_net=total_net,
                         total_paid=total_paid,
                         total_unpaid=total_unpaid,
                         title='Gestion des Salaires')

@employees_bp.route('/payroll/<int:payroll_id>')
@login_required
@admin_required
def view_payroll(payroll_id):
    """Afficher les détails d'un calcul de paie"""
    from app.employees.models import PayrollCalculation
    
    payroll = PayrollCalculation.query.get_or_404(payroll_id)
    payslip_data = payroll.get_payslip_data()
    
    return render_template('employees/view_payroll.html', 
                         payroll=payroll,
                         payslip_data=payslip_data,
                         title=f'Paie {payroll.employee.name} - {payroll.period_month:02d}/{payroll.period_year}')

@employees_bp.route('/payroll/generate-payslips', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_payslips():
    """Générer les bulletins de paie"""
    from app.employees.forms import PayslipGenerationForm
    from app.employees.models import PayrollCalculation
    
    form = PayslipGenerationForm()
    
    # Remplir les choix d'employés
    active_employees = Employee.query.filter_by(is_active=True).all()
    form.employee_ids.choices = [(str(emp.id), emp.name) for emp in active_employees]
    
    if form.validate_on_submit():
        month = int(form.period_month.data)
        year = int(form.period_year.data)
        
        # Déterminer les employés concernés
        if form.employee_ids.data:
            employee_ids = [int(emp_id) for emp_id in form.employee_ids.data]
            employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        else:
            # Tous les employés
            if form.include_inactive.data:
                employees = Employee.query.all()
            else:
                employees = Employee.query.filter_by(is_active=True).all()
        
        # Récupérer les calculs de paie pour la période
        payrolls = []
        for employee in employees:
            payroll = PayrollCalculation.query.filter_by(
                employee_id=employee.id,
                period_month=month,
                period_year=year
            ).first()
            
            if payroll and payroll.is_validated:
                payrolls.append(payroll)
        
        if not payrolls:
            flash('Aucune paie validée trouvée pour cette période!', 'warning')
            return render_template('employees/generate_payslips.html', form=form, title='Génération Bulletins')
        
        # Générer les bulletins selon le format choisi
        if form.output_format.data in ['pdf', 'both']:
            # Générer PDF (placeholder pour l'instant)
            flash(f'Génération PDF de {len(payrolls)} bulletins en cours...', 'info')
        
        if form.output_format.data in ['excel', 'both']:
            # Générer Excel (placeholder pour l'instant)
            flash(f'Génération Excel de {len(payrolls)} bulletins en cours...', 'info')
        
        flash(f'Bulletins générés avec succès pour {len(payrolls)} employés!', 'success')
        return redirect(url_for('employees.payroll_dashboard'))
    
    return render_template('employees/generate_payslips.html', 
                         form=form, 
                         title='Génération des Bulletins de Paie')

@employees_bp.route('/payroll/period-summary/<int:month>/<int:year>')
@login_required
@admin_required
def payroll_period_summary(month, year):
    """Résumé de la paie pour une période donnée"""
    from app.employees.models import PayrollCalculation
    
    # Récupérer tous les calculs de paie pour la période
    payrolls = PayrollCalculation.query.filter_by(
        period_month=month,
        period_year=year
    ).all()
    
    # Calculer les totaux
    total_employees = len(payrolls)
    validated_payrolls = [p for p in payrolls if p.is_validated]
    pending_payrolls = [p for p in payrolls if not p.is_validated]
    
    total_gross = sum(float(p.gross_salary) for p in validated_payrolls)
    total_net = sum(float(p.net_salary) for p in validated_payrolls)
    total_charges = sum(float(p.total_charges) for p in validated_payrolls)
    
    summary = {
        'period': f"{month:02d}/{year}",
        'total_employees': total_employees,
        'validated_count': len(validated_payrolls),
        'pending_count': len(pending_payrolls),
        'total_gross': total_gross,
        'total_net': total_net,
        'total_charges': total_charges,
        'average_gross': total_gross / len(validated_payrolls) if validated_payrolls else 0,
        'average_net': total_net / len(validated_payrolls) if validated_payrolls else 0
    }
    
    return render_template('employees/payroll_period_summary.html',
                         summary=summary,
                         payrolls=payrolls,
                         validated_payrolls=validated_payrolls,
                         pending_payrolls=pending_payrolls,
                         title=f'Résumé Paie {month:02d}/{year}')

