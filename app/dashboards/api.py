"""
API Dashboard pour ERP Fée Maison
Endpoints pour dashboards journalier et mensuel
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required
from decorators import admin_required
from extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from decimal import Decimal
import json
import logging

# Imports des modèles
from models import Order, OrderItem, Product, Category
from app.employees.models import Employee, AttendanceRecord, OrderIssue
from app.accounting.models import Account, JournalEntry, JournalEntryLine
from app.sales.models import CashRegisterSession, CashMovement

# Imports des services reports (Phase 1 - Intégration IA)
from app.reports.services import (
    DailySalesReportService,
    StockAlertReportService,
    MonthlyProfitLossService,
    WeeklyProductPerformanceService
)

# Import AI Manager (Phase 1 - Intégration IA)
from app.ai import AIManager

# Logger
logger = logging.getLogger(__name__)

# Création du blueprint
dashboard_api = Blueprint('dashboard_api', __name__)

# ==========================================
# DASHBOARD JOURNALIER - PILOTAGE OPÉRATIONNEL
# ==========================================

@dashboard_api.route('/daily/production', methods=['GET'])
@login_required
@admin_required
def daily_production():
    """Section Production - Commandes en retard et urgentes"""
    
    now = datetime.utcnow()
    today = date.today()
    
    # Commandes en retard (due_date < now)
    overdue_orders = Order.query.filter(
        and_(
            Order.due_date < now,
            Order.status.in_(['pending', 'in_production'])
        )
    ).order_by(Order.due_date.asc()).all()
    
    # Commandes urgentes (dans les 2h)
    urgent_orders = Order.query.filter(
        and_(
            Order.due_date >= now,
            Order.due_date <= now + timedelta(hours=2),
            Order.status.in_(['pending', 'in_production'])
        )
    ).order_by(Order.due_date.asc()).all()
    
    # Commandes normales (plus de 2h)
    normal_orders = Order.query.filter(
        and_(
            Order.due_date > now + timedelta(hours=2),
            Order.status.in_(['pending', 'in_production'])
        )
    ).order_by(Order.due_date.asc()).all()
    
    # Statistiques
    stats = {
        'overdue_count': len(overdue_orders),
        'urgent_count': len(urgent_orders),
        'normal_count': len(normal_orders),
        'total_production': len(overdue_orders) + len(urgent_orders) + len(normal_orders)
    }
    
    # Formatage des données
    def format_order(order):
        time_diff = (order.due_date - now).total_seconds() / 3600
        return {
            'id': order.id,
            'customer_name': order.customer_name or 'N/A',
            'due_date': order.due_date.isoformat(),
            'time_remaining_hours': round(time_diff, 1),
            'total_amount': float(order.total_amount or 0),
            'status': order.status,
            'items_count': order.get_items_count(),
            'priority': 'overdue' if time_diff < 0 else 'urgent' if time_diff <= 2 else 'normal'
        }
    
    return jsonify({
        'success': True,
        'data': {
            'stats': stats,
            'overdue_orders': [format_order(o) for o in overdue_orders],
            'urgent_orders': [format_order(o) for o in urgent_orders],
            'normal_orders': [format_order(o) for o in normal_orders]
        }
    })

@dashboard_api.route('/daily/stock', methods=['GET'])
@login_required
@admin_required
def daily_stock():
    """Section Stock - Alertes et niveaux critiques
    
    PHASE 1 - Intégration app/reports : Utilise StockAlertReportService (remplacement complet)
    """
    
    today = date.today()
    
    # PHASE 1 - Utiliser StockAlertReportService pour alertes stock
    try:
        report_data = StockAlertReportService.generate()
        logger.info("[REPORT] Data loaded from StockAlertReportService")
        
        # Extraction des données depuis le rapport
        out_of_stock = report_data.get('out_of_stock', [])
        low_stock_products = report_data.get('low_stock_products', [])
        
        # Format des produits (pour compatibilité front-end)
        def format_product(product_data):
            if isinstance(product_data, dict):
                # Déjà formaté par le service
                return product_data
            else:
                # Objet Product
                return {
                    'id': product_data.id,
                    'name': product_data.name,
                    'category': product_data.category.name if product_data.category else 'N/A',
                    'stock_comptoir': float(product_data.stock_comptoir or 0),
                    'stock_local': float(product_data.stock_ingredients_local or 0),
                    'stock_magasin': float(product_data.stock_ingredients_magasin or 0),
                    'seuil_comptoir': float(product_data.seuil_min_comptoir or 0),
                    'seuil_local': float(product_data.seuil_min_ingredients_local or 0),
                    'seuil_magasin': float(product_data.seuil_min_ingredients_magasin or 0),
                    'total_value': float(product_data.total_stock_value or 0)
                }
        
        # Valeur totale du stock
        total_stock_value = db.session.query(func.sum(Product.total_stock_value)).scalar() or 0
        
        # Mouvements aujourd'hui (basé sur les commandes)
        today_movements = Order.query.filter(
            func.date(Order.created_at) == today
        ).count()
        
        # Métadonnées IA disponibles
        benchmark = report_data.get('benchmark', {})
        
        return jsonify({
            'success': True,
            'data': {
                'stats': {
                    'out_of_stock_count': len(out_of_stock),
                    'low_stock_count': len(low_stock_products),
                    'total_stock_value': float(total_stock_value),
                    'today_movements': today_movements,
                    # Métadonnées IA (Phase 1)
                    'benchmark': benchmark
                },
                'out_of_stock': [format_product(p) for p in out_of_stock],
                'low_stock': [format_product(p) for p in low_stock_products]
            }
        })
        
    except Exception as e:
        logger.error(f"[REPORT] Error loading StockAlertReportService: {e}")
        # Fallback sur calcul direct si erreur
        out_of_stock = Product.query.filter(
            or_(
                Product.stock_comptoir <= 0,
                Product.stock_ingredients_local <= 0,
                Product.stock_ingredients_magasin <= 0
            )
        ).all()
        
        low_stock = Product.query.filter(
            or_(
                and_(Product.stock_comptoir > 0, Product.stock_comptoir <= Product.seuil_min_comptoir),
                and_(Product.stock_ingredients_local > 0, Product.stock_ingredients_local <= Product.seuil_min_ingredients_local),
                and_(Product.stock_ingredients_magasin > 0, Product.stock_ingredients_magasin <= Product.seuil_min_ingredients_magasin)
            )
        ).all()
        
        total_stock_value = db.session.query(func.sum(Product.total_stock_value)).scalar() or 0
        today_movements = Order.query.filter(func.date(Order.created_at) == today).count()
        
        def format_product(product):
            return {
                'id': product.id,
                'name': product.name,
                'category': product.category.name if product.category else 'N/A',
                'stock_comptoir': float(product.stock_comptoir or 0),
                'stock_local': float(product.stock_ingredients_local or 0),
                'stock_magasin': float(product.stock_ingredients_magasin or 0),
                'seuil_comptoir': float(product.seuil_min_comptoir or 0),
                'seuil_local': float(product.seuil_min_ingredients_local or 0),
                'seuil_magasin': float(product.seuil_min_ingredients_magasin or 0),
                'total_value': float(product.total_stock_value or 0)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'stats': {
                    'out_of_stock_count': len(out_of_stock),
                    'low_stock_count': len(low_stock),
                    'total_stock_value': float(total_stock_value),
                    'today_movements': today_movements
                },
                'out_of_stock': [format_product(p) for p in out_of_stock],
                'low_stock': [format_product(p) for p in low_stock]
            }
        })

@dashboard_api.route('/daily/sales', methods=['GET'])
@login_required
@admin_required
def daily_sales():
    """Section Ventes - CA et commandes du jour
    
    PHASE 1 - Intégration app/reports : Utilise DailySalesReportService pour cohérence des calculs
    """
    
    today = date.today()
    
    # PHASE 1 - Utiliser DailySalesReportService pour revenue et transactions
    try:
        report_data = DailySalesReportService.generate(today)
        logger.info("[REPORT] Data loaded from DailySalesReportService")
        
        daily_revenue = report_data['total_revenue']
        total_orders = report_data['total_transactions']
        
        # Métadonnées IA disponibles (pour enrichissement futur)
        growth_rate = report_data.get('growth_rate', 0)
        trend_direction = report_data.get('trend_direction', 'stable')
        
    except Exception as e:
        logger.error(f"[REPORT] Error loading DailySalesReportService: {e}")
        # Fallback sur calcul direct si erreur
        daily_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(
                func.date(Order.created_at) == today,
                Order.status.in_(['delivered', 'completed'])
            )
        ).scalar() or 0
        total_orders = Order.query.filter(func.date(Order.created_at) == today).count()
        growth_rate = 0
        trend_direction = 'stable'
    
    # Commandes du jour (pour répartition par statut)
    daily_orders = Order.query.filter(
        func.date(Order.created_at) == today
    ).all()
    
    # Commandes par statut
    orders_by_status = {}
    for order in daily_orders:
        status = order.status
        if status not in orders_by_status:
            orders_by_status[status] = {'count': 0, 'amount': 0}
        orders_by_status[status]['count'] += 1
        orders_by_status[status]['amount'] += float(order.total_amount or 0)
    
    # Session de caisse (spécifique au dashboard)
    cash_session = CashRegisterSession.query.filter_by(is_open=True).first()
    
    # Mouvements de caisse aujourd'hui
    today_movements = CashMovement.query.filter(
        func.date(CashMovement.created_at) == today
    ).all()
    
    cash_in = sum(float(m.amount) for m in today_movements if m.movement_type == 'in')
    cash_out = sum(float(m.amount) for m in today_movements if m.movement_type == 'out')
    
    return jsonify({
        'success': True,
        'data': {
            'stats': {
                'daily_revenue': float(daily_revenue),
                'total_orders': total_orders,
                'delivered_orders': len([o for o in daily_orders if o.status in ['delivered', 'completed']]),
                'cash_session_open': cash_session is not None,
                'cash_in_today': cash_in,
                'cash_out_today': cash_out,
                'net_cash_flow': cash_in - cash_out,
                # Métadonnées IA (Phase 1)
                'growth_rate': growth_rate,
                'trend_direction': trend_direction
            },
            'orders_by_status': orders_by_status,
            'cash_session': {
                'is_open': cash_session is not None,
                'opened_at': cash_session.opened_at.isoformat() if cash_session else None,
                'initial_amount': float(cash_session.initial_amount) if cash_session else 0
            }
        }
    })

@dashboard_api.route('/daily/employees', methods=['GET'])
@login_required
@admin_required
def daily_employees():
    """Section Employés - Présence et performance"""
    
    today = date.today()
    
    # Employés actifs
    active_employees = Employee.query.filter_by(is_active=True).all()
    
    # Pointages aujourd'hui
    today_attendance = AttendanceRecord.query.filter(
        func.date(AttendanceRecord.timestamp) == today
    ).all()
    
    # Grouper par employé
    attendance_by_employee = {}
    for record in today_attendance:
        emp_id = record.employee_id
        if emp_id not in attendance_by_employee:
            attendance_by_employee[emp_id] = {'in': None, 'out': None}
        
        if record.punch_type == 'in':
            attendance_by_employee[emp_id]['in'] = record.timestamp
        elif record.punch_type == 'out':
            attendance_by_employee[emp_id]['out'] = record.timestamp
    
    # Calculer les heures travaillées
    employee_stats = []
    for emp in active_employees:
        attendance = attendance_by_employee.get(emp.id, {})
        hours_worked = 0
        
        if attendance.get('in') and attendance.get('out'):
            duration = (attendance['out'] - attendance['in']).total_seconds() / 3600
            hours_worked = round(duration, 2)
        
        employee_stats.append({
            'id': emp.id,
            'name': emp.name,
            'role': emp.get_role_display(),
            'is_present': emp.id in attendance_by_employee,
            'clocked_in': attendance.get('in').isoformat() if attendance.get('in') else None,
            'clocked_out': attendance.get('out').isoformat() if attendance.get('out') else None,
            'hours_worked': hours_worked
        })
    
    # Statistiques globales
    present_count = len([e for e in employee_stats if e['is_present']])
    total_hours = sum(e['hours_worked'] for e in employee_stats)
    
    return jsonify({
        'success': True,
        'data': {
            'stats': {
                'total_employees': len(active_employees),
                'present_today': present_count,
                'absent_today': len(active_employees) - present_count,
                'total_hours_worked': total_hours,
                'attendance_rate': (present_count / len(active_employees) * 100) if active_employees else 0
            },
            'employees': employee_stats
        }
    })

# ==========================================
# DASHBOARD MENSUEL - ANALYSE STRATÉGIQUE
# ==========================================

@dashboard_api.route('/monthly/overview', methods=['GET'])
@login_required
@admin_required
def monthly_overview():
    """Vue d'ensemble mensuelle - KPIs stratégiques
    
    PHASE 1 - Intégration app/reports : Utilise MonthlyProfitLossService (remplacement complet)
    """
    
    # Paramètres de date
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # PHASE 1 - Utiliser MonthlyProfitLossService pour revenue, expenses, net_profit
    try:
        report_data = MonthlyProfitLossService.generate(year, month)
        logger.info("[REPORT] Data loaded from MonthlyProfitLossService")
        
        # Extraction des KPIs depuis le rapport
        monthly_revenue = report_data['revenue']
        monthly_expenses = report_data['expenses']
        net_profit = report_data['net_income']
        profit_margin = report_data['net_margin']
        
        # Métadonnées IA disponibles
        growth_rate = report_data.get('growth_rate', 0)
        trend_direction = report_data.get('trend_direction', 'stable')
        variance = report_data.get('variance', 0)
        benchmark = report_data.get('benchmark', {})
        
    except Exception as e:
        logger.error(f"[REPORT] Error loading MonthlyProfitLossService: {e}")
        # Fallback sur calcul direct si erreur
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        monthly_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime,
                Order.status.in_(['delivered', 'completed'])
            )
        ).scalar() or 0
        
        monthly_expenses = 0
        try:
            expense_accounts = Account.query.filter(Account.code.startswith('6')).all()
            for account in expense_accounts:
                expense_amount = db.session.query(func.sum(JournalEntryLine.debit_amount))\
                    .join(JournalEntry)\
                    .filter(JournalEntryLine.account_id == account.id)\
                    .filter(JournalEntry.entry_date >= start_date)\
                    .filter(JournalEntry.entry_date <= end_date)\
                    .scalar() or 0
                monthly_expenses += float(expense_amount)
        except:
            pass
        
        net_profit = float(monthly_revenue) - monthly_expenses
        profit_margin = (net_profit / float(monthly_revenue) * 100) if monthly_revenue > 0 else 0
        growth_rate = 0
        trend_direction = 'stable'
        variance = 0
        benchmark = {}
    
    # Nombre de commandes (non inclus dans MonthlyProfitLossService)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    monthly_orders = Order.query.filter(
        and_(
            Order.created_at >= start_datetime,
            Order.created_at <= end_datetime
        )
    ).count()
    
    # Valeur stock fin de mois
    stock_value = db.session.query(func.sum(Product.total_stock_value)).scalar() or 0
    
    # Employés actifs
    active_employees = Employee.query.filter_by(is_active=True).count()
    
    # Masse salariale
    total_salary_cost = db.session.query(func.sum(Employee.salaire_fixe + Employee.prime))\
        .filter(Employee.is_active == True)\
        .scalar() or 0
    
    return jsonify({
        'success': True,
        'data': {
            'period': {
                'year': year,
                'month': month,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'kpis': {
                'monthly_revenue': float(monthly_revenue),
                'monthly_orders': monthly_orders,
                'monthly_expenses': float(monthly_expenses),
                'net_profit': float(net_profit),
                'profit_margin': float(profit_margin),
                'stock_value': float(stock_value),
                'active_employees': active_employees,
                'total_salary_cost': float(total_salary_cost),
                'revenue_per_employee': float(monthly_revenue) / active_employees if active_employees > 0 else 0,
                # Métadonnées IA (Phase 1)
                'growth_rate': growth_rate,
                'trend_direction': trend_direction,
                'variance': variance,
                'benchmark': benchmark
            }
        }
    })

@dashboard_api.route('/monthly/revenue-trend', methods=['GET'])
@login_required
@admin_required
def monthly_revenue_trend():
    """Tendance des revenus sur 12 mois"""
    
    # Paramètres
    months = request.args.get('months', type=int, default=12)
    
    trend_data = []
    current_date = datetime.now()
    
    for i in range(months):
        # Calculer la date
        if current_date.month - i <= 0:
            year = current_date.year - 1
            month = 12 + (current_date.month - i)
        else:
            year = current_date.year
            month = current_date.month - i
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # CA du mois
        monthly_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime,
                Order.status.in_(['delivered', 'completed'])
            )
        ).scalar() or 0
        
        # Nombre de commandes
        monthly_orders = Order.query.filter(
            and_(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime
            )
        ).count()
        
        trend_data.append({
            'period': f"{year}-{month:02d}",
            'year': year,
            'month': month,
            'revenue': float(monthly_revenue),
            'orders': monthly_orders,
            'avg_order_value': float(monthly_revenue) / monthly_orders if monthly_orders > 0 else 0
        })
    
    return jsonify({
        'success': True,
        'data': list(reversed(trend_data))  # Plus ancien au plus récent
    })

@dashboard_api.route('/monthly/product-performance', methods=['GET'])
@login_required
@admin_required
def monthly_product_performance():
    """Performance des produits - Top vendeurs
    
    PHASE 1 - Intégration app/reports : Utilise WeeklyProductPerformanceService avec dates mensuelles
    """
    
    # Paramètres
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    limit = request.args.get('limit', type=int, default=10)
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # PHASE 1 - Utiliser WeeklyProductPerformanceService avec dates mensuelles
    try:
        report_data = WeeklyProductPerformanceService.generate(start_date, end_date)
        logger.info("[REPORT] Data loaded from WeeklyProductPerformanceService")
        
        # Extraction des données depuis le rapport
        performance_data = report_data.get('performance_data', [])
        
        # Tri par revenue (top_by_revenue)
        top_by_revenue = sorted(performance_data, key=lambda x: x.get('revenue', 0), reverse=True)[:limit]
        
        # Tri par quantité (top_by_quantity)
        top_by_quantity = sorted(performance_data, key=lambda x: x.get('units_sold', 0), reverse=True)[:limit]
        
        # Format des données (pour compatibilité front-end)
        def format_product_data(product_data):
            return {
                'id': product_data.get('product_id'),
                'name': product_data.get('product_name'),
                'category': product_data.get('category', 'N/A'),
                'total_quantity': float(product_data.get('units_sold', 0)),
                'total_revenue': float(product_data.get('revenue', 0)),
                'avg_price': float(product_data.get('revenue', 0)) / float(product_data.get('units_sold', 1)) if product_data.get('units_sold', 0) > 0 else 0
            }
        
        return jsonify({
            'success': True,
            'data': {
                'top_by_revenue': [format_product_data(p) for p in top_by_revenue],
                'top_by_quantity': [format_product_data(p) for p in top_by_quantity]
            }
        })
        
    except Exception as e:
        logger.error(f"[REPORT] Error loading WeeklyProductPerformanceService: {e}")
        # Fallback sur calcul direct si erreur
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Top produits par CA
        top_products = db.session.query(
            Product.id,
            Product.name,
            Category.name.label('category_name'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
        ).join(OrderItem).join(Order).join(Category, isouter=True).filter(
            and_(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime,
                Order.status.in_(['delivered', 'completed'])
            )
        ).group_by(Product.id, Product.name, Category.name)\
         .order_by(desc(func.sum(OrderItem.quantity * OrderItem.unit_price)))\
         .limit(limit).all()
        
        # Top produits par quantité
        top_quantity = db.session.query(
            Product.id,
            Product.name,
            Category.name.label('category_name'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
        ).join(OrderItem).join(Order).join(Category, isouter=True).filter(
            and_(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime,
                Order.status.in_(['delivered', 'completed'])
            )
        ).group_by(Product.id, Product.name, Category.name)\
         .order_by(desc(func.sum(OrderItem.quantity)))\
         .limit(limit).all()
        
        def format_product_data(product_data):
            return {
                'id': product_data.id,
                'name': product_data.name,
                'category': product_data.category_name or 'N/A',
                'total_quantity': float(product_data.total_quantity or 0),
                'total_revenue': float(product_data.total_revenue or 0),
                'avg_price': float(product_data.total_revenue or 0) / float(product_data.total_quantity or 1)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'top_by_revenue': [format_product_data(p) for p in top_products],
                'top_by_quantity': [format_product_data(p) for p in top_quantity]
            }
        })

@dashboard_api.route('/monthly/employee-performance', methods=['GET'])
@login_required
@admin_required
def monthly_employee_performance():
    """Performance des employés - Productivité"""
    
    # Paramètres
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Employés actifs
    active_employees = Employee.query.filter_by(is_active=True).all()
    
    employee_performance = []
    
    for emp in active_employees:
        # CA généré par l'employé
        employee_revenue = db.session.query(func.sum(Order.total_amount))\
            .join(Order.produced_by)\
            .filter(
                and_(
                    Employee.id == emp.id,
                    Order.created_at >= start_datetime,
                    Order.created_at <= end_datetime,
                    Order.status.in_(['completed', 'delivered'])
                )
            ).scalar() or 0
        
        # Nombre de commandes produites
        employee_orders = Order.query.join(Order.produced_by).filter(
            and_(
                Employee.id == emp.id,
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime
            )
        ).count()
        
        # Problèmes de qualité
        quality_issues = OrderIssue.query.filter(
            and_(
                OrderIssue.employee_id == emp.id,
                OrderIssue.detected_at >= start_datetime,
                OrderIssue.detected_at <= end_datetime
            )
        ).count()
        
        # Coût employé
        employee_cost = emp.get_monthly_salary_cost(year, month)
        
        # ROI employé
        roi = (float(employee_revenue) / employee_cost * 100) if employee_cost > 0 else 0
        
        # Taux d'erreur
        error_rate = (quality_issues / employee_orders * 100) if employee_orders > 0 else 0
        
        employee_performance.append({
            'id': emp.id,
            'name': emp.name,
            'role': emp.get_role_display(),
            'revenue_generated': float(employee_revenue),
            'orders_produced': employee_orders,
            'quality_issues': quality_issues,
            'error_rate': error_rate,
            'monthly_cost': employee_cost,
            'roi': roi,
            'avg_order_value': float(employee_revenue) / employee_orders if employee_orders > 0 else 0
        })
    
    # Trier par ROI
    employee_performance.sort(key=lambda x: x['roi'], reverse=True)
    
    return jsonify({
        'success': True,
        'data': {
            'employees': employee_performance,
            'summary': {
                'total_employees': len(active_employees),
                'total_revenue': sum(e['revenue_generated'] for e in employee_performance),
                'total_cost': sum(e['monthly_cost'] for e in employee_performance),
                'avg_roi': sum(e['roi'] for e in employee_performance) / len(employee_performance) if employee_performance else 0,
                'avg_error_rate': sum(e['error_rate'] for e in employee_performance) / len(employee_performance) if employee_performance else 0
            }
        }
    })

# ==========================================
# ENDPOINTS UTILITAIRES
# ==========================================

@dashboard_api.route('/refresh', methods=['POST'])
@login_required
@admin_required
def refresh_dashboard():
    """Forcer le rafraîchissement des données"""
    # Ici on pourrait ajouter du cache invalidation si nécessaire
    return jsonify({
        'success': True,
        'message': 'Dashboard refreshed successfully',
        'timestamp': datetime.utcnow().isoformat()
    })

# ==========================================
# ENDPOINTS IA (PHASE 1)
# ==========================================

@dashboard_api.route('/daily/ai-insights', methods=['GET'])
@login_required
@admin_required
def daily_ai_insights():
    """Analyses IA pour le dashboard journalier (multi-rapports)
    
    PHASE 1 - Intégration app/ai : Analyse LLM des rapports quotidiens
    """
    try:
        ai_manager = AIManager()
        logger.info("[AI] Requesting daily AI insights")
        
        # Analyse multi-rapports (ventes, stock, production)
        insights = {
            'sales': None,
            'stock': None,
            'production': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Analyse ventes
        try:
            sales_analysis = ai_manager.analyze_reports('daily_sales', prompt_type='daily_analysis')
            insights['sales'] = sales_analysis
            logger.info("[AI] Sales analysis completed")
        except Exception as e:
            logger.warning(f"[AI] Sales analysis failed: {e}")
            insights['sales'] = {
                'status': 'fallback',
                'message': 'Analyse IA indisponible pour les ventes (mode hors ligne)',
                'analysis': 'Consultez les rapports standards pour plus de détails.'
            }
        
        # Analyse stock (détection anomalies)
        try:
            stock_analysis = ai_manager.analyze_reports('daily_stock_alerts', prompt_type='anomaly_detection')
            insights['stock'] = stock_analysis
            logger.info("[AI] Stock analysis completed")
        except Exception as e:
            logger.warning(f"[AI] Stock analysis failed: {e}")
            insights['stock'] = {
                'status': 'fallback',
                'message': 'Analyse IA indisponible pour le stock (mode hors ligne)',
                'analysis': 'Consultez les alertes stock standards.'
            }
        
        # Analyse production
        try:
            production_analysis = ai_manager.analyze_reports('daily_production', prompt_type='daily_analysis')
            insights['production'] = production_analysis
            logger.info("[AI] Production analysis completed")
        except Exception as e:
            logger.warning(f"[AI] Production analysis failed: {e}")
            insights['production'] = {
                'status': 'fallback',
                'message': 'Analyse IA indisponible pour la production (mode hors ligne)',
                'analysis': 'Consultez les rapports de production standards.'
            }
        
        return jsonify({
            'success': True,
            'data': insights,
            'source': 'ai_manager',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[AI] Error in daily_ai_insights: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la génération des insights IA: {str(e)}',
            'fallback': 'Utilisez les rapports standards en attendant.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@dashboard_api.route('/daily/sales-forecast', methods=['GET'])
@login_required
@admin_required
def daily_sales_forecast():
    """Prévisions Prophet pour les ventes (7 jours)
    
    PHASE 1 - Intégration app/ai : Prédictions Prophet
    """
    try:
        days = request.args.get('days', type=int, default=7)
        ai_manager = AIManager()
        logger.info(f"[AI] Requesting sales forecast for {days} days")
        
        # Génération des prévisions
        forecast = ai_manager.generate_forecasts('daily_sales', days=days)
        logger.info("[AI] Sales forecast completed")
        
        return jsonify({
            'success': True,
            'data': forecast,
            'source': 'prophet',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[AI] Error in daily_sales_forecast: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la génération des prévisions: {str(e)}',
            'fallback': 'Les prévisions sont temporairement indisponibles.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@dashboard_api.route('/daily/anomalies', methods=['GET'])
@login_required
@admin_required
def daily_anomalies():
    """Détection d'anomalies IA sur les ventes du jour
    
    PHASE 1 - Intégration app/ai : Détection anomalies avec z-score + LLM
    """
    try:
        ai_manager = AIManager()
        logger.info("[AI] Requesting anomaly detection")
        
        # Détection d'anomalies
        anomalies = ai_manager.detect_anomalies('daily_sales')
        logger.info("[AI] Anomaly detection completed")
        
        return jsonify({
            'success': True,
            'data': anomalies,
            'source': 'ai_manager',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[AI] Error in daily_anomalies: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la détection d\'anomalies: {str(e)}',
            'fallback': 'La détection d\'anomalies est temporairement indisponible.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@dashboard_api.route('/monthly/ai-summary', methods=['GET'])
@login_required
@admin_required
def monthly_ai_summary():
    """Résumé stratégique IA mensuel (analyse LLM complète)
    
    PHASE 1 - Intégration app/ai : Résumé stratégique mensuel avec recommandations
    """
    try:
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        reference_date = date(year, month, 1)
        
        ai_manager = AIManager()
        logger.info(f"[AI] Requesting monthly AI summary for {year}-{month:02d}")
        
        # Génération du résumé stratégique
        summary = ai_manager.get_ai_summary('monthly', reference_date=reference_date)
        logger.info("[AI] Monthly AI summary completed")
        
        return jsonify({
            'success': True,
            'data': summary,
            'source': 'ai_manager',
            'period': {
                'year': year,
                'month': month
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[AI] Error in monthly_ai_summary: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la génération du résumé IA: {str(e)}',
            'fallback': 'Le résumé stratégique est temporairement indisponible.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@dashboard_api.route('/export/monthly', methods=['GET'])
@login_required
@admin_required
def export_monthly_dashboard():
    """Export PDF du dashboard mensuel"""
    try:
        from weasyprint import HTML
        from flask import render_template_string
        import tempfile
        import os
        
        # Récupérer les paramètres
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Récupérer les données du dashboard
        overview_data = get_monthly_overview_data(year, month)
        revenue_data = get_monthly_revenue_trend_data()
        product_data = get_monthly_product_performance_data(year, month)
        employee_data = get_monthly_employee_performance_data(year, month)
        
        # Template HTML pour le PDF
        pdf_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Dashboard Mensuel - {{ month }}/{{ year }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .section { margin-bottom: 25px; }
                .section h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 15px 0; }
                .kpi-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }
                .kpi-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
                .kpi-label { color: #7f8c8d; font-size: 14px; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #3498db; color: white; }
                .positive { color: #27ae60; }
                .negative { color: #e74c3c; }
                .footer { margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Dashboard Mensuel - Fée Maison</h1>
                <h2>{{ month }}/{{ year }}</h2>
                <p>Généré le {{ generation_date }}</p>
            </div>
            
            <div class="section">
                <h2>📊 Vue d'Ensemble</h2>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{{ "{:,.0f}".format(overview.kpis.monthly_revenue) }} DA</div>
                        <div class="kpi-label">Chiffre d'Affaires</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{{ "{:,.0f}".format(overview.kpis.net_profit) }} DA</div>
                        <div class="kpi-label">Bénéfice Net</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{{ overview.kpis.profit_margin|round(1) }}%</div>
                        <div class="kpi-label">Marge Bénéficiaire</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{{ overview.kpis.monthly_orders }}</div>
                        <div class="kpi-label">Commandes</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🏆 Top Produits</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Produit</th>
                            <th>Quantité Vendue</th>
                            <th>CA Généré</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for product in product_data.top_by_revenue[:5] %}
                        <tr>
                            <td>{{ product.name }}</td>
                            <td>{{ product.quantity_sold }}</td>
                            <td>{{ "{:,.0f}".format(product.revenue) }} DA</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>👥 Performance Employés</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Employé</th>
                            <th>Rôle</th>
                            <th>Score</th>
                            <th>ROI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in employee_data.employees %}
                        <tr>
                            <td>{{ emp.name }}</td>
                            <td>{{ emp.role }}</td>
                            <td>{{ emp.score }}</td>
                            <td>{{ emp.roi|round(1) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>ERP Fée Maison - Rapport généré automatiquement</p>
            </div>
        </body>
        </html>
        """
        
        # Rendu du template
        html_content = render_template_string(pdf_template,
            month=month, year=year,
            generation_date=datetime.now().strftime("%d/%m/%Y à %H:%M"),
            overview=overview_data,
            product_data=product_data,
            employee_data=employee_data
        )
        
        # Génération du PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Création du fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf)
            tmp_file_path = tmp_file.name
        
        # Envoi du fichier
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=f'dashboard_mensuel_{year}_{month:02d}.pdf',
            mimetype='application/pdf'
        )
        
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'WeasyPrint non installé. Installez-le avec: pip install weasyprint'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la génération du PDF: {str(e)}'
        }), 500 