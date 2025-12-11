from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
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

class Profile(db.Model):
    """Profils utilisateurs avec permissions granulaires"""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Permissions stockées en JSON
    # Format: {"ventes_pos": true, "caisse_ouverture": true, ...}
    permissions = db.Column(db.JSON, nullable=False, default=dict)
    
    # Relations
    users = db.relationship('User', backref='profile', lazy='dynamic')
    
    def has_permission(self, permission_key):
        """Vérifie si le profil a une permission spécifique"""
        return self.permissions.get(permission_key, False)
    
    def __repr__(self):
        return f'<Profile {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # Conservé pour compatibilité
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est admin (via role ou profil)"""
        if self.role == 'admin':
            return True
        if self.profile and self.profile.name.lower() == 'admin':
            return True
        return False
    
    def has_permission(self, permission_key):
        """Vérifie si l'utilisateur a une permission via son profil"""
        # Admin a tous les accès
        if self.is_admin:
            return True
        # Vérifier via profil
        if self.profile:
            return self.profile.has_permission(permission_key)
        # Fallback : vérifier via role (compatibilité)
        return False
    
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
    show_in_pos = db.Column(db.Boolean, default=True, nullable=False, server_default='true')
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
    value_deficit_total = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')

    seuil_min_comptoir = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_local = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_magasin = db.Column(db.Float, default=0.0)
    seuil_min_consommables = db.Column(db.Float, default=0.0)
    
    last_stock_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    valeur_stock_ingredients_magasin = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    valeur_stock_ingredients_local = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    valeur_stock_comptoir = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    valeur_stock_consommables = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    deficit_stock_ingredients_magasin = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    deficit_stock_ingredients_local = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    deficit_stock_comptoir = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')
    deficit_stock_consommables = db.Column(db.Numeric(12, 4), nullable=False, default=0.0, server_default='0.0')

    image_filename = db.Column(db.String(255), nullable=True)
    
    # Gestion de la péremption
    shelf_life_days = db.Column(db.Integer, nullable=True)  # Durée de conservation en jours
    requires_expiry_tracking = db.Column(db.Boolean, default=False)  # Suivi de péremption requis
    
    # Peut être vendu directement (pour ingrédients et consommables)
    can_be_sold = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    
    # Peut être acheté directement (pour produits finis)
    # Exemple: tartes préparées en interne mais parfois achetées quand pas le temps
    can_be_purchased = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    
    # Unité de vente (peut être différente de l'unité de base)
    # Exemple: unit='g' (base) mais sale_unit='kg' (vente)
    # Si None, utilise 'unit' par défaut
    sale_unit = db.Column(db.String(20), nullable=True)
    
    @property
    def display_sale_unit(self):
        """Retourne l'unité de vente à afficher (sale_unit ou unit par défaut)"""
        return self.sale_unit or self.unit

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

    def update_stock_by_location(self, location_key: str, quantity_change: float, unit_cost_override=None) -> bool:
        """
        Met à jour le stock d'un produit à un emplacement spécifique ainsi que la valorisation associée.
        Autorise les stocks négatifs mais conserve une valorisation cohérente grâce à un déficit de valeur
        (consommation à découvert) qui sera résorbé lors des prochaines entrées.
        """
        from flask import current_app
        import traceback
        
        location_mappings = {
            'stock_ingredients_magasin': ('stock_ingredients_magasin', 'valeur_stock_ingredients_magasin', 'deficit_stock_ingredients_magasin'),
            'stock_ingredients_local': ('stock_ingredients_local', 'valeur_stock_ingredients_local', 'deficit_stock_ingredients_local'),
            'stock_comptoir': ('stock_comptoir', 'valeur_stock_comptoir', 'deficit_stock_comptoir'),
            'stock_consommables': ('stock_consommables', 'valeur_stock_consommables', 'deficit_stock_consommables')
        }
        
        mapping = location_mappings.get(location_key)
        if not mapping:
            return False
        
        qty_attr, value_attr, deficit_attr = mapping
        
        # TRACE: Si on modifie stock_comptoir, logger
        if qty_attr == 'stock_comptoir':
            old_stock_comptoir = float(getattr(self, 'stock_comptoir', 0.0))
            stack = traceback.extract_stack()
            caller = stack[-2] if len(stack) >= 2 else stack[-1] if stack else None
            caller2 = stack[-3] if len(stack) >= 3 else None
            caller3 = stack[-4] if len(stack) >= 4 else None
            current_app.logger.error(f"🚨 TRACE update_stock_by_location - stock_comptoir modifié! Produit: {self.name} (ID: {self.id}), Location: {location_key}, Changement: {quantity_change}, Avant: {old_stock_comptoir}")
            current_app.logger.error(f"🚨 Appelant direct: {caller.filename if caller else 'unknown'}:{caller.lineno if caller else 0} - {caller.name if caller else 'unknown'}")
            if caller2:
                current_app.logger.error(f"🚨 Appelant niveau 2: {caller2.filename}:{caller2.lineno} - {caller2.name}")
            if caller3:
                current_app.logger.error(f"🚨 Appelant niveau 3: {caller3.filename}:{caller3.lineno} - {caller3.name}")
            current_app.logger.error(f"🚨 Code appelant: {caller.line if caller else 'unknown'}")
            print(f"🚨🚨🚨 MODIFICATION STOCK_COMPTOIR DÉTECTÉE! Produit: {self.name} (ID: {self.id}), Changement: {quantity_change}, Avant: {old_stock_comptoir}")
        
        if unit_cost_override is not None:
            unit_cost = Decimal(str(unit_cost_override))
        else:
            unit_cost = Decimal(str(self.cost_price or 0.0))
        qty_change = Decimal(str(quantity_change))
        
        current_qty = Decimal(str(getattr(self, qty_attr) or 0.0))
        new_qty = current_qty + qty_change
        setattr(self, qty_attr, float(new_qty))
        
        # TRACE: Si on a modifié stock_comptoir, vérifier la nouvelle valeur
        if qty_attr == 'stock_comptoir':
            new_stock_comptoir = float(getattr(self, 'stock_comptoir', 0.0))
            current_app.logger.warning(f"TRACE update_stock_by_location - stock_comptoir APRÈS modification! Produit: {self.name} (ID: {self.id}), Avant: {old_stock_comptoir}, Après: {new_stock_comptoir}")
        
        current_value = Decimal(str(getattr(self, value_attr) or 0.0))
        current_deficit = Decimal(str(getattr(self, deficit_attr) or 0.0))
        total_value = Decimal(str(self.total_stock_value or 0.0))
        total_deficit = Decimal(str(self.value_deficit_total or 0.0))
        
        def q(value: Decimal) -> Decimal:
            return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        if qty_change < 0:
            requested = abs(qty_change)
            available_qty = max(Decimal('0'), current_qty)
            qty_from_stock = min(requested, available_qty)
            shortage_qty = requested - qty_from_stock
            
            if qty_from_stock > 0:
                value_to_remove = q(qty_from_stock * unit_cost)
                value_to_remove = min(value_to_remove, current_value)
                current_value -= value_to_remove
                total_value = max(Decimal('0'), total_value - value_to_remove)
            
            if shortage_qty > 0:
                value_shortage = q(shortage_qty * unit_cost)
                current_deficit += value_shortage
                total_deficit += value_shortage
        
        elif qty_change > 0:
            value_increase = q(qty_change * unit_cost)
            
            if current_deficit > 0 and value_increase > 0:
                applied_to_deficit = min(value_increase, current_deficit)
                current_deficit -= applied_to_deficit
                value_increase -= applied_to_deficit
                total_deficit = max(Decimal('0'), total_deficit - applied_to_deficit)
            
            if value_increase > 0:
                current_value += value_increase
                total_value += value_increase
        # qty_change == 0 → pas de variation de valeur
        
        setattr(self, value_attr, q(max(Decimal('0'), current_value)))
        setattr(self, deficit_attr, q(max(Decimal('0'), current_deficit)))
        self.total_stock_value = q(max(Decimal('0'), total_value))
        self.value_deficit_total = q(max(Decimal('0'), total_deficit))
        self.last_stock_update = datetime.utcnow()
        return True

    def get_stock_display(self, location_type='total'):
        stock_value = 0
        if location_type == 'total':
            stock_value = self.total_stock_all_locations
        else:
            stock_value = self.get_stock_by_location_type(location_type)
        
        return self.format_quantity_display(stock_value)
    
    def format_quantity_display(self, quantity):
        """Formate une quantité donnée pour l'affichage avec conversion automatique"""
        display_unit = self.unit.lower() if self.unit else 'unité'
        base_unit = self.base_unit_for_recipes()
        
        if quantity == 0:
            return f"0 {display_unit}"
        
        try:
            # Auto-conversion pour les grammes >= 1000 → kg
            if display_unit == 'g' and quantity >= 1000:
                display_value = quantity / 1000
                return f"{display_value:,.3f} kg".replace(",", " ").replace(".", ",")
            
            # Auto-conversion pour les millilitres >= 1000 → L
            elif display_unit == 'ml' and quantity >= 1000:
                display_value = quantity / 1000
                return f"{display_value:,.3f} L".replace(",", " ").replace(".", ",")
            
            # Cas spécial pour kg (déjà en kg, pas de conversion)
            elif display_unit == 'kg':
                display_value = quantity / 1000  # Stock est en grammes, afficher en kg
                return f"{display_value:,.3f} kg".replace(",", " ").replace(".", ",")
            
            # Cas spécial pour L (déjà en L, pas de conversion)
            elif display_unit == 'l':
                display_value = quantity / 1000  # Stock est en ml, afficher en L
                return f"{display_value:,.3f} L".replace(",", " ").replace(".", ",")
            
            # Pour les autres unités (pièce, unité, etc.)
            else:
                return f"{int(quantity)} {display_unit}"
                
        except Exception as e:
            return f"{quantity} {base_unit} (erreur)"

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
    
    # Client (nouvelle approche centralisée)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)  # Nullable pour compatibilité
    
    # Informations client (ancien système - gardé pour compatibilité)
    customer_name = db.Column(db.String(200))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    delivery_option = db.Column(db.String(20), default='pickup')
    due_date = db.Column(db.DateTime, nullable=False)
    delivery_cost = db.Column(db.Numeric(10, 2), default=0.0)
    delivery_zone = db.Column(db.String(100), nullable=True)  # Commune / zone de livraison
    deliveryman_id = db.Column(db.Integer, db.ForeignKey('deliverymen.id'), nullable=True)  # Champ livreur
    status = db.Column(db.String(50), default='pending', index=True)
    notes = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    amount_paid = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    payment_paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    produced_by = db.relationship('Employee', secondary=order_employees, back_populates='orders_produced')
    deliveryman = db.relationship('Deliveryman', backref='orders')
    
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
            'waiting_for_pickup': 'En attente de retrait',
            'out_for_delivery': 'En livraison',
            'delivered': 'Livrée',
            'delivered_unpaid': 'Livrée Non Payé',
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
            'waiting_for_pickup': 'primary',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'delivered_unpaid': 'warning',
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
            # Distinguer les ordres de production pour le comptoir des commandes client
            if self.order_type == 'counter_production_request':
                # Ordre de production : incrémenter le stock_comptoir (disponible à la vente)
                self._increment_shop_stock_with_value()
            else:
                # Commande client : mettre à jour uniquement la valeur (pas le stock_comptoir car réservé)
                self._increment_stock_value_only_for_customer_order()
            return True
        return False
    
    def mark_as_delivered(self):
        if self.status == 'ready_at_shop':
            self.status = 'delivered'
            # Distinguer les commandes client des autres types
            if self.order_type == 'customer_order':
                # Commande client : ne pas décrémenter stock_comptoir car il n'a jamais été incrémenté
                # Juste mettre à jour la valeur comptable (déjà fait lors de la production)
                # Pas besoin de décrémenter car le stock était réservé, pas disponible
                pass
            else:
                # Autres types (in_store, etc.) : décrémenter le stock_comptoir
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
        UTILISÉ UNIQUEMENT POUR LES ORDRES DE PRODUCTION POUR LE COMPTOIR.
        
        IMPORTANT: On utilise unit_cost_override pour que update_stock_by_location
        utilise le coût de la recette (et non le cost_price actuel du produit).
        Cela évite la double comptabilisation et garantit la cohérence entre
        valeur_stock_comptoir et total_stock_value.
        """
        from extensions import db
        for item in self.items:
            product_fini = item.product
            if product_fini and product_fini.recipe_definition:
                # 1. Calculer le coût unitaire basé sur la recette
                cost_per_unit = product_fini.recipe_definition.cost_per_unit
                quantity_to_increment = float(item.quantity)
                
                # 2. Incrémenter le stock comptoir avec le coût de la recette
                # unit_cost_override garantit que la valeur ajoutée est basée sur le coût de production
                product_fini.update_stock_by_location(
                    'stock_comptoir', 
                    quantity_to_increment,
                    unit_cost_override=float(cost_per_unit)
                )
                
                # 3. Recalculer le PMP du produit fini
                # total_stock_value et valeur_stock_comptoir sont déjà mis à jour par update_stock_by_location
                new_total_stock_qty = Decimal(str(product_fini.total_stock_all_locations))
                if new_total_stock_qty > 0:
                    product_fini.cost_price = product_fini.total_stock_value / new_total_stock_qty
                
                db.session.add(product_fini)
                value_added = cost_per_unit * Decimal(str(quantity_to_increment))
                print(f"INCREMENT COMPTOIR: {quantity_to_increment} {product_fini.unit} de {product_fini.name} (Valeur: {value_added:.2f} DA)")
    
    def _increment_stock_value_only_for_customer_order(self):
        """
        Met à jour uniquement la valeur du stock pour les commandes client.
        N'incrémente PAS le stock_comptoir car les produits sont réservés pour le client.
        Utilisé pour la comptabilité et le calcul du PMP, mais pas pour le stock disponible.
        """
        from extensions import db
        from flask import current_app
        import traceback
        
        for item in self.items:
            product_fini = item.product
            if not product_fini:
                continue
                
            quantity = float(item.quantity)
            
            # IMPORTANT: Sauvegarder le stock_comptoir AVANT toute modification
            stock_comptoir_avant = float(product_fini.stock_comptoir or 0.0)
            current_app.logger.info(f"TRACE - Commande #{self.id} - Produit {product_fini.name} (ID: {product_fini.id}) - Stock comptoir AVANT: {stock_comptoir_avant}")
            
            value_to_increment = Decimal('0.0')
            
            # Calculer la valeur à ajouter
            if product_fini.recipe_definition:
                # Produit avec recette : utiliser le coût de production
                cost_per_unit = product_fini.recipe_definition.cost_per_unit
                value_to_increment = cost_per_unit * Decimal(str(quantity))
            elif product_fini.cost_price:
                # Produit sans recette : utiliser le PMP existant
                value_to_increment = product_fini.cost_price * Decimal(str(quantity))
            else:
                # Pas de coût disponible : valeur à 0
                value_to_increment = Decimal('0.0')
            
            # Vérifier le stock_comptoir avant modification de total_stock_value
            stock_comptoir_apres_total_stock = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres_total_stock:
                current_app.logger.error(f"TRACE - Stock comptoir modifié APRÈS lecture initiale! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres_total_stock}")
            
            # Incrémenter la valeur totale du stock (pour la comptabilité)
            product_fini.total_stock_value = (product_fini.total_stock_value or Decimal('0.0')) + value_to_increment
            
            # Vérifier le stock_comptoir après modification de total_stock_value
            stock_comptoir_apres_total_stock = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres_total_stock:
                current_app.logger.error(f"TRACE - Stock comptoir modifié APRÈS modification total_stock_value! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres_total_stock}")
                stack = traceback.format_stack()
                current_app.logger.error(f"TRACE - Stack: {''.join(stack)}")
            
            # Recalculer le PMP du produit fini
            # IMPORTANT: Pour les commandes client, on ne doit PAS inclure le stock_comptoir
            # dans le calcul du PMP car ces produits sont réservés, pas disponibles à la vente
            # On calcule le stock total SANS le stock_comptoir pour le PMP
            stock_sans_comptoir = (
                Decimal(str(product_fini.stock_ingredients_local or 0.0)) +
                Decimal(str(product_fini.stock_ingredients_magasin or 0.0)) +
                Decimal(str(product_fini.stock_consommables or 0.0))
            )
            # Pour les commandes client, on ajoute la quantité produite (réservée) au calcul
            # mais on ne l'ajoute PAS au stock_comptoir
            stock_pour_pmp = stock_sans_comptoir + Decimal(str(quantity))
            
            # Vérifier le stock_comptoir avant modification de cost_price
            stock_comptoir_apres_calc_pmp = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres_calc_pmp:
                current_app.logger.error(f"TRACE - Stock comptoir modifié APRÈS calcul PMP (avant modification cost_price)! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres_calc_pmp}")
            
            if stock_pour_pmp > 0:
                product_fini.cost_price = product_fini.total_stock_value / stock_pour_pmp
            
            # Vérifier le stock_comptoir après modification de cost_price
            stock_comptoir_apres_cost_price = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres_cost_price:
                current_app.logger.error(f"TRACE - Stock comptoir modifié APRÈS modification cost_price! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres_cost_price}")
                stack = traceback.format_stack()
                current_app.logger.error(f"TRACE - Stack: {''.join(stack)}")
            
            # VÉRIFICATION CRITIQUE: Le stock_comptoir ne doit PAS avoir changé
            stock_comptoir_apres = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres:
                error_msg = f"ERREUR CRITIQUE: Stock comptoir modifié lors de la réception d'une commande client! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres}, Produit: {product_fini.name}, Commande: #{self.id}"
                current_app.logger.error(error_msg)
                stack = traceback.format_stack()
                current_app.logger.error(f"TRACE - Stack complète: {''.join(stack)}")
                print(f"❌ {error_msg}")
                # Restaurer le stock_comptoir à sa valeur d'origine
                product_fini.stock_comptoir = stock_comptoir_avant
            
            # NE PAS incrémenter stock_comptoir car c'est réservé pour le client
            db.session.add(product_fini)
            
            # Vérifier le stock_comptoir après db.session.add
            stock_comptoir_apres_add = float(product_fini.stock_comptoir or 0.0)
            if stock_comptoir_avant != stock_comptoir_apres_add:
                current_app.logger.error(f"TRACE - Stock comptoir modifié APRÈS db.session.add! Avant: {stock_comptoir_avant}, Après: {stock_comptoir_apres_add}")
                # Restaurer à nouveau
                product_fini.stock_comptoir = stock_comptoir_avant
            
            print(f"COMMANDE CLIENT - Valeur ajoutée (stock réservé): {quantity} {product_fini.unit} de {product_fini.name} (Valeur: {value_to_increment:.2f} DA) - Stock comptoir: {stock_comptoir_avant} (inchangé)")

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
    
    def restore_stock_on_cancellation(self):
        """
        Restaure le stock comptoir lors de l'annulation d'une commande de livraison PDV.
        Réincrémente le stock et la valeur pour chaque produit.
        """
        for item in self.items:
            product_fini = item.product
            if product_fini:
                # 1. Réincrémenter la quantité en stock
                quantity_to_restore = float(item.quantity)
                product_fini.update_stock_by_location('stock_comptoir', quantity_to_restore)

                # 2. Calculer la valeur à restaurer basée sur le PMP actuel
                pmp_produit_fini = product_fini.cost_price or Decimal('0.0')
                value_to_restore = Decimal(quantity_to_restore) * pmp_produit_fini

                # 3. Réincrémenter la valeur totale du stock du produit
                product_fini.total_stock_value = (product_fini.total_stock_value or Decimal('0.0')) + value_to_restore

                # Le PMP ne change pas lors d'une restauration
                db.session.add(product_fini)
    
    def decrement_ingredients_stock_on_production(self):
        """
        Décrémente le stock des ingrédients ET consommables lors de la production d'un produit fini,
        en tenant compte du rendement de la recette (yield_quantity).
        """
        for item in self.items:
            product_fini = item.product
            if not product_fini:
                continue
            
            # 1. DÉCRÉMENTATION DES INGRÉDIENTS (si recette existe)
            if product_fini.recipe_definition:
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
                    print(f"Décrémentation ingrédient: {ingredient_product.name} - {needed_qty:.3f} {ingredient_in_recipe.unit} (stock: {stock_attr})")
            
            # 2. DÉCRÉMENTATION DES CONSOMMABLES (toujours exécutée)
            # Deux systèmes: Ancien (ConsumableRecipe) et Nouveau (ConsumableCategory)
            
            # --- ANCIEN SYSTÈME : Recettes individuelles ---
            from app.consumables.models import ConsumableRecipe, ConsumableCategory
            consumable_recipes = ConsumableRecipe.query.filter(
                ConsumableRecipe.finished_product_id == product_fini.id
            ).all()
            
            if consumable_recipes:
                for consumable_recipe in consumable_recipes:
                    consumable_product = consumable_recipe.consumable_product
                    if not consumable_product:
                        continue
                    
                    # Quantité de consommable par unité produite
                    qty_per_unit = float(consumable_recipe.quantity_per_unit)
                    # Quantité totale à décrémenter pour la production réelle
                    needed_qty_consumable = qty_per_unit * float(item.quantity)
                    
                    # Décrémentation du stock consommables
                    consumable_product.update_stock_by_location('stock_consommables', -needed_qty_consumable)
                    
                    # Log/debug
                    print(f"Décrémentation consommable (recette): {consumable_product.name} - {needed_qty_consumable:.3f} {consumable_product.unit} (stock_consommables)")
            
            # --- NOUVEAU SYSTÈME : Catégories avec plages de quantités ---
            # Trouver si une catégorie de consommables existe pour cette catégorie de produit
            if product_fini.category:
                consumable_category = ConsumableCategory.query.filter(
                    ConsumableCategory.product_category_id == product_fini.category.id,
                    ConsumableCategory.is_active == True
                ).first()
                
                if consumable_category:
                    # Utiliser la logique intelligente des catégories
                    consumables_needed = consumable_category.calculate_consumables_needed(int(item.quantity))
                    
                    for consumable_product, quantity in consumables_needed:
                        if not consumable_product:
                            continue
                        
                        # Décrémentation du stock consommables
                        consumable_product.update_stock_by_location('stock_consommables', -float(quantity))
                        
                        # Log/debug
                        print(f"Décrémentation consommable (catégorie): {consumable_product.name} - {quantity} {consumable_product.unit} (stock_consommables)")

    def calculate_total_amount(self):
        items_total = Decimal('0.0')
        for item in self.items:
            items_total += item.subtotal
        delivery_cost = Decimal(self.delivery_cost or 0)
        self.total_amount = (items_total + delivery_cost).quantize(Decimal('0.01'))
        return self.total_amount

    def update_payment_status(self):
        total = Decimal(self.total_amount or 0)
        paid = Decimal(self.amount_paid or 0)
        if total <= 0:
            if paid > 0:
                self.payment_status = 'paid'
                if not self.payment_paid_at:
                    self.payment_paid_at = datetime.utcnow()
            else:
                self.payment_status = 'pending'
                self.payment_paid_at = None
            return

        if paid >= total:
            self.payment_status = 'paid'
            if not self.payment_paid_at:
                self.payment_paid_at = datetime.utcnow()
        elif paid > 0:
            self.payment_status = 'partial'
            self.payment_paid_at = None
        else:
            self.payment_status = 'pending'
            self.payment_paid_at = None

    @property
    def balance_due(self):
        total = Decimal(self.total_amount or 0)
        paid = Decimal(self.amount_paid or 0)
        remaining = (total - paid).quantize(Decimal('0.01'))
        if remaining < Decimal('0.00'):
            return Decimal('0.00')
        return remaining

    @property
    def amount_paid_value(self):
        return float(Decimal(self.amount_paid or 0))

    @property
    def balance_due_value(self):
        return float(self.balance_due)
    
    @property
    def get_delivery_address(self):
        """
        Retourne l'adresse de livraison en priorité:
        1. customer_address (adresse complète stockée dans la commande)
        2. delivery_zone (commune/zone de livraison)
        3. customer.delivery_address (adresse de livraison du client)
        4. customer.address (adresse principale du client)
        """
        # 1. Adresse complète stockée directement dans la commande
        if self.customer_address and self.customer_address.strip():
            return self.customer_address
        
        # 2. Zone de livraison (commune)
        if self.delivery_zone and self.delivery_zone.strip():
            return self.delivery_zone
        
        # 3. Adresse depuis le client lié
        if self.customer:
            # Priorité à l'adresse de livraison spécifique
            if self.customer.delivery_address:
                return self.customer.delivery_address
            # Sinon adresse principale
            if self.customer.address:
                return self.customer.address
        
        return None
    
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
    
    # Suivi de réception individuelle
    is_received = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    received_at = db.Column(db.DateTime, nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    
    # Relations
    received_by = db.relationship('Employee', foreign_keys=[received_by_id])
    
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
    deliveryman_id = db.Column(db.Integer, db.ForeignKey('deliverymen.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_register_session.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    order = db.relationship('Order', backref='delivery_debts')
    deliveryman = db.relationship('Deliveryman', backref='delivery_debts')
    session = db.relationship('CashRegisterSession', backref='delivery_debts')
    
    def __repr__(self):
        return f'<DeliveryDebt {self.id} - Order {self.order_id} - Livreur {self.deliveryman_id}>'

# ==================== MODÈLES B2B ====================

# Table de liaison pour les factures et commandes
invoice_orders = db.Table('invoice_orders',
    db.Column('invoice_id', db.Integer, db.ForeignKey('invoices.id'), primary_key=True),
    db.Column('b2b_order_id', db.Integer, db.ForeignKey('b2b_orders.id'), primary_key=True)
)

# ==================== MODÈLES CLIENTS ET FOURNISSEURS ====================

class Supplier(db.Model):
    """Fournisseurs - Base centralisée pour tous les achats"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations principales
    company_name = db.Column(db.String(200), nullable=False, index=True)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Informations commerciales
    tax_number = db.Column(db.String(50))  # NIF/RC
    payment_terms = db.Column(db.Integer, default=30)  # Jours de paiement
    bank_details = db.Column(db.Text)  # RIB et informations bancaires
    
    # Catégorisation
    supplier_type = db.Column(db.String(50), default='general')  # general, ingredients, equipment, services
    notes = db.Column(db.Text)
    
    # Statut et dates
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    purchases = db.relationship('Purchase', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.company_name}>'
    
    @property
    def total_purchases(self):
        """Montant total des achats chez ce fournisseur"""
        return sum(purchase.total_amount for purchase in self.purchases if purchase.total_amount)
    
    @property
    def active_purchases_count(self):
        """Nombre d'achats en cours"""
        from app.purchases.models import PurchaseStatus, Purchase
        return self.purchases.filter(
            Purchase.status.in_([PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED])
        ).count()


