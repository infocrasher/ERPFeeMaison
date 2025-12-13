from datetime import date, datetime, timedelta
import math
from statistics import mean

from flask import current_app, render_template, request
from flask_login import login_required
from sqlalchemy import func, desc, case

from extensions import db
from models import Order, OrderItem, Product
from app.reports.services import DailySalesReportService, ReportService # Modified import
from app.reports.kpi_service import RealKpiService
from app.sales.models import CashRegisterSession, CashMovement
from app.purchases.models import Purchase
from app.stock.models import StockMovement
from app.reports.services import (
    DailySalesReportService,
    ProductionReportService,
    StockAlertReportService,
    PrimeCostReportService,
    _compute_revenue
)
from app.employees.models import Employee, AttendanceSummary
from decorators import admin_required
from app.orders.dashboard_routes import dashboard_bp
# ⏸️ AI désactivé temporairement pour performance
# from app.ai import AIManager
import logging

logger = logging.getLogger(__name__)


@dashboard_bp.route('/', methods=['GET'])
@login_required
@admin_required
def unified_dashboard():
    """Dashboard global unifié."""
    date_str = request.args.get('date')
    period = request.args.get('period', 'day')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except (TypeError, ValueError):
        target_date = date.today()

    dashboard_context = build_dashboard_context(target_date, period)
    
    # 🆕 AJOUT : KPIs Réels (Pilotage Financier)
    dashboard_context['real_kpis'] = RealKpiService.get_daily_kpis(target_date)
    
    # Empêcher la mise en cache pour forcer le recalcul
    response = render_template('dashboard.html', data=dashboard_context)
    from flask import make_response
    response = make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


def build_dashboard_context(target_date, period):
    today = target_date
    now = datetime.utcnow()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    trend_days = 30 if period == 'month' else 7

    sales_report = load_daily_sales_report(today)
    production_report = load_production_report(today)
    stock_report = load_stock_report()
    prime_cost_report = load_prime_cost_report(today)

    real_kpis = RealKpiService.get_daily_kpis(today)

    overview = build_overview_block(sales_report, today)
    stock_summary = build_stock_block(stock_report, today, week_start, now, trend_days)
    production_block, ingredient_summary = build_production_block(production_report, today, now)
    sales_block = build_sales_block(sales_report, today, week_start, week_end, month_start, month_end, period)
    purchases_block = build_purchase_block(ingredient_summary, today)
    cash_block = build_cash_block(today)
    attendance_block = build_attendance_block(today)
    overdue_orders = build_overdue_orders(today, now)
    alerts_block = build_alerts_block(stock_summary, production_block, overdue_orders)
    metric_cards = build_metric_cards(
        overview,
        prime_cost_report,
        sales_block,
        stock_summary,
        cash_block,
        attendance_block,
        alerts_block,
        real_kpis
    )
    # ⏸️ AI désactivé temporairement pour performance
    # ai_insights = build_ai_insights_block(today, sales_report, stock_summary, production_block)
    ai_insights = {'available': False, 'sales': None, 'stock': None, 'production': None, 'forecast': None}
    
    insights_block = build_insights_block(
        sales_report,
        stock_summary,
        production_block,
        cash_block,
        prime_cost_report,
        alerts_block,
        ai_insights
    )
    tables_block = build_tables_block(stock_summary, sales_block, overdue_orders, purchases_block)

    chart_payload = build_chart_payload(
        production_block,
        stock_summary,
        sales_block,
        attendance_block,
        cash_block,
        trend_days,
        today
    )

    return {
        'generated_at': now,
        'selected_date': today,
        'period': period,
        'location': 'Fée Maison - Boutique Centrale',
        'overview': overview,
        'metric_cards': metric_cards,
        'production': production_block,
        'stock': stock_summary,
        'sales': sales_block,
        'purchases': purchases_block,
        'cash': cash_block,
        'hr': attendance_block,
        'alerts': alerts_block,
        'insights': insights_block,
        'tables': tables_block,
        'chart_payload': chart_payload
    }


def load_daily_sales_report(report_date):
    try:
        report = DailySalesReportService.generate(report_date)
    except Exception as exc:
        current_app.logger.exception("[Dashboard] DailySalesReportService failed: %s", exc)
        report = {
            'total_revenue': 0.0,
            'total_transactions': 0,
            'average_basket': 0.0,
            'top_products': [],
            'top_products_json': [],
            'sales_by_category': [],
            'sales_by_category_json': [],
            'hourly_sales': [],
            'hourly_sales_json': [],
            'growth_rate': 0.0,
            'trend_direction': 'stable',
            'benchmark': {},
        }
    return report


