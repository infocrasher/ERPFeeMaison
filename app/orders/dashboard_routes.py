from flask import render_template, jsonify, Blueprint, request, flash
from flask_login import login_required
from models import Order, Product, OrderItem
from app.employees.models import Employee
from app.sales.models import CashRegisterSession
from datetime import datetime, timedelta
from decorators import admin_required
from extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

# Mapping des jours de la semaine en français
DAYS_FR = {
    'Monday': 'Lundi',
    'Tuesday': 'Mardi',
    'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi',
    'Friday': 'Vendredi',
    'Saturday': 'Samedi',
    'Sunday': 'Dimanche'
}

@dashboard_bp.route('/production')
@login_required
@admin_required
def production_dashboard():
    """Dashboard de production - Groupé par heure avec remarques"""
    
    # Récupérer les commandes normales
    orders_to_produce = Order.query.filter(
        Order.status.in_(['pending', 'in_production'])
    ).order_by(Order.due_date.asc()).all()
    
    # Calcul des stats pour l'en-tête
    # Force UTC+1 (Algérie/France Hivers) car le serveur est en UTC
    now = datetime.utcnow() + timedelta(hours=1)
    orders_on_time = 0
    orders_soon = 0
    orders_overdue = 0
    
    # Structure : {date: {heure: [commandes]}}
    # date au format 'YYYY-MM-DD' pour trier facilement
    orders_by_date = {}
    
    for order in orders_to_produce:
        order_items = order.items.all() if hasattr(order.items, 'all') else (order.items or [])
        
        # Calculer la priorité
        if order.due_date:
            time_diff_hours = (order.due_date - now).total_seconds() / 3600
            if time_diff_hours < 0:
                orders_overdue += 1
                priority = 'overdue'
            elif time_diff_hours < 2:
                orders_soon += 1
                priority = 'urgent'
            else:
                orders_on_time += 1
                priority = 'normal'
            
            # Grouper par date puis par heure
            date_key = order.due_date.strftime('%Y-%m-%d')  # Pour trier
            day_name_en = order.due_date.strftime('%A')
            day_name_fr = DAYS_FR.get(day_name_en, day_name_en)
            date_display = f"{day_name_fr} {order.due_date.strftime('%d/%m/%y')}"  # Format affichage: "Dimanche 16/11/25"
            hour_key = order.due_date.strftime('%Hh')
            hour_value = order.due_date.hour
            
            # Calculer le temps restant
            diff_seconds = int((order.due_date - now).total_seconds())
            diff_minutes = diff_seconds // 60
            
            if diff_seconds < 0:
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
            elif diff_minutes <= 30:
                time_label = f"{diff_minutes}min"
            elif diff_minutes <= 120:
                hours = diff_minutes // 60
                mins = diff_minutes % 60
                time_label = f"{hours}h {mins}min"
            else:
                days = diff_seconds // 86400
                hours = (diff_seconds % 86400) // 3600
                mins = (diff_seconds % 3600) // 60
                
                if days > 0:
                    time_label = f"{days}j {hours}h"
                else:
                    time_label = f"{hours}h {mins}min"
        else:
            date_key = '9999-12-31'  # Pour mettre à la fin
            date_display = 'Sans date'
            hour_key = 'Sans horaire'
            hour_value = 99  # Pour mettre à la fin
            time_label = 'Sans horaire'
            priority = 'normal'
        
        # Construire la liste des produits avec quantités
        products_list = []
        for item in order_items:
            if item.product:
                # FILTRE PRODUCTION (Demandé le 12/12/2025)
                # Si le produit fini est marqué comme "Peut être acheté" (can_be_purchased=True),
                # on ne l'affiche pas en production (ex: Canettes, Jus...).
                # On suppose qu'il est géré par le stock magasin/frigo, pas par les cuisiniers.
                if item.product.can_be_purchased:
                    continue
                    
                qty = int(item.quantity) if float(item.quantity).is_integer() else float(item.quantity)
                products_list.append({
                    'name': item.product.name,
                    'quantity': qty
                })
        
        # Créer l'entrée de commande
        order_entry = {
            'id': order.id,
            'customer': order.customer_name or '-',
            'notes': order.notes or '',  # Remarques de la commande
            'products': products_list,
            'time_label': time_label,
            'priority': priority,
            'due_time': order.due_date.strftime('%H:%M') if order.due_date else '--',  # Heure de livraison/retrait prévue
            'hour_value': hour_value,  # Pour trier
            'delivery_option': order.delivery_option if order.delivery_option else None,  # Option de livraison (delivery/pickup)
            'customer_address': order.customer_address.strip() if order.customer_address else ''  # Adresse de livraison
        }
        
        # Ajouter à la structure groupée par date puis heure
        if date_key not in orders_by_date:
            orders_by_date[date_key] = {
                'date_display': date_display,
                'hours': {}
            }
        
        if hour_key not in orders_by_date[date_key]['hours']:
            orders_by_date[date_key]['hours'][hour_key] = []
        
        orders_by_date[date_key]['hours'][hour_key].append(order_entry)
    
    # Trier les dates et les heures dans chaque date
    sorted_dates = []
    for date_key in sorted(orders_by_date.keys()):
        date_data = orders_by_date[date_key]
        sorted_hours = sorted(date_data['hours'].items(), key=lambda x: x[1][0]['hour_value'] if x[1] else 99)
        sorted_dates.append({
            'date_key': date_key,
            'date_display': date_data['date_display'],
            'hours': sorted_hours
        })
    
    total_orders = len(orders_to_produce)
    
    return render_template('dashboards/production_dashboard.html',
                         orders_by_date=sorted_dates,
                         orders_on_time=orders_on_time,
                         orders_soon=orders_soon,
                         orders_overdue=orders_overdue,
                         total_orders=total_orders,
                         title="Dashboard Production")

