from datetime import datetime, date, timedelta
from sqlalchemy import func, case
from extensions import db
from models import Order, OrderItem, Product
from app.employees.models import Employee, AttendanceSummary, AttendanceRecord
from app.sales.models import CashMovement
from app.purchases.models import Purchase
from app.inventory.models import DailyWaste

class RealKpiService:
    """
    Service pour calculer les KPIs 'Réels' basés sur:
    - CA au moment de la livraison (pour les commandes)
    - Coûts réels (Matière + Main d'oeuvre du jour)
    """

    @staticmethod
    def get_daily_kpis(target_date=None):
        if target_date is None:
            target_date = date.today()
        
        # 1. CA RÉALISÉ (POS + Livraisons du jour)
        # ----------------------------------------------------------------
        
        # A. Ventes POS (comptabilisées à la création)
        pos_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type == 'in_store',
                func.date(Order.created_at) == target_date
            ).scalar() or 0.0
            
        pos_count = db.session.query(func.count(Order.id))\
            .filter(
                Order.order_type == 'in_store',
                func.date(Order.created_at) == target_date
            ).scalar() or 0

        # B. Commandes Livrées/Terminées ce jour
        # IMPORTANT: Ne comptabiliser que les commandes créées ET livrées le même jour
        # Exclure les ordres de production (counter_production_request) qui ont montant=0
        shop_revenue = db.session.query(func.sum(Order.total_amount))\
            .filter(
                Order.order_type != 'in_store',
                Order.order_type != 'counter_production_request',  # Exclure les ordres de production
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.created_at) == target_date,  # Créée le jour J
                func.date(Order.due_date) == target_date  # Livrée le jour J
            ).scalar() or 0.0

        shop_count = db.session.query(func.count(Order.id))\
            .filter(
                Order.order_type != 'in_store',
                Order.order_type != 'counter_production_request',  # Exclure les ordres de production
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.created_at) == target_date,  # Créée le jour J
                func.date(Order.due_date) == target_date  # Livrée le jour J
            ).scalar() or 0
            
        total_revenue = float(pos_revenue) + float(shop_revenue)
        
        # 2. COGS (Coût des ventes)
        # ----------------------------------------------------------------
        
        # A. Coût Matière (Ingrédients des produits vendus/livrés ce jour)
        # On doit récupérer tous les items des commandes concernées
        
        # Identifiants des commandes POS du jour
        pos_order_ids = db.session.query(Order.id).filter(
            Order.order_type == 'in_store',
            func.date(Order.created_at) == target_date
        ).all()
        pos_ids = [r[0] for r in pos_order_ids]
        
        # Identifiants des commandes Shop créées ET livrées ce jour (exclure ordres de production)
        shop_order_ids = db.session.query(Order.id).filter(
            Order.order_type != 'in_store',
            Order.order_type != 'counter_production_request',  # Exclure les ordres de production
            Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
            func.date(Order.created_at) == target_date,  # Créée le jour J
            func.date(Order.due_date) == target_date  # Livrée le jour J
        ).all()
        shop_ids = [r[0] for r in shop_order_ids]
        
        all_order_ids = pos_ids + shop_ids
        
        cogs_ingredients = 0.0
        if all_order_ids:
            # Somme (Quantité * Cost Price du produit)
            # Note: Idéalement cost_price historique, mais ici cost_price actuel
            cogs_query = db.session.query(
                func.sum(OrderItem.quantity * Product.cost_price)
            ).join(Product, OrderItem.product_id == Product.id)\
             .filter(OrderItem.order_id.in_(all_order_ids))
            
            cogs_ingredients = cogs_query.scalar() or 0.0

        # B. Coût Main d'Oeuvre (Labor Cost)
        # Basé sur les présences du jour (Temps Réel)
        labor_cost = 0.0
        
        # On utilise get_daily_summary pour avoir les heures calculées à la volée
        # au lieu de AttendanceSummary qui peut être vide
        daily_attendance = AttendanceRecord.get_daily_summary(target_date)
        
        for emp_data in daily_attendance.values():
            emp = emp_data['employee']
            hours = float(emp_data['total_hours'] or 0)
            
            if not emp or hours <= 0:
                continue
                
            # Calcul du taux horaire
            if emp.hourly_rate and emp.hourly_rate > 0:
                rate = float(emp.hourly_rate)
            elif emp.salaire_fixe and emp.salaire_fixe > 0:
                # Estimation: Salaire / 208 heures (26 jours * 8h)
                rate = float(emp.salaire_fixe) / 208.0
            else:
                rate = 0.0
            
            labor_cost += (hours * rate)
            
        total_cogs = float(cogs_ingredients) + labor_cost
        
        # 3. MARGE NETTE
        # ----------------------------------------------------------------
        net_margin = total_revenue - total_cogs
        margin_percent = (net_margin / total_revenue * 100) if total_revenue > 0 else 0.0

        # 4. AUTRES KPIS
        # ----------------------------------------------------------------
        
        # Ticket Moyen
        avg_ticket_pos = (float(pos_revenue) / pos_count) if pos_count > 0 else 0.0
        avg_ticket_shop = (float(shop_revenue) / shop_count) if shop_count > 0 else 0.0
        
        # Sorties de Caisse
        cash_out = db.session.query(func.sum(CashMovement.amount))\
            .filter(
                func.lower(CashMovement.type).in_(['sortie', 'retrait', 'paiement']),
                func.date(CashMovement.created_at) == target_date
            ).scalar() or 0.0
            
        # Valeur Achat du Jour
        purchases_today = db.session.query(func.sum(Purchase.total_amount))\
            .filter(func.date(Purchase.created_at) == target_date)\
            .scalar() or 0.0

        # Dette Livreur du Jour (Reste à payer sur les commandes livrées ce jour)
        # On prend les commandes Shop livrées ce jour (due_date) et on somme le reste à payer
        # (total_amount - amount_paid)
        delivery_debt = 0.0
        shop_orders_debt = db.session.query(Order.total_amount, Order.amount_paid)\
            .filter(
                Order.order_type != 'in_store',
                Order.order_type != 'counter_production_request',  # Exclure les ordres de production
                Order.status.in_(['delivered', 'completed', 'delivered_unpaid']),
                func.date(Order.created_at) == target_date,  # Créée le jour J
                func.date(Order.due_date) == target_date  # Livrée le jour J
            ).all()
            
        for o_total, o_paid in shop_orders_debt:
            debt = float(o_total or 0) - float(o_paid or 0)
            if debt > 0:
                delivery_debt += debt
            
        return {
            'revenue': {
                'total': round(total_revenue, 2),
                'pos': round(float(pos_revenue), 2),
                'shop': round(float(shop_revenue), 2)
            },
            'counts': {
                'pos': pos_count,
                'shop': shop_count,
                'total': pos_count + shop_count
            },
            'cogs': {
                'total': round(total_cogs, 2),
                'ingredients': round(float(cogs_ingredients), 2),
                'labor': round(labor_cost, 2)
            },
            'margin': {
                'net': round(net_margin, 2),
                'percent': round(margin_percent, 1)
            },
            'avg_ticket': {
                'pos': round(avg_ticket_pos, 2),
                'shop': round(avg_ticket_shop, 2)
            },
            'cash': {
                'out': round(float(cash_out), 2)
            },
            'purchases': {
                'today': round(float(purchases_today), 2)
            },
            'delivery_debt': round(delivery_debt, 2)
        }
