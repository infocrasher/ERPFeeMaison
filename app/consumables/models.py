"""
Modèles pour la gestion des consommables
Module: app/consumables/models.py
"""

from datetime import datetime
from app import db

class ConsumableUsage(db.Model):
    """Utilisation estimée des consommables basée sur les ventes"""
    __tablename__ = 'consumable_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    usage_date = db.Column(db.Date, nullable=False, index=True)
    estimated_quantity_used = db.Column(db.Float, nullable=False)
    actual_quantity_used = db.Column(db.Float, nullable=True)  # Saisie manuelle
    estimated_value = db.Column(db.Numeric(12, 4), nullable=False, default=0.0)
    actual_value = db.Column(db.Numeric(12, 4), nullable=True)
    calculation_method = db.Column(db.String(50), nullable=False)  # 'sales_based', 'manual', 'recipe_based'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='consumable_usage')
    
    @property
    def variance(self):
        """Écart entre estimation et réalité"""
        if self.actual_quantity_used is not None:
            return self.actual_quantity_used - self.estimated_quantity_used
        return None
    
    @property
    def variance_percentage(self):
        """Pourcentage d'écart"""
        if self.actual_quantity_used is not None and self.estimated_quantity_used > 0:
            return (self.variance / self.estimated_quantity_used) * 100
        return None
    
    def __repr__(self):
        return f'<ConsumableUsage {self.product.name if self.product else "N/A"} - {self.usage_date}>'

class ConsumableAdjustment(db.Model):
    """Ajustements manuels des consommables"""
    __tablename__ = 'consumable_adjustments'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    adjustment_date = db.Column(db.Date, nullable=False, index=True)
    adjustment_type = db.Column(db.String(50), nullable=False)  # 'inventory', 'waste', 'correction'
    quantity_adjusted = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    adjusted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='consumable_adjustments')
    adjusted_by = db.relationship('User', backref='consumable_adjustments')
    
    def __repr__(self):
        return f'<ConsumableAdjustment {self.product.name if self.product else "N/A"} - {self.quantity_adjusted}>'

class ConsumableRecipe(db.Model):
    """Recettes d'utilisation des consommables par produit fini"""
    __tablename__ = 'consumable_recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    finished_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    consumable_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_per_unit = db.Column(db.Float, nullable=False)  # Quantité de consommable par unité de produit fini
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    finished_product = db.relationship('Product', foreign_keys=[finished_product_id], backref='consumable_recipes')
    consumable_product = db.relationship('Product', foreign_keys=[consumable_product_id], backref='consumable_ingredients')
    
    def __repr__(self):
        return f'<ConsumableRecipe {self.finished_product.name} -> {self.consumable_product.name}>'

class ConsumableCategory(db.Model):
    """Catégories de consommables avec plages de quantités automatiques"""
    __tablename__ = 'consumable_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "Gâteaux individuels", "Pâtisseries familiales"
    description = db.Column(db.Text)
    product_category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    product_category = db.relationship('Category', backref='consumable_categories')
    ranges = db.relationship('ConsumableRange', backref='consumable_category', cascade='all, delete-orphan', order_by='ConsumableRange.min_quantity')
    
    def __repr__(self):
        return f'<ConsumableCategory {self.name}>'
    
    def get_consumable_for_quantity(self, quantity):
        """
        Retourne le consommable approprié pour une quantité donnée
        Retourne : (ConsumableRange, nombre_de_boites)
        """
        # Trouver la plage qui correspond
        range_obj = ConsumableRange.query.filter(
            ConsumableRange.category_id == self.id,
            ConsumableRange.min_quantity <= quantity,
            ConsumableRange.max_quantity >= quantity
        ).first()
        
        if range_obj:
            return range_obj, 1
        
        # Si pas de plage exacte, utiliser la plus grande plage disponible
        largest_range = ConsumableRange.query.filter(
            ConsumableRange.category_id == self.id
        ).order_by(ConsumableRange.max_quantity.desc()).first()
        
        if largest_range:
            # Calculer le nombre de boîtes nécessaires
            boxes_needed = (quantity + largest_range.max_quantity - 1) // largest_range.max_quantity
            return largest_range, boxes_needed
        
        return None, 0
    
    def calculate_consumables_needed(self, quantity):
        """
        Calcule les consommables nécessaires pour une quantité donnée
        Retourne une liste de tuples (consommable, quantité)
        Gère les multiples boîtes intelligemment
        """
        result = []
        remaining = quantity
        
        # Trier les plages par capacité décroissante
        ranges = ConsumableRange.query.filter(
            ConsumableRange.category_id == self.id
        ).order_by(ConsumableRange.max_quantity.desc()).all()
        
        for range_obj in ranges:
            if remaining <= 0:
                break
            
            # Trouver la meilleure combinaison
            if remaining >= range_obj.min_quantity:
                boxes_needed = remaining // range_obj.max_quantity
                if boxes_needed > 0:
                    result.append((range_obj.consumable_product, boxes_needed))
                    remaining -= boxes_needed * range_obj.max_quantity
        
        # Si il reste des pièces, utiliser la plus petite boîte disponible
        if remaining > 0:
            smallest_range = ConsumableRange.query.filter(
                ConsumableRange.category_id == self.id,
                ConsumableRange.max_quantity >= remaining
            ).order_by(ConsumableRange.max_quantity.asc()).first()
            
            if smallest_range:
                result.append((smallest_range.consumable_product, 1))
        
        return result

class ConsumableRange(db.Model):
    """Plages de quantités pour les catégories de consommables"""
    __tablename__ = 'consumable_ranges'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('consumable_categories.id'), nullable=False)
    min_quantity = db.Column(db.Integer, nullable=False)  # Plage min
    max_quantity = db.Column(db.Integer, nullable=False)  # Plage max
    consumable_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_per_unit = db.Column(db.Float, nullable=False, default=1.0)  # Nombre de consommables par unité
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    consumable_product = db.relationship('Product', backref='consumable_ranges')
    
    def __repr__(self):
        return f'<ConsumableRange {self.min_quantity}-{self.max_quantity} : {self.consumable_product.name if self.consumable_product else "N/A"}>'
    
    def get_capacity_display(self):
        """Affiche la capacité de la plage"""
        return f"{self.min_quantity}-{self.max_quantity} pièces"