@dashboard_bp.route('/shop')
@login_required
@admin_required
def shop_dashboard():
    # Get date filter from query params
    selected_date_str = request.args.get('date')
    selected_date = None
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format de date invalide', 'warning')
            selected_date = None
    
    # Get search query
    search_query = request.args.get('search', '').strip()
    
    # Build base queries with optional date filter
    # 1. En Production - Commandes Client
    query_customer = Order.query.filter(
        Order.status.in_(['in_production', 'pending']),
        Order.order_type == 'customer_order'
    )
    if selected_date:
        query_customer = query_customer.filter(db.func.date(Order.due_date) == selected_date)
    if search_query:
        query_customer = query_customer.filter(
            db.or_(
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%'),
                Order.customer_address.ilike(f'%{search_query}%'),
                Order.items.any(db.func.lower(Product.name).contains(search_query.lower()))
            )
        ).join(Order.items).join(OrderItem.product)
    customer_orders_in_production = query_customer.order_by(Order.due_date.asc()).all()

    # 1b. En Production - Ordres de Production
    query_production = Order.query.filter(
        Order.status.in_(['in_production', 'pending']),
        Order.order_type != 'customer_order'
    )
    if selected_date:
        query_production = query_production.filter(db.func.date(Order.due_date) == selected_date)
    if search_query:
        query_production = query_production.filter(
            Order.items.any(db.func.lower(Product.name).contains(search_query.lower()))
        ).join(Order.items).join(OrderItem.product)
    production_orders_in_production = query_production.order_by(Order.due_date.asc()).all()
    
    # 2. En attente de retrait (commandes client pickup)
    query_pickup = Order.query.filter(
        Order.status == 'waiting_for_pickup',
        Order.order_type == 'customer_order',
        Order.delivery_option == 'pickup'
    )
    if selected_date:
        query_pickup = query_pickup.filter(db.func.date(Order.due_date) == selected_date)
    if search_query:
        query_pickup = query_pickup.filter(
            db.or_(
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%'),
                Order.items.any(db.func.lower(Product.name).contains(search_query.lower()))
            )
        ).join(Order.items).join(OrderItem.product)
    orders_waiting_pickup = query_pickup.order_by(Order.due_date.asc()).all()
    
    # 3. Prêt à livrer (commandes client delivery ET commandes PDV livraison)
    query_delivery = Order.query.filter(
        Order.status == 'ready_at_shop',
        Order.delivery_option == 'delivery',
        Order.order_type.in_(['customer_order', 'in_store'])
    )
    if selected_date:
        query_delivery = query_delivery.filter(db.func.date(Order.due_date) == selected_date)
    if search_query:
        query_delivery = query_delivery.filter(
            db.or_(
                Order.customer_name.ilike(f'%{search_query}%'),
                Order.customer_phone.ilike(f'%{search_query}%'),
                Order.customer_address.ilike(f'%{search_query}%'),
                Order.items.any(db.func.lower(Product.name).contains(search_query.lower()))
            )
        ).join(Order.items).join(OrderItem.product)
    orders_ready_delivery = query_delivery.order_by(Order.due_date.asc()).all()
    
    # 4. Au comptoir (ordres de production terminés - visibles 24h)
    cutoff_datetime = datetime.utcnow() - timedelta(days=1)
    query_counter = Order.query.filter(
        Order.status == 'completed',
        Order.order_type == 'counter_production_request',
        Order.created_at >= cutoff_datetime
    )
    if selected_date:
        query_counter = query_counter.filter(db.func.date(Order.created_at) == selected_date)
    if search_query:
        query_counter = query_counter.filter(
            Order.items.any(db.func.lower(Product.name).contains(search_query.lower()))
        ).join(Order.items).join(OrderItem.product)
    orders_at_counter = query_counter.order_by(Order.created_at.desc()).limit(10).all()
    
    # Vérifier si une session de caisse est ouverte
    cash_session_open = CashRegisterSession.query.filter_by(is_open=True).first() is not None
    
    # Récupérer les employés de production pour le modal
    from app.employees.models import Employee
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production'])
    ).order_by(Employee.name).all()
    
    # Get today's date for default value
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('dashboards/shop_dashboard.html',
                         customer_orders_in_production=customer_orders_in_production,
                         production_orders_in_production=production_orders_in_production,
                         orders_waiting_pickup=orders_waiting_pickup,
                         orders_ready_delivery=orders_ready_delivery,
                         orders_at_counter=orders_at_counter,
                         cash_session_open=cash_session_open,
                         employees=employees,
                         selected_date=selected_date_str,
                         today_date=today_date,
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

@dashboard_bp.route('/api/production-orders-count')
@login_required
def production_orders_count():
    """API pour compter les commandes en production (pour notification sonore)"""
    count = Order.query.filter(
        Order.status.in_(['pending', 'in_production'])
    ).count()
    return jsonify({'count': count, 'timestamp': datetime.utcnow().isoformat()})

@dashboard_bp.route('/shop/toggle-item/<int:item_id>', methods=['POST'])
@login_required
def toggle_item_reception(item_id):
    """Bascule l'état de réception d'un produit (reçu / non reçu)"""
    item = OrderItem.query.get_or_404(item_id)
    
    # Inverser l'état
    item.is_received = not item.is_received
    
    if item.is_received:
        item.received_at = datetime.utcnow()
        # Si nous avions un lien User -> Employee, nous pourrions l'ajouter ici
        # item.received_by_id = ...
    else:
        item.received_at = None
        item.received_by_id = None
        
    db.session.commit()
    
    # Vérifier si tous les articles de la commande sont reçus
    order = item.order
    total_items = order.items.count()
    received_items = order.items.filter_by(is_received=True).count()
    
    all_received = (received_items == total_items) and (total_items > 0)
    percentage = int((received_items / total_items) * 100) if total_items > 0 else 0
    
    return jsonify({
        'success': True, 
        'is_received': item.is_received,
        'received_at': item.received_at.isoformat() if item.received_at else None,
        'all_received': all_received,
        'percentage': percentage,
        'order_id': order.id
    })