def load_production_report(report_date):
    try:
        report = ProductionReportService.generate(report_date)
    except Exception as exc:
        current_app.logger.exception("[Dashboard] ProductionReportService failed: %s", exc)
        report = {
            'total_units': 0.0,
            'total_orders': 0,
            'production_by_product': [],
            'production_by_product_json': [],
            'efficiency_rate': 0.0,
            'production_orders': [],
            'growth_rate': 0.0,
            'trend_direction': 'stable',
        }
    return report


def load_stock_report():
    try:
        report = StockAlertReportService.generate()
    except Exception as exc:
        current_app.logger.exception("[Dashboard] StockAlertReportService failed: %s", exc)
        report = {
            'low_stock_products': [],
            'out_of_stock': [],
            'benchmark': {},
        }
    return report


def load_prime_cost_report(report_date):
    try:
        report = PrimeCostReportService.generate(report_date)
    except Exception as exc:
        current_app.logger.exception("[Dashboard] PrimeCostReportService failed: %s", exc)
        report = {
            'date': report_date,
            'revenue': 0.0,
            'cogs': 0.0,
            'labor_cost': 0.0,
            'prime_cost': 0.0,
            'prime_cost_percentage': 0.0,
            'gross_margin': 0.0,
            'gross_margin_percentage': 0.0
        }
    return report


def build_overview_block(sales_report, today):
    # Utiliser la fonction utilitaire partagée pour garantir la cohérence avec stock overview
    from app.stock.utils import calculate_total_stock_value
    stock_value = calculate_total_stock_value()
    return {
        'daily_revenue': float(sales_report.get('total_revenue', 0.0)),
        'daily_orders': int(sales_report.get('total_transactions', 0)),
        'avg_basket': float(sales_report.get('average_basket', 0.0)),
        'stock_value': stock_value,
        'today': today.strftime('%d/%m/%Y')
    }


