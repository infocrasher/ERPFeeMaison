from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from flask_login import UserMixin
from extensions import db

# Import de la table de liaison depuis employees
from app.employees.models import order_employees
from app.deliverymen.models import Deliveryman

CONVERSION_FACTORS = {
    'kg_g': 1000, 'g_kg': 0.001,
    'l_ml': 1000, 'ml_l': 0.001,
}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# ... autres modèles ...

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_type = db.Column(db.String(50), nullable=False, default='customer_order')
    customer_name = db.Column(db.String(200))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    delivery_option = db.Column(db.String(20), default='pickup')
    due_date = db.Column(db.DateTime, nullable=False)
    delivery_cost = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(50), default='pending', index=True)
    notes = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ajout du champ livreur
    deliveryman_id = db.Column(db.Integer, db.ForeignKey('deliverymen.id'), nullable=True)
    deliveryman = db.relationship('Deliveryman', backref='orders')

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    produced_by = db.relationship('Employee', secondary=order_employees, back_populates='orders_produced')

    @property
    def order_date(self):
        return self.due_date
    
    @property
    def items_count(self):
        if hasattr(self.items, 'count'): return self.items.count()
        return len(self.items)

    def get_items_count(self):
        return self.items.count() if hasattr(self.items, 'count') else len(self.items)
    
    def get_items_total(self):
        return float(sum(item.subtotal for item in self.items))
    
    def get_producers_names(self):
        return [emp.name for emp in self.produced_by]
    
    def get_main_producer(self):
        return self.produced_by[0] if self.produced_by else None
    
    def assign_producer(self, employee):
        if employee not in self.produced_by:
            self.produced_by.append(employee)
    
    def remove_producer(self, employee):
        if employee in self.produced_by:
            self.produced_by.remove(employee)
    
    def get_order_type_display(self):
        order_types = {
            'customer_order': 'Commande Client',
            'counter_production_request': 'Ordre de Production',
            'in_store': 'Vente au Comptoir'
        }
        return order_types.get(self.order_type, self.order_type.title())
    
    def get_status_display(self):
        status_types = {
            'pending': 'En attente',
            'cancelled': 'Annulée',
            'completed': 'Terminée',
            'in_production': 'En production',
            'ready_at_shop': 'Reçue au magasin',
            'out_for_delivery': 'En livraison',
            'delivered': 'Livrée',
            'in_progress': 'En préparation',
            'ready': 'Prête',
            'awaiting_payment': 'En attente de paiement'
        }
        return status_types.get(self.status, self.status.title())
    
    def get_delivery_option_display(self):
        if not self.delivery_option:
            return "Non spécifié"
        delivery_options = {
            'pickup': 'Retrait en magasin',
            'delivery': 'Livraison à domicile'
        }
        return delivery_options.get(self.delivery_option, self.delivery_option.title())
    
    def get_status_color_class(self):
        status_colors = {
            'pending': 'secondary',
            'in_production': 'warning',
            'ready_at_shop': 'info',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger',
            'awaiting_payment': 'warning'
        }
        return status_colors.get(self.status, 'secondary')
    
    def should_appear_in_calendar(self):
        return self.status in ['pending', 'in_production']
    
    def can_be_received_at_shop(self):
        return self.status == 'in_production'
    
    def can_be_delivered(self):
        return self.status == 'ready_at_shop'
    
    def mark_as_in_production(self):
        if self.status == 'pending':
            self.status = 'in_production'
            return True
        return False
    
    def mark_as_received_at_shop(self):
        if self.status == 'in_production':
            self.status = 'ready_at_shop'
            self._increment_shop_stock_with_value()
            return True
        return False
    
    def mark_as_delivered(self):
        if self.status == 'ready_at_shop':
            self.status = 'delivered'
            self._decrement_stock_with_value_on_delivery()
            return True
        return False
    
    def _increment_shop_stock(self):
        """Méthode dépréciée. Utiliser _increment_shop_stock_with_value."""
        print("AVERTISSEMENT: _increment_shop_stock est dépréciée et ne met pas à jour la valeur du stock.")
        for item in self.items:
            if item.product:
                item.product.update_stock_by_location('stock_comptoir', float(item.quantity))
    # ... autres méthodes ...

    def calculate_total_amount(self):
        items_total = Decimal('0.0')
        for item in self.items:
            items_total += item.subtotal
        delivery_cost = Decimal(self.delivery_cost or 0)
        self.total_amount = items_total + delivery_cost
        return self.total_amount
    
    def get_items_subtotal(self):
        return sum(item.subtotal for item in self.items)
    
    def get_formatted_due_date(self):
        if self.due_date:
            return self.due_date.strftime('%d/%m/%Y à %H:%M')
        return "Non définie"
    
    def get_formatted_due_date_short(self):
        if self.due_date:
            return self.due_date.strftime('%d/%m à %H:%M')
        return "Non définie"
    
    def is_overdue(self):
        if not self.due_date: return False
        return self.due_date < datetime.utcnow() and self.status not in ['completed', 'cancelled', 'delivered']
    
    def get_priority_class(self):
        if self.is_overdue(): return 'danger'
        elif self.status == 'ready_at_shop': return 'success'
        elif self.status == 'in_production': return 'warning'
        return 'info'
    
    def __repr__(self):
        return f'<Order {self.id}: {self.customer_name or "Sans nom"}>'

# ... autres modèles ... 