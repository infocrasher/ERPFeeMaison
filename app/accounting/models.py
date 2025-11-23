"""
Modèles comptables pour ERP Fée Maison
Plan comptable, journaux, écritures et rapports
"""

from datetime import datetime, date
from enum import Enum
from extensions import db
from decimal import Decimal


class AccountType(Enum):
    """Types de comptes comptables selon le plan comptable algérien"""
    CLASSE_1 = "1"  # Comptes de capitaux
    CLASSE_2 = "2"  # Comptes d'immobilisations
    CLASSE_3 = "3"  # Comptes de stocks
    CLASSE_4 = "4"  # Comptes de tiers
    CLASSE_5 = "5"  # Comptes financiers
    CLASSE_6 = "6"  # Comptes de charges
    CLASSE_7 = "7"  # Comptes de produits


class AccountNature(Enum):
    """Nature des comptes (débit/crédit)"""
    DEBIT = "debit"      # Compte de débit (actif, charges)
    CREDIT = "credit"    # Compte de crédit (passif, produits)


class JournalType(Enum):
    """Types de journaux comptables"""
    VENTES = "VT"        # Journal des ventes
    ACHATS = "AC"       # Journal des achats
    CAISSE = "CA"       # Journal de caisse
    BANQUE = "BQ"      # Journal de banque
    OPERATIONS_DIVERSES = "OD"  # Opérations diverses


class Account(db.Model):
    """Plan comptable - Comptes comptables"""
    __tablename__ = 'accounting_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # Ex: 411001
    name = db.Column(db.String(200), nullable=False)  # Ex: Clients - Ventes de marchandises
    account_type = db.Column(db.Enum(AccountType), nullable=False)
    account_nature = db.Column(db.Enum(AccountNature), nullable=False)
    
    # Hiérarchie des comptes
    parent_id = db.Column(db.Integer, db.ForeignKey('accounting_accounts.id'), nullable=True)
    level = db.Column(db.Integer, default=1)  # Niveau dans la hiérarchie
    
    # Propriétés du compte
    is_active = db.Column(db.Boolean, default=True)
    is_detail = db.Column(db.Boolean, default=True)  # Compte de détail (peut recevoir des écritures)
    
    # Métadonnées
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    parent = db.relationship('Account', remote_side=[id], backref='children')
    journal_entries = db.relationship('JournalEntryLine', backref='account', lazy='dynamic')
    
    def __repr__(self):
        return f'<Account {self.code} - {self.name}>'
    
    @property
    def balance(self):
        """Calcul du solde du compte"""
        total_debit = sum(line.debit_amount for line in self.journal_entries if line.debit_amount)
        total_credit = sum(line.credit_amount for line in self.journal_entries if line.credit_amount)
        
        if self.account_nature == AccountNature.DEBIT:
            return total_debit - total_credit
        else:
            return total_credit - total_debit