def build_production_block(production_report, today, now):
    production_orders = Order.query.filter(
        Order.status.in_(['pending', 'in_production']),
        func.date(Order.due_date) == today
    ).order_by(Order.due_date.asc()).all()

    orders_by_priority = []
    urgent_orders = 0
    overdue_orders = 0
    total_units_required = 0

    for order in production_orders:
        order_items = order.items.all() if hasattr(order.items, 'all') else (order.items or [])
        time_diff_hours = (order.due_date - now).total_seconds() / 3600 if order.due_date else 0
        if time_diff_hours < 0:
            priority = 'overdue'
            overdue_orders += 1
        elif time_diff_hours <= 2:
            priority = 'urgent'
            urgent_orders += 1
        else:
            priority = 'normal'
        units = sum(float(item.quantity) for item in order_items)
        total_units_required += units

        quantity_total = units
        if quantity_total.is_integer():
            quantity_display = f"{int(quantity_total)} pcs"
        else:
            quantity_display = f"{quantity_total:.1f} pcs"

        primary_product = None
        if order_items:
            first_item = order_items[0]
            if first_item.product:
                primary_product = first_item.product.name
        if not primary_product:
            primary_product = order.customer_name or f"Commande #{order.id}"

        time_label = "Sans horaire"
        if order.due_date:
            minutes_remaining = int((order.due_date - now).total_seconds() // 60)
            if minutes_remaining < 0:
                time_label = f"Retard {abs(minutes_remaining)} min"
            else:
                hours = minutes_remaining // 60
                mins = minutes_remaining % 60
                if hours > 0:
                    time_label = f"Dans {hours}h{mins:02d}"
                else:
                    time_label = f"Dans {mins} min"
        else:
            minutes_remaining = 0

        orders_by_priority.append({
            'id': order.id,
            'customer': order.customer_name or 'Sans nom',
            'due_date': order.due_date.strftime('%H:%M') if order.due_date else 'N/A',
            'items_count': order.get_items_count(),
            'priority': priority,
            'amount': float(order.total_amount or 0),
            'primary_product': primary_product,
            'quantity_display': quantity_display,
            'time_label': time_label,
            'time_minutes': minutes_remaining,
        })

    ingredient_summary = compute_ingredient_requirements(production_orders)
    total_ingredients = len(ingredient_summary)
    if total_ingredients:
        available_count = len([i for i in ingredient_summary if i['stock'] >= i['needed_qty']])
        availability_percent = round(available_count / total_ingredients * 100, 1)
    else:
        availability_percent = 100.0

    total_needed_quantity = sum(item['needed_qty'] for item in ingredient_summary)
    total_missing_quantity = sum(item['missing'] for item in ingredient_summary)

    production_block = {
        'total_units': float(production_report.get('total_units', 0.0)) or total_units_required,
        'total_orders': len(production_orders),
        'urgent_orders': urgent_orders,
        'overdue_orders': overdue_orders,
        'orders': orders_by_priority,
        'ingredients': ingredient_summary,
        'availability_percent': availability_percent,
        'missing_alerts': [i for i in ingredient_summary if i['missing'] > 0][:5],
        'bar': build_production_bar_data(production_report),
        'donut': {
            'available': max(total_needed_quantity - total_missing_quantity, 0),
            'missing': total_missing_quantity
        }
    }
    return production_block, ingredient_summary


def build_production_bar_data(production_report):
    rows = production_report.get('production_by_product_json') or []
    labels = [row['name'] for row in rows]
    data = [row['quantity_produced'] for row in rows]
    return {'labels': labels, 'data': data}


def compute_ingredient_requirements(orders):
    needs = {}
    for order in orders:
        for item in order.items:
            product = item.product
            if not product or not product.recipe_definition:
                continue
            recipe = product.recipe_definition
            for ingredient_in_recipe in recipe.ingredients:
                ingredient_product = ingredient_in_recipe.product
                if not ingredient_product:
                    continue
                qty_per_unit = float(ingredient_in_recipe.quantity_needed) / float(recipe.yield_quantity or 1)
                needed_qty = qty_per_unit * float(item.quantity)
                entry = needs.setdefault(ingredient_product.id, {
                    'id': ingredient_product.id,
                    'name': ingredient_product.name,
                    'unit': ingredient_in_recipe.unit or ingredient_product.unit,
                    'stock': float(ingredient_product.stock_ingredients_magasin or 0),
                    'min_stock': float(ingredient_product.seuil_min_ingredients_magasin or 0),
                    'needed_qty': 0.0,
                    'deadline': order.due_date,
                    'orders': set()
                })
                entry['needed_qty'] += needed_qty
                entry['stock'] = float(ingredient_product.stock_ingredients_magasin or 0)
                if order.due_date and entry['deadline']:
                    entry['deadline'] = min(entry['deadline'], order.due_date)
                elif order.due_date and not entry['deadline']:
                    entry['deadline'] = order.due_date
                entry['orders'].add(order.id)

    summary = []
    for entry in needs.values():
        needed = entry['needed_qty']
        stock = entry['stock']
        missing = max(0.0, needed - stock)
        summary.append({
            'id': entry['id'],
            'name': entry['name'],
            'unit': entry['unit'],
            'stock': round(stock, 2),
            'needed_qty': round(needed, 2),
            'missing': round(missing, 2),
            'orders_count': len(entry['orders']),
            'deadline': entry['deadline'],
            'purchase_qty': smart_round(missing),
        })
    summary.sort(key=lambda x: x['missing'], reverse=True)
    return summary


def smart_round(quantity):
    if quantity <= 0:
        return 0
    if quantity <= 100:
        step = 50
    elif quantity <= 500:
        step = 100
    elif quantity <= 1000:
        step = 200
    else:
        step = 500
    return math.ceil(quantity / step) * step


def build_stock_block(stock_report, today, week_start, now, trend_days):
    low_stock = stock_report.get('low_stock_products', [])
    out_of_stock = stock_report.get('out_of_stock', [])

    def format_product(prod):
        if isinstance(prod, dict):
            return prod
        return {
            'id': prod.id,
            'name': prod.name,
            'stock_magasin': float(prod.stock_ingredients_magasin or 0),
            'stock_local': float(prod.stock_ingredients_local or 0),
            'stock_comptoir': float(prod.stock_comptoir or 0),
            'min_magasin': float(prod.seuil_min_ingredients_magasin or 0),
            'category': prod.category.name if prod.category else 'N/A'
        }

    stock_variation = compute_stock_variation(trend_days)
    heatmap = compute_stock_heatmap(7)
    stock_movements = compute_stock_movements(today)

    # Calculer les achats du jour : utiliser payment_date si payé, sinon created_at
    # Un achat peut être créé un jour et payé un autre jour
    purchase_cost_today = float(
        db.session.query(func.sum(Purchase.total_amount))
        .filter(
            db.or_(
                # Achats payés aujourd'hui
                db.and_(
                    Purchase.is_paid == True,
                    Purchase.payment_date == today
                ),
                # Achats créés aujourd'hui mais non payés
                db.and_(
                    db.or_(Purchase.is_paid == False, Purchase.is_paid.is_(None)),
                    func.date(Purchase.created_at) == today
                )
            )
        )
        .scalar() or 0
    )
    purchase_cost_week = float(
        db.session.query(func.sum(Purchase.total_amount))
        .filter(func.date(Purchase.created_at).between(week_start, today))
        .scalar() or 0
    )

    consumption_week = compute_consumption_value(week_start, now)
    ratio = round((consumption_week / purchase_cost_week) * 100, 1) if purchase_cost_week > 0 else None

    # Utiliser la fonction utilitaire partagée pour garantir la cohérence avec stock overview
    from app.stock.utils import calculate_total_stock_value
    total_value = calculate_total_stock_value()

    return {
        'total_value': total_value,
        'out_of_stock': [format_product(p) for p in out_of_stock],
        'low_stock': [format_product(p) for p in low_stock],
        'variation': stock_variation,
        'heatmap': heatmap,
        'purchase_today': purchase_cost_today,
        'purchase_week': purchase_cost_week,
        'consumption_ratio': ratio,
        'movements': stock_movements,
    }


def compute_stock_variation(days):
    start = datetime.utcnow().date() - timedelta(days=days - 1)
    results = []
    for i in range(days):
        day = start + timedelta(days=i)
        total_value = db.session.query(
            func.sum(StockMovement.quantity * func.coalesce(StockMovement.unit_cost, 0))
        ).filter(func.date(StockMovement.created_at) == day).scalar() or 0
        results.append({
            'label': day.strftime('%d/%m'),
            'value': float(total_value)
        })
    return results


def compute_stock_heatmap(days):
    start_dt = datetime.utcnow() - timedelta(days=days)
    rows = db.session.query(
        Product.name,
        func.sum(func.abs(StockMovement.quantity)).label('qty')
    ).join(Product, Product.id == StockMovement.product_id).filter(
        StockMovement.created_at >= start_dt,
        StockMovement.quantity < 0,
        Product.product_type == 'ingredient'
    ).group_by(Product.id, Product.name).order_by(desc('qty')).limit(6).all()
    return [{'label': row.name, 'value': float(row.qty or 0)} for row in rows]


def compute_stock_movements(target_date):
    incoming = db.session.query(
        func.sum(StockMovement.quantity * func.coalesce(StockMovement.unit_cost, 0))
    ).filter(
        func.date(StockMovement.created_at) == target_date,
        StockMovement.quantity > 0
    ).scalar() or 0

    outgoing = db.session.query(
        func.sum(func.abs(StockMovement.quantity) * func.coalesce(StockMovement.unit_cost, 0))
    ).filter(
        func.date(StockMovement.created_at) == target_date,
        StockMovement.quantity < 0
    ).scalar() or 0

    return {
        'incoming': float(incoming),
        'outgoing': float(outgoing),
        'net': float(incoming) - float(outgoing)
    }


def compute_consumption_value(start_date, end_datetime):
    start_dt = datetime.combine(start_date, datetime.min.time())
    rows = db.session.query(
        func.sum(func.abs(StockMovement.quantity * func.coalesce(StockMovement.unit_cost, 0)))
    ).filter(
        StockMovement.created_at >= start_dt,
        StockMovement.created_at <= end_datetime,
        StockMovement.quantity < 0
    ).scalar() or 0
    return float(rows)


def compute_order_type_breakdown(target_date):
    channel_case = case(
        (Order.delivery_option == 'delivery', 'delivery'),
        else_='pickup'
    )

    channel_case = case(
        (Order.order_type == 'in_store', 'store'),
        (Order.order_type == 'counter_production_request', 'production'),
        else_=channel_case
    )

    rows = db.session.query(
        channel_case.label('channel'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('revenue')
    ).filter(
        func.date(Order.created_at) == target_date,
        Order.status != 'cancelled'
    ).group_by('channel').all()

    label_map = {
        'delivery': 'Livraison',
        'pickup': 'Emporté',
        'store': 'Magasin',
        'production': 'Production'
    }

    return [
        {
            'channel': row.channel,
            'label': label_map.get(row.channel, row.channel.title()),
            'count': int(row.count or 0),
            'revenue': float(row.revenue or 0)
        } for row in rows
    ]


def build_sales_block(sales_report, today, week_start, week_end, month_start, month_end, period):
    daily_revenue = float(sales_report.get('total_revenue', 0.0))
    weekly_revenue = float(_compute_revenue(start_date=week_start, end_date=week_end))
    monthly_revenue = float(_compute_revenue(start_date=month_start, end_date=month_end))

    weekly_orders = Order.query.filter(
        func.date(Order.created_at).between(week_start, week_end)
    ).count()
    monthly_orders = Order.query.filter(
        func.date(Order.created_at).between(month_start, month_end)
    ).count()

    daily_orders = Order.query.filter(func.date(Order.created_at) == today).all()
    delivered_orders = [o for o in daily_orders if o.status in ['delivered', 'completed']]
    on_time_deliveries = [
        o for o in delivered_orders
        if o.due_date and o.due_date >= datetime.utcnow()
    ]
    on_time_rate = round(len(on_time_deliveries) / len(delivered_orders) * 100, 1) if delivered_orders else 100.0

    payment_modes = []
    payment_modes_json = []
    if hasattr(Order, 'payment_method'):
        payment_rows = db.session.query(
            Order.payment_method,
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) == today
        ).group_by(Order.payment_method).all()
        payment_modes = [{'label': row.payment_method or 'indéfini', 'value': int(row.count)} for row in payment_rows]
        payment_modes_json = payment_modes
    else:
        payment_modes = [{'label': 'Indéfini', 'value': len(daily_orders)}] if daily_orders else []
        payment_modes_json = payment_modes

    top_products = sales_report.get('top_products') or []
    category_breakdown = sales_report.get('sales_by_category_json', [])
    hourly_sales = sales_report.get('hourly_sales_json', [])
    order_type_breakdown = compute_order_type_breakdown(today)

    return {
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'daily_orders': len(daily_orders),
        'weekly_orders': weekly_orders,
        'monthly_orders': monthly_orders,
        'average_basket': float(sales_report.get('average_basket', 0.0)),
        'on_time_rate': on_time_rate,
        'top_products': top_products,
        'payment_modes': payment_modes,
        'top_products_json': sales_report.get('top_products_json', []),
        'payment_modes_json': payment_modes_json,
        'category_breakdown': category_breakdown,
        'hourly_sales': hourly_sales,
        'order_types': order_type_breakdown,
        'growth_rate': sales_report.get('growth_rate', 0.0),
        'trend_direction': sales_report.get('trend_direction', 'stable'),
        'period': period
    }


def build_purchase_block(ingredient_summary, today):
    pending = []
    for item in ingredient_summary:
        if item['purchase_qty'] > 0:
            pending.append({
                'id': item['id'],
                'name': item['name'],
                'stock': item['stock'],
                'needed': item['needed_qty'],
                'missing': item['missing'],
                'unit': item['unit'],
                'to_buy': item['purchase_qty'],
                'deadline': item['deadline'].strftime('%H:%M') if item['deadline'] else 'ASAP'
            })
    pending.sort(key=lambda x: x['missing'], reverse=True)

    return {
        'pending': pending,
        'completed': [],
        'last_update': today.strftime('%d/%m/%Y')
    }


def build_cash_block(target_date):
    session = CashRegisterSession.query.filter_by(is_open=True).order_by(
        CashRegisterSession.opened_at.desc()
    ).first()

    movements = CashMovement.query.filter(
        func.date(CashMovement.created_at) == target_date
    ).all()

    entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
    exit_types = {'sortie', 'retrait', 'frais', 'paiement'}

    cash_in = 0.0
    cash_out = 0.0

    for movement in movements:
        movement_type = (movement.type or '').lower()
        if movement_type in exit_types:
            cash_out += float(movement.amount or 0)
        elif movement_type in entry_types:
            cash_in += float(movement.amount or 0)
        else:
            if float(movement.amount or 0) >= 0:
                cash_in += float(movement.amount or 0)
            else:
                cash_out += abs(float(movement.amount or 0))

    net = cash_in - cash_out

    history = compute_cash_history(target_date, 7)

    return {
        'session_open': bool(session),
        'session_id': session.id if session else None,
        'session_amount': float(session.initial_amount) if session else 0.0,
        'cash_in': cash_in,
        'cash_out': cash_out,
        'net': net,
        'history': history
    }


def compute_cash_history(reference_date, days):
    history = []
    for i in range(days):
        day = reference_date - timedelta(days=days - i - 1)
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == day
        ).all()
        entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
        exit_types = {'sortie', 'retrait', 'frais', 'paiement'}
        cash_in = 0.0
        cash_out = 0.0
        for movement in movements:
            movement_type = (movement.type or '').lower()
            amount = float(movement.amount or 0)
            if movement_type in exit_types:
                cash_out += amount
            elif movement_type in entry_types or amount >= 0:
                cash_in += amount
            else:
                cash_out += abs(amount)
        history.append({
            'label': day.strftime('%d/%m'),
            'net': round(cash_in - cash_out, 2)
        })
    return history


