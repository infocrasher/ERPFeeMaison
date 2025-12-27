"""
Service d'intégration comptable automatique
Génère les écritures comptables depuis les autres modules
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from flask_login import current_user
from extensions import db
from .models import Journal, Account, JournalEntry, JournalEntryLine, JournalType
from sqlalchemy import func


class AccountingIntegrationService:
    """Service pour les intégrations comptables automatiques"""
    
    @staticmethod
    def create_sale_entry(order_id, sale_amount, payment_method='cash', description=None):
        """
        Créer une écriture de vente
        
        Args:
            order_id: ID de la commande
            sale_amount: Montant de la vente
            payment_method: Mode de paiement ('cash', 'bank', 'credit')
            description: Description de l'écriture
        """
        try:
            # Récupérer le journal des ventes
            journal = Journal.query.filter_by(journal_type=JournalType.VENTES, is_active=True).first()
            if not journal:
                raise ValueError("Journal des ventes (VT) non trouvé ou inactif")
            
            # Comptes comptables (Mapping robuste pour B2B et ventes classiques)
            bank_methods = ['bank', 'cheque', 'virement', 'traite']
            cash_methods = ['cash', 'espece']
            
            if payment_method in cash_methods:
                debit_account = Account.query.filter_by(code='530', is_active=True).first()  # Caisse
            elif payment_method in bank_methods:
                debit_account = Account.query.filter_by(code='512', is_active=True).first()  # Banque
            else:  # credit ou client B2B en attente
                debit_account = Account.query.filter_by(code='411', is_active=True).first()  # Clients
            
            credit_account = Account.query.filter_by(code='701', is_active=True).first()  # Ventes de marchandises
            
            if not debit_account:
                # Fallback sur le code explicite pour le message d'erreur
                msg_code = '530' if payment_method in cash_methods else '512' if payment_method in bank_methods else '411'
                raise ValueError(f"Compte comptable débit ({msg_code}) non trouvé ou inactif pour le mode de paiement '{payment_method}'")
            if not credit_account:
                raise ValueError("Compte comptable crédit (701 - Ventes) non trouvé ou inactif")
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=date.today(),
                description=description or f"Vente commande #{order_id}",
                reference=f"CMD-{order_id}" if order_id and order_id != 999 else "TEST-VENTE",
                created_by_id=current_user.id if current_user.is_authenticated else 1,
                is_validated=True  # Valider automatiquement les écritures de vente
            )
            
            # Générer la référence
            entry.generate_reference()
            
            db.session.add(entry)
            db.session.flush()
            
            # Ligne de débit (encaissement)
            debit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=debit_account.id,
                debit_amount=sale_amount,
                credit_amount=0,
                description=f"Encaissement vente CMD-{order_id}",
                line_number=1
            )
            
            # Ligne de crédit (vente)
            credit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=credit_account.id,
                debit_amount=0,
                credit_amount=sale_amount,
                description=f"Vente marchandises CMD-{order_id}",
                line_number=2
            )
            
            db.session.add(debit_line)
            db.session.add(credit_line)
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def create_purchase_entry(purchase_id, purchase_amount, payment_method='cash', description=None, payment_date=None):
        """
        Créer une écriture d'achat
        
        Args:
            purchase_id: ID de l'achat
            purchase_amount: Montant de l'achat
            payment_method: Mode de paiement ('cash', 'bank', 'credit')
            description: Description de l'écriture
            payment_date: Date de paiement (si None, utilise date.today())
        """
        try:
            # Vérifier si une écriture existe déjà pour ce bon
            existing_entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase_id}").first()
            if existing_entry:
                raise ValueError(f"Une écriture comptable existe déjà pour ce bon d'achat (ACH-{purchase_id})")
            
            # Récupérer le journal des achats
            journal = Journal.query.filter_by(journal_type=JournalType.ACHATS, is_active=True).first()
            if not journal:
                raise ValueError("Journal des achats (AC) non trouvé ou inactif")
            
            # Comptes comptables
            debit_account = Account.query.filter_by(code='601', is_active=True).first()  # Achats de marchandises
            
            if payment_method == 'cash':
                credit_account = Account.query.filter_by(code='530', is_active=True).first()  # Caisse
            elif payment_method == 'bank':
                credit_account = Account.query.filter_by(code='512', is_active=True).first()  # Banque
            else:  # credit
                credit_account = Account.query.filter_by(code='401', is_active=True).first()  # Fournisseurs
            
            if not debit_account:
                raise ValueError("Compte comptable débit (601 - Achats) non trouvé ou inactif")
            if not credit_account:
                raise ValueError(f"Compte comptable crédit ({'530' if payment_method == 'cash' else '512' if payment_method == 'bank' else '401'}) non trouvé ou inactif")
            
            # Utiliser la date de paiement si fournie, sinon date du jour
            entry_date = payment_date.date() if payment_date and hasattr(payment_date, 'date') else (payment_date if isinstance(payment_date, date) else date.today())
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=entry_date,
                description=description or f"Achat #{purchase_id}",
                reference=f"ACH-{purchase_id}" if purchase_id and purchase_id != 999 else "TEST-ACHAT",
                created_by_id=current_user.id if current_user.is_authenticated else 1,
                is_validated=True  # Valider automatiquement les écritures d'achat
            )
            
            # Générer la référence
            entry.generate_reference()
            
            db.session.add(entry)
            db.session.flush()
            
            # Ligne de débit (achat)
            debit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=debit_account.id,
                debit_amount=purchase_amount,
                credit_amount=0,
                description=f"Achat marchandises ACH-{purchase_id}",
                line_number=1
            )
            
            # Ligne de crédit (paiement)
            credit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=credit_account.id,
                debit_amount=0,
                credit_amount=purchase_amount,
                description=f"Paiement achat ACH-{purchase_id}",
                line_number=2
            )
            
            db.session.add(debit_line)
            db.session.add(credit_line)
            # Ne pas faire de commit ici - laisser l'appelant gérer le commit
            db.session.flush()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def create_cash_movement_entry(cash_movement_id, amount, movement_type, description):
        """Créer une écriture comptable pour un mouvement de caisse"""
        try:
            # Récupérer les comptes nécessaires
            cash_account = Account.query.filter_by(code='530', is_active=True).first()  # Caisse
            
            if not cash_account:
                raise ValueError("Compte Caisse (530) non trouvé ou inactif")
            
            # Récupérer le journal de caisse
            cash_journal = Journal.query.filter_by(code='CA', is_active=True).first()
            if not cash_journal:
                raise ValueError("Journal Caisse (CA) non trouvé ou inactif")
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=cash_journal.id,
                entry_date=date.today(),
                description=description,
                reference=f"CASH-{cash_movement_id}",
                created_by_id=current_user.id if current_user else 1
            )
            entry.generate_reference()
            
            if movement_type == 'in':
                # Entrée de caisse : Débit Caisse, Crédit Produits divers
                products_account = Account.query.filter_by(code='758', is_active=True).first()
                if not products_account:
                    raise ValueError("Compte Produits divers (758) non trouvé ou inactif")
                
                # Ligne débit - Caisse
                debit_line = JournalEntryLine(
                    account_id=cash_account.id,
                    debit_amount=amount,
                    credit_amount=0,
                    description=description,
                    line_number=1
                )
                
                # Ligne crédit - Produits divers
                credit_line = JournalEntryLine(
                    account_id=products_account.id,
                    debit_amount=0,
                    credit_amount=amount,
                    description=description,
                    line_number=2
                )
                
            else:  # movement_type == 'out'
                # Sortie de caisse : Débit Charges diverses, Crédit Caisse
                charges_account = Account.query.filter_by(code='658', is_active=True).first()
                if not charges_account:
                    raise ValueError("Compte Charges diverses (658) non trouvé ou inactif")
                
                # Ligne débit - Charges diverses
                debit_line = JournalEntryLine(
                    account_id=charges_account.id,
                    debit_amount=amount,
                    credit_amount=0,
                    description=description,
                    line_number=1
                )
                
                # Ligne crédit - Caisse
                credit_line = JournalEntryLine(
                    account_id=cash_account.id,
                    debit_amount=0,
                    credit_amount=amount,
                    description=description,
                    line_number=2
                )
            
            # Ajouter les lignes à l'écriture
            entry.lines = [debit_line, credit_line]
            
            # Sauvegarder
            db.session.add(entry)
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def create_bank_deposit_entry(cash_movement_id, amount, description):
        """Créer une écriture comptable pour un dépôt de caisse vers banque"""
        try:
            # Récupérer les comptes nécessaires
            cash_account = Account.query.filter_by(code='530', is_active=True).first()  # Caisse
            bank_account = Account.query.filter_by(code='512', is_active=True).first()  # Banque
            
            if not cash_account:
                raise ValueError("Compte Caisse (530) non trouvé ou inactif")
            if not bank_account:
                raise ValueError("Compte Banque (512) non trouvé ou inactif")
            
            # Récupérer le journal de banque
            bank_journal = Journal.query.filter_by(code='BQ', is_active=True).first()
            if not bank_journal:
                raise ValueError("Journal Banque (BQ) non trouvé ou inactif")
            
            # Créer l'écriture de transfert (Caisse → Banque)
            entry = JournalEntry(
                journal_id=bank_journal.id,
                entry_date=date.today(),
                description=description,
                reference=f"DEPOSIT-{cash_movement_id}",
                created_by_id=current_user.id if current_user else 1
            )
            entry.generate_reference()
            
            # Ligne débit - Banque (augmentation)
            debit_line = JournalEntryLine(
                account_id=bank_account.id,
                debit_amount=amount,
                credit_amount=0,
                description=description,
                line_number=1
            )
            
            # Ligne crédit - Caisse (diminution)
            credit_line = JournalEntryLine(
                account_id=cash_account.id,
                debit_amount=0,
                credit_amount=amount,
                description=description,
                line_number=2
            )
            
            # Ajouter les lignes à l'écriture
            entry.lines = [debit_line, credit_line]
            
            # Sauvegarder
            db.session.add(entry)
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def create_stock_adjustment_entry(adjustment_id, amount, adjustment_type, description=None):
        """
        Créer une écriture d'ajustement de stock
        
        Args:
            adjustment_id: ID de l'ajustement
            amount: Montant de l'ajustement
            adjustment_type: Type ('increase' ou 'decrease')
            description: Description de l'écriture
        """
        try:
            # Récupérer le journal des opérations diverses
            journal = Journal.query.filter_by(journal_type=JournalType.OPERATIONS_DIVERSES, is_active=True).first()
            if not journal:
                raise ValueError("Journal des opérations diverses (OD) non trouvé ou inactif")
            
            # Comptes comptables
            stock_account = Account.query.filter_by(code='300', is_active=True).first()  # Stocks de marchandises
            
            if adjustment_type == 'increase':
                # Augmentation de stock
                debit_account = stock_account
                credit_account = Account.query.filter_by(code='758', is_active=True).first()  # Produits divers
            else:
                # Diminution de stock
                debit_account = Account.query.filter_by(code='658', is_active=True).first()  # Charges diverses
                credit_account = stock_account
            
            if not debit_account:
                raise ValueError(f"Compte comptable débit ({'300' if adjustment_type == 'increase' else '658'}) non trouvé ou inactif")
            if not credit_account:
                raise ValueError(f"Compte comptable crédit ({'758' if adjustment_type == 'increase' else '300'}) non trouvé ou inactif")
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=date.today(),
                description=description or f"Ajustement stock #{adjustment_id}",
                reference=f"STK-{adjustment_id}",
                created_by_id=current_user.id if current_user.is_authenticated else 1
            )
            
            # Générer la référence
            entry.generate_reference()
            
            db.session.add(entry)
            db.session.flush()
            
            # Ligne de débit
            debit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=debit_account.id,
                debit_amount=amount,
                credit_amount=0,
                description=f"Ajustement stock {adjustment_type} #{adjustment_id}",
                line_number=1
            )
            
            # Ligne de crédit
            credit_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=credit_account.id,
                debit_amount=0,
                credit_amount=amount,
                description=f"Ajustement stock {adjustment_type} #{adjustment_id}",
                line_number=2
            )
            
            db.session.add(debit_line)
            db.session.add(credit_line)
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def create_payroll_entry(payroll_id, gross_salary, net_salary, description=None):
        """
        Créer une écriture de calcul de salaire (sans charges sociales automatiques)
        
        Args:
            payroll_id: ID du calcul de paie
            gross_salary: Salaire brut
            net_salary: Salaire net
            description: Description de l'écriture
        """
        try:
            # Récupérer le journal des opérations diverses
            journal = Journal.query.filter_by(journal_type=JournalType.OPERATIONS_DIVERSES, is_active=True).first()
            if not journal:
                raise ValueError("Journal des opérations diverses (OD) non trouvé ou inactif")
            
            # Comptes comptables
            salary_account = Account.query.filter_by(code='641', is_active=True).first()  # Rémunérations du personnel
            payable_account = Account.query.filter_by(code='421', is_active=True).first()  # Personnel - Rémunérations dues
            
            if not salary_account:
                raise ValueError("Compte Rémunérations du personnel (641) non trouvé ou inactif")
            if not payable_account:
                raise ValueError("Compte Personnel - Rémunérations dues (421) non trouvé ou inactif")
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=date.today(),
                description=description or f"Calcul salaire #{payroll_id}",
                reference=f"PAY-{payroll_id}",
                created_by_id=current_user.id if current_user.is_authenticated else 1
            )
            
            # Générer la référence
            entry.generate_reference()
            
            db.session.add(entry)
            db.session.flush()
            
            # Ligne 1: Débit Rémunérations du personnel (641)
            salary_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=salary_account.id,
                debit_amount=gross_salary,
                credit_amount=0,
                description=f"Salaire brut #{payroll_id}",
                line_number=1
            )
            
            # Ligne 2: Crédit Personnel - Rémunérations dues (421)
            payable_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=payable_account.id,
                debit_amount=0,
                credit_amount=net_salary,
                description=f"Salaire net à payer #{payroll_id}",
                line_number=2
            )
            
            db.session.add(salary_line)
            db.session.add(payable_line)
            
            # Valider automatiquement l'écriture de calcul de salaire
            entry.is_validated = True
            entry.validated_at = datetime.utcnow()
            entry.validated_by_id = current_user.id if current_user.is_authenticated else 1
            
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def create_salary_payment_entry(payroll_id, employee_id, net_salary, payment_method, description=None):
        """
        Créer une écriture de paiement de salaire
        
        Args:
            payroll_id: ID du calcul de paie
            employee_id: ID de l'employé
            net_salary: Salaire net à payer
            payment_method: Mode de paiement ('cash' ou 'bank')
            description: Description de l'écriture
        """
        try:
            # Récupérer le journal approprié
            if payment_method == 'cash':
                journal = Journal.query.filter_by(journal_type=JournalType.CAISSE, is_active=True).first()
                payment_account = Account.query.filter_by(code='530', is_active=True).first()  # Caisse
            else:  # bank
                journal = Journal.query.filter_by(journal_type=JournalType.BANQUE, is_active=True).first()
                payment_account = Account.query.filter_by(code='512', is_active=True).first()  # Banque
            
            if not journal:
                raise ValueError(f"Journal {payment_method} ({'CA' if payment_method == 'cash' else 'BQ'}) non trouvé ou inactif")
            
            # Comptes comptables
            payable_account = Account.query.filter_by(code='421', is_active=True).first()  # Personnel - Rémunérations dues
            
            if not payment_account:
                raise ValueError(f"Compte paiement ({'530' if payment_method == 'cash' else '512'}) non trouvé ou inactif")
            if not payable_account:
                raise ValueError("Compte Personnel - Rémunérations dues (421) non trouvé ou inactif")
            
            # Créer l'écriture
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=date.today(),
                description=description or f"Paiement salaire #{payroll_id} - Employé #{employee_id}",
                reference=f"PAY-{payroll_id}",
                created_by_id=current_user.id if current_user.is_authenticated else 1
            )
            
            # Générer la référence
            entry.generate_reference()
            
            db.session.add(entry)
            db.session.flush()
            
            # Ligne 1: Débit Personnel - Rémunérations dues (421)
            payable_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=payable_account.id,
                debit_amount=net_salary,
                credit_amount=0,
                description=f"Paiement salaire employé #{employee_id}",
                line_number=1
            )
            
            # Ligne 2: Crédit Caisse/Banque (530/512)
            payment_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=payment_account.id,
                debit_amount=0,
                credit_amount=net_salary,
                description=f"Paiement par {payment_method} - Employé #{employee_id}",
                line_number=2
            )
            
            db.session.add(payable_line)
            db.session.add(payment_line)
            
            # Valider automatiquement l'écriture de paiement de salaire
            entry.is_validated = True
            entry.validated_at = datetime.utcnow()
            entry.validated_by_id = current_user.id if current_user.is_authenticated else 1
            
            db.session.commit()
            
            return entry
            
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def validate_payroll_entries():
        """
        Valider toutes les écritures de salaires en statut brouillon
        et les lier aux PayrollCalculation correspondants
        """
        try:
            from app.employees.models import PayrollCalculation
            
            # Rechercher toutes les écritures de salaires non validées
            payroll_entries = JournalEntry.query.filter(
                JournalEntry.description.like('%Calcul salaire%'),
                JournalEntry.is_validated == False
            ).all()
            
            payment_entries = JournalEntry.query.filter(
                JournalEntry.description.like('%Paiement salaire%'),
                JournalEntry.is_validated == False
            ).all()
            
            validated_count = 0
            
            # Valider les écritures de calcul
            for entry in payroll_entries:
                entry.is_validated = True
                entry.validated_at = datetime.utcnow()
                entry.validated_by_id = current_user.id if current_user and current_user.is_authenticated else 1
                validated_count += 1
                
                # Essayer de lier à un PayrollCalculation
                if 'PAY-' in entry.reference:
                    payroll_id = entry.reference.replace('PAY-', '')
                    try:
                        payroll = PayrollCalculation.query.get(int(payroll_id))
                        if payroll and not payroll.payroll_entry_id:
                            payroll.payroll_entry_id = entry.id
                    except (ValueError, TypeError):
                        pass
            
            # Valider les écritures de paiement
            for entry in payment_entries:
                entry.is_validated = True
                entry.validated_at = datetime.utcnow()
                entry.validated_by_id = current_user.id if current_user and current_user.is_authenticated else 1
                validated_count += 1
                
                # Essayer de lier à un PayrollCalculation
                if 'PAY-' in entry.reference:
                    payroll_id = entry.reference.replace('PAY-', '')
                    try:
                        payroll = PayrollCalculation.query.get(int(payroll_id))
                        if payroll and not payroll.payment_entry_id:
                            payroll.payment_entry_id = entry.id
                    except (ValueError, TypeError):
                        pass
            
            db.session.commit()
            return validated_count
            
        except Exception as e:
            db.session.rollback()
            raise e

class DashboardService:
    """Service pour calculer les KPIs du dashboard comptabilité"""
    
    @staticmethod
    def get_daily_revenue(target_date=None):
        """Calculer le CA du jour"""
        if target_date is None:
            target_date = date.today()
        
        # Récupérer les ventes du jour depuis les écritures comptables
        from .models import Account, JournalEntryLine, JournalEntry
        
        # Compte 701 - Ventes de marchandises
        sales_account = Account.query.filter_by(code='701').first()
        if not sales_account:
            return 0
        
        # Calculer les ventes du jour
        daily_sales = db.session.query(func.sum(JournalEntryLine.credit_amount))\
            .join(JournalEntry)\
            .filter(JournalEntryLine.account_id == sales_account.id)\
            .filter(JournalEntry.entry_date == target_date)\
            .scalar() or 0
        
        return float(daily_sales)
    
    @staticmethod
    def get_monthly_revenue(year=None, month=None):
        """Calculer le CA du mois"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        from .models import Account, JournalEntryLine, JournalEntry
        
        # Compte 701 - Ventes de marchandises
        sales_account = Account.query.filter_by(code='701').first()
        if not sales_account:
            return 0
        
        # Premier et dernier jour du mois
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Calculer les ventes du mois
        monthly_sales = db.session.query(func.sum(JournalEntryLine.credit_amount))\
            .join(JournalEntry)\
            .filter(JournalEntryLine.account_id == sales_account.id)\
            .filter(JournalEntry.entry_date >= first_day)\
            .filter(JournalEntry.entry_date <= last_day)\
            .scalar() or 0
        
        return float(monthly_sales)
    
    @staticmethod
    def get_monthly_expenses(year=None, month=None):
        """Calculer les charges du mois"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        from .models import Account, JournalEntryLine, JournalEntry
        
        # Premier et dernier jour du mois
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Récupérer tous les comptes de charges (classe 6)
        expense_accounts = Account.query.filter(Account.code.startswith('6')).all()
        
        total_expenses = 0
        for account in expense_accounts:
            monthly_expense = db.session.query(func.sum(JournalEntryLine.debit_amount))\
                .join(JournalEntry)\
                .filter(JournalEntryLine.account_id == account.id)\
                .filter(JournalEntry.entry_date >= first_day)\
                .filter(JournalEntry.entry_date <= last_day)\
                .scalar() or 0
            total_expenses += float(monthly_expense)
        
        return total_expenses
    
    @staticmethod
    def get_cash_balance():
        """Calculer le solde de caisse actuel en temps réel"""
        from app.sales.models import CashRegisterSession, CashMovement
        
        # Récupérer la session de caisse ouverte
        session = CashRegisterSession.query.filter_by(is_open=True).first()
        if not session:
            return 0
        
        # Calculer le solde : fond initial + entrées - sorties
        total_entrees = sum(m.amount for m in session.movements if m.type == 'entrée')
        total_sorties = sum(m.amount for m in session.movements if m.type == 'sortie')
        
        solde_caisse = session.initial_amount + total_entrees - total_sorties
        return float(solde_caisse)
    
    @staticmethod
    def get_bank_balance():
        """Calculer le solde bancaire actuel en temps réel"""
        from app.accounting.models import Account, JournalEntryLine, JournalEntry
        
        # Récupérer le compte banque (512)
        bank_account = Account.query.filter_by(code='512').first()
        if not bank_account:
            return 0
        
        # Calculer le solde depuis les écritures comptables
        # Débits (augmentations) - Crédits (diminutions)
        total_debits = db.session.query(func.sum(JournalEntryLine.debit_amount))\
            .join(JournalEntry)\
            .filter(JournalEntryLine.account_id == bank_account.id)\
            .scalar() or 0
        
        total_credits = db.session.query(func.sum(JournalEntryLine.credit_amount))\
            .join(JournalEntry)\
            .filter(JournalEntryLine.account_id == bank_account.id)\
            .scalar() or 0
        
        solde_banque = float(total_debits) - float(total_credits)
        return solde_banque
    
    @staticmethod
    def get_daily_revenue_trend(days=30):
        """Obtenir l'évolution du CA sur X jours"""
        from .models import Account, JournalEntryLine, JournalEntry
        
        sales_account = Account.query.filter_by(code='701').first()
        if not sales_account:
            return []
        
        trend_data = []
        today = date.today()
        
        for i in range(days):
            target_date = today - timedelta(days=i)
            daily_sales = db.session.query(func.sum(JournalEntryLine.credit_amount))\
                .join(JournalEntry)\
                .filter(JournalEntryLine.account_id == sales_account.id)\
                .filter(JournalEntry.entry_date == target_date)\
                .scalar() or 0
            
            trend_data.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'revenue': float(daily_sales)
            })
        
        return list(reversed(trend_data))  # Plus ancien au plus récent
    
    @staticmethod
    def get_expense_breakdown(year=None, month=None):
        """Répartition des charges par catégorie"""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        from .models import Account, JournalEntryLine, JournalEntry
        
        # Premier et dernier jour du mois
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Catégories d'expenses principales
        expense_categories = {
            'Achats': ['601', '602', '606'],  # Matières premières, emballages, fournitures
            'Personnel': ['641', '645'],      # Salaires, charges sociales
            'Services': ['613', '615', '627'], # Loyers, entretien, services bancaires
            'Autres': ['658', '681']          # Charges diverses, amortissements
        }
        
        breakdown = []
        total_expenses = 0
        
        for category, account_codes in expense_categories.items():
            category_total = 0
            
            for code in account_codes:
                account = Account.query.filter_by(code=code).first()
                if account:
                    amount = db.session.query(func.sum(JournalEntryLine.debit_amount))\
                        .join(JournalEntry)\
                        .filter(JournalEntryLine.account_id == account.id)\
                        .filter(JournalEntry.entry_date >= first_day)\
                        .filter(JournalEntry.entry_date <= last_day)\
                        .scalar() or 0
                    category_total += float(amount)
            
            if category_total > 0:
                breakdown.append({
                    'category': category,
                    'amount': category_total
                })
                total_expenses += category_total
        
        # Calculer les pourcentages
        for item in breakdown:
            item['percentage'] = (item['amount'] / total_expenses * 100) if total_expenses > 0 else 0
        
        return breakdown
    
    @staticmethod
    def get_recent_transactions(limit=10):
        """Obtenir les dernières transactions"""
        from .models import JournalEntry, JournalEntryLine
        
        recent_entries = JournalEntry.query\
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())\
            .limit(limit).all()
        
        transactions = []
        for entry in recent_entries:
            # Calculer le montant total (on prend le total des débits ou crédits, le plus grand)
            total_amount = max(entry.total_debit, entry.total_credit)
            
            transactions.append({
                'date': entry.entry_date,
                'reference': entry.reference,
                'description': entry.description,
                'amount': float(total_amount),
                'type': 'Crédit' if entry.total_credit > entry.total_debit else 'Débit'
            })
        
        return transactions
    
    @staticmethod
    def calculate_ratios(monthly_revenue, monthly_expenses, monthly_purchases=None):
        """Calculer les ratios financiers clés"""
        ratios = {}
        
        # Marge brute (approximation si pas de données détaillées)
        if monthly_purchases is None:
            # Estimer les achats à partir du compte 601
            from .models import Account, JournalEntryLine, JournalEntry
            purchases_account = Account.query.filter_by(code='601').first()
            if purchases_account:
                today = date.today()
                first_day = date(today.year, today.month, 1)
                if today.month == 12:
                    last_day = date(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
                
                monthly_purchases = db.session.query(func.sum(JournalEntryLine.debit_amount))\
                    .join(JournalEntry)\
                    .filter(JournalEntryLine.account_id == purchases_account.id)\
                    .filter(JournalEntry.entry_date >= first_day)\
                    .filter(JournalEntry.entry_date <= last_day)\
                    .scalar() or 0
                monthly_purchases = float(monthly_purchases)
            else:
                monthly_purchases = 0
        
        # Calcul des ratios
        if monthly_revenue > 0:
            ratios['marge_brute'] = ((monthly_revenue - monthly_purchases) / monthly_revenue) * 100
            ratios['ratio_charges'] = (monthly_expenses / monthly_revenue) * 100
        else:
            ratios['marge_brute'] = 0
            ratios['ratio_charges'] = 0
        
        # Point mort (seuil de rentabilité)
        ratios['seuil_rentabilite'] = monthly_expenses
        ratios['progression_seuil'] = (monthly_revenue / monthly_expenses * 100) if monthly_expenses > 0 else 0
        
        return ratios 