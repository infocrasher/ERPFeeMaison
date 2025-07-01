from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from flask_login import UserMixin
from extensions import db

# Import de la table de liaison depuis employees
from app.employees.models import order_employees

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

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    product_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 4))
    unit = db.Column(db.String(20), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    quantity_in_stock = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock_comptoir = db.Column(db.Float, default=0.0, nullable=False)
    stock_ingredients_local = db.Column(db.Float, default=0.0, nullable=False) 
    stock_ingredients_magasin = db.Column(db.Float, default=0.0, nullable=False)
    stock_consommables = db.Column(db.Float, default=0.0, nullable=False)
    
    total_stock_value = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')

    seuil_min_comptoir = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_local = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_magasin = db.Column(db.Float, default=0.0)
    seuil_min_consommables = db.Column(db.Float, default=0.0)
    
    last_stock_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    valeur_stock_ingredients_magasin = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    valeur_stock_ingredients_local = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')

    image_filename = db.Column(db.String(255), nullable=True)

    @property
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'product_type': self.product_type,
            'unit': self.unit,
            'cost_price': float(self.cost_price) if self.cost_price is not None else 0.0,
            'stock_ingredients_magasin': float(self.stock_ingredients_magasin) if self.stock_ingredients_magasin is not None else 0.0,
        }
    
    @property
    def total_stock_all_locations(self):
        return (self.stock_comptoir + self.stock_ingredients_local + 
                self.stock_ingredients_magasin + self.stock_consommables)
    
    @property
    def stock_value_total(self):
        cost = self.cost_price or 0.0
        return float(self.total_stock_all_locations) * float(cost)
    
    def get_stock_by_location_type(self, location_type):
        location_mapping = {
            'comptoir': self.stock_comptoir,
            'ingredients_local': self.stock_ingredients_local,
            'ingredients_magasin': self.stock_ingredients_magasin,
            'consommables': self.stock_consommables
        }
        return location_mapping.get(location_type, 0.0)
    
    def get_seuil_min_by_location(self, location_type):
        seuil_mapping = {
            'comptoir': self.seuil_min_comptoir or 0.0,
            'ingredients_local': self.seuil_min_ingredients_local or 0.0,
            'ingredients_magasin': self.seuil_min_ingredients_magasin or 0.0,
            'consommables': self.seuil_min_consommables or 0.0
        }
        return seuil_mapping.get(location_type, 0.0)
    
    def is_low_stock_by_location(self, location_type):
        current_stock = self.get_stock_by_location_type(location_type)
        min_threshold = self.get_seuil_min_by_location(location_type)
        return current_stock <= min_threshold
    
    def get_low_stock_locations(self):
        locations = ['comptoir', 'ingredients_local', 'ingredients_magasin', 'consommables']
        return [loc for loc in locations if self.is_low_stock_by_location(loc)]
    
    def get_location_display_name(self, location_type):
        names = {
            'comptoir': 'Stock Vente',
            'ingredients_local': 'Labo B',
            'ingredients_magasin': 'Labo A (Réserve)',
            'consommables': 'Stock Consommables'
        }
        return names.get(location_type, location_type.title())

    def update_stock_location(self, location_type, quantity_change):
        return self.update_stock_by_location(location_type, quantity_change)

    def get_stock_by_location(self, location_key: str) -> float:
        return getattr(self, location_key, 0.0)

    def update_stock_by_location(self, location_key: str, quantity_change: float) -> bool:
        """Met à jour le stock d'un produit à un emplacement spécifique"""
        if location_key == 'stock_ingredients_magasin':
            current_value = self.stock_ingredients_magasin or 0.0
            self.stock_ingredients_magasin = max(0, current_value + quantity_change)
        elif location_key == 'stock_ingredients_local':
            current_value = self.stock_ingredients_local or 0.0
            self.stock_ingredients_local = max(0, current_value + quantity_change)
        elif location_key == 'stock_comptoir':
            current_value = self.stock_comptoir or 0.0
            self.stock_comptoir = max(0, current_value + quantity_change)
        elif location_key == 'stock_consommables':
            current_value = self.stock_consommables or 0.0
            self.stock_consommables = max(0, current_value + quantity_change)
        else:
            return False
        
        self.last_stock_update = datetime.utcnow()
        return True

    def get_stock_display(self, location_type='total'):
        stock_value = 0
        if location_type == 'total':
            stock_value = self.total_stock_all_locations
        else:
            stock_value = self.get_stock_by_location_type(location_type)
        display_unit = self.unit.lower()
        base_unit = self.base_unit_for_recipes()
        if stock_value == 0:
            return f"0 {display_unit.upper()}"
        try:
            if display_unit == 'kg' and base_unit == 'g':
                display_value = stock_value / 1000
                return f"{display_value:,.3f} kg".replace(",", " ").replace(".", ",")
            if display_unit == 'l' and base_unit == 'ml':
                display_value = stock_value / 1000
                return f"{display_value:,.3f} L".replace(",", " ").replace(".", ",")
            return f"{int(stock_value)} {display_unit}"
        except Exception:
            return f"{stock_value} {base_unit} (brut)"

    def base_unit_for_recipes(self):
        unit_lower = self.unit.lower()
        if unit_lower in ['kg', 'g', 'mg']:
            return 'g'
        if unit_lower in ['l', 'cl', 'ml']:
            return 'ml'
        return unit_lower
    
    def __repr__(self):
        return f'<Product {self.name}>'

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_needed = db.Column(db.Numeric(10, 3), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='recipe_uses')
    
    def _convert_unit_cost(self):
        if not self.product or not self.product.cost_price:
            return Decimal('0.0')
        product_unit = self.product.unit.upper()
        recipe_unit = self.unit.upper()
        base_cost = Decimal(self.product.cost_price)
        if product_unit == recipe_unit:
            return base_cost
        conversions = {
            ('KG', 'G'): base_cost / 1000,
            ('L', 'ML'): base_cost / 1000,
            ('G', 'KG'): base_cost * 1000,
            ('ML', 'L'): base_cost * 1000,
            ('KG', 'MG'): base_cost / 1000000,
            ('L', 'CL'): base_cost / 100,
        }
        conversion_key = (product_unit, recipe_unit)
        if conversion_key in conversions:
            return conversions[conversion_key]
        print(f"⚠️ Conversion non trouvée: {product_unit} → {recipe_unit} pour {self.product.name}")
        return base_cost
    
    @property
    def cost(self):
        if not self.product or not self.product.cost_price:
            return Decimal('0.0')
        converted_cost_per_unit = self._convert_unit_cost()
        return Decimal(self.quantity_needed) * converted_cost_per_unit
    
    def __repr__(self):
        return f'<RecipeIngredient {self.recipe.name} - {self.product.name}>'
    