def build_attendance_block(target_date):
    total_employees = Employee.query.filter(Employee.is_active.is_(True)).count()
    
    # Essayer d'abord avec AttendanceSummary
    summaries = AttendanceSummary.query.filter(
        AttendanceSummary.work_date == target_date
    ).all()

    # Si pas de AttendanceSummary, utiliser AttendanceRecord
    if not summaries:
        from app.employees.models import AttendanceRecord
        daily_summary = AttendanceRecord.get_daily_summary(target_date)
        
        # Convertir le format AttendanceRecord.get_daily_summary en format similaire à AttendanceSummary
        present = len([
            emp_data for emp_data in daily_summary.values()
            if emp_data.get('status') == 'present'
        ])
        
        presence_rate = round((present / total_employees) * 100, 1) if total_employees else 0.0
        
        # Calculer les heures travaillées depuis daily_summary
        workers_data = []
        for emp_id, emp_data in daily_summary.items():
            employee = emp_data.get('employee')
            if employee:
                total_hours = emp_data.get('total_hours', 0)
                workers_data.append({
                    'name': employee.name,
                    'hours': round(total_hours, 2)
                })
        
        # Trier par heures travaillées
        top_workers_data = sorted(workers_data, key=lambda x: x['hours'], reverse=True)[:5]
        best_employee = top_workers_data[0] if top_workers_data else None
        
        return {
            'total': total_employees,
            'present': present,
            'presence_rate': presence_rate,
            'top_workers': top_workers_data,
            'best_employee': best_employee
        }
    
    # Si AttendanceSummary existe, utiliser le code original
    present = len([
        summary for summary in summaries
        if not summary.is_absent and summary.is_present
    ])

    presence_rate = round((present / total_employees) * 100, 1) if total_employees else 0.0

    def compute_hours(summary):
        worked = float(summary.worked_hours or 0)
        overtime = float(summary.overtime_hours or 0)
        return round(worked + overtime, 2)

    top_workers = sorted(
        summaries,
        key=lambda s: compute_hours(s),
        reverse=True
    )[:5]

    top_workers_data = [
        {
            'name': summary.employee.name if summary.employee else 'Employé',
            'hours': compute_hours(summary)
        } for summary in top_workers
    ]

    best_employee = top_workers_data[0] if top_workers_data else None

    return {
        'total': total_employees,
        'present': present,
        'presence_rate': presence_rate,
        'top_workers': top_workers_data,
        'best_employee': best_employee
    }