class Journal(db.Model):
    """Journaux comptables"""
    __tablename__ = 'accounting_journals'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # Ex: VT, AC, CA
    name = db.Column(db.String(100), nullable=False)  # Ex: Journal des Ventes
    journal_type = db.Column(db.Enum(JournalType), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    entries = db.relationship('JournalEntry', backref='journal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Journal {self.code} - {self.name}>'


class FiscalYear(db.Model):
    """Exercices comptables"""
    __tablename__ = 'accounting_fiscal_years'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)  # Ex: 2024
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    entries = db.relationship('JournalEntry', backref='fiscal_year', lazy='dynamic')
    
    def __repr__(self):
        return f'<FiscalYear {self.year}>'


class JournalEntry(db.Model):
    """Écritures comptables"""
    __tablename__ = 'accounting_journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    entry_number = db.Column(db.String(50), unique=True, nullable=False)  # Ex: VT-2024-001
    entry_date = db.Column(db.Date, nullable=False, index=True)
    
    # Références
    journal_id = db.Column(db.Integer, db.ForeignKey('accounting_journals.id'), nullable=False)
    fiscal_year_id = db.Column(db.Integer, db.ForeignKey('accounting_fiscal_years.id'), nullable=True)
    
    # Informations
    description = db.Column(db.Text, nullable=False)
    reference = db.Column(db.String(100))  # Référence externe (facture, commande, etc.)
    
    # Validation
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relations
    lines = db.relationship('JournalEntryLine', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_journal_entries')
    validated_by = db.relationship('User', foreign_keys=[validated_by_id], backref='validated_journal_entries')
    
    def __repr__(self):
        return f'<JournalEntry {self.entry_number}>'
    
    @property
    def total_debit(self):
        return sum(line.debit_amount or 0 for line in self.lines)
    
    @property
    def total_credit(self):
        return sum(line.credit_amount or 0 for line in self.lines)
    
    @property
    def is_balanced(self):
        """Vérifie si l'écriture est équilibrée (débit = crédit)"""
        return abs(self.total_debit - self.total_credit) < Decimal('0.01')


class JournalEntryLine(db.Model):
    """Lignes d'écriture comptable"""
    __tablename__ = 'accounting_journal_entry_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('accounting_journal_entries.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounting_accounts.id'), nullable=False)
    
    # Montants
    debit_amount = db.Column(db.Numeric(12, 2), default=0.0)
    credit_amount = db.Column(db.Numeric(12, 2), default=0.0)
    
    # Description
    description = db.Column(db.Text)
    
    # Métadonnées
    line_number = db.Column(db.Integer)  # Numéro de ligne dans l'écriture
    
    def __repr__(self):
        return f'<JournalEntryLine {self.id} - {self.debit_amount or 0} / {self.credit_amount or 0}>'


class HistoricalAccountingData(db.Model):
    """
    Données historiques de comptabilité extraites des fichiers Excel
    Utilisées pour Prophet et les analyses IA
    """
    __tablename__ = 'historical_accounting_data'
    
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.Date, nullable=False, index=True, unique=True)  # Date unique par jour
    
    # Données financières
    revenue = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # CA journalier
    purchases = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # Achats journaliers
    salaries = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # Salaires
    rent = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # Loyer
    other_expenses = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)  # Autres dépenses
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contrainte unique sur la date
    __table_args__ = (
        db.Index('idx_historical_data_date', 'record_date'),
    )
    
    def __repr__(self):
        return f'<HistoricalAccountingData {self.record_date} - {self.revenue} DA>'
    
    @property
    def net_profit(self):
        """Bénéfice net = Revenue - (Purchases + Salaries + Rent + Other)"""
        return Decimal(self.revenue or 0) - (
            Decimal(self.purchases or 0) +
            Decimal(self.salaries or 0) +
            Decimal(self.rent or 0) +
            Decimal(self.other_expenses or 0)
        )


class BusinessConfig(db.Model):
    """
    Configuration des objectifs et paramètres métier
    Singleton : une seule instance active à la fois
    """
    __tablename__ = 'business_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Objectifs financiers
    monthly_objective = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    daily_objective = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    yearly_objective = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    
    # Paramètres stock
    stock_rotation_days = db.Column(db.Integer, default=30, nullable=False)
    
    # Paramètres qualité
    quality_target_percent = db.Column(db.Numeric(5, 2), default=95.0, nullable=False)
    
    # Paramètres RH
    standard_work_hours_per_day = db.Column(db.Numeric(4, 2), default=8.0, nullable=False)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relations
    updated_by = db.relationship('User', backref='updated_business_configs')
    
    @classmethod
    def get_current(cls):
        """Récupère la configuration actuelle (singleton)"""
        config = cls.query.first()
        if not config:
            # Créer une configuration par défaut si elle n'existe pas
            config = cls(
                monthly_objective=Decimal('0.0'),
                daily_objective=Decimal('0.0'),
                yearly_objective=Decimal('0.0'),
                stock_rotation_days=30,
                quality_target_percent=Decimal('95.0'),
                standard_work_hours_per_day=Decimal('8.0')
            )
            db.session.add(config)
            db.session.commit()
        return config
    
    def __repr__(self):
        return f'<BusinessConfig - Objectif mensuel: {self.monthly_objective} DA>'
