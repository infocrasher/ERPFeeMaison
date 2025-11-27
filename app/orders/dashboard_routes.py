from flask import render_template, jsonify, Blueprint
from flask_login import login_required
from models import Order, Product
from app.employees.models import Employee
from app.sales.models import CashRegisterSession
from datetime import datetime, timedelta
from decorators import admin_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/production')
@login_required
@admin_required
def production_dashboard():
    """Dashboard de production pour Rayan"""
    
    # Récupérer les commandes normales
    orders_to_produce = Order.query.filter(
        Order.status.in_(['pending', 'in_production'])
    ).order_by(Order.due_date.asc()).all()
    
    # Calcul des stats pour l'en-tête
    now = datetime.utcnow()
    orders_on_time = 0
    orders_soon = 0
    orders_overdue = 0
    orders_wall = []
    
    for order in orders_to_produce:
        order_items = order.items.all() if hasattr(order.items, 'all') else (order.items or [])
        if order.due_date:
            time_diff_hours = (order.due_date - now).total_seconds() / 3600
            if time_diff_hours < 0:
                orders_overdue += 1
            elif time_diff_hours < 2:
                orders_soon += 1
            else:
                orders_on_time += 1
        total_qty = sum(float(item.quantity) for item in order_items)
        if total_qty.is_integer():
            quantity_label = f"{int(total_qty)} pcs"
        else:
            quantity_label = f"{total_qty:.1f} pcs"
        
        # Afficher TOUS les produits de la commande (pas seulement le premier)
        products_list = []
        for item in order_items:
            if item.product:
                qty = int(item.quantity) if float(item.quantity).is_integer() else item.quantity
                products_list.append(f"{item.product.name} (x{qty})")
        
        if products_list:
            primary_product = ", ".join(products_list)
        else:
            primary_product = order.customer_name or f"Commande #{order.id}"
        
        if order.due_date:
            diff_seconds = int((order.due_date - now).total_seconds())
            diff_minutes = diff_seconds // 60
            
            if diff_seconds < 0:
                # En retard - afficher en jours/heures/minutes
                abs_seconds = abs(diff_seconds)
                days_late = abs_seconds // 86400
                hours_late = (abs_seconds % 86400) // 3600
                mins_late = (abs_seconds % 3600) // 60
                
                if days_late > 0:
                    time_label = f"Retard {days_late}j {hours_late}h"
                elif hours_late > 0:
                    time_label = f"Retard {hours_late}h {mins_late}min"
                else:
                    time_label = f"Retard {mins_late}min"
                priority = 'overdue'
            elif diff_minutes <= 30:
                time_label = f"{diff_minutes}min"
                priority = 'urgent'
            elif diff_minutes <= 120:
                hours = diff_minutes // 60
                mins = diff_minutes % 60
                time_label = f"{hours}h {mins}min"
                priority = 'urgent'
            else:
                # Plus de 2h - afficher en jours/heures/minutes
                days = diff_seconds // 86400
                hours = (diff_seconds % 86400) // 3600
                mins = (diff_seconds % 3600) // 60
                
                if days > 0:
                    time_label = f"{days}j {hours}h"
                else:
                    time_label = f"{hours}h {mins}min"
                priority = 'normal'
        else:
            diff_minutes = 0
            time_label = 'Sans horaire'
            priority = 'normal'
        orders_wall.append({
            'id': order.id,
            'primary_product': primary_product,
            'quantity_label': quantity_label,
            'time_label': time_label,
            'priority': priority,
            'customer': order.customer_name or '-',
            'due_time': order.due_date.strftime('%H:%M') if order.due_date else '--'
        })
    
    total_orders = len(orders_to_produce)
    
    return render_template('dashboards/production_dashboard.html',
                         orders=orders_to_produce,
                         orders_wall=orders_wall,
                         orders_on_time=orders_on_time,
                         orders_soon=orders_soon,
                         orders_overdue=orders_overdue,
                         total_orders=total_orders,
                         title="Dashboard Production")