def build_overdue_orders(target_date, now):
    rows = Order.query.filter(
        Order.status.notin_(['delivered', 'completed', 'cancelled']),
        Order.due_date.isnot(None),
        Order.due_date < now
    ).order_by(Order.due_date.asc()).limit(10).all()

    overdue = []
    for order in rows:
        delay = now - order.due_date
        hours = round(delay.total_seconds() / 3600, 1)
        overdue.append({
            'id': order.id,
            'customer': order.customer_name or 'Client',
            'amount': float(order.total_amount or 0),
            'status': order.get_status_display(),
            'delay_hours': hours
        })
    return overdue


def build_alerts_block(stock_summary, production_block, overdue_orders):
    critical_stock = len(stock_summary.get('out_of_stock', []))
    low_stock = len(stock_summary.get('low_stock', []))
    production_overdue = production_block.get('overdue_orders', 0)
    delayed_orders = len(overdue_orders)
    total = critical_stock + low_stock + production_overdue + delayed_orders
    return {
        'critical_stock': critical_stock,
        'low_stock': low_stock,
        'production_overdue': production_overdue,
        'delayed_orders': delayed_orders,
        'total': total
    }


def build_metric_cards(overview, prime_cost, sales_block, stock_summary, cash_block, attendance_block, alerts_block, real_kpis=None):
    # Fallback si real_kpis n'est pas fourni (mode dégradé)
    if not real_kpis:
        real_kpis = {
            'revenue': {'total': 0, 'pos': 0, 'shop': 0},
            'cogs': {'total': 0, 'ingredients': 0, 'labor': 0},
            'margin': {'net': 0, 'percent': 0},
            'counts': {'total': 0},
            'delivery_debt': 0
        }

    revenue = real_kpis['revenue']['total'] # Was sales_block.get('daily_revenue')
    growth = sales_block.get('growth_rate', 0.0)
    
    # Marge Brute remplacée par COGS ou gardée ? L'utilisateur veut "COGS" et "Main d'oeuvre".
    # Je vais remplacer Marge Brute par COGS global, et ajouter Main d'Oeuvre.
    cogs_total = real_kpis['cogs']['total']
    
    net_margin_value = real_kpis['margin']['net']
    net_margin_pct = real_kpis['margin']['percent']

    cards = [
        {
            'label': 'CA du jour',
            'value': revenue,
            'unit': 'DA',
            'delta': None,
            'breakdown': [
                {'label': 'POS', 'value': real_kpis['revenue']['pos']},
                {'label': 'Cmd', 'value': real_kpis['revenue']['shop']}
            ],
            'icon': 'bi-cash-stack',
            'tone': 'success'
        },
        {
            'label': 'Prime Cost (Coût de Revient)',
            'value': cogs_total,
            'unit': 'DA',
            'delta': None,
            'breakdown': [
                {'label': 'COGS (Mat)', 'value': real_kpis['cogs']['ingredients']},
                {'label': 'MO', 'value': real_kpis['cogs']['labor']}
            ],
            'icon': 'bi-tools',
            'tone': 'danger'
        },
        {
            'label': 'Marge nette',
            'value': net_margin_value,
            'unit': 'DA',
            'delta': net_margin_pct,
            'trend_label': '% du CA',
            'icon': 'bi-pie-chart',
            'tone': 'primary'
        },
        {
            'label': 'Commandes',
            'value': real_kpis['counts']['total'],
            'unit': 'cmdes',
            'delta': None,
            'breakdown': [
                {'label': 'POS', 'value': real_kpis['counts']['pos']},
                {'label': 'Cmd', 'value': real_kpis['counts']['shop']}
            ],
            'icon': 'bi-bag-check',
            'tone': 'warning'
        },
        {
            'label': 'Dette Livreur',
            'value': real_kpis.get('delivery_debt', 0),
            'unit': 'DA',
            'delta': None,
            'trend_label': 'reste à encaisser',
            'icon': 'bi-bicycle',
            'tone': 'orange'
        },
         {
            'label': 'Main d\'Oeuvre',
            'value': real_kpis['cogs']['labor'],
            'unit': 'DA',
            'delta': None,
            'trend_label': 'coût RH jour',
            'icon': 'bi-people-fill',
            'tone': 'secondary'
        },
        {
            'label': 'Valeur stock',
            'value': stock_summary.get('total_value', 0.0),
            'unit': 'DA',
            'delta': stock_summary.get('consumption_ratio', 0.0) or 0.0,
            'trend_label': 'ratio conso/achats',
            'icon': 'bi-box-seam',
            'tone': 'purple'
        },
        {
            'label': 'Flux caisse',
            'value': cash_block.get('net', 0.0),
            'unit': 'DA',
            'delta': cash_block.get('cash_in', 0.0),
            'trend_label': 'entrées / sorties',
            'icon': 'bi-wallet2',
            'tone': 'teal',
            'extra': {
                'cash_in': cash_block.get('cash_in', 0.0),
                'cash_out': cash_block.get('cash_out', 0.0)
            }
        },
        {
            'label': 'Alertes critiques',
            'value': alerts_block.get('total', 0),
            'unit': 'issues',
            'delta': alerts_block.get('critical_stock', 0),
            'trend_label': 'ruptures',
            'icon': 'bi-exclamation-triangle',
            'tone': 'danger'
        }
    ]
    return cards
