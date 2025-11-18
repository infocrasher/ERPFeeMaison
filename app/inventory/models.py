"""
Modèles pour la gestion d'inventaire physique vs théorique
Module: app/inventory/models.py
"""

from datetime import datetime
from enum import Enum
from extensions import db
from models import User
from sqlalchemy import func

class InventoryStatus(Enum):
    """Statuts possibles d'un inventaire"""
    EN_COURS = "en_cours"           # Inventaire créé, saisie en cours
    COMPLETE = "complete"           # Saisie terminée, en attente validation
    VALIDE = "valide"              # Validé, ajustements appliqués
    CLOTURE = "cloture"            # Clôturé définitivement

class VarianceLevel(Enum):
    """Niveaux d'écart pour classification"""
    OK = "ok"                      # < 5% - Acceptable
    NORMAL = "normal"              # 5-10% - Normal
    CRITIQUE = "critique"          # > 10% - Critique

class AdjustmentReason(Enum):
    """Motifs d'ajustement de stock"""
    INVENDU_DONNE = "invendu_donne"           # Invendu donné gratuitement
    PEREMPTION = "peremption"                 # Produit périmé
    VOL_PERTE = "vol_perte"                   # Vol ou perte
    ERREUR_SAISIE = "erreur_saisie"           # Erreur de saisie antérieure
    VENTE_NON_ENREGISTREE = "vente_non_enregistree"  # Vente oubliée
    PRODUCTION_NON_DECLAREE = "production_non_declaree"  # Production non déclarée
    AUTRE = "autre"                           # Autre motif

