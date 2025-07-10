"""
Modèles comptables pour ERP Fée Maison
Plan comptable, journaux, écritures et rapports
"""

from datetime import datetime
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
    DEBIT = "debit"    # Actif, Charges
    CREDIT = "credit"  # Passif, Produits


class JournalType(Enum):
    """Types de journaux comptables"""
    VENTES = "VT"      # Journal des ventes
    ACHATS = "AC"      # Journal des achats
    CAISSE = "CA"      # Journal de caisse
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
    code = db.Column(db.String(5), unique=True, nullable=False)  # Ex: VT, AC, CA
    name = db.Column(db.String(100), nullable=False)  # Ex: Journal des ventes
    journal_type = db.Column(db.Enum(JournalType), nullable=False)
    
    # Configuration du journal
    is_active = db.Column(db.Boolean, default=True)
    sequence = db.Column(db.Integer, default=1)  # Numérotation automatique
    
    # Comptes par défaut
    default_debit_account_id = db.Column(db.Integer, db.ForeignKey('accounting_accounts.id'))
    default_credit_account_id = db.Column(db.Integer, db.ForeignKey('accounting_accounts.id'))
    
    # Métadonnées
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    default_debit_account = db.relationship('Account', foreign_keys=[default_debit_account_id])
    default_credit_account = db.relationship('Account', foreign_keys=[default_credit_account_id])
    entries = db.relationship('JournalEntry', backref='journal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Journal {self.code} - {self.name}>'
    
    def get_next_sequence(self):
        """Obtenir le prochain numéro de séquence"""
        last_entry = self.entries.order_by(JournalEntry.sequence.desc()).first()
        if last_entry:
            return last_entry.sequence + 1
        return 1


class JournalEntry(db.Model):
    """Écritures comptables (en-tête)"""
    __tablename__ = 'accounting_journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)  # Ex: VT-2025-001
    
    # Journal et numérotation
    journal_id = db.Column(db.Integer, db.ForeignKey('accounting_journals.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    
    # Dates
    entry_date = db.Column(db.Date, nullable=False)  # Date de l'écriture
    accounting_date = db.Column(db.Date, nullable=False)  # Date comptable
    
    # Description et références
    description = db.Column(db.String(255), nullable=False)
    reference_document = db.Column(db.String(100))  # Ex: Facture F-2025-001
    
    # Liens avec autres modules
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'))
    cash_movement_id = db.Column(db.Integer, db.ForeignKey('cash_movement.id'))
    
    # État de l'écriture
    is_validated = db.Column(db.Boolean, default=False)
    validated_at = db.Column(db.DateTime)
    validated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Métadonnées
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    lines = db.relationship('JournalEntryLine', backref='journal_entry', cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    validated_by = db.relationship('User', foreign_keys=[validated_by_id])
    
    def __repr__(self):
        return f'<JournalEntry {self.reference}>'
    
    @property
    def total_debit(self):
        """Total des débits de l'écriture"""
        return sum(line.debit_amount for line in self.lines if line.debit_amount)
    
    @property
    def total_credit(self):
        """Total des crédits de l'écriture"""
        return sum(line.credit_amount for line in self.lines if line.credit_amount)
    
    @property
    def is_balanced(self):
        """Vérifier si l'écriture est équilibrée"""
        return abs(self.total_debit - self.total_credit) < 0.01
    
    def generate_reference(self):
        """Générer la référence automatique"""
        if self.journal_id and not self.reference:
            # Récupérer le journal si pas encore chargé
            if not hasattr(self, '_journal_cache'):
                self._journal_cache = Journal.query.get(self.journal_id)
            
            year = self.entry_date.year
            sequence = self._journal_cache.get_next_sequence()
            self.reference = f"{self._journal_cache.code}-{year}-{sequence:03d}"
            self.sequence = sequence


class JournalEntryLine(db.Model):
    """Lignes d'écritures comptables"""
    __tablename__ = 'accounting_journal_entry_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('accounting_journal_entries.id'), nullable=False)
    
    # Compte et montants
    account_id = db.Column(db.Integer, db.ForeignKey('accounting_accounts.id'), nullable=False)
    debit_amount = db.Column(db.Numeric(12, 2), default=0)
    credit_amount = db.Column(db.Numeric(12, 2), default=0)
    
    # Description et références
    description = db.Column(db.String(255))
    reference = db.Column(db.String(100))
    
    # Métadonnées
    line_number = db.Column(db.Integer, nullable=False)  # Numéro de ligne dans l'écriture
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<JournalEntryLine {self.journal_entry.reference}-{self.line_number}>'


class FiscalYear(db.Model):
    """Exercices comptables"""
    __tablename__ = 'accounting_fiscal_years'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Ex: Exercice 2025
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # État de l'exercice
    is_current = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
    closed_at = db.Column(db.DateTime)
    closed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    closed_by = db.relationship('User')
    
    def __repr__(self):
        return f'<FiscalYear {self.name}>' 