def build_ai_insights_block(report_date, sales_report, stock_summary, production_block):
    """Génère les analyses IA combinées (OpenAI + Groq) pour optimiser les coûts"""
    ai_insights = {
        'sales': None,
        'stock': None,
        'production': None,
        'forecast': None,
        'available': False
    }
    
    try:
        # Utiliser Groq pour les analyses rapides (gratuit), OpenAI pour les analyses critiques
        ai_groq = AIManager(llm_provider='groq') if _has_groq() else None
        ai_openai = AIManager(llm_provider='openai') if _has_openai() else None
        
        # Analyse ventes (Groq si disponible, sinon OpenAI, sinon fallback)
        try:
            if ai_groq:
                sales_analysis = ai_groq.analyze_reports('daily_sales', report_date, prompt_type='daily_analysis')
                ai_insights['sales'] = {
                    'analysis': sales_analysis.get('analysis', ''),
                    'provider': 'groq',
                    'model': sales_analysis.get('model', 'N/A')
                }
            elif ai_openai:
                sales_analysis = ai_openai.analyze_reports('daily_sales', report_date, prompt_type='daily_analysis')
                ai_insights['sales'] = {
                    'analysis': sales_analysis.get('analysis', ''),
                    'provider': 'openai',
                    'model': sales_analysis.get('model', 'N/A')
                }
        except Exception as e:
            logger.warning(f"[AI] Erreur analyse ventes: {e}")
        
        # Analyse stock (Groq si disponible)
        try:
            if ai_groq:
                stock_analysis = ai_groq.analyze_reports('daily_stock_alerts', report_date, prompt_type='anomaly_detection')
                ai_insights['stock'] = {
                    'analysis': stock_analysis.get('analysis', ''),
                    'provider': 'groq',
                    'model': stock_analysis.get('model', 'N/A')
                }
        except Exception as e:
            logger.warning(f"[AI] Erreur analyse stock: {e}")
        
        # Prévisions Prophet (gratuit, pas de coût LLM)
        try:
            ai_prophet = AIManager()
            forecast = ai_prophet.generate_forecasts('daily_sales', days=7, report_date=report_date)
            if forecast.get('success'):
                ai_insights['forecast'] = forecast.get('forecast', [])
        except Exception as e:
            logger.warning(f"[AI] Erreur prévisions Prophet: {e}")
        
        ai_insights['available'] = any([ai_insights['sales'], ai_insights['stock'], ai_insights['forecast']])
        
    except Exception as e:
        logger.error(f"[AI] Erreur génération insights IA: {e}")
    
    return ai_insights