class Inventory(db.Model):
    """
    Inventaire mensuel par emplacement
    Un inventaire = une session d'inventaire pour un mois donné
    """
    __tablename__ = 'inventories'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    inventory_date = db.Column(db.Date, nullable=False, index=True)  # Date de l'inventaire (fin de mois)
    month = db.Column(db.Integer, nullable=False)  # Mois (1-12)
    year = db.Column(db.Integer, nullable=False)   # Année
    
    # Emplacements concernés (exclu comptoir selon vos spécifications)
    include_ingredients_magasin = db.Column(db.Boolean, default=True)
    include_ingredients_local = db.Column(db.Boolean, default=True) 
    include_consommables = db.Column(db.Boolean, default=True)
    
    # Statut et workflow
    status = db.Column(db.Enum(InventoryStatus), default=InventoryStatus.EN_COURS, nullable=False)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    completed_at = db.Column(db.DateTime)  # Date de fin de saisie
    validated_at = db.Column(db.DateTime)  # Date de validation
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Statistiques calculées
    total_products = db.Column(db.Integer, default=0)  # Nombre de produits inventoriés
    products_with_variance = db.Column(db.Integer, default=0)  # Produits avec écart
    total_variance_value = db.Column(db.Numeric(12, 4), default=0.0)  # Valeur totale des écarts
    
    # Notes et commentaires
    notes = db.Column(db.Text)
    
    # Relations
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_inventories')
    validated_by = db.relationship('User', foreign_keys=[validated_by_id], backref='validated_inventories')
    items = db.relationship('InventoryItem', backref='inventory', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Inventory {self.month}/{self.year} - {self.status.value}>'
    
    @property
    def title(self):
        """Titre formaté de l'inventaire"""
        months = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        return f"Inventaire {months[self.month]} {self.year}"
    
    @property
    def locations_list(self):
        """Liste des emplacements inclus dans cet inventaire"""
        locations = []
        if self.include_ingredients_magasin:
            locations.append('ingredients_magasin')
        if self.include_ingredients_local:
            locations.append('ingredients_local')
        if self.include_consommables:
            locations.append('consommables')
        return locations
    
    @property
    def variance_percentage(self):
        """Pourcentage d'écart global"""
        if self.total_products == 0:
            return 0.0
        return (self.products_with_variance / self.total_products) * 100
    
    def can_be_edited(self):
        """Vérifie si l'inventaire peut encore être modifié"""
        return self.status in [InventoryStatus.EN_COURS, InventoryStatus.COMPLETE]
    
    def can_be_validated(self):
        """Vérifie si l'inventaire peut être validé"""
        return self.status == InventoryStatus.COMPLETE
    
    def update_statistics(self):
        """Met à jour les statistiques calculées"""
        items = self.items.all()
        self.total_products = len(items)
        self.products_with_variance = len([item for item in items if item.has_variance])
        self.total_variance_value = sum([item.variance_value or 0 for item in items])

class InventoryItem(db.Model):
    """
    Ligne d'inventaire pour un produit dans un emplacement donné
    """
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relations
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Emplacement concerné
    location_type = db.Column(db.String(50), nullable=False)  # ingredients_magasin, ingredients_local, consommables
    
    # Stocks
    theoretical_stock = db.Column(db.Float, nullable=False, default=0.0)  # Stock système au moment de l'inventaire
    physical_stock = db.Column(db.Float)  # Stock physique saisi (NULL = pas encore saisi)
    
    # Écart calculé automatiquement
    variance = db.Column(db.Float)  # Écart = physique - théorique
    variance_percentage = db.Column(db.Float)  # Pourcentage d'écart
    variance_level = db.Column(db.Enum(VarianceLevel))  # Niveau d'écart
    
    # Valorisation
    unit_cost = db.Column(db.Numeric(10, 4))  # Coût unitaire au moment de l'inventaire
    variance_value = db.Column(db.Numeric(12, 4))  # Valeur de l'écart (variance × coût)
    
    # Motif et commentaires
    adjustment_reason = db.Column(db.Enum(AdjustmentReason))  # Motif de l'écart
    notes = db.Column(db.Text)  # Commentaires libres
    
    # Métadonnées de saisie
    counted_at = db.Column(db.DateTime)  # Date/heure de saisie du stock physique
    counted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Qui a saisi
    
    # Ajustement appliqué
    adjustment_applied = db.Column(db.Boolean, default=False)  # Ajustement appliqué au stock
    adjustment_applied_at = db.Column(db.DateTime)  # Date d'application de l'ajustement
    
    # Relations
    product = db.relationship('Product', backref='inventory_items')
    counted_by = db.relationship('User', backref='counted_inventory_items')
    
    def __repr__(self):
        return f'<InventoryItem {self.product.name if self.product else "N/A"} - {self.location_type}>'
    
    @property
    def has_variance(self):
        """Indique s'il y a un écart"""
        return self.variance is not None and abs(self.variance) > 0.01  # Seuil de 0.01 pour éviter les erreurs d'arrondi
    
    @property
    def is_counted(self):
        """Indique si le stock physique a été saisi"""
        return self.physical_stock is not None
    
    def calculate_variance(self):
        """Calcule l'écart et ses dérivés"""
        if self.physical_stock is None:
            self.variance = None
            self.variance_percentage = None
            self.variance_level = None
            self.variance_value = None
            return
        
        # Calcul de l'écart
        self.variance = self.physical_stock - self.theoretical_stock
        
        # Calcul du pourcentage d'écart
        if self.theoretical_stock != 0:
            self.variance_percentage = (self.variance / self.theoretical_stock) * 100
        else:
            self.variance_percentage = 100.0 if self.physical_stock > 0 else 0.0
        
        # Détermination du niveau d'écart
        abs_percentage = abs(self.variance_percentage)
        if abs_percentage < 5:
            self.variance_level = 'ok'
        elif abs_percentage <= 10:
            self.variance_level = 'normal'
        else:
            self.variance_level = 'critique'
        
        # Calcul de la valeur de l'écart
        if self.unit_cost:
            self.variance_value = self.variance * float(self.unit_cost)
        else:
            self.variance_value = 0.0
    
    def apply_adjustment(self):
        """Applique l'ajustement au stock du produit"""
        if self.adjustment_applied or not self.has_variance:
            return False
        
        # Récupérer le produit et mettre à jour le stock selon l'emplacement
        product = self.product
        if not product:
            return False
        
        # Appliquer l'ajustement selon l'emplacement
        if self.location_type == 'ingredients_magasin':
            product.stock_ingredients_magasin = self.physical_stock
        elif self.location_type == 'ingredients_local':
            product.stock_ingredients_local = self.physical_stock
        elif self.location_type == 'consommables':
            product.stock_consommables = self.physical_stock
        
        # Marquer comme appliqué
        self.adjustment_applied = True
        self.adjustment_applied_at = datetime.utcnow()
        
        # Mettre à jour la date de dernière modification du stock
        product.last_stock_update = datetime.utcnow()
        
        return True

class InventorySnapshot(db.Model):
    """
    Instantané des stocks au moment de la création de l'inventaire
    Permet de tracer l'historique et les évolutions
    """
    __tablename__ = 'inventory_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Stocks au moment de la création de l'inventaire
    stock_ingredients_magasin = db.Column(db.Float, default=0.0)
    stock_ingredients_local = db.Column(db.Float, default=0.0)
    stock_consommables = db.Column(db.Float, default=0.0)
    
    # Coût et valeur au moment de l'inventaire
    cost_price = db.Column(db.Numeric(10, 4))
    total_value = db.Column(db.Numeric(12, 4))
    
    # Métadonnées
    snapshot_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    inventory = db.relationship('Inventory', backref='snapshots')
    product = db.relationship('Product', backref='inventory_snapshots')
    
    def __repr__(self):
        return f'<InventorySnapshot {self.product.name if self.product else "N/A"}>'

class WasteReason(Enum):
    """Raisons des invendus"""
    PEREMPTION = "peremption"      # Péremption
    INVENDU = "invendu"           # Invendu
    CASSE = "casse"               # Casse
    DON = "don"                   # Don gratuit

class DailyWaste(db.Model):
    """Déclaration quotidienne des invendus"""
    __tablename__ = 'daily_waste'
    
    id = db.Column(db.Integer, primary_key=True)
    waste_date = db.Column(db.Date, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    declared_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    declared_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='waste_declarations')
    declared_by = db.relationship('User', backref='waste_declarations')
    
    @property
    def value_lost(self):
        """Valeur perdue calculée"""
        if self.product and self.product.cost_price:
            return float(self.quantity) * float(self.product.cost_price)
        return 0.0
    
    def __repr__(self):
        return f'<DailyWaste {self.product.name if self.product else "N/A"} - {self.quantity} - {self.reason.value}>'

class WeeklyComptoirInventory(db.Model):
    """Inventaire hebdomadaire du comptoir"""
    __tablename__ = 'weekly_comptoir_inventories'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_date = db.Column(db.Date, nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=False)  # Numéro de semaine
    year = db.Column(db.Integer, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='EN_COURS', nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    created_by = db.relationship('User', backref='weekly_inventories')
    items = db.relationship('WeeklyComptoirItem', backref='inventory', lazy='dynamic', cascade="all, delete-orphan")
    
    @property
    def title(self):
        """Titre formaté de l'inventaire"""
        return f"Inventaire Comptoir Semaine {self.week_number} - {self.year}"
    
    def can_be_edited(self):
        """Vérifie si l'inventaire peut encore être modifié"""
        return self.status in [InventoryStatus.EN_COURS, InventoryStatus.COMPLETE]
    
    def __repr__(self):
        return f'<WeeklyComptoirInventory Semaine {self.week_number} - {self.year}>'

class WeeklyComptoirItem(db.Model):
    """Ligne d'inventaire hebdomadaire pour un produit du comptoir"""
    __tablename__ = 'weekly_comptoir_items'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('weekly_comptoir_inventories.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    theoretical_stock = db.Column(db.Float, nullable=False)
    physical_stock = db.Column(db.Float, nullable=True)
    
    variance = db.Column(db.Float, default=0.0)
    variance_percentage = db.Column(db.Float, default=0.0)
    variance_level = db.Column(db.String(50), default='ok')
    
    theoretical_value = db.Column(db.Numeric(12, 4), nullable=False, default=0.0)
    physical_value = db.Column(db.Numeric(12, 4), nullable=False, default=0.0)
    variance_value = db.Column(db.Numeric(12, 4), nullable=False, default=0.0)
    
    unit_cost = db.Column(db.Numeric(10, 4), nullable=True)
    counted_at = db.Column(db.DateTime, nullable=True)
    counted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text)
    
    # Relations
    product = db.relationship('Product', backref='weekly_comptoir_items')
    counted_by = db.relationship('User', backref='weekly_counted_items')
    
    @property
    def is_counted(self):
        """Vérifie si l'item a été compté"""
        return self.physical_stock is not None
    
    @property
    def has_variance(self):
        """Vérifie s'il y a un écart"""
        return self.variance != 0 if self.physical_stock is not None else False
    
    def calculate_variance(self):
        """Calcule l'écart et ses dérivés"""
        if self.physical_stock is None:
            self.variance = None
            self.variance_percentage = None
            self.variance_level = None
            self.variance_value = None
            return
        
        # Calcul de l'écart
        self.variance = self.physical_stock - self.theoretical_stock
        
        # Calcul du pourcentage d'écart
        if self.theoretical_stock != 0:
            self.variance_percentage = (self.variance / self.theoretical_stock) * 100
        else:
            self.variance_percentage = 100.0 if self.physical_stock > 0 else 0.0
        
        # Détermination du niveau d'écart
        abs_percentage = abs(self.variance_percentage)
        if abs_percentage < 5:
            self.variance_level = 'ok'
        elif abs_percentage <= 10:
            self.variance_level = 'normal'
        else:
            self.variance_level = 'critique'
        
        # Calcul de la valeur de l'écart
        if self.unit_cost:
            self.variance_value = self.variance * float(self.unit_cost)
        else:
            self.variance_value = 0.0
    
    def __repr__(self):
        return f'<WeeklyComptoirItem {self.product.name if self.product else "N/A"} - {self.physical_stock}/{self.theoretical_stock}>'