@dashboard_bp.route('/shop')
@login_required
@admin_required
def shop_dashboard():
    # 1. En Production (toutes commandes)
    orders_in_production = Order.query.filter(
        Order.status == 'in_production'
    ).order_by(Order.due_date.asc()).all()
    
    # 2. En attente de retrait (commandes client pickup)
    orders_waiting_pickup = Order.query.filter(
        Order.status == 'waiting_for_pickup',
        Order.order_type == 'customer_order',
        Order.delivery_option == 'pickup'
    ).order_by(Order.due_date.asc()).all()
    
    # 3. Prêt à livrer (commandes client delivery)
    orders_ready_delivery = Order.query.filter(
        Order.status == 'ready_at_shop',
        Order.order_type == 'customer_order',
        Order.delivery_option == 'delivery'
    ).order_by(Order.due_date.asc()).all()
    
    # 4. Au comptoir (ordres de production terminés - visibles 24h)
    cutoff_datetime = datetime.utcnow() - timedelta(days=1)
    orders_at_counter = Order.query.filter(
        Order.status == 'completed',
        Order.order_type == 'counter_production_request',
        Order.created_at >= cutoff_datetime
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    # 5. Livré Non Payé (commandes livrées en attente paiement)
    orders_delivered_unpaid = Order.query.filter(
        Order.status == 'delivered_unpaid'
    ).order_by(Order.due_date.asc()).all()
    
    # Vérifier si une session de caisse est ouverte
    cash_session_open = CashRegisterSession.query.filter_by(is_open=True).first() is not None
    
    return render_template('dashboards/shop_dashboard.html',
                         orders_in_production=orders_in_production,
                         orders_waiting_pickup=orders_waiting_pickup,
                         orders_ready_delivery=orders_ready_delivery,
                         orders_at_counter=orders_at_counter,
                         orders_delivered_unpaid=orders_delivered_unpaid,
                         cash_session_open=cash_session_open,
                         title="Dashboard Magasin")

@dashboard_bp.route('/ingredients-alerts')
@login_required
@admin_required
def ingredients_alerts():
    low_stock_ingredients = Product.query.filter(
        Product.product_type == 'ingredient',
        Product.quantity_in_stock <= 5
    ).order_by(Product.name.asc()).all()
    out_of_stock_ingredients = Product.query.filter(
        Product.product_type == 'ingredient',
        Product.quantity_in_stock <= 0
    ).order_by(Product.name.asc()).all()
    return render_template('dashboards/ingredients_alerts.html',
                         low_stock_ingredients=low_stock_ingredients,
                         out_of_stock_ingredients=out_of_stock_ingredients,
                         title="Alertes Ingrédients")

@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    today = datetime.now().date()
    orders_today = Order.query.filter(
        Order.created_at >= today
    ).count()
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    low_stock_count = Product.query.filter(Product.quantity_in_stock <= 5).count()
    overdue_orders = Order.query.filter(
        Order.due_date < datetime.utcnow(),
        Order.status.in_(['pending', 'in_production'])
    ).count()
    return render_template('dashboards/admin_dashboard.html',
                         orders_today=orders_today,
                         active_employees=active_employees,
                         low_stock_count=low_stock_count,
                         overdue_orders=overdue_orders,
                         title="Dashboard Administrateur")

@dashboard_bp.route('/sales')
@login_required
@admin_required
def sales_dashboard():
    current_month = datetime.now().replace(day=1)
    delivered_orders = Order.query.filter(
        Order.status == 'delivered',
        Order.updated_at >= current_month
    ).count()
    return render_template('dashboards/sales_dashboard.html',
                         delivered_orders=delivered_orders,
                         title="Dashboard Ventes")

@dashboard_bp.route('/api/orders-stats')
@login_required
@admin_required
def orders_stats_api():
    stats = {
        'pending': Order.query.filter_by(status='pending').count(),
        'in_production': Order.query.filter_by(status='in_production').count(),
        'ready_at_shop': Order.query.filter_by(status='ready_at_shop').count(),
        'delivered': Order.query.filter_by(status='delivered').count()
    }
    return jsonify(stats)