def _has_groq():
    """Vérifie si Groq est disponible"""
    import os
    return bool(os.getenv('GROQ_API_KEY'))

def _has_openai():
    """Vérifie si OpenAI est disponible"""
    import os
    return bool(os.getenv('OPENAI_API_KEY'))

def build_insights_block(sales_report, stock_summary, production_block, cash_block, prime_cost_report, alerts_block, ai_insights=None):
    growth = sales_report.get('growth_rate', 0.0)
    trend = sales_report.get('trend_direction', 'stable')
    banner_level = 'info'
    banner_message = "Performance stable."
    if growth <= -5:
        banner_level = 'danger'
        banner_message = f"Baisse de {abs(growth):.1f}% vs veille. Vérifier promos."
    elif growth >= 5:
        banner_level = 'success'
        banner_message = f"Croissance +{growth:.1f}% vs veille."

    insights = []
    insights.append({
        'title': 'Ventes',
        'icon': 'bi-graph-up',
        'severity': 'success' if growth >= 0 else 'warning',
        'message': f"Tendance {trend}. CA jour: {sales_report.get('total_revenue', 0):,.0f} DA."
    })

    insights.append({
        'title': 'Marge',
        'icon': 'bi-percent',
        'severity': 'info',
        'message': f"Marge brute {prime_cost_report.get('gross_margin_percentage', 0):.1f}% · Prime cost {prime_cost_report.get('prime_cost_percentage', 0):.1f}%."
    })

    low_stock = stock_summary.get('low_stock', [])
    critical_name = low_stock[0]['name'] if low_stock else None
    insights.append({
        'title': 'Stock critique',
        'icon': 'bi-droplet-half',
        'severity': 'danger' if critical_name else 'success',
        'message': f"{critical_name} proche du seuil." if critical_name else "Aucune rupture détectée."
    })

    cash_net = cash_block.get('net', 0.0)
    insights.append({
        'title': 'Trésorerie',
        'icon': 'bi-wallet',
        'severity': 'success' if cash_net >= 0 else 'warning',
        'message': f"Flux net {cash_net:,.0f} DA aujourd'hui."
    })

    production_alert = production_block.get('overdue_orders', 0)
    insights.append({
        'title': 'Production',
        'icon': 'bi-tools',
        'severity': 'warning' if production_alert else 'success',
        'message': f"{production_alert} ordres en retard" if production_alert else "Production à jour."
    })

    result = {
        'banner': {
            'level': banner_level,
            'message': banner_message
        },
        'cards': insights[:3],
        'extended': insights,
        'ai': ai_insights or {}
    }
    
    return result