class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, unique=True)
    yield_quantity = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    yield_unit = db.Column(db.String(50), nullable=False, default='pièces', server_default='pièces')
    preparation_time = db.Column(db.Integer)
    cooking_time = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    production_location = db.Column(
        db.String(50), 
        nullable=False, 
        default='ingredients_magasin', 
        server_default='ingredients_magasin'
    )
    
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    finished_product = db.relationship('Product', foreign_keys=[product_id], backref=db.backref('recipe_definition', uselist=False))
    
    @property
    def total_cost(self):
        return sum(ing.cost for ing in self.ingredients)
    
    @property
    def cost_per_unit(self):
        return self.total_cost / Decimal(self.yield_quantity) if self.yield_quantity > 0 else Decimal('0.0')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

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

    def _increment_shop_stock_with_value(self):
        """
        Incrémente le stock comptoir ET sa valeur pour les produits finis.
        Calcule aussi le PMP du produit fini.
        """
        from extensions import db
        for item in self.items:
            product_fini = item.product
            if product_fini and product_fini.recipe_definition:
                # 1. Incrémenter la quantité en stock comptoir
                quantity_to_increment = float(item.quantity)
                product_fini.update_stock_by_location('stock_comptoir', quantity_to_increment)
                
                # 2. Calculer la valeur à ajouter (basée sur le coût de production)
                cost_per_unit = product_fini.recipe_definition.cost_per_unit
                value_to_increment = cost_per_unit * Decimal(str(quantity_to_increment))
                
                # 3. Incrémenter la valeur totale du stock
                product_fini.total_stock_value = (product_fini.total_stock_value or Decimal('0.0')) + value_to_increment
                
                # 4. Recalculer le PMP du produit fini
                new_total_stock_qty = Decimal(str(product_fini.total_stock_all_locations))
                if new_total_stock_qty > 0:
                    product_fini.cost_price = product_fini.total_stock_value / new_total_stock_qty
                
                db.session.add(product_fini)
                print(f"INCREMENT COMPTOIR: {quantity_to_increment} {product_fini.unit} de {product_fini.name} (Valeur: {value_to_increment:.2f} DA)")

    def _decrement_stock_with_value_on_delivery(self):
        """
        Décrémente le stock de vente (comptoir) ET sa valeur correspondante lors d'une vente.
        """
        for item in self.items:
            product_fini = item.product
            if product_fini:
                # 1. On décrémente la quantité en stock
                quantity_to_decrement = float(item.quantity)
                product_fini.update_stock_by_location('stock_comptoir', -quantity_to_decrement)

                # 2. On calcule la valeur de ce qui a été vendu en se basant sur le PMP du produit fini
                pmp_produit_fini = product_fini.cost_price or Decimal('0.0')
                value_to_decrement = Decimal(quantity_to_decrement) * pmp_produit_fini

                # 3. On décrémente la valeur totale du stock du produit
                product_fini.total_stock_value = (product_fini.total_stock_value or Decimal('0.0')) - value_to_decrement

                # Le PMP du produit fini ne change pas lors d'une sortie de stock.
    
    def decrement_ingredients_stock_on_production(self):
        """
        Décrémente le stock des ingrédients lors de la production d'un produit fini,
        en tenant compte du rendement de la recette (yield_quantity).
        """
        for item in self.items:
            product_fini = item.product
            if product_fini and product_fini.recipe_definition:
                recipe = product_fini.recipe_definition
                labo_key = recipe.production_location
                # Pour chaque ingrédient de la recette
                for ingredient_in_recipe in recipe.ingredients:
                    ingredient_product = ingredient_in_recipe.product
                    if not ingredient_product:
                        continue
                    # Quantité d'ingrédient par unité produite
                    qty_per_unit = float(ingredient_in_recipe.quantity_needed) / float(recipe.yield_quantity)
                    # Quantité totale à décrémenter pour la production réelle
                    needed_qty = qty_per_unit * float(item.quantity)
                    # Mapping de la localisation
                    location_map = {
                        "ingredients_magasin": "stock_ingredients_magasin",
                        "ingredients_local": "stock_ingredients_local"
                    }
                    stock_attr = location_map.get(labo_key, labo_key)
                    # Décrémentation du stock
                    ingredient_product.update_stock_by_location(stock_attr, -needed_qty)
                    # Log/debug
                    print(f"Décrémentation: {ingredient_product.name} - {needed_qty:.3f} {ingredient_in_recipe.unit} (stock: {stock_attr})")

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

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_subtotal(self):
        return float(Decimal(self.quantity) * Decimal(self.unit_price))
    
    @property
    def price_at_order(self):
        return self.unit_price
    
    @property
    def subtotal(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)
    
    def get_formatted_subtotal(self):
        return f"{self.subtotal:.2f} DA"
    
    def get_formatted_unit_price(self):
        return f"{self.unit_price:.2f} DA"
    
    def get_formatted_quantity(self):
        if self.quantity == int(self.quantity): return str(int(self.quantity))
        return f"{self.quantity:.2f}"
    
    def __repr__(self):
        return f'<OrderItem {self.product.name if self.product else "N/A"}: {self.quantity}x{self.unit_price}>'

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    base_unit = db.Column(db.String(10), nullable=False)
    conversion_factor = db.Column(db.Numeric(10, 3), nullable=False)
    unit_type = db.Column(db.String(20), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'base_unit': self.base_unit,
            'conversion_factor': float(self.conversion_factor),
            'unit_type': self.unit_type,
            'display_order': self.display_order
        }
    
    def __repr__(self):
        return f'<Unit {self.name}>'
    
    def to_base_unit(self, quantity):
        return float(quantity) * float(self.conversion_factor)
    
    def from_base_unit(self, base_quantity):
        return float(base_quantity) / float(self.conversion_factor)
    
    @property
    def display_name(self):
        return f"{self.name} ({self.unit_type})"

class DeliveryDebt(db.Model):
    __tablename__ = 'delivery_debts'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    deliveryman_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_register_session.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    order = db.relationship('Order', backref='delivery_debts')
    deliveryman = db.relationship('Employee', backref='delivery_debts')
    session = db.relationship('CashRegisterSession', backref='delivery_debts')
    
    def __repr__(self):
        return f'<DeliveryDebt {self.id} - Order {self.order_id} - Livreur {self.deliveryman_id}>'