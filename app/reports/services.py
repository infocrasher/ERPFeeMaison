"""
Services pour la génération de rapports
Contient toute la logique métier pour les calculs et analyses
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, case
from extensions import db
from models import Product, Order, OrderItem, Category
from app.sales.models import CashRegisterSession, CashMovement
from app.employees.models import Employee, WorkHours, PayrollEntry, PayrollPeriod, AttendanceSummary
from app.inventory.models import DailyWaste
from app.purchases.models import Purchase
from app.accounting.services import DashboardService
import yaml
import os


# ============================================================================
# CONFIGURATION BENCHMARKS
# ============================================================================

# Cache pour éviter de recharger le fichier YAML à chaque appel
_benchmarks_cache = None


def _load_benchmarks():
    """
    Charge la configuration des benchmarks depuis config/benchmarks.yaml
    Utilise un cache pour optimiser les performances
    
    Returns:
        dict: Configuration des benchmarks
    """
    global _benchmarks_cache
    
    if _benchmarks_cache is not None:
        return _benchmarks_cache
    
    # Chemin du fichier de configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config',
        'benchmarks.yaml'
    )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _benchmarks_cache = yaml.safe_load(f)
        return _benchmarks_cache
    except Exception as e:
        # Fallback : valeurs par défaut si le fichier n'existe pas
        print(f"⚠️  Impossible de charger config/benchmarks.yaml: {e}")
        return {
            'daily_sales': {'target_revenue': 50000.0},
            'daily_prime_cost': {'target_percentage': 68.0},
            'daily_production': {'target_efficiency': 80.0},
            'daily_stock_alerts': {'target_alerts': 0},
            'daily_waste_loss': {'target_percentage': 5.0},
            'weekly_product_performance': {'target_growth': 0.0},
            'weekly_stock_rotation': {'target_days_min': 7, 'target_days_max': 14, 'target_days_optimal': 10.5},
            'weekly_labor_cost': {'target_ratio_min': 25.0, 'target_ratio_max': 30.0, 'target_ratio_optimal': 27.5},
            'weekly_cash_flow': {'target_balance': 0.0},
            'monthly_gross_margin': {'target_percentage': 60.0},
            'monthly_profit_loss': {'target_net_margin': 10.0},
            'trend_threshold': 5.0
        }


# ============================================================================
# FONCTIONS UTILITAIRES POUR LES RAPPORTS
# ============================================================================

def _compute_revenue(report_date=None, start_date=None, end_date=None):
    """
    Fonction utilitaire pour calculer le chiffre d'affaires de manière cohérente.
    Utilise sum(OrderItem.quantity * OrderItem.unit_price) pour garantir la cohérence.
    Gère les valeurs NULL via coalesce pour éviter les erreurs de calcul.
    
    Args:
        report_date: Date unique pour un rapport quotidien
        start_date: Date de début pour une période
        end_date: Date de fin pour une période
        
    Returns:
        float: Chiffre d'affaires calculé (0.0 si aucune vente)
    """
    query = db.session.query(
        func.sum(
            func.coalesce(OrderItem.quantity, 0) * func.coalesce(OrderItem.unit_price, 0)
        )
    ).select_from(OrderItem).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.status.in_(['completed', 'delivered', 'delivered_unpaid'])
    )
    
    # Filtrage par date
    if report_date:
        query = query.filter(func.date(Order.created_at) == report_date)
    elif start_date and end_date:
        query = query.filter(
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date
        )
    
    result = query.scalar() or 0
    return float(result)


def _get_orders_filter_real(report_date=None, start_date=None, end_date=None):
    """
    Helper pour construire le filtre de commandes selon la logique RealKpiService.
    Retourne une condition SQLAlchemy qui filtre :
    - POS : order_type == 'in_store' ET created_at == date
    - Shop : order_type != 'in_store' ET status livré ET due_date == date
    
    Args:
        report_date: Date unique pour un rapport quotidien
        start_date: Date de début pour une période
        end_date: Date de fin pour une période
        
    Returns:
        SQLAlchemy filter condition
    """
    from sqlalchemy import or_, and_
    
    if report_date:
        # POS : créées ce jour
        pos_condition = and_(
            Order.order_type == 'in_store',
            func.date(Order.created_at) == report_date
        )
        
        # Shop : livrées ce jour (exclure ordres de production)
        shop_condition = and_(
            Order.order_type != 'in_store',
            Order.order_type != 'counter_production_request',  # Exclure les ordres de production
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.due_date) == report_date
        )
        
        return or_(pos_condition, shop_condition)
    
    elif start_date and end_date:
        # POS : créées dans la période
        pos_condition = and_(
            Order.order_type == 'in_store',
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date
        )
        
        # Shop : créées ET livrées dans la période (exclure ordres de production)
        shop_condition = and_(
            Order.order_type != 'in_store',
            Order.order_type != 'counter_production_request',  # Exclure les ordres de production
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.created_at) >= start_date,  # Créée dans la période
            func.date(Order.created_at) <= end_date,
            func.date(Order.due_date) >= start_date,  # Livrée dans la période
            func.date(Order.due_date) <= end_date
        )
        
        return or_(pos_condition, shop_condition)
    
    # Par défaut, retourner une condition qui ne filtre rien (pour éviter les erreurs)
    return Order.id.isnot(None)


def _compute_revenue_real(report_date=None, start_date=None, end_date=None):
    """
    Fonction utilitaire pour calculer le chiffre d'affaires selon la logique RealKpiService.
    Utilise la logique correcte :
    - POS : created_at == date (comptabilisé à la création)
    - Shop : due_date == date ET status livré (comptabilisé à la livraison)
    
    Cette fonction remplace progressivement _compute_revenue() pour garantir la cohérence
    avec le dashboard qui utilise RealKpiService.
    
    Args:
        report_date: Date unique pour un rapport quotidien
        start_date: Date de début pour une période
        end_date: Date de fin pour une période
        
    Returns:
        float: Chiffre d'affaires calculé (0.0 si aucune vente)
    """
    from models import Order, OrderItem
    
    # Pour une date unique
    if report_date:
        # POS : commandes créées ce jour
        # Utiliser Order.total_amount comme RealKpiService pour inclure tous les frais
        pos_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type == 'in_store',
                func.date(Order.created_at) == report_date
            ).scalar() or 0.0
        
        # Shop : commandes créées ET livrées ce jour
        # Utiliser Order.total_amount comme RealKpiService pour inclure les frais de livraison
        # IMPORTANT: Exclure les ordres de production (counter_production_request) qui ont montant=0
        # Ne comptabiliser que les commandes créées ET livrées le même jour
        shop_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type != 'in_store',
                Order.order_type != 'counter_production_request',  # Exclure les ordres de production
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.created_at) == report_date,  # Créée le jour J
                func.date(Order.due_date) == report_date  # Livrée le jour J
            ).scalar() or 0.0
        
        return float(pos_revenue) + float(shop_revenue)
    
    # Pour une période (start_date, end_date)
    elif start_date and end_date:
        # POS : commandes créées dans la période
        # Utiliser Order.total_amount comme RealKpiService
        pos_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type == 'in_store',
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date
            ).scalar() or 0.0
        
        # Shop : commandes créées ET livrées dans la période
        # Utiliser Order.total_amount comme RealKpiService pour inclure les frais de livraison
        # IMPORTANT: Exclure les ordres de production (counter_production_request) qui ont montant=0
        # Ne comptabiliser que les commandes créées ET livrées dans la période
        shop_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type != 'in_store',
                Order.order_type != 'counter_production_request',  # Exclure les ordres de production
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.created_at) >= start_date,  # Créée dans la période
                func.date(Order.created_at) <= end_date,
                func.date(Order.due_date) >= start_date,  # Livrée dans la période
                func.date(Order.due_date) <= end_date
            ).scalar() or 0.0
        
        return float(pos_revenue) + float(shop_revenue)
    
    # Si aucun paramètre, retourner 0
    return 0.0


def _compute_growth_rate(current_value, previous_value):
    """
    Calcule le taux de croissance entre deux valeurs.
    
    Args:
        current_value: Valeur actuelle
        previous_value: Valeur précédente
        
    Returns:
        float: Taux de croissance en % (arrondi à 2 décimales)
    """
    if previous_value and previous_value > 0:
        growth = ((current_value - previous_value) / previous_value) * 100
    elif current_value > 0:
        growth = 100.0  # Croissance maximale si pas de valeur précédente
    else:
        growth = 0.0
    
    return round(growth, 2)


def _determine_trend(growth_rate, threshold=None):
    """
    Détermine la tendance basée sur le taux de croissance.
    
    Args:
        growth_rate: Taux de croissance en %
        threshold: Seuil de sensibilité (None = utilise config, défaut: 5%)
        
    Returns:
        str: 'up', 'down', ou 'stable'
    """
    if threshold is None:
        benchmarks = _load_benchmarks()
        threshold = benchmarks.get('trend_threshold', 5.0)
    
    if growth_rate > threshold:
        return 'up'
    elif growth_rate < -threshold:
        return 'down'
    else:
        return 'stable'


def _compute_variance(values_list):
    """
    Calcule la variance (écart-type) d'une liste de valeurs.
    Version simplifiée pour l'analyse IA.
    
    Args:
        values_list: Liste de valeurs numériques
        
    Returns:
        float: Écart-type arrondi à 2 décimales
    """
    if not values_list or len(values_list) < 2:
        return 0.0
    
    # Calcul de la moyenne
    mean = sum(values_list) / len(values_list)
    
    # Calcul de la variance
    variance = sum((x - mean) ** 2 for x in values_list) / len(values_list)
    
    # Écart-type (racine carrée de la variance)
    import math
    std_dev = math.sqrt(variance)
    
    return round(std_dev, 2)


def _get_temporal_metadata(reference_date):
    """
    Génère les métadonnées temporelles pour une date donnée.
    Utile pour l'analyse IA (saisonnalité, patterns, etc.)
    
    Args:
        reference_date: Date de référence (date object)
        
    Returns:
        dict: Métadonnées temporelles
    """
    if not reference_date:
        reference_date = date.today()
    
    # Jours de la semaine en français
    days_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    
    return {
        'day_of_week': days_fr[reference_date.weekday()],
        'day_of_week_num': reference_date.weekday() + 1,  # 1=Lundi, 7=Dimanche
        'week_of_month': (reference_date.day - 1) // 7 + 1,
        'week_of_year': reference_date.isocalendar()[1],
        'month': reference_date.month,
        'month_name': reference_date.strftime('%B'),
        'quarter': (reference_date.month - 1) // 3 + 1,
        'is_weekend': reference_date.weekday() >= 5,
        'is_month_start': reference_date.day <= 7,
        'is_month_end': reference_date.day >= 23,
        'is_holiday': False  # TODO: Intégrer calendrier des jours fériés
    }


def _get_stock_value(reference_date=None, location='comptoir'):
    """
    Fonction utilitaire pour calculer la valeur totale du stock à une date donnée.
    
    Note : Cette version utilise le stock actuel comme approximation.
    Lorsqu'un système d'historique de stock sera disponible, cette fonction
    pourra être étendue pour interroger les snapshots historiques.
    
    Args:
        reference_date: Date de référence (non utilisée actuellement, 
                       préparée pour évolution future)
        location: Emplacement du stock à considérer
                 'comptoir' : stock_comptoir (défaut)
                 'local' : stock_ingredients_local
                 'magasin' : stock_ingredients_magasin
                 'consommables' : stock_consommables
                 'all' : somme de tous les emplacements
        
    Returns:
        float: Valeur totale du stock (stock * cost_price)
    """
    # Actuellement : utilise le stock actuel (instantané)
    # TODO Future : Interroger table d'historique de stock si disponible
    
    # Définir le champ de stock selon l'emplacement
    if location == 'comptoir':
        stock_field = Product.stock_comptoir
    elif location == 'local':
        stock_field = Product.stock_ingredients_local
    elif location == 'magasin':
        stock_field = Product.stock_ingredients_magasin
    elif location == 'consommables':
        stock_field = Product.stock_consommables
    elif location == 'all':
        # Somme de tous les emplacements
        stock_field = (
            func.coalesce(Product.stock_comptoir, 0) +
            func.coalesce(Product.stock_ingredients_local, 0) +
            func.coalesce(Product.stock_ingredients_magasin, 0) +
            func.coalesce(Product.stock_consommables, 0)
        )
    else:
        # Par défaut : comptoir
        stock_field = Product.stock_comptoir
    
    total_stock_value = db.session.query(
        func.sum(
            func.coalesce(stock_field, 0) * func.coalesce(Product.cost_price, 0)
        )
    ).scalar() or 0
    
    return float(total_stock_value)


class ReportService:
    """Service de base pour les rapports"""
    
    @staticmethod
    def get_date_range(period='day', custom_start=None, custom_end=None):
        """
        Obtenir une plage de dates selon la période
        
        Args:
            period: 'day', 'week', 'month', 'custom'
            custom_start: Date de début personnalisée
            custom_end: Date de fin personnalisée
        
        Returns:
            tuple: (start_date, end_date)
        """
        today = date.today()
        
        if period == 'day':
            return today, today
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period == 'month':
            start = date(today.year, today.month, 1)
            if today.month == 12:
                end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            return start, end
        elif period == 'custom' and custom_start and custom_end:
            return custom_start, custom_end
        else:
            return today, today


class DailySalesReportService:
    """Rapport de ventes quotidien"""
    
    @staticmethod
    def generate(report_date=None):
        """Générer le rapport de ventes quotidien"""
        if not report_date:
            report_date = date.today()
        
        # Utiliser le filtre cohérent avec RealKpiService
        orders_filter = _get_orders_filter_real(report_date=report_date)
        
        # Ventes du jour (POS créées ce jour + Shop livrées ce jour)
        orders = Order.query.filter(orders_filter).all()
        
        # Calculs de base (utilisation de la fonction utilitaire cohérente)
        total_revenue = _compute_revenue_real(report_date=report_date)
        total_transactions = len(orders)
        average_basket = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Top 5 produits (utiliser le filtre cohérent)
        top_products_rows = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('quantity'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
        ).select_from(Product).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).group_by(Product.id, Product.name).order_by(
            func.sum(OrderItem.quantity * OrderItem.unit_price).desc()
        ).limit(5).all()
        top_products_json = [
            {
                'name': row.name,
                'quantity': float(row.quantity or 0),
                'revenue': float(row.revenue or 0)
            } for row in top_products_rows
        ]
        
        # Ventes par catégorie (utiliser le filtre cohérent)
        sales_by_category_rows = db.session.query(
            Category.name,
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
        ).select_from(Category).join(
            Product, Product.category_id == Category.id
        ).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).group_by(Category.id, Category.name).all()
        sales_by_category_json = [
            {
                'name': row.name,
                'revenue': float(row.revenue or 0)
            } for row in sales_by_category_rows
        ]
        
        # Ventes par heure (utiliser created_at pour POS, due_date pour Shop)
        # On utilise case pour sélectionner la bonne date selon le type de commande
        date_for_hour = case(
            (Order.order_type == 'in_store', Order.created_at),
            else_=Order.due_date
        )
        hourly_sales_rows = db.session.query(
            extract('hour', date_for_hour).label('hour'),
            func.count(func.distinct(Order.id)).label('transactions'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
        ).select_from(Order).join(
            OrderItem, OrderItem.order_id == Order.id
        ).filter(orders_filter).group_by('hour').order_by('hour').all()
        hourly_sales_json = [
            {
                'hour': int(row.hour or 0),
                'transactions': int(row.transactions or 0),
                'revenue': float(row.revenue or 0)
            } for row in hourly_sales_rows
        ]
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec le jour précédent (growth_rate)
        previous_date = report_date - timedelta(days=1)
        previous_revenue = _compute_revenue_real(report_date=previous_date)
        growth_rate = _compute_growth_rate(total_revenue, previous_revenue)
        trend_direction = _determine_trend(growth_rate)
        
        # Variance sur les ventes horaires
        hourly_revenues = [item['revenue'] for item in hourly_sales_json]
        variance = _compute_variance(hourly_revenues)
        variance_context = ['hourly_revenues']  # Variables incluses dans variance
        
        # Benchmark : objectif de CA quotidien (depuis config)
        benchmarks = _load_benchmarks()
        target_daily_revenue = benchmarks['daily_sales']['target_revenue']
        benchmark = {
            'target': target_daily_revenue,
            'current': total_revenue,
            'variance': total_revenue - target_daily_revenue,
            'achievement_rate': (total_revenue / target_daily_revenue * 100) if target_daily_revenue > 0 else 0
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(report_date)
        
        return {
            'date': report_date,
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'average_basket': average_basket,
            'top_products': top_products_rows,
            'top_products_json': top_products_json,
            'sales_by_category': sales_by_category_rows,
            'sales_by_category_json': sales_by_category_json,
            'hourly_sales': hourly_sales_rows,
            'hourly_sales_json': hourly_sales_json,
            'orders': orders,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class PrimeCostReportService:
    """Rapport de coût de revient quotidien (Prime Cost)"""
    
    @staticmethod
    def generate(report_date=None, _skip_comparisons=False):
        """Générer le rapport Prime Cost"""
        if not report_date:
            report_date = date.today()
        
        # Chiffre d'affaires (utilise DailySalesReportService qui est maintenant cohérent)
        revenue = DailySalesReportService.generate(report_date)['total_revenue']
        
        # COGS (Cost of Goods Sold) - calcul cohérent avec RealKpiService
        # IMPORTANT : Utiliser la même méthode que RealKpiService pour garantir la cohérence
        # On calcule directement via une requête SQL : OrderItem.quantity * Product.cost_price
        
        # Récupérer les IDs des commandes concernées (même logique que RealKpiService)
        pos_order_ids = db.session.query(Order.id).filter(
            Order.order_type == 'in_store',
            func.date(Order.created_at) == report_date
        ).all()
        pos_ids = [r[0] for r in pos_order_ids]
        
        shop_order_ids = db.session.query(Order.id).filter(
            Order.order_type != 'in_store',
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.due_date) == report_date
        ).all()
        shop_ids = [r[0] for r in shop_order_ids]
        
        all_order_ids = pos_ids + shop_ids
        
        # Calculer le COGS directement via requête SQL (même méthode que RealKpiService)
        if all_order_ids:
            cogs_query = db.session.query(
                func.sum(OrderItem.quantity * Product.cost_price)
            ).join(Product, OrderItem.product_id == Product.id)\
             .filter(OrderItem.order_id.in_(all_order_ids))
            
            cogs = float(cogs_query.scalar() or 0.0)
        else:
            cogs = 0.0
        
        # Coût de main d'œuvre du jour
        # Utiliser AttendanceSummary si disponible, sinon AttendanceRecord
        from app.employees.models import AttendanceSummary, AttendanceRecord
        
        labor_cost = db.session.query(
            func.sum((AttendanceSummary.worked_hours + AttendanceSummary.overtime_hours) * Employee.hourly_rate)
        ).select_from(AttendanceSummary).join(
            Employee, Employee.id == AttendanceSummary.employee_id
        ).filter(
            AttendanceSummary.work_date == report_date
        ).scalar() or 0
        labor_cost = float(labor_cost)
        
        # Si pas de AttendanceSummary, calculer depuis AttendanceRecord
        if labor_cost == 0:
            daily_summary = AttendanceRecord.get_daily_summary(report_date)
            labor_cost = 0.0
            for emp_id, emp_data in daily_summary.items():
                employee = emp_data.get('employee')
                if employee:
                    total_hours = emp_data.get('total_hours', 0)
                    hourly_rate = float(employee.hourly_rate or 0)
                    labor_cost += total_hours * hourly_rate
        
        # Calculs
        prime_cost = cogs + labor_cost
        prime_cost_percentage = (prime_cost / revenue * 100) if revenue > 0 else 0
        gross_margin = revenue - cogs
        gross_margin_percentage = (gross_margin / revenue * 100) if revenue > 0 else 0
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec le jour précédent (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                previous_date = report_date - timedelta(days=1)
                previous_data = PrimeCostReportService.generate(previous_date, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(prime_cost_percentage, previous_data['prime_cost_percentage'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les principaux coûts
        variance = _compute_variance([revenue, cogs, labor_cost, prime_cost])
        variance_context = ['revenue', 'cogs', 'labor_cost', 'prime_cost']
        
        # Benchmark : objectif prime_cost (depuis config)
        benchmarks = _load_benchmarks()
        target_prime_cost_percentage = benchmarks['daily_prime_cost']['target_percentage']
        benchmark = {
            'target': target_prime_cost_percentage,
            'current': prime_cost_percentage,
            'variance': prime_cost_percentage - target_prime_cost_percentage,
            'is_within_target': prime_cost_percentage <= target_prime_cost_percentage
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(report_date)
        
        return {
            'date': report_date,
            'revenue': revenue,
            'cogs': cogs,
            'labor_cost': labor_cost,
            'prime_cost': prime_cost,
            'prime_cost_percentage': prime_cost_percentage,
            'gross_margin': gross_margin,
            'gross_margin_percentage': gross_margin_percentage,
            'is_profitable': prime_cost_percentage <= 68,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class ProductionReportService:
    """Rapport de production quotidienne"""
    
    @staticmethod
    def generate(report_date=None, _skip_comparisons=False):
        """Générer le rapport de production"""
        if not report_date:
            report_date = date.today()
        
        # Ordres de production du jour
        production_orders = Order.query.filter(
            func.date(Order.created_at) == report_date,
            Order.order_type == 'counter_production_request'
        ).all()
        
        production_rows = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('quantity_produced'),
            Product.unit
        ).select_from(Product).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            func.date(Order.created_at) == report_date,
            Order.order_type == 'counter_production_request'
        ).group_by(Product.id, Product.name, Product.unit).all()
        production_by_product_json = [
            {
                'name': row.name,
                'quantity_produced': float(row.quantity_produced or 0),
                'unit': row.unit
            } for row in production_rows
        ]
        
        total_units = sum(item['quantity_produced'] for item in production_by_product_json)
        total_orders = len(production_orders)
        
        # Taux d'efficacité : ratio unités produites / nombre de commandes
        # Plus ce ratio est élevé, plus la production est efficace par commande
        efficiency_rate = (total_units / total_orders * 100) if total_orders > 0 else 0
        efficiency_rate = round(efficiency_rate, 2)
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec le jour précédent (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                previous_date = report_date - timedelta(days=1)
                previous_data = ProductionReportService.generate(previous_date, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(total_units, previous_data['total_units'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les quantités produites par produit
        production_quantities = [float(p['quantity_produced']) for p in production_by_product_json]
        variance = _compute_variance(production_quantities)
        variance_context = ['production_quantities_by_product']
        
        # Benchmark : objectif efficiency_rate (depuis config)
        benchmarks = _load_benchmarks()
        target_efficiency = benchmarks['daily_production']['target_efficiency']
        benchmark = {
            'target': target_efficiency,
            'current': efficiency_rate,
            'variance': efficiency_rate - target_efficiency,
            'is_efficient': efficiency_rate >= target_efficiency
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(report_date)
        
        return {
            'date': report_date,
            'total_units': total_units,
            'total_orders': total_orders,
            'production_by_product': production_rows,
            'production_by_product_json': production_by_product_json,
            'efficiency_rate': efficiency_rate,
            'production_orders': production_orders,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class StockAlertReportService:
    """Rapport d'alerte de stock quotidien"""
    
    @staticmethod
    def generate():
        """Générer le rapport d'alerte de stock"""
        
        # Produits sous seuil
        low_stock_products = Product.query.filter(
            Product.stock_comptoir <= Product.seuil_min_comptoir,
            Product.seuil_min_comptoir > 0
        ).all()
        
        # Ruptures de stock
        out_of_stock = Product.query.filter(
            Product.stock_comptoir == 0
        ).all()
        
        # Surstock (exemple: > 100 unités)
        overstock = Product.query.filter(
            Product.stock_comptoir > 100
        ).all()
        
        # Jours de couverture (estimation)
        coverage_data = []
        for product in Product.query.filter(Product.stock_comptoir > 0).all():
            # Ventes moyennes des 7 derniers jours
            avg_sales = db.session.query(
                func.avg(OrderItem.quantity)
            ).select_from(OrderItem).join(
                Order, Order.id == OrderItem.order_id
            ).filter(
                OrderItem.product_id == product.id,
                Order.created_at >= datetime.now() - timedelta(days=7),
                Order.status.in_(['completed', 'delivered'])
            ).scalar() or 0
            
            if avg_sales > 0:
                days_coverage = product.stock_comptoir / float(avg_sales)
                if days_coverage < 3:  # Moins de 3 jours
                    coverage_data.append({
                        'product': product,
                        'days_coverage': days_coverage
                    })
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Pas de comparaison temporelle (rapport instantané)
        total_alerts = len(low_stock_products) + len(out_of_stock)
        growth_rate = 0.0  # N/A pour rapport instantané
        trend_direction = 'stable'
        
        # Variance sur jours de couverture
        coverage_days = [c['days_coverage'] for c in coverage_data]
        variance = _compute_variance(coverage_days) if coverage_days else 0.0
        variance_context = ['coverage_days']
        
        # Benchmark : objectif alertes (depuis config)
        benchmarks = _load_benchmarks()
        target_alerts = benchmarks['daily_stock_alerts']['target_alerts']
        benchmark = {
            'target': target_alerts,
            'current': total_alerts,
            'variance': total_alerts - target_alerts,
            'is_healthy': total_alerts == target_alerts
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(date.today())
        
        return {
            'low_stock_products': low_stock_products,
            'out_of_stock': out_of_stock,
            'overstock': overstock,
            'coverage_data': coverage_data,
            'total_alerts': total_alerts,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class WasteLossReportService:
    """Rapport des pertes et gaspillage"""
    
    @staticmethod
    def generate(start_date=None, end_date=None, _skip_comparisons=False):
        """Générer le rapport de gaspillage"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Déclarations d'invendus
        waste_declarations = DailyWaste.query.filter(
            DailyWaste.waste_date >= start_date,
            DailyWaste.waste_date <= end_date
        ).all()
        
        # Valeur totale perdue
        total_value_lost = sum([w.value_lost for w in waste_declarations])
        
        # Répartition par cause
        waste_by_reason = {}
        for waste in waste_declarations:
            reason = waste.reason
            if reason not in waste_by_reason:
                waste_by_reason[reason] = {'count': 0, 'value': 0.0}
            waste_by_reason[reason]['count'] += 1
            waste_by_reason[reason]['value'] += waste.value_lost
        
        # Coût alimentaire total (COGS) - utiliser filtre cohérent avec RealKpiService
        orders_filter = _get_orders_filter_real(start_date=start_date, end_date=end_date)
        total_cogs = db.session.query(
            func.sum(OrderItem.quantity * Product.cost_price)
        ).select_from(OrderItem).join(
            Product, Product.id == OrderItem.product_id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).scalar() or 1  # Éviter division par zéro
        total_cogs = float(total_cogs)
        
        # Pourcentage du coût alimentaire
        waste_percentage = (total_value_lost / total_cogs * 100) if total_cogs > 0 else 0
        
        # Convertir les objets DailyWaste en dictionnaires pour la sérialisation JSON
        waste_declarations_data = []
        for waste in waste_declarations:
            waste_declarations_data.append({
                'id': waste.id,
                'waste_date': waste.waste_date.isoformat() if waste.waste_date else None,
                'product_id': waste.product_id,
                'product_name': waste.product.name if waste.product else 'Produit supprimé',
                'quantity': float(waste.quantity),
                'reason': waste.reason,
                'value_lost': float(waste.value_lost),
                'notes': waste.notes,
                'declared_at': waste.declared_at.isoformat() if waste.declared_at else None
            })
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec période précédente (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                period_length = (end_date - start_date).days + 1
                previous_start = start_date - timedelta(days=period_length)
                previous_end = start_date - timedelta(days=1)
                previous_data = WasteLossReportService.generate(previous_start, previous_end, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(total_value_lost, previous_data['total_value_lost'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les valeurs perdues par déclaration
        waste_values = [w['value_lost'] for w in waste_declarations_data]
        variance = _compute_variance(waste_values)
        variance_context = ['waste_values_per_declaration']
        
        # Benchmark : objectif (depuis config)
        benchmarks = _load_benchmarks()
        target_waste_percentage = benchmarks['daily_waste_loss']['target_percentage']
        benchmark = {
            'target': target_waste_percentage,
            'current': waste_percentage,
            'variance': waste_percentage - target_waste_percentage,
            'is_acceptable': waste_percentage < target_waste_percentage
        }
        
        # Métadonnées temporelles (date de fin de période)
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_value_lost': float(total_value_lost),
            'waste_by_reason': waste_by_reason,
            'waste_percentage': float(waste_percentage),
            'is_acceptable': waste_percentage < 5,
            'waste_declarations': waste_declarations_data,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class WeeklyProductPerformanceService:
    """Rapport de performance hebdomadaire des produits"""
    
    @staticmethod
    def generate(start_date=None, end_date=None):
        """Générer le rapport de performance produits"""
        if not start_date or not end_date:
            start_date, end_date = ReportService.get_date_range('week')
        
        # Ventes par produit cette semaine - utiliser filtre cohérent avec RealKpiService
        orders_filter = _get_orders_filter_real(start_date=start_date, end_date=end_date)
        current_week_sales = db.session.query(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label('quantity_sold'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
        ).select_from(Product).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).group_by(Product.id, Product.name).all()
        
        # Ventes semaine précédente - utiliser filtre cohérent
        prev_start = start_date - timedelta(days=7)
        prev_end = end_date - timedelta(days=7)
        prev_orders_filter = _get_orders_filter_real(start_date=prev_start, end_date=prev_end)
        prev_week_sales = db.session.query(
            Product.id,
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
        ).select_from(Product).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(prev_orders_filter).group_by(Product.id).all()
        
        # Créer un dict pour comparaison
        prev_sales_dict = {p.id: float(p.revenue) for p in prev_week_sales}
        
        # Calculer la croissance
        performance_data = []
        for product in current_week_sales:
            prev_revenue = prev_sales_dict.get(product.id, 0)
            current_revenue = float(product.revenue)
            
            if prev_revenue > 0:
                growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
            else:
                growth = 100 if current_revenue > 0 else 0
            
            performance_data.append({
                'product_name': product.name,
                'quantity_sold': product.quantity_sold,
                'revenue': current_revenue,
                'growth': growth
            })
        
        # Trier par revenu
        performance_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Growth rate global : somme des revenus actuels vs précédents
        total_revenue = sum([p['revenue'] for p in performance_data])
        previous_revenue_list = [prev_sales_dict.get(p.id, 0) for p in current_week_sales]
        previous_revenue = sum(previous_revenue_list)
        growth_rate = _compute_growth_rate(total_revenue, previous_revenue)
        trend_direction = _determine_trend(growth_rate)
        
        # Variance sur les revenus produits
        product_revenues = [p['revenue'] for p in performance_data]
        variance = _compute_variance(product_revenues)
        variance_context = ['product_revenues']
        
        # Benchmark : objectif croissance (depuis config)
        benchmarks = _load_benchmarks()
        target_growth = benchmarks['weekly_product_performance']['target_growth']
        benchmark = {
            'target': target_growth,
            'current': growth_rate,
            'variance': growth_rate - target_growth,
            'is_growing': growth_rate > target_growth
        }
        
        # Métadonnées temporelles (date de fin de période)
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'performance_data': performance_data,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class StockRotationReportService:
    """Rapport de rotation des stocks hebdomadaire"""
    
    @staticmethod
    def generate(start_date=None, end_date=None, _skip_comparisons=False):
        """Générer le rapport de rotation des stocks"""
        if not start_date or not end_date:
            start_date, end_date = ReportService.get_date_range('week')
        
        # COGS de la période - utiliser filtre cohérent avec RealKpiService
        orders_filter = _get_orders_filter_real(start_date=start_date, end_date=end_date)
        cogs = db.session.query(
            func.sum(OrderItem.quantity * Product.cost_price)
        ).select_from(OrderItem).join(
            Product, Product.id == OrderItem.product_id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).scalar() or 0
        cogs = float(cogs)
        
        # Valeur moyenne du stock (formule correcte : moyenne période)
        # Note : Utilisation stock actuel comme approximation (voir _get_stock_value)
        stock_start = _get_stock_value(reference_date=start_date)
        stock_end = _get_stock_value(reference_date=end_date)
        stock_moyen = (stock_start + stock_end) / 2 if (stock_start + stock_end) > 0 else 1
        
        # Pour compatibilité avec templates existants
        total_stock_value = stock_moyen
        
        # Rotation = COGS / Stock moyen (formule comptable correcte)
        rotation_ratio = cogs / stock_moyen if stock_moyen > 0 else 0
        rotation_ratio = round(rotation_ratio, 2)
        
        # Jours de stock = Stock / (COGS / jours période)
        days_in_period = (end_date - start_date).days + 1
        daily_cogs = cogs / days_in_period if days_in_period > 0 else 0
        days_of_stock = total_stock_value / daily_cogs if daily_cogs > 0 else 0
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec période précédente (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                period_length = days_in_period
                previous_start = start_date - timedelta(days=period_length) if period_length <= 31 else start_date - timedelta(days=7)
                previous_end = start_date - timedelta(days=1)
                previous_data = StockRotationReportService.generate(previous_start, previous_end, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(rotation_ratio, previous_data['rotation_ratio'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur [cogs, stock_value, rotation_ratio, days_of_stock]
        variance = _compute_variance([cogs, total_stock_value, rotation_ratio, days_of_stock])
        variance_context = ['cogs', 'total_stock_value', 'rotation_ratio', 'days_of_stock']
        
        # Benchmark : objectif jours de stock (depuis config)
        benchmarks = _load_benchmarks()
        target_days_min = benchmarks['weekly_stock_rotation']['target_days_min']
        target_days_max = benchmarks['weekly_stock_rotation']['target_days_max']
        target_days_optimal = benchmarks['weekly_stock_rotation']['target_days_optimal']
        benchmark = {
            'target_min': target_days_min,
            'target_max': target_days_max,
            'current': days_of_stock,
            'variance': days_of_stock - target_days_optimal,
            'is_optimal': target_days_min <= days_of_stock <= target_days_max
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'cogs': cogs,
            'total_stock_value': total_stock_value,
            'rotation_ratio': rotation_ratio,
            'days_of_stock': days_of_stock,
            'is_optimal': 7 <= days_of_stock <= 14,  # Cible: 1-2 semaines
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class LaborCostReportService:
    """Rapport de coût de main d'œuvre hebdomadaire"""
    
    @staticmethod
    def generate(start_date=None, end_date=None, _skip_comparisons=False):
        """Générer le rapport de coût de main d'œuvre"""
        if not start_date or not end_date:
            start_date, end_date = ReportService.get_date_range('week')
        
        # Coût total du personnel
        # Utiliser AttendanceSummary qui a work_date et worked_hours
        total_labor_cost = db.session.query(
            func.sum((AttendanceSummary.worked_hours + AttendanceSummary.overtime_hours) * Employee.hourly_rate)
        ).select_from(AttendanceSummary).join(
            Employee, Employee.id == AttendanceSummary.employee_id
        ).filter(
            AttendanceSummary.work_date >= start_date,
            AttendanceSummary.work_date <= end_date
        ).scalar() or 0
        total_labor_cost = float(total_labor_cost)
        
        # Heures travaillées
        total_hours = db.session.query(
            func.sum(AttendanceSummary.worked_hours + AttendanceSummary.overtime_hours)
        ).filter(
            AttendanceSummary.work_date >= start_date,
            AttendanceSummary.work_date <= end_date
        ).scalar() or 0
        total_hours = float(total_hours)
        
        # Heures supplémentaires
        overtime_hours = db.session.query(
            func.sum(AttendanceSummary.overtime_hours)
        ).filter(
            AttendanceSummary.work_date >= start_date,
            AttendanceSummary.work_date <= end_date
        ).scalar() or 0
        overtime_hours = float(overtime_hours)
        
        # Chiffre d'affaires de la période (utilisation de la fonction cohérente avec RealKpiService)
        revenue = _compute_revenue_real(start_date=start_date, end_date=end_date)
        if revenue == 0:
            revenue = 1  # Éviter division par zéro
        
        # Ratio coût main d'œuvre / CA
        labor_cost_ratio = (total_labor_cost / revenue * 100) if revenue > 0 else 0
        
        # Productivité (CA par heure travaillée)
        productivity = revenue / total_hours if total_hours > 0 else 0
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec période précédente (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                period_length = (end_date - start_date).days + 1
                previous_start = start_date - timedelta(days=period_length)
                previous_end = start_date - timedelta(days=1)
                previous_data = LaborCostReportService.generate(previous_start, previous_end, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(labor_cost_ratio, previous_data['labor_cost_ratio'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur [revenue, labor_cost, hours, productivity]
        variance = _compute_variance([revenue, total_labor_cost, total_hours, productivity])
        variance_context = ['revenue', 'total_labor_cost', 'total_hours', 'productivity']
        
        # Benchmark : objectif ratio (depuis config)
        benchmarks = _load_benchmarks()
        target_ratio_min = benchmarks['weekly_labor_cost']['target_ratio_min']
        target_ratio_max = benchmarks['weekly_labor_cost']['target_ratio_max']
        target_ratio_optimal = benchmarks['weekly_labor_cost']['target_ratio_optimal']
        benchmark = {
            'target_min': target_ratio_min,
            'target_max': target_ratio_max,
            'current': labor_cost_ratio,
            'variance': labor_cost_ratio - target_ratio_optimal,
            'is_optimal': target_ratio_min <= labor_cost_ratio <= target_ratio_max
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_labor_cost': total_labor_cost,
            'total_hours': total_hours,
            'overtime_hours': overtime_hours,
            'revenue': revenue,
            'labor_cost_ratio': labor_cost_ratio,
            'productivity': productivity,
            'is_optimal': 25 <= labor_cost_ratio <= 30,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class CashFlowForecastService:
    """Prévision de trésorerie hebdomadaire"""
    
    @staticmethod
    def generate(start_date=None, end_date=None, _skip_comparisons=False):
        """Générer la prévision de trésorerie"""
        if not start_date or not end_date:
            start_date, end_date = ReportService.get_date_range('week')
        
        # Encaissements prévus (ventes complétées - utilisation fonction cohérente avec RealKpiService)
        expected_inflows = _compute_revenue_real(start_date=start_date, end_date=end_date)
        
        # Décaissements prévus (achats)
        # Correction : Prioriser payment_date si disponible, sinon requested_date
        # Évite le double comptage si les deux dates sont dans la période
        purchases_outflows = db.session.query(
            func.sum(Purchase.total_amount)
        ).filter(
            or_(
                # Cas 1 : payment_date renseigné et dans la période
                and_(
                    Purchase.payment_date.isnot(None),
                    Purchase.payment_date >= start_date,
                    Purchase.payment_date <= end_date
                ),
                # Cas 2 : payment_date non renseigné, on utilise requested_date
                and_(
                    Purchase.payment_date.is_(None),
                    func.date(Purchase.requested_date) >= start_date,
                    func.date(Purchase.requested_date) <= end_date
                )
            )
        ).scalar() or 0
        purchases_outflows = float(purchases_outflows)
        
        # Décaissements salaires : corriger pour capturer les périodes qui chevauchent
        # Correction : Périodes où start_date <= end_date_rapport AND end_date >= start_date_rapport
        payroll_outflows = db.session.query(
            func.sum(PayrollEntry.net_salary)
        ).select_from(PayrollEntry).join(
            PayrollPeriod, PayrollPeriod.id == PayrollEntry.period_id
        ).filter(
            PayrollPeriod.start_date <= end_date,
            PayrollPeriod.end_date >= start_date
        ).scalar() or 0
        payroll_outflows = float(payroll_outflows)
        
        total_outflows = purchases_outflows + payroll_outflows
        
        # Solde prévisionnel
        net_cash_flow = expected_inflows - total_outflows
        
        # Solde actuel (via accounting)
        current_balance = DashboardService.get_cash_balance() + DashboardService.get_bank_balance()
        
        # Solde prévisionnel final
        forecasted_balance = current_balance + net_cash_flow
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec période précédente (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                period_length = (end_date - start_date).days + 1
                previous_start = start_date - timedelta(days=period_length)
                previous_end = start_date - timedelta(days=1)
                previous_data = CashFlowForecastService.generate(previous_start, previous_end, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(net_cash_flow, previous_data['net_cash_flow'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les flux
        variance = _compute_variance([expected_inflows, purchases_outflows, payroll_outflows, net_cash_flow])
        variance_context = ['expected_inflows', 'purchases_outflows', 'payroll_outflows', 'net_cash_flow']
        
        # Benchmark : objectif solde (depuis config)
        benchmarks = _load_benchmarks()
        target_balance = benchmarks['weekly_cash_flow']['target_balance']
        benchmark = {
            'target': target_balance,
            'current': forecasted_balance,
            'variance': forecasted_balance - target_balance,
            'is_healthy': forecasted_balance > target_balance
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'current_balance': current_balance,
            'expected_inflows': expected_inflows,
            'purchases_outflows': purchases_outflows,
            'payroll_outflows': payroll_outflows,
            'total_outflows': total_outflows,
            'net_cash_flow': net_cash_flow,
            'forecasted_balance': forecasted_balance,
            'is_healthy': forecasted_balance > 0,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class MonthlyGrossMarginService:
    """Marge brute mensuelle par catégorie"""
    
    @staticmethod
    def generate(year=None, month=None, _skip_comparisons=False):
        """Générer le rapport de marge brute mensuelle"""
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Ventes et COGS par catégorie - utiliser filtre cohérent avec RealKpiService
        orders_filter = _get_orders_filter_real(start_date=start_date, end_date=end_date)
        category_data = db.session.query(
            Category.name,
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue'),
            func.sum(OrderItem.quantity * Product.cost_price).label('cogs')
        ).select_from(Category).join(
            Product, Product.category_id == Category.id
        ).join(
            OrderItem, OrderItem.product_id == Product.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).group_by(Category.id, Category.name).all()
        
        # Calculer les marges
        margin_data = []
        for cat in category_data:
            revenue = float(cat.revenue or 0)
            cogs = float(cat.cogs or 0)
            gross_margin = revenue - cogs
            gross_margin_percentage = (gross_margin / revenue * 100) if revenue > 0 else 0
            
            margin_data.append({
                'category': cat.name,
                'revenue': revenue,
                'cogs': cogs,
                'gross_margin': gross_margin,
                'gross_margin_percentage': gross_margin_percentage
            })
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Calculer le revenue total (nécessaire pour benchmark et comparaison)
        total_revenue = sum([m['revenue'] for m in margin_data])
        
        # Comparaison avec mois précédent (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                if month == 1:
                    previous_year, previous_month = year - 1, 12
                else:
                    previous_year, previous_month = year, month - 1
                previous_data = MonthlyGrossMarginService.generate(previous_year, previous_month, _skip_comparisons=True)
                # Revenue total précédent
                previous_revenue = sum([m['revenue'] for m in previous_data['margin_data']])
                growth_rate = _compute_growth_rate(total_revenue, previous_revenue)
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les marges par catégorie
        margin_percentages = [m['gross_margin_percentage'] for m in margin_data]
        variance = _compute_variance(margin_percentages)
        variance_context = ['gross_margin_percentage_by_category']
        
        # Benchmark : objectif marge brute (depuis config)
        benchmarks = _load_benchmarks()
        target_margin = benchmarks['monthly_gross_margin']['target_percentage']
        total_cogs = sum([m['cogs'] for m in margin_data])
        global_margin_percentage = ((total_revenue - total_cogs) / total_revenue * 100) if total_revenue > 0 else 0
        benchmark = {
            'target': target_margin,
            'current': global_margin_percentage,
            'variance': global_margin_percentage - target_margin,
            'is_healthy': global_margin_percentage >= target_margin
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'margin_data': margin_data,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


class MonthlyProfitLossService:
    """Compte de résultat mensuel (P&L)"""
    
    @staticmethod
    def generate(year=None, month=None, _skip_comparisons=False):
        """Générer le compte de résultat mensuel"""
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Chiffre d'affaires (utilisation fonction cohérente avec RealKpiService)
        revenue = _compute_revenue_real(start_date=start_date, end_date=end_date)
        
        # COGS - utiliser le même filtre que le CA pour garantir la cohérence
        orders_filter = _get_orders_filter_real(start_date=start_date, end_date=end_date)
        cogs = db.session.query(
            func.sum(OrderItem.quantity * Product.cost_price)
        ).select_from(OrderItem).join(
            Product, Product.id == OrderItem.product_id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(orders_filter).scalar() or 0
        cogs = float(cogs)
        
        # Marge brute
        gross_margin = revenue - cogs
        gross_margin_percentage = (gross_margin / revenue * 100) if revenue > 0 else 0
        
        # Charges (via accounting)
        expenses = DashboardService.get_monthly_expenses()
        
        # EBITDA (approximation)
        ebitda = gross_margin - expenses
        
        # Résultat net (simplifié)
        net_income = ebitda
        net_margin_percentage = (net_income / revenue * 100) if revenue > 0 else 0
        
        # ============================================================================
        # MÉTADONNÉES IA
        # ============================================================================
        
        # Comparaison avec mois précédent (éviter récursion infinie)
        if not _skip_comparisons:
            try:
                if month == 1:
                    previous_year, previous_month = year - 1, 12
                else:
                    previous_year, previous_month = year, month - 1
                previous_data = MonthlyProfitLossService.generate(previous_year, previous_month, _skip_comparisons=True)
                growth_rate = _compute_growth_rate(revenue, previous_data['revenue'])
                trend_direction = _determine_trend(growth_rate)
            except:
                growth_rate = 0.0
                trend_direction = 'stable'
        else:
            growth_rate = 0.0
            trend_direction = 'stable'
        
        # Variance sur les principaux indicateurs
        variance = _compute_variance([revenue, cogs, gross_margin, expenses, ebitda, net_income])
        variance_context = ['revenue', 'cogs', 'gross_margin', 'expenses', 'ebitda', 'net_income']
        
        # Benchmark : objectif marge nette (depuis config)
        benchmarks = _load_benchmarks()
        target_net_margin = benchmarks['monthly_profit_loss']['target_net_margin']
        benchmark = {
            'target': target_net_margin,
            'current': net_margin_percentage,
            'variance': net_margin_percentage - target_net_margin,
            'is_profitable': net_margin_percentage >= target_net_margin
        }
        
        # Métadonnées temporelles
        metadata = _get_temporal_metadata(end_date)
        
        return {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'revenue': revenue,
            'cogs': cogs,
            'gross_margin': gross_margin,
            'gross_margin_percentage': gross_margin_percentage,
            'expenses': expenses,
            'ebitda': ebitda,
            'net_income': net_income,
            'net_margin_percentage': net_margin_percentage,
            # Métadonnées IA
            'growth_rate': growth_rate,
            'variance': variance,
            'variance_context': variance_context,
            'trend_direction': trend_direction,
            'benchmark': benchmark,
            'metadata': metadata
        }


def analyse_ia(resume_donnees: dict) -> str:
    """
    Placeholder pour analyse IA
    À connecter plus tard à une API (OpenAI, Mistral, etc.)
    
    Args:
        resume_donnees: Dictionnaire contenant les données du rapport
    
    Returns:
        str: Analyse textuelle (placeholder pour l'instant)
    """
    return "Analyse IA en attente de connexion..."


class DailyProfitabilityService:
    """
    Rapport Rentabilité & Trésorerie (P&L vs Cash)
    Compare la performance (CA basé sur livraisons) avec la trésorerie (encaissements réels)
    """
    
    @staticmethod
    def get_daily_metrics(target_date):
        """
        Récupère les métriques quotidiennes pour une date donnée.
        Réutilise les logiques existantes du Dashboard.
        
        Returns:
            dict: Métriques quotidiennes (CA, COGS, Labor, Cash) + détails des commandes
        """
        from app.reports.kpi_service import RealKpiService
        from app.sales.models import CashMovement
        from models import Order
        
        # 1. Récupérer les KPIs depuis RealKpiService (même logique que le dashboard)
        kpis = RealKpiService.get_daily_kpis(target_date)
        
        # 2. Calculer les encaissements depuis CashMovement (même logique que FLUX CAISSE)
        entry_types = {'entrée', 'vente', 'acompte', 'deposit'}
        exit_types = {'sortie', 'retrait', 'frais', 'paiement'}
        
        movements = CashMovement.query.filter(
            func.date(CashMovement.created_at) == target_date
        ).all()
        
        cash_in = 0.0
        cash_out = 0.0
        cash_movements_detail = []  # 🆕 Liste des mouvements de caisse
        
        for movement in movements:
            movement_type = (movement.type or '').lower()
            amount = float(movement.amount or 0)
            if movement_type in exit_types:
                cash_out += amount
            elif movement_type in entry_types or amount >= 0:
                cash_in += amount
                # 🆕 Enregistrer les détails des entrées
                cash_movements_detail.append({
                    'id': movement.id,
                    'time': movement.created_at.strftime('%H:%M') if movement.created_at else 'N/A',
                    'type': movement.type or 'Entrée',
                    'reason': movement.reason or 'Sans raison',
                    'notes': movement.notes or '',
                    'amount': amount,
                    'order_id': movement.order_id if hasattr(movement, 'order_id') else None
                })
            else:
                cash_out += abs(amount)
        
        # 3. Extraire les métriques
        ca_ventes = kpis['revenue']['total']  # CA Performance (ventes)
        cogs = kpis['cogs']['ingredients']    # Coût Matière
        labor_cost = kpis['cogs']['labor']    # Main d'œuvre
        encaissement = cash_in                 # Encaissements réels
        
        # 4. Calculer les métriques dérivées
        marge_nette = ca_ventes - cogs - labor_cost
        ecart_cash = encaissement - ca_ventes  # Écart Cash vs Ventes
        
        # 5. 🆕 DÉTAIL DES COMMANDES - CA VENTES
        # 5.1 Commandes POS (Ventes au Comptoir)
        pos_orders_query = Order.query.filter(
            Order.order_type == 'in_store',
            func.date(Order.created_at) == target_date
        ).order_by(Order.created_at.desc())
        
        pos_orders_detail = []
        for order in pos_orders_query:
            pos_orders_detail.append({
                'id': order.id,
                'time': order.created_at.strftime('%H:%M') if order.created_at else 'N/A',
                'amount': float(order.total_amount or 0)
            })
        
        # 5.2 Commandes Shop créées ET livrées le même jour
        shop_orders_same_day_query = Order.query.filter(
            Order.order_type != 'in_store',
            Order.order_type != 'counter_production_request',
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.created_at) == target_date,
            func.date(Order.due_date) == target_date
        ).order_by(Order.created_at.desc())
        
        shop_orders_same_day_detail = []
        for order in shop_orders_same_day_query:
            shop_orders_same_day_detail.append({
                'id': order.id,
                'customer': order.customer_name or 'Sans nom',
                'amount': float(order.total_amount or 0),
                'time': order.due_date.strftime('%H:%M') if order.due_date else 'N/A'
            })
        
        # 6. 🆕 DÉTAIL DES COMMANDES - ENCAISSEMENTS (Commandes anciennes)
        # Toutes les commandes Shop livrées aujourd'hui MAIS créées avant
        old_orders_paid_today_query = Order.query.filter(
            Order.order_type != 'in_store',
            Order.order_type != 'counter_production_request',
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.due_date) == target_date,  # Livrée aujourd'hui
            func.date(Order.created_at) != target_date  # Mais créée avant
        ).order_by(Order.total_amount.desc())
        
        old_orders_detail = []
        total_old_orders_amount = 0.0
        
        for order in old_orders_paid_today_query:
            total = float(order.total_amount or 0)
            paid = float(order.amount_paid or 0)
            
            # ⚠️ LIMITATION : On affiche le total de la commande
            # car CashMovement n'a pas de lien direct avec order_id
            # L'écart peut être gonflé si un acompte a été versé avant aujourd'hui
            
            total_old_orders_amount += paid  # On compte ce qui est payé (pas le total)
            
            old_orders_detail.append({
                'id': order.id,
                'created_date': order.created_at.strftime('%d/%m/%Y') if order.created_at else 'N/A',
                'delivered_date': order.due_date.strftime('%d/%m/%Y') if order.due_date else 'N/A',
                'customer': order.customer_name or 'Sans nom',
                'amount': paid,  # Ce qui est payé TODAY (amount_paid)
                'total_order': total,  # Total de la commande
                'has_advance': (paid > 0 and paid < total)  # Y a-t-il eu un acompte ?
            })
        
        return {
            'date': target_date,
            'ca_ventes': round(ca_ventes, 2),
            'cogs': round(cogs, 2),
            'labor_cost': round(labor_cost, 2),
            'marge_nette': round(marge_nette, 2),
            'encaissement': round(encaissement, 2),
            'ecart_cash': round(ecart_cash, 2),
            'cash_out': round(cash_out, 2),
            # Métriques additionnelles utiles
            'pos_count': kpis['counts']['pos'],
            'shop_count': kpis['counts']['shop'],
            'total_orders': kpis['counts']['total'],
            'delivery_debt': kpis['delivery_debt'],
            # Pourcentages
            'cogs_percent': round((cogs / ca_ventes * 100) if ca_ventes > 0 else 0, 1),
            'labor_percent': round((labor_cost / ca_ventes * 100) if ca_ventes > 0 else 0, 1),
            'margin_percent': round((marge_nette / ca_ventes * 100) if ca_ventes > 0 else 0, 1),
            # 🆕 DÉTAILS DES COMMANDES
            'pos_orders': pos_orders_detail,
            'shop_orders_same_day': shop_orders_same_day_detail,
            'old_orders_paid_today': old_orders_detail,
            'old_orders_count': len(old_orders_detail),
            'old_orders_total': round(total_old_orders_amount, 2),
            # 🆕 DÉTAILS DES MOUVEMENTS DE CAISSE
            'cash_movements': cash_movements_detail,
            'cash_movements_total': round(cash_in, 2)
        }
    
    @staticmethod
    def generate(start_date=None, end_date=None):
        """
        Génère le rapport de rentabilité & trésorerie pour une période.
        
        Args:
            start_date: Date de début (défaut: 7 jours en arrière)
            end_date: Date de fin (défaut: aujourd'hui)
        
        Returns:
            dict: Rapport complet avec données quotidiennes et totaux
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=6)  # 7 jours par défaut
        
        # Générer les métriques pour chaque jour
        daily_data = []
        current_date = start_date
        
        totals = {
            'ca_ventes': 0.0,
            'cogs': 0.0,
            'labor_cost': 0.0,
            'marge_nette': 0.0,
            'encaissement': 0.0,
            'ecart_cash': 0.0,
            'total_orders': 0
        }
        
        while current_date <= end_date:
            metrics = DailyProfitabilityService.get_daily_metrics(current_date)
            daily_data.append(metrics)
            
            # Cumuler les totaux
            totals['ca_ventes'] += metrics['ca_ventes']
            totals['cogs'] += metrics['cogs']
            totals['labor_cost'] += metrics['labor_cost']
            totals['marge_nette'] += metrics['marge_nette']
            totals['encaissement'] += metrics['encaissement']
            totals['ecart_cash'] += metrics['ecart_cash']
            totals['total_orders'] += metrics['total_orders']
            
            current_date += timedelta(days=1)
        
        # Calculer les pourcentages sur la période
        totals['cogs_percent'] = round((totals['cogs'] / totals['ca_ventes'] * 100) if totals['ca_ventes'] > 0 else 0, 1)
        totals['labor_percent'] = round((totals['labor_cost'] / totals['ca_ventes'] * 100) if totals['ca_ventes'] > 0 else 0, 1)
        totals['margin_percent'] = round((totals['marge_nette'] / totals['ca_ventes'] * 100) if totals['ca_ventes'] > 0 else 0, 1)
        
        # Arrondir les totaux
        for key in ['ca_ventes', 'cogs', 'labor_cost', 'marge_nette', 'encaissement', 'ecart_cash']:
            totals[key] = round(totals[key], 2)
        
        # Préparer les données pour les graphiques
        chart_data = {
            'labels': [d['date'].strftime('%d/%m') for d in daily_data],
            'ca_ventes': [d['ca_ventes'] for d in daily_data],
            'encaissement': [d['encaissement'] for d in daily_data],
            'marge_nette': [d['marge_nette'] for d in daily_data],
            'ecart_cash': [d['ecart_cash'] for d in daily_data]
        }
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'daily_data': daily_data,
            'totals': totals,
            'chart_data': chart_data,
            'days_count': len(daily_data)
        }

