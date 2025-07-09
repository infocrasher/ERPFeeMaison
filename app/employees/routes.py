# -*- coding: utf-8 -*-
"""
app/employees/routes.py
Routes pour la gestion des employés
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db
from app.employees.models import Employee
from app.employees.forms import EmployeeForm, EmployeeSearchForm, WorkScheduleForm, AnalyticsPeriodForm, WorkHoursForm, PayrollCalculationForm
from decorators import admin_required
from datetime import datetime, timedelta, date
from sqlalchemy import func, text
from decimal import Decimal

# Imports pour analytics seront fait dynamiquement

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
    
    return render_template('employees/view_employee.html',
                         employee=employee,
                         monthly_revenue=monthly_revenue,
                         productivity_score=productivity_score,
                         orders_count=orders_count,
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

# API pour les dashboards
@employees_bp.route('/api/production-staff')
@login_required
@admin_required
def get_production_staff():
    """API pour récupérer les employés de production actifs"""
    
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production', 'patissier'])
    ).order_by(Employee.name).all()
    
    return jsonify([{
        'id': emp.id,
        'name': emp.name,
        'role': emp.role,
        'role_display': emp.role.replace('_', ' ').title()
    } for emp in employees])

@employees_bp.route('/api/stats')
@login_required
@admin_required
def get_employees_stats():
    """API pour les statistiques employés"""
    
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    stats = {
        'total_employees': Employee.query.count(),
        'active_employees': Employee.query.filter(Employee.is_active == True).count(),
        'production_staff': Employee.query.filter(
            Employee.is_active == True,
            Employee.role.in_(['production', 'chef_production', 'assistant_production', 'patissier'])
        ).count()
    }
    
    return jsonify(stats)

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
            form.load_from_schedule(current_schedule)
    
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
    
    # Import dynamique pour éviter les conflits de métadonnées
    try:
        from models import Order
    except ImportError as e:
        flash(f"Module commandes non disponible: {str(e)}", "error")
        return redirect(url_for('employees.view_employee', employee_id=employee_id))
    
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
    
    # 🆕 Vérifier si l'employé peut être évalué
    if not employee.can_be_evaluated():
        flash(f"Les employés en support ({employee.get_role_display()}) ne sont pas évalués sur la performance.", "info")
        kpis = {
            'can_be_evaluated': False,
            'role_display': employee.get_role_display(),
            'start_date': start_date,
            'end_date': end_date
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
    ca_per_hour = float(orders_ca / estimated_hours_period) if estimated_hours_period > 0 else 0
    
    # Commandes par heure
    orders_per_hour = (orders_count / estimated_hours_period) if estimated_hours_period > 0 else 0
    
    # 🎯 SCORE POLYVALENCE
    if employee.is_production_role() or employee.is_sales_role():
        # Calculer le nombre de produits différents travaillés
        try:
            from models import Product
            
            distinct_products = db.session.query(func.count(func.distinct(Product.id))).select_from(
                Order
            ).join(Order.items).join(Product).join(Order.produced_by).filter(
                Employee.id == employee.id,
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime
            ).scalar() or 0
            
            total_products = Product.query.count()
            polyvalence_score = (distinct_products / total_products * 100) if total_products > 0 else 0
            
        except ImportError:
            distinct_products = 0
            total_products = 1
            polyvalence_score = 0
    else:
        distinct_products = 0
        total_products = 1
        polyvalence_score = 0
    
    # 🔍 KPI QUALITÉ (problèmes détectés)
    from app.employees.models import OrderIssue
    
    issues_count = OrderIssue.query.filter(
        OrderIssue.employee_id == employee.id,
        OrderIssue.detected_at >= start_datetime,
        OrderIssue.detected_at <= end_datetime
    ).count()
    
    error_rate = (issues_count / orders_count * 100) if orders_count > 0 else 0
    
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
        punctuality_score = 85  # À calculer avec les données de pointage
        presence_score = 90     # À calculer avec les données de pointage
        
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

@employees_bp.route('/payroll/calculate', methods=['GET', 'POST'])
@login_required
@admin_required
def calculate_payroll():
    """Calculer la paie pour une période donnée"""
    from app.employees.forms import PayrollCalculationForm
    from app.employees.models import PayrollCalculation, WorkHours
    
    form = PayrollCalculationForm()
    
    # Remplir les choix d'employés
    active_employees = Employee.query.filter_by(is_active=True).all()
    form.employee_id.choices = [(str(emp.id), emp.name) for emp in active_employees]
    
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
        monthly_hours = 173.33
        payroll.hourly_rate = float(employee.salaire_fixe) / monthly_hours
        payroll.overtime_rate = payroll.hourly_rate * 1.5  # Majoration 50%
        
        # Mettre à jour les taux de charges
        payroll.social_security_rate = form.social_security_rate.data
        payroll.unemployment_rate = form.unemployment_rate.data
        payroll.retirement_rate = form.retirement_rate.data
        
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
        
        flash('Paie calculée avec succès!', 'success')
        return redirect(url_for('employees.view_payroll', payroll_id=payroll.id))
    
    return render_template('employees/payroll_calculation.html', 
                         form=form, 
                         title='Calcul de Paie')

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