def build_tables_block(stock_summary, sales_block, overdue_orders, purchases_block):
    return {
        'low_stock': stock_summary.get('low_stock', [])[:6],
        'delayed_orders': overdue_orders[:6],
        'top_products': sales_block.get('top_products', [])[:5],
        'purchase_list': purchases_block.get('pending', [])[:6]
    }


def build_chart_payload(production_block, stock_block, sales_block, attendance_block, cash_block, trend_days, reference_date):
    revenue_trend = compute_revenue_trend_series(reference_date, trend_days)
    attendance_series = [worker['hours'] for worker in attendance_block.get('top_workers', [])]

    on_time = max(production_block.get('total_orders', 0) - production_block.get('overdue_orders', 0), 0)
    production_status = {
        'on_time': on_time,
        'overdue': production_block.get('overdue_orders', 0),
        'urgent': production_block.get('urgent_orders', 0)
    }

    return {
        'revenueTrend': revenue_trend,
        'orderTypeStacked': sales_block.get('order_types', []),
        'categoryDonut': sales_block.get('category_breakdown', []),
        'hourlyHeatmap': sales_block.get('hourly_sales', []),
        'productionBar': production_block.get('bar'),
        'productionStatus': production_status,
        'ingredientDonut': production_block.get('donut'),
        'stockLine': stock_block.get('variation'),
        'stockHeatmap': stock_block.get('heatmap'),
        'stockMovements': stock_block.get('movements'),
        'salesTopProducts': sales_block.get('top_products_json'),
        'paymentModes': sales_block.get('payment_modes_json'),
        'attendanceSparkline': attendance_series,
        'cashHistory': cash_block.get('history', [])
    }


def compute_revenue_trend_series(reference_date, days, forecast_points=3):
    labels = []
    actuals = []
    for i in range(days):
        current_day = reference_date - timedelta(days=days - i - 1)
        labels.append(current_day.strftime('%d/%m'))
        actuals.append(float(_compute_revenue(report_date=current_day)))

    diffs = [actuals[i] - actuals[i - 1] for i in range(1, len(actuals))] if len(actuals) > 1 else [0]
    avg_diff = mean(diffs) if diffs else 0

    forecast_labels = []
    forecast_values = []
    last_value = actuals[-1] if actuals else 0

    for i in range(1, forecast_points + 1):
        day = reference_date + timedelta(days=i)
        forecast_labels.append(day.strftime('%d/%m'))
        last_value = max(last_value + avg_diff, 0)
        forecast_values.append(last_value)

    combined_labels = labels + forecast_labels
    actual_series = actuals + [None] * len(forecast_labels)
    forecast_series = [None] * len(labels) + forecast_values

    return {
        'labels': combined_labels,
        'actual': actual_series,
        'forecast': forecast_series
    }