class Customer(db.Model):
    """Clients particuliers - Différent des clients B2B (entreprises)"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations personnelles
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(120))
    
    # Adresses
    address = db.Column(db.Text)
    delivery_address = db.Column(db.Text)  # Adresse de livraison différente si nécessaire
    
    # Informations complémentaires
    birth_date = db.Column(db.Date)
    customer_type = db.Column(db.String(50), default='regular')  # regular, vip, occasional
    preferred_delivery = db.Column(db.String(20), default='pickup')  # pickup, delivery
    
    # Historique et préférences
    notes = db.Column(db.Text)
    allergies = db.Column(db.Text)  # Allergies alimentaires
    preferences = db.Column(db.Text)  # Préférences culinaires
    
    # Statut et dates
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_order_date = db.Column(db.DateTime)
    
    # Relations
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Nom complet du client"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_orders(self):
        """Nombre total de commandes"""
        return self.orders.count()
    
    @property
    def total_spent(self):
        """Montant total dépensé"""
        return sum(order.total_amount for order in self.orders if order.total_amount)
    
    @property
    def display_phone(self):
        """Téléphone formaté pour affichage"""
        if self.phone and len(self.phone) >= 10:
            # Format: 0556 25 03 70
            phone = self.phone.replace(' ', '').replace('-', '')
            if len(phone) == 10:
                return f"{phone[:4]} {phone[4:6]} {phone[6:8]} {phone[8:]}"
        return self.phone


class B2BClient(db.Model):
    """Clients B2B (entreprises)"""
    __tablename__ = 'b2b_clients'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Informations de facturation
    tax_number = db.Column(db.String(50))  # NIF
    payment_terms = db.Column(db.Integer, default=30)  # Jours de paiement
    credit_limit = db.Column(db.Numeric(12, 2), default=0.0)
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    orders = db.relationship('B2BOrder', backref='b2b_client', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='b2b_client', lazy='dynamic')
    
    def __repr__(self):
        return f'<B2BClient {self.company_name}>'

class B2BOrder(db.Model):
    """Commandes B2B"""
    __tablename__ = 'b2b_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    b2b_client_id = db.Column(db.Integer, db.ForeignKey('b2b_clients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Informations de commande
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    delivery_date = db.Column(db.Date, nullable=False)
    
    # Gestion des périodes multi-jours
    is_multi_day = db.Column(db.Boolean, default=False)
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    
    # Statut et montants
    status = db.Column(db.String(50), default='pending', index=True)
    total_amount = db.Column(db.Numeric(12, 2), default=0.0)
    
    # Notes et métadonnées
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    items = db.relationship('B2BOrderItem', backref='b2b_order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<B2BOrder {self.order_number}>'
    
    def generate_order_number(self):
        """Générer le numéro de commande automatiquement"""
        if not self.order_number:
            year = datetime.now().year
            prefix = f"B2B-{year}-"
            # Récupérer tous les numéros existants de l'année et trouver le max séquentiel
            existing = db.session.query(B2BOrder.order_number) \
                .filter(B2BOrder.order_number.like(f"{prefix}%")).all()
            max_seq = 0
            for (num,) in existing:
                try:
                    seq = int((num or "").split('-')[-1])
                    if seq > max_seq:
                        max_seq = seq
                except Exception:
                    continue
            next_seq = max_seq + 1
            candidate = f"{prefix}{next_seq:03d}"
            # Sécuriser l'unicité en bouclant si collision (concurrence)
            while db.session.query(B2BOrder.id).filter_by(order_number=candidate).first() is not None:
                next_seq += 1
                candidate = f"{prefix}{next_seq:03d}"
            self.order_number = candidate
    
    def calculate_total_amount(self):
        """Calculer le montant total de la commande"""
        total = sum(item.subtotal for item in self.items)
        self.total_amount = total
        return total
    
    def get_status_display(self):
        """Afficher le statut en français"""
        status_types = {
            'pending': 'En attente',
            'in_production': 'En production',
            'ready_at_shop': 'Reçue au magasin',
            'delivered': 'Livrée',
            'completed': 'Terminée',
            'cancelled': 'Annulée'
        }
        return status_types.get(self.status, self.status.title())

class B2BOrderItem(db.Model):
    """Lignes de commande B2B"""
    __tablename__ = 'b2b_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    b2b_order_id = db.Column(db.Integer, db.ForeignKey('b2b_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)  # Permettre None pour les produits composés
    
    # Quantités et prix
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Description personnalisée
    description = db.Column(db.String(255))
    
    # Relations
    product = db.relationship('Product')
    
    @property
    def subtotal(self):
        """Calculer le sous-total de la ligne"""
        return float(self.quantity) * float(self.unit_price)
    
    def __repr__(self):
        return f'<B2BOrderItem {self.product.name if self.product else "Produit composé"} x {self.quantity}>'

class Invoice(db.Model):
    """Factures B2B"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    b2b_client_id = db.Column(db.Integer, db.ForeignKey('b2b_clients.id'), nullable=False)
    
    # Type de facture
    invoice_type = db.Column(db.String(20), default='proforma')  # proforma, final
    
    # Dates
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    # Montants
    subtotal = db.Column(db.Numeric(12, 2), default=0.0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0.0)
    total_amount = db.Column(db.Numeric(12, 2), default=0.0)
    
    # Mode de paiement
    payment_method = db.Column(db.String(20), default='cheque')  # cheque, espece, virement, traite
    
    # Statut
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid, overdue, cancelled
    payment_date = db.Column(db.Date, nullable=True)
    
    # Métadonnées
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    invoice_items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    b2b_orders = db.relationship('B2BOrder', secondary=invoice_orders, backref='invoices')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def generate_invoice_number(self):
        """Générer le numéro de facture automatiquement"""
        if not self.invoice_number:
            year = datetime.now().year
            count = Invoice.query.filter(
                db.extract('year', Invoice.created_at) == year
            ).count() + 1
            self.invoice_number = f"FEE-{year}-{count:03d}"
    
    def calculate_amounts(self):
        """Calculer les montants de la facture"""
        self.subtotal = sum(item.total_price for item in self.invoice_items)
        # TVA 19% (à adapter selon vos besoins)
        self.tax_amount = self.subtotal * Decimal('0.19')
        self.total_amount = self.subtotal + self.tax_amount
        return self.total_amount
    
    def get_status_display(self):
        """Afficher le statut en français"""
        status_types = {
            'draft': 'Brouillon',
            'sent': 'Envoyée',
            'paid': 'Payée',
            'overdue': 'En retard',
            'cancelled': 'Annulée'
        }
        return status_types.get(self.status, self.status.title())

class InvoiceItem(db.Model):
    """Lignes de facture"""
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Relations
    product = db.relationship('Product')
    
    def __repr__(self):
        return f'<InvoiceItem {self.description